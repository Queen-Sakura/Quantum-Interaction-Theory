# ============================================================================
# EE2 Test Helper v2.0 — 镜 (Windows) 端
# ============================================================================
# 用法:
#   .\ee2_test.ps1                    一键：复制 → 启动 → 提示写回
#   .\ee2_test.ps1 -SkipLaunch        仅复制，不启动（手动测试用）
#
# 协议:
#   真 → 镜: [BUILD] 时间 | 描述 | 修改文件
#   镜 → 真: [TEST] 时间 | 通过/崩溃/异常 | 具体现象
# ============================================================================

param(
    [string]$SourcePath  = "Z:\EE2Victory\地球帝国2胜利版测试\Empire Earth II",
    [string]$TestPath    = "D:\Games\EE2Test\Empire Earth II",
    [string]$DialogueBook = "Z:\ArgoShared\节点对话簿.md",
    [switch]$SkipLaunch
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗"
Write-Host "║  EE2 Test Helper v2.0 · 镜 (Windows)     ║"
Write-Host "║  $(Get-Date -Format 'yyyy-MM-dd HH:mm')                             ║"
Write-Host "╚══════════════════════════════════════════╝"
Write-Host ""

# ── Step 0: 检查前置条件 ────────────────────────────────────
if (-not (Test-Path $DialogueBook)) {
    Write-Host "❌ 找不到节点对话簿: $DialogueBook" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $SourcePath)) {
    Write-Host "❌ 源目录不存在: $SourcePath" -ForegroundColor Red
    exit 1
}

# ── Step 1: 读取最新 BUILD ──────────────────────────────────
$Dialogue = Get-Content $DialogueBook -Raw -Encoding UTF8
$BuildPattern = '## 真 → 镜 · BUILD · (.+?)$'
$BuildMatches = [regex]::Matches($Dialogue, $BuildPattern)

if ($BuildMatches.Count -eq 0) {
    Write-Host "📭 没有待测试的 BUILD" -ForegroundColor Yellow
    exit 0
}

$LastBuild = $BuildMatches[$BuildMatches.Count - 1]
$BuildTime = $LastBuild.Groups[1].Value.Trim()

# 提取修改描述
$BuildSection = $LastBuild.Value
$DescPattern = '\*\*修改描述\*\*:\s*(.+?)$'
$DescMatch = [regex]::Match($BuildSection, $DescPattern, [System.Text.RegularExpressions.RegexOptions]::Multiline)
$BuildDesc = if ($DescMatch.Success) { $DescMatch.Groups[1].Value.Trim() } else { "(无描述)" }

Write-Host "📦 最新 BUILD: ${BuildTime}" -ForegroundColor Green
Write-Host "   描述: ${BuildDesc}"
Write-Host ""

# ── Step 2: 确认源文件 ──────────────────────────────────────
$FilesToCopy = @(
    @{Src="zips_ee2x\EE2X_db.zip";        Dst="zips_ee2x\EE2X_db.zip"}
)
# UnofficialVersionConfig.txt 已手动测试稳定，不再每次覆盖

$Missing = @()
foreach ($f in $FilesToCopy) {
    $srcFull = Join-Path $SourcePath $f.Src
    if (-not (Test-Path $srcFull)) {
        $Missing += $f.Src
    }
}

if ($Missing.Count -gt 0) {
    Write-Host "❌ 源文件缺失:" -ForegroundColor Red
    $Missing | ForEach-Object { Write-Host "   $_" -ForegroundColor Red }
    exit 1
}

Write-Host "✅ 源文件检查通过" -ForegroundColor Green
Write-Host ""

# ── Step 3: 复制到测试目录 ──────────────────────────────────
Write-Host "📋 复制文件到测试目录..." -ForegroundColor Cyan
Write-Host "   源: ${SourcePath}"
Write-Host "   目标: ${TestPath}"
Write-Host ""

foreach ($f in $FilesToCopy) {
    $srcFull = Join-Path $SourcePath $f.Src
    $dstFull = Join-Path $TestPath $f.Dst
    $dstDir  = Split-Path $dstFull -Parent

    if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    Copy-Item -Path $srcFull -Destination $dstFull -Force
    $srcSize = (Get-Item $srcFull).Length
    $srcDate = (Get-Item $srcFull).LastWriteTime.ToString('HH:mm:ss')
    Write-Host "   ✅ $($f.Src)  →  $($f.Dst)  ($srcSize B · ${srcDate})" -ForegroundColor Green
}

Write-Host ""

if ($SkipLaunch) {
    Write-Host "⏸ 跳过启动 (SkipLaunch)" -ForegroundColor Yellow
    exit 0
}

# ── Step 4: 启动游戏 ────────────────────────────────────────
# 优先找启动器，找不到就用 EE2X.exe
$Launcher = Join-Path $SourcePath "地球帝国二代远航版启动器.exe"
$ExeFile  = Join-Path $TestPath "EE2X.exe"

if (Test-Path $Launcher) {
    Write-Host "🚀 启动: 地球帝国二代远航版启动器.exe" -ForegroundColor Green
    Start-Process -FilePath $Launcher -WorkingDirectory $SourcePath
} elseif (Test-Path $ExeFile) {
    Write-Host "🚀 启动: EE2X.exe (测试目录)" -ForegroundColor Green
    Start-Process -FilePath $ExeFile -WorkingDirectory $TestPath
} else {
    Write-Host "⚠️ 未找到启动器，请手动启动:" -ForegroundColor Yellow
    Write-Host "   $TestPath\EE2X.exe"
    Write-Host "   或 $SourcePath\地球帝国二代远航版启动器.exe"
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "🎮 测试检查项:"
Write-Host "   1. 游戏能否正常启动"
Write-Host "   2. 地图黑边是否消失 (removeblackcarpet)"
Write-Host "   3. 调试控制台是否可用 (~ 键)"
Write-Host "   4. 有无崩溃或异常"
Write-Host ""
Write-Host "📝 测试完成后，告诉镜结果。"
Write-Host "   镜自动写入对话簿 → 真收到通知。"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host ""

# ── Step 5: 输出写回模板 ────────────────────────────────────
Write-Host "📋 回复模板 (镜 → 真):" -ForegroundColor Cyan
Write-Host ""
Write-Host '## 镜 → 真 · TEST · [时间]'
Write-Host ''
Write-Host '**BUILD**: ' $BuildTime
Write-Host '**结果**: [通过 / 崩溃 / 异常]'
Write-Host '**描述**: [具体现象]'
Write-Host ""
