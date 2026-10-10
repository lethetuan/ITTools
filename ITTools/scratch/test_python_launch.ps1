# test_python_launch.ps1
# Giả lập chính xác cách Python subprocess.Popen với shell=True + STARTUPINFO sẽ chạy

$tmpDir = "$env:TEMP\ittools_winget"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

# Tao queue test
$q = '{"package_ids":["SumatraPDF.SumatraPDF"],"catalog_map":{"SumatraPDF.SumatraPDF":"SumatraPDF"}}'
$qf = "$tmpDir\q_pytest.json"
$sf = "$tmpDir\s_pytest.json"
[System.IO.File]::WriteAllText($qf, $q, [System.Text.Encoding]::UTF8)

if (Test-Path $sf) { Remove-Item $sf -Force }

# Chay qua cmd.exe (shell=True se goi cmd.exe /c ...)
$ps1 = "d:\AllinOne\ITTools\modules\winget_runner.ps1"
$cmdLine = "cmd.exe /c powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ps1`" -QueueFile `"$qf`" -StatusFile `"$sf`""

$pinfo = New-Object System.Diagnostics.ProcessStartInfo
$pinfo.FileName  = "cmd.exe"
$pinfo.Arguments = "/c powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ps1`" -QueueFile `"$qf`" -StatusFile `"$sf`""
$pinfo.UseShellExecute = $false
$pinfo.CreateNoWindow  = $true
$pinfo.RedirectStandardOutput = $false
$pinfo.RedirectStandardError  = $false

$proc = [System.Diagnostics.Process]::Start($pinfo)
Write-Host "PID: $($proc.Id)"
Write-Host "Cho 10 giay..."
Start-Sleep -Seconds 10

if (Test-Path $sf) {
    Write-Host "=== STATUS FILE ==="
    $data = Get-Content $sf | ConvertFrom-Json
    Write-Host "is_running: $($data.is_running)"
    Write-Host "finished: $($data.finished)"
    Write-Host "status_text: $($data.status_text)"
    Write-Host "success_count: $($data.success_count)"
    $data.log | ForEach-Object { Write-Host "  LOG: $_" }
} else {
    Write-Host "THAT BAI: Status file khong xuat hien!"
}
