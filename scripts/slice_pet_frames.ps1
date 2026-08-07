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
        # Background is white/light gray
        if ($c.R -gt 240 -and $c.G -gt 240 -and $c.B -gt 240) {
            $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
        } else {
            $cleanBmp.SetPixel($x, $y, $c)
        }
    }
}

# Also erase text labels:
# Text labels are at:
# Y=0 to 25 ("IDLE (6 frames)")
# Y=145 to 165 ("WALK (6 frames)")
# Y=280 to 300 ("WAVE (4 frames)")
# Y=420 to 440 ("GESTURES (6 frames)")
for ($x = 0; $x -lt 250; $x++) {
    for ($y = 0; $y -lt 25; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 145; $y -lt 165; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 280; $y -lt 300; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
    for ($y = 420; $y -lt 440; $y++) { $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0)) }
}

$cleanBmp.Save("$outDir\spritesheet_clean.png", [System.Drawing.Imaging.ImageFormat]::Png)

# Let's define the 4 rows precisely
# Row 1 IDLE: Y from 25 to 142
# Row 2 WALK: Y from 165 to 278
# Row 3 WAVE: Y from 300 to 415
# Row 4 GESTURES: Y from 440 to 555

$CANVAS_W = 90
$CANVAS_H = 120

function Build-Strip($rowName, $yTop, $yBottom) {
    $subDir = "$outDir\$rowName"
    if (!(Test-Path $subDir)) { New-Item -ItemType Directory -Path $subDir -Force | Out-Null }

    # Find character segments in this Y band
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

    Write-Output "[$rowName] Found $($segments.Count) frames."

    # Create strip bitmap
    $stripW = $CANVAS_W * $segments.Count
    $stripBmp = New-Object System.Drawing.Bitmap $stripW, $CANVAS_H
    $stripG = [System.Drawing.Graphics]::FromImage($stripBmp)
    $stripG.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
    $stripG.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half

    $idx = 0
    foreach ($seg in $segments) {
        $x1 = $seg[0]
        $x2 = $seg[1]
        
        # Calculate character tight bounds
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

        # Center on CANVAS_W x CANVAS_H, anchored at bottom
        $offsetX = [Math]::Floor(($CANVAS_W - $charW) / 2)
        $offsetY = $CANVAS_H - $charH - 4 # 4px bottom padding

        # 1. Save single frame
        $frameBmp = New-Object System.Drawing.Bitmap $CANVAS_W, $CANVAS_H
        $fg = [System.Drawing.Graphics]::FromImage($frameBmp)
        $fg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
        $srcRect = New-Object System.Drawing.Rectangle $minX, $minY, $charW, $charH
        $destRect = New-Object System.Drawing.Rectangle $offsetX, $offsetY, $charW, $charH
        $fg.DrawImage($cleanBmp, $destRect, $srcRect, [System.Drawing.GraphicsUnit]::Pixel)
        $fg.Dispose()

        $frameBmp.Save("$subDir\frame_$idx.png", [System.Drawing.Imaging.ImageFormat]::Png)
        $frameBmp.Dispose()

        # 2. Draw onto strip
        $stripDestRect = New-Object System.Drawing.Rectangle ($idx * $CANVAS_W + $offsetX), $offsetY, $charW, $charH
        $stripG.DrawImage($cleanBmp, $stripDestRect, $srcRect, [System.Drawing.GraphicsUnit]::Pixel)

        $idx++
    }

    $stripG.Dispose()
    $stripBmp.Save("$outDir\anim_$rowName.png", [System.Drawing.Imaging.ImageFormat]::Png)
    $stripBmp.Dispose()
    Write-Output "[$rowName] Created strip $outDir\anim_$rowName.png ($stripW x $CANVAS_H)"
}

Build-Strip "idle" 25 142
Build-Strip "walk" 165 278
Build-Strip "wave" 300 415
Build-Strip "gestures" 440 555

$rawBmp.Dispose()
$cleanBmp.Dispose()
Write-Output "All pet animation strips generated successfully!"
