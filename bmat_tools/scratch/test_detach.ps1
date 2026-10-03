# test_detach.ps1 - Kiem tra chay detached process

# Tao queue file
$tmpDir = "$env:TEMP\bmat_winget"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

$q = '{"package_ids":["7zip.7zip"],"catalog_map":{"7zip.7zip":"7-Zip"}}'
$qf = "$tmpDir\q_detach_test.json"
$sf = "$tmpDir\s_detach_test.json"

[System.IO.File]::WriteAllText($qf, $q, [System.Text.Encoding]::UTF8)
Write-Host "Queue: $qf"
Write-Host "Status: $sf"

# Xoa status cu neu co
if (Test-Path $sf) { Remove-Item $sf -Force }

# Chay giong het Python: DETACHED_PROCESS | CREATE_NO_WINDOW
$pinfo = New-Object System.Diagnostics.ProcessStartInfo
$pinfo.FileName  = "powershell.exe"
$pinfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"d:\AllinOne\bmat_tools\modules\winget_runner.ps1`" -QueueFile `"$qf`" -StatusFile `"$sf`""
$pinfo.UseShellExecute  = $false   # Quan trong: FALSE = detached (giong Python Popen)
$pinfo.CreateNoWindow   = $true
$pinfo.RedirectStandardOutput = $false
$pinfo.RedirectStandardError  = $false

$proc = [System.Diagnostics.Process]::Start($pinfo)
Write-Host "PID da khoi chay: $($proc.Id)"
Write-Host "Cho 6 giay..."
Start-Sleep -Seconds 6

if (Test-Path $sf) {
    Write-Host "=== STATUS FILE SAU 6 GIAY ==="
    Get-Content $sf
} else {
    Write-Host "LOI: Status file CHUA XUAT HIEN sau 6 giay - PS script bi crash!"
}
