# Build a 600x900 portrait (library_600x900.jpg) from a game's cached hero (1600x1200) + header (460x215), for games
# whose Steam cache has no portrait capsule. Usage: make_portrait.ps1 <src dir>
param([string]$dir)
Add-Type -AssemblyName System.Drawing
$hero = [Drawing.Image]::FromFile((Join-Path $dir 'library_hero.jpg'))
$head = [Drawing.Image]::FromFile((Join-Path $dir 'header.jpg'))
$bmp = New-Object Drawing.Bitmap 600, 900
$g = [Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = 'HighQualityBicubic'; $g.SmoothingMode = 'AntiAlias'
# cover-fit the hero into 600x900 (crop the sides)
$s = [Math]::Max(600 / $hero.Width, 900 / $hero.Height)
$w = $hero.Width * $s; $h = $hero.Height * $s
$g.DrawImage($hero, (600 - $w) / 2, (900 - $h) / 2, $w, $h)
# header art across the top as the title, with a soft dark band behind it
$hw = 560; $hh = [int]($head.Height * $hw / $head.Width)
$band = New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(150, 0, 0, 0))
$g.FillRectangle($band, 0, 0, 600, $hh + 40)
$g.DrawImage($head, 20, 20, $hw, $hh)
$out = Join-Path $dir 'library_600x900.jpg'
$bmp.Save($out, [Drawing.Imaging.ImageFormat]::Jpeg)
$g.Dispose(); $bmp.Dispose(); $hero.Dispose(); $head.Dispose()
"wrote $out"
