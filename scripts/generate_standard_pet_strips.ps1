Add-Type -AssemblyName System.Drawing

$srcPath = "C:\Users\zhaichong\.gemini\antigravity\brain\5715eb46-9691-4787-ac56-9bf331a0f860\.user_uploaded\media_1786084679924.png"
$rawBmp = [System.Drawing.Bitmap]::FromFile($srcPath)
$outDir = "d:\build\zbuild\public\pet"
if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

# 1. Clean background: remove pure white background (#FFFFFF -> transparent)
$cleanBmp = New-Object System.Drawing.Bitmap $rawBmp.Width, $rawBmp.Height
for ($x = 0; $x -lt $rawBmp.Width; $x++) {
    for ($y = 0; $y -lt $rawBmp.Height; $y++) {
        $c = $rawBmp.GetPixel($x, $y)
        # Background is white/light gray (threshold > 235)
        if ($c.R -gt 235 -and $c.G -gt 235 -and $c.B -gt 235) {
            $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
        } else {
            $cleanBmp.SetPixel($x, $y, $c)
        }
    }
}

# Erase text labels on left side
for ($x = 0; $x -lt 250; $x++) {
    for ($y = 0; $y -lt 28; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 145; $y -lt 170; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 280; $y -lt 305; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 420; $y -lt 445; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
}

# Standard dimensions for each frame in the sprite sheet:
# Width = 64px, Height = 74px (Fits perfectly in the 64px x 74px mascot box!)
$FRAME_W = 64
$FRAME_H = 74
$SCALE = 0.64 # 115px * 0.64 = ~73.6px height

function Build-Normalized-Strip($rowName, $yTop, $yBottom) {
    # Find segments
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
            if (($x - $segStart) -gt 25) {
                $segments += ,@($segStart, $x)
            }
        }
    }
    if ($inSeg -and (($cleanBmp.Width - $segStart) -gt 25)) {
        $segments += ,@($segStart, $cleanBmp.Width)
    }

    $frameCount = $segments.Count
    Write-Output "[$rowName] Found $frameCount frames."

    $stripW = $FRAME_W * $frameCount
    $stripBmp = New-Object System.Drawing.Bitmap $stripW, $FRAME_H
    $g = [System.Drawing.Graphics]::FromImage($stripBmp)
    # Use Nearest Neighbor to keep pixel art super sharp without blur
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::None

    $idx = 0
    foreach ($seg in $segments) {
        $x1 = $seg[0]
        $x2 = $seg[1]

        # Find tight bounding box of this character
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

        # Center in $FRAME_W x $FRAME_H canvas, anchored at bottom (padding 2px from bottom)
        $destX = [Math]::Floor(($FRAME_W - $destW) / 2) + ($idx * $FRAME_W)
        $destY = $FRAME_H - $destH - 2

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

Build-Normalized-Strip "idle" 25 142
Build-Normalized-Strip "walk" 165 278
Build-Normalized-Strip "wave" 300 415
Build-Normalized-Strip "gestures" 440 555

$rawBmp.Dispose()
$cleanBmp.Dispose()
Write-Output "Standardized strips generated successfully!"
