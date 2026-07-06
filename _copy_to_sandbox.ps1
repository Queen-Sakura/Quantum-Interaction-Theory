$unc = "\\121.41.213.128\ArgoShare\EE2Victory"
$dstDir = "D:\Games\胜利测试\Empire Earth II"

# Find the source directory
$dirs = Get-ChildItem $unc -Directory
$srcDir = $dirs | Where-Object { $_.Name -match "地球帝国2" } | Select-Object -First 1
if (-not $srcDir) { Write-Host "找不到源目录"; exit 1 }

$srcPath = Join-Path $srcDir.FullName "Empire Earth II"
Write-Host "SRC: $srcPath"

$srcZip = Join-Path $srcPath "zips_ee2x\EE2X_db.zip"
$srcCfg = Join-Path $srcPath "UnofficialVersionConfig.txt"

if (Test-Path $srcZip) {
    $dstZip = "$dstDir\zips_ee2x\EE2X_db.zip"
    Copy-Item $srcZip $dstZip -Force
    Write-Host "OK ZIP: $((Get-Item $dstZip).Length) B"
} else { Write-Host "MISSING ZIP" }

if (Test-Path $srcCfg) {
    $dstCfg = "$dstDir\UnofficialVersionConfig.txt"
    Copy-Item $srcCfg $dstCfg -Force
    Write-Host "OK CFG: $((Get-Item $dstCfg).Length) B"
} else { Write-Host "MISSING CFG" }
