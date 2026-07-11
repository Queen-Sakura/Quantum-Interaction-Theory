# Argo 共享 Claude 记忆同步（Z:盘双向）
# 用法: 在 Windows PowerShell 跑 .\claude-sync.ps1，然后再跑 claude

$LINUX  = "Z:"
$ARGO   = "D:\Argo"
$WIN    = "$env:USERPROFILE"

Write-Host "🐍 Argo Sync: 九头蛇记忆同步..." -ForegroundColor Cyan

# 确保目录存在
$dirs = @(
    "$ARGO",
    "$ARGO\ArgoShared",
    "$ARGO\ArgoShared\Q",
    "$ARGO\ArgoShared\reports",
    "$WIN\.claude\projects\-root\memory"
)
foreach ($d in $dirs) {
    if (!(Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

# === 1. 记忆文件 — 同步到 Claude 项目目录 ===
$linuxMem = "$LINUX\.claude\projects\-root\memory"
$winMem   = "$WIN\.claude\projects\-root\memory"
robocopy $linuxMem $winMem /MIR /R:2 /NDL /NJH /NJS
robocopy $winMem $linuxMem /MIR /R:2 /NDL /NJH /NJS

# === 2. CLAUDE.md → D:\Argo ===
robocopy $LINUX\ $ARGO\ CLAUDE.md /R:2 /NDL /NJH /NJS

# === 3. settings.json ===
robocopy "$LINUX\.claude" "$WIN\.claude" settings.json /R:2 /NDL /NJH /NJS

# === 4. 进度条脚本 → D:\Argo ===
robocopy "$LINUX\.claude" $ARGO statusline-context.sh /R:2 /NDL /NJH /NJS

# === 5. ArgoShared 工作文件 → D:\Argo ===
robocopy "$LINUX\ArgoShared" "$ARGO\ArgoShared" /MIR /R:2 /NDL /NJH /NJS /XD .git qit_repo "魔都三件套" WechatNews xinyi_chat membrane_render 归档

Write-Host "Argo Sync: 完成" -ForegroundColor Green
Write-Host "启动: cd D:\Argo && claude --resume" -ForegroundColor Cyan
