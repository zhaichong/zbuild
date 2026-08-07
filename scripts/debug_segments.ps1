Add-Type -AssemblyName System.Drawing
$srcPath = "C:\Users\zhaichong\.gemini\antigravity\brain\5715eb46-9691-4787-ac56-9bf331a0f860\.user_uploaded\media_1786084679924.png"
$rawBmp = [System.Drawing.Bitmap]::FromFile($srcPath)

$cleanBmp = New-Object System.Drawing.Bitmap $rawBmp.Width, $rawBmp.Height
for ($x = 0; $x -lt $rawBmp.Width; $x++) {
    for ($y = 0; $y -lt $rawBmp.Height; $y++) {
        $c = $rawBmp.GetPixel($x, $y)
        if ($c.R -gt 235 -and $c.G -gt 235 -and $c.B -gt 235) {
            $cleanBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 0, 0, 0))
        } else {
            $cleanBmp.SetPixel($x, $y, $c)
        }
    }
}

function Check-Row($name, $yTop, $yBottom) {
    Write-Output "=== $name (y=$yTop..$yBottom) ==="
    $colHas = @()
    for ($x = 0; $x -lt $cleanBmp.Width; $x++) {
        $has = $false
        for ($y = $yTop; $y -le $yBottom; $y++) {
            $c = $cleanBmp.GetPixel($x, $y)
            if ($c.A -gt 100) { $has = $true; break }
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

    $f = 0
    foreach ($seg in $segments) {
        $x1 = $seg[0]; $x2 = $seg[1]
        $minY = $yBottom; $maxY = $yTop; $minX = $x2; $maxX = $x1
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
        $w = $maxX - $minX + 1
        $h = $maxY - $minY + 1
        Write-Output ("Frame " + $f + ": x=" + $minX + ".." + $maxX + " (w=" + $w + "), y=" + $minY + ".." + $maxY + " (h=" + $h + ")")
        $f++
    }
}

Check-Row "idle" 20 140
Check-Row "walk" 155 280
Check-Row "wave" 295 418
Check-Row "gestures" 436 556

$rawBmp.Dispose()
$cleanBmp.Dispose()
