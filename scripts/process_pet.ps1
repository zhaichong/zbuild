Add-Type -AssemblyName System.Drawing

$srcPath = "C:\Users\zhaichong\.gemini\antigravity\brain\5715eb46-9691-4787-ac56-9bf331a0f860\.user_uploaded\media_1786084679924.png"
$outDir = "d:\build\zbuild\public\pet"
if (!(Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

$bmp = [System.Drawing.Bitmap]::FromFile($srcPath)
Write-Output "Image Size: $($bmp.Width) x $($bmp.Height)"

# Copy raw spritesheet
$bmp.Save("$outDir\spritesheet_raw.png", [System.Drawing.Imaging.ImageFormat]::Png)

# Let's create a transparent version (convert pure white #FFFFFF background to transparent)
$transparentBmp = New-Object System.Drawing.Bitmap $bmp.Width, $bmp.Height
for ($x = 0; $x -lt $bmp.Width; $x++) {
    for ($y = 0; $y -lt $bmp.Height; $y++) {
        $c = $bmp.GetPixel($x, $y)
        # If color is white or nearly white background, set to transparent
        if ($c.R -gt 245 -and $c.G -gt 245 -and $c.B -gt 245) {
            $transparentBmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb(0, 255, 255, 255))
        } else {
            $transparentBmp.SetPixel($x, $y, $c)
        }
    }
}
$transparentBmp.Save("$outDir\spritesheet_trans.png", [System.Drawing.Imaging.ImageFormat]::Png)

Write-Output "Saved transparent spritesheet to $outDir\spritesheet_trans.png"

$bmp.Dispose()
$transparentBmp.Dispose()
