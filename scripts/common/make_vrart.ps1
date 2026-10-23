# Builds Steam library art with the red VR label for the Steam Frame's VR entries.
# Input:  src\<base appid>\...\{library_600x900,library_capsule,header,library_header,library_hero}.jpg, logo.png
# Output: out\<target id>p.png (portrait), <id>.png (wide), <id>_hero.png, <id>_logo.png (shortcuts only)
Add-Type -AssemblyName System.Drawing
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$src = Join-Path $root 'src'; $out = Join-Path $root 'out'
New-Item -ItemType Directory -Force $out | Out-Null

function Find-Art($base, [string[]]$names) {
    foreach ($n in $names) {
        $f = Get-ChildItem -Recurse -File (Join-Path $src $base) | Where-Object { $_.Name -eq $n } | Select-Object -First 1
        if ($f) { return $f.FullName }
    }
    return $null
}

function New-Canvas($path, $w, $h) {
    $img = [System.Drawing.Image]::FromFile($path)
    $bmp = New-Object System.Drawing.Bitmap $w, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = 'HighQualityBicubic'; $g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'
    # cover-fit
    $s = [Math]::Max($w / $img.Width, $h / $img.Height)
    $dw = $img.Width * $s; $dh = $img.Height * $s
    $g.DrawImage($img, ($w - $dw) / 2, ($h - $dh) / 2, $dw, $dh)
    $img.Dispose()
    return @($bmp, $g)
}

function Add-Pill($g, $w, $cy, $text, $fontPx) {
    $font = New-Object System.Drawing.Font('Arial', $fontPx, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $sz = $g.MeasureString($text, $font)
    $ph = [int]($fontPx * 1.6); $pw = [int]($sz.Width + $fontPx * 1.3)
    $x = [int](($w - $pw) / 2); $y = [int]($cy - $ph / 2); $r = [int]($ph * 0.28)
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.AddArc($x, $y, 2 * $r, 2 * $r, 180, 90); $path.AddArc($x + $pw - 2 * $r, $y, 2 * $r, 2 * $r, 270, 90)
    $path.AddArc($x + $pw - 2 * $r, $y + $ph - 2 * $r, 2 * $r, 2 * $r, 0, 90); $path.AddArc($x, $y + $ph - 2 * $r, 2 * $r, 2 * $r, 90, 90)
    $path.CloseFigure()
    $shadow = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(120, 0, 0, 0))
    $g.TranslateTransform(0, [int]($fontPx * 0.12)); $g.FillPath($shadow, $path); $g.ResetTransform()
    $g.FillPath((New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 204, 18, 24))), $path)
    $fmt = New-Object System.Drawing.StringFormat; $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
    $g.DrawString($text, $font, [System.Drawing.Brushes]::White, (New-Object System.Drawing.RectangleF($x, ($y + 1), $pw, $ph)), $fmt)
}

function Add-Title($g, $w, $cy, $text, $fontPx) {
    $font = New-Object System.Drawing.FontFamily('Arial')
    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $fmt = New-Object System.Drawing.StringFormat; $fmt.Alignment = 'Center'; $fmt.LineAlignment = 'Center'
    $path.AddString($text, $font, [int][System.Drawing.FontStyle]::Bold, $fontPx, (New-Object System.Drawing.RectangleF(0, ($cy - $fontPx), $w, ($fontPx * 2))), $fmt)
    $pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::Black), ($fontPx * 0.12); $pen.LineJoin = 'Round'
    $g.DrawPath($pen, $path); $g.FillPath([System.Drawing.Brushes]::White, $path)
}

function Save($bmp, $g, $name) { $g.Dispose(); $bmp.Save((Join-Path $out $name), [System.Drawing.Imaging.ImageFormat]::Png); $bmp.Dispose() }

# target id, base appid, label, optional title, shortcut? (shortcuts also get hero + logo)
$jobs = @(
    @(2813758474, 2310,    'QUAKE VR',      '',           $true),
    @(2316100907, 2310,    'QUAKE VR',      'TEAM BEEF',  $true),
    @(3255137504, 9010,    'RTCW VR',       '',           $true),
    @(3063768737, 1592280, 'SELACO VR',     '',           $true),
    @(3173477041, 2320,    'QUAKE II VR',   '',           $true),
    @(4045669378, 3730,    'AVP VR',        '',           $true),
    @(3138655638, 208200,  'DOOM 3 VR',     '',           $true),
    @(2341077394, 21090,   'F.E.A.R. VR',   '',           $true),
    @(4268466633, 3286930, 'GZDOOM VR',     'HERETIC',    $true),
    @(2541150700, 3286930, 'GZDOOM VR',     'HEXEN',      $true),
    @(2150730901, 3286930, 'GZDOOM VR',     'DEATHKINGS', $true),
    @(3668573126, 2200,    'QUAKE III VR',  '',           $true),
    @(3975090014, 519860,  'DUSK HD VR',    '',           $true),
    @(3229493339, 550,     'L4D2 VR',       '',           $true),
    @(4037750409, 620,     'PORTAL 2 VR',   '',           $true),
    @(3641501148, 622650,  'BENDY VR',      '',           $true),
    @(238010,     238010,  'DEUS EX VR',    '',           $false),
    @(287700,     287700,  'MGS V VR',      '',           $false),
    @(12150,      12150,   'MAX PAYNE 2 VR','',           $false)
)
foreach ($j in $jobs) {
    $id, $base, $label, $title, $isShortcut = $j
    $portrait = Find-Art $base @('library_600x900.jpg', 'library_capsule.jpg')
    $wide = Find-Art $base @('header.jpg', 'library_header.jpg')
    $hero = Find-Art $base @('library_hero.jpg')
    $logo = Find-Art $base @('logo.png')
    if ($portrait) {
        $bmp, $g = New-Canvas $portrait 600 900
        if ($title) { Add-Pill $g 600 690 $label 38; Add-Title $g 600 800 $title 92 } else { Add-Pill $g 600 820 $label 42 }
        Save $bmp $g "${id}p.png"
    } else { Write-Warning "$id no portrait" }
    if ($wide) {
        $bmp, $g = New-Canvas $wide 920 430
        if ($title) { Add-Pill $g 920 300 $label 34; Add-Title $g 920 375 $title 58 } else { Add-Pill $g 920 370 $label 38 }
        Save $bmp $g "${id}.png"
    } else { Write-Warning "$id no wide" }
    if ($isShortcut) {
        if ($hero) { $bmp, $g = New-Canvas $hero 1920 620; Save $bmp $g "${id}_hero.png" }
        if ($logo) { Copy-Item -Force $logo (Join-Path $out "${id}_logo.png") }
    }
    "$id $label $title"
}
