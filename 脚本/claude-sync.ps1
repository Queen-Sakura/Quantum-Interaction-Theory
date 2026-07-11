# Argo Sync - Z: to D:\Argo
$LINUX  = 'Z:'
$ARGO   = 'D:\Argo'
$WIN    = $env:USERPROFILE

Write-Host 'Argo Sync: Starting...' -ForegroundColor Cyan

$dirs = @(
    $ARGO,
    "$ARGO\ArgoShared",
    "$ARGO\ArgoShared\Q",
    "$ARGO\ArgoSharedeports",
    "$WIN\.claude\projects\-root\memory"
)
foreach ($d in $dirs) {
    if (!(Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

Write-Host '  [1/5] Memory files...' -ForegroundColor Yellow
$linuxMem = "$LINUX\.claude\projects\-root\memory"
$winMem   = "$WIN\.claude\projects\-root\memory"
robocopy $linuxMem $winMem /MIR /R:2 /NDL /NJH /NJS
robocopy $winMem $linuxMem /MIR /R:2 /NDL /NJH /NJS

Write-Host '  [2/5] CLAUDE.md...' -ForegroundColor Yellow
robocopy $LINUX\ $ARGO\ CLAUDE.md /R:2 /NDL /NJH /NJS

Write-Host '  [3/5] settings.json...' -ForegroundColor Yellow
robocopy "$LINUX\.claude" "$WIN\.claude" settings.json /R:2 /NDL /NJH /NJS

Write-Host '  [4/5] statusline script...' -ForegroundColor Yellow
robocopy "$LINUX\.claude" $ARGO statusline-context.sh /R:2 /NDL /NJH /NJS

Write-Host '  [5/5] ArgoShared files...' -ForegroundColor Yellow
robocopy "$LINUX\ArgoShared" "$ARGO\ArgoShared" /MIR /R:2 /NDL /NJH /NJS /XD .git qit_repo

Write-Host 'Argo Sync: DONE' -ForegroundColor Green
Write-Host 'Next: cd D:\Argo ; claude --resume' -ForegroundColor Cyan
