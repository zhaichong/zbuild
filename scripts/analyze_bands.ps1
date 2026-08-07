Add-Type -AssemblyName System.Drawing
$srcPath = "C:\Users\zhaichong\.gemini\antigravity\brain\5715eb46-9691-4787-ac56-9bf331a0f860\.user_uploaded\media_1786084679924.png"
$bmp = [System.Drawing.Bitmap]::FromFile($srcPath)
Write-Output "Image Size: $($bmp.Width) x $($bmp.Height)"

$rowCounts = @()
for ($y = 0; $y -lt $bmp.Height; $y++) {
    $nonWhite = 0
    for ($x = 0; $x -lt $bmp.Width; $x++) {
        $c = $bmp.GetPixel($x, $y)
        if ($c.R -lt 235 -or $c.G -lt 235 -or $c.B -lt 235) {
            $nonWhite++
        }
    }
    $rowCounts += $nonWhite
}

$inBand = $false
$start = 0
for ($y = 0; $y -lt $bmp.Height; $y++) {
    if ($rowCounts[$y] -gt 20 -and -not $inBand) {
        $inBand = $true
        $start = $y
    } elseif ($rowCounts[$y] -le 20 -and $inBand) {
        $inBand = $false
        Write-Output "Band: y=$start to $y (Height=$($y - $start))"
    }
}
if ($inBand) {
    Write-Output "Band: y=$start to $($bmp.Height)"
}
$bmp.Dispose()
