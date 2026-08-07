Add-Type -AssemblyName System.Drawing

$srcPath = "C:\Users\zhaichong\.gemini\antigravity\brain\5715eb46-9691-4787-ac56-9bf331a0f860\.user_uploaded\media_1786084679924.png"
$rawBmp = [System.Drawing.Bitmap]::FromFile($srcPath)
$outDir = "d:\build\zbuild\public\pet"
if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

# 1. Clean background & text labels
$cleanBmp = New-Object System.Drawing.Bitmap $rawBmp.Width, $rawBmp.Height
for ($x = 0; $x -lt $rawBmp.Width; $x++) {
    for ($y = 0; $y -lt $rawBmp.Height; $y++) {
        $c = $rawBmp.GetPixel($x, $y)
        # Background is white/light gray (threshold > 230)
        if ($c.R -gt 230 -and $c.G -gt 230 -and $c.B -gt 230) {
            $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
        } else {
            $cleanBmp.SetPixel($x, $y, $c)
        }
    }
}

# Erase label text rows cleanly
for ($x = 0; $x -lt $rawBmp.Width; $x++) {
    for ($y = 0; $y -lt 25; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 137; $y -le 158; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 278; $y -le 297; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 414; $y -le 435; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
}

# Standard dimensions for each frame:
$FRAME_W = 72
$FRAME_H = 80
$SCALE = 0.58
$BASELINE_PADDING_BOTTOM = 3 # 3px from bottom

function Build-Perfect-Strip($rowName, $yTop, $yBottom, $rowBaselineY) {
    $colHas = @()
    for ($x = 0; $x -lt $cleanBmp.Width; $x++) {
        $has = $false
        for ($y = $yTop; $y -le $yBottom; $y++) {
            $c = $cleanBmp.GetPixel($x, $y)
            if ($c.A -gt 100) {
                $has = $true
                break
            }
        }
        $colHas += $has
    }

    $segments = @()
    $inSeg = $false
    $segStart = 0
    for ($x = 0; $x -lt $cleanBmp.Width; $x++) {
        if ($colHas[$x] -and -not $inSeg) {
            $inSeg = $true
            $segStart = $x
        } elseif (-not $colHas[$x] -and $inSeg) {
            $inSeg = $false
            if (($x - $segStart) -gt 20) {
                $segments += ,@($segStart, $x)
            }
        }
    }
    if ($inSeg -and (($cleanBmp.Width - $segStart) -gt 20)) {
        $segments += ,@($segStart, $cleanBmp.Width)
    }

    $frameCount = $segments.Count
    Write-Output "[$rowName] Found $frameCount frames."

    $stripW = $FRAME_W * $frameCount
    $stripBmp = New-Object System.Drawing.Bitmap $stripW, $FRAME_H
    $g = [System.Drawing.Graphics]::FromImage($stripBmp)
    # High-quality pixel art rendering (Nearest Neighbor preserves sharp pixels)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None

    $idx = 0
    foreach ($seg in $segments) {
        $x1 = $seg[0]
        $x2 = $seg[1]

        # Find tight bounding box
        $minY = $yBottom; $maxY = $yTop
        $minX = $x2; $maxX = $x1
        for ($px = $x1; $px -lt $x2; $px++) {
            for ($py = $yTop; $py -le $yBottom; $py++) {
                $c = $cleanBmp.GetPixel($px, $py)
                if ($c.A -gt 100) {
                    if ($py -lt $minY) { $minY = $py }
                    if ($py -gt $maxY) { $maxY = $py }
                    if ($px -lt $minX) { $minX = $px }
                    if ($px -gt $maxX) { $maxX = $px }
                }
            }
        }

        $charW = $maxX - $minX + 1
        $charH = $maxY - $minY + 1

        # Target scaled size
        $destW = [Math]::Round($charW * $SCALE)
        $destH = [Math]::Round($charH * $SCALE)

        # Center horizontally in $FRAME_W
        $destX = [Math]::Floor(($FRAME_W - $destW) / 2) + ($idx * $FRAME_W)
        
        # Ground to row baseline for natural walking/standing animation
        $bottomDiff = ($rowBaselineY - $maxY) * $SCALE
        $destY = [Math]::Round($FRAME_H - $destH - $BASELINE_PADDING_BOTTOM - $bottomDiff)
        if ($destY -lt 1) { $destY = 1 }

        $srcRect = New-Object System.Drawing.Rectangle $minX, $minY, $charW, $charH
        $destRect = New-Object System.Drawing.Rectangle $destX, $destY, $destW, $destH

        $g.DrawImage($cleanBmp, $destRect, $srcRect, [System.Drawing.GraphicsUnit]::Pixel)
        $idx++
    }

    $g.Dispose()
    $stripBmp.Save("$outDir\anim_$rowName.png", [System.Drawing.Imaging.ImageFormat]::Png)
    $stripBmp.Dispose()
    Write-Output "[$rowName] Saved $outDir\anim_$rowName.png ($stripW x $FRAME_H, $frameCount frames @ ${FRAME_W}x${FRAME_H})"
}

# Full row ranges and foot baseline coordinates:
Build-Perfect-Strip "idle" 25 137 136
Build-Perfect-Strip "walk" 159 278 277
Build-Perfect-Strip "wave" 298 414 413
Build-Perfect-Strip "gestures" 436 555 554

$rawBmp.Dispose()
$cleanBmp.Dispose()
Write-Output "All perfect strips generated successfully!"
