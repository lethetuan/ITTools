# diag.ps1 - Kiem tra trang thai cai dat
$sf = "$env:TEMP\ittools_winget\status.json"
$qf = "$env:TEMP\ittools_winget\queue.json"

Write-Host "=== STATUS.JSON ==="
if (Test-Path $sf) {
    $d = Get-Content $sf | ConvertFrom-Json
    Write-Host "is_running  : $($d.is_running)"
    Write-Host "finished    : $($d.finished)"
    Write-Host "percentage  : $($d.percentage)"
    Write-Host "total       : $($d.total)"
    Write-Host "status_text : $($d.status_text)"
    $age = [int]((Get-Date) - (Get-Item $sf).LastWriteTime).TotalSeconds
    Write-Host "File age    : $age giay"
} else {
    Write-Host "KHONG CO status.json"
}

Write-Host ""
Write-Host "=== QUEUE.JSON ==="
if (Test-Path $qf) {
    $q = Get-Content $qf | ConvertFrom-Json
    Write-Host "package_ids : $($q.package_ids -join ', ')"
} else {
    Write-Host "KHONG CO queue.json"
}

Write-Host ""
Write-Host "=== PROCESS WINGET ==="
$wg = Get-Process -Name winget -ErrorAction SilentlyContinue
if ($wg) { $wg | Select-Object Id,CPU | Format-Table -AutoSize }
else { Write-Host "Khong co winget.exe dang chay" }

Write-Host "=== PROCESS POWERSHELL ==="
Get-Process -Name powershell -ErrorAction SilentlyContinue | Select-Object Id,CPU | Format-Table -AutoSize
