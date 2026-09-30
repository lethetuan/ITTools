# ============================================================
# winget_runner.ps1  v4 (Dynamic Queue)
# Cai dat am cac goi winget doc lap voi ung dung chinh.
# Ho tro bo sung goi vao hang doi (dynamic queue) trong khi dang chay.
# Script nay chay tach biet - khong bi anh huong khi tat app.
# Tham so: -QueueFile <duong dan json> -StatusFile <duong dan json>
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$QueueFile,

    [Parameter(Mandatory=$true)]
    [string]$StatusFile
)

# ── Helpers ──────────────────────────────────────────────────────────────────
function Write-Status {
    param($data)
    $data["pid"] = $PID
    $data["updated_at"] = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    $retries = 5
    while ($retries -gt 0) {
        try {
            $json = $data | ConvertTo-Json -Depth 4 -Compress:$false
            $tmpFile = "$StatusFile.tmp"
            [System.IO.File]::WriteAllText($tmpFile, $json, [System.Text.Encoding]::UTF8)
            Move-Item -Path $tmpFile -Destination $StatusFile -Force
            break
        } catch {
            $retries--
            Start-Sleep -Milliseconds 100
        }
    }
}

function Now { return (Get-Date -Format "HH:mm:ss") }

function Is-Canceled {
    $cancelFile = [System.IO.Path]::ChangeExtension($StatusFile, ".cancel")
    return (Test-Path $cancelFile)
}

function Remove-CancelFile {
    $cancelFile = [System.IO.Path]::ChangeExtension($StatusFile, ".cancel")
    Remove-Item $cancelFile -Force -ErrorAction SilentlyContinue
}

try {
    # ── Doc hang doi ban dau ──────────────────────────────────────────────────
    if (-not (Test-Path $QueueFile)) {
        Write-Status @{
            is_running=$false; finished=$true; canceled=$false
            status_text="Loi: Khong tim thay file hang doi."
            percentage=0; current_index=0; total=0
            success_count=0; error_count=0
            current_package_id=""; current_package_name=""; log=@()
        }
        exit 1
    }

    try {
        $rawJson  = [System.IO.File]::ReadAllText($QueueFile, [System.Text.Encoding]::UTF8)
        $queue    = $rawJson | ConvertFrom-Json
    } catch {
        Write-Status @{
            is_running=$false; finished=$true; canceled=$false
            status_text="Loi: Khong the doc file hang doi: $_"
            percentage=0; current_index=0; total=0
            success_count=0; error_count=0
            current_package_id=""; current_package_name=""; log=@()
        }
        exit 1
    }

    $packages = @()
    if ($null -ne $queue.package_ids) {
        $packages = @($queue.package_ids)
    }
    $names = @{}
    if ($null -ne $queue.catalog_map) {
        foreach ($prop in $queue.catalog_map.PSObject.Properties) {
            $names[$prop.Name] = $prop.Value
        }
    }

    $total        = $packages.Count
    $successCount = 0
    $errorCount   = 0
    $logLines     = [System.Collections.Generic.List[string]]::new()
    $processedIds = [System.Collections.Generic.HashSet[string]]::new()
    $currentIndex = 0

    Write-Status @{
        is_running=$true; finished=$false; canceled=$false
        status_text="Dang chuan bi cai dat $total phan mem..."
        percentage=3; current_index=0; total=$total
        success_count=0; error_count=0
        current_package_id=""; current_package_name=""
        log=@()
    }

    # ── Vong lap cai dat dong (ho tro them goi moi khi dang chay) ─────────────
    while ($true) {
        # 1. Kiem tra yeu cau dung/huy
        if (Is-Canceled) {
            $logLines.Add("[$(Now)] [HUY] Da dung theo yeu cau nguoi dung.")
            Write-Status @{
                is_running=$false; finished=$true; canceled=$true
                status_text="Da dung. Da cai $successCount/$total phan mem thanh cong."
                percentage=100; current_index=$currentIndex; total=$total
                success_count=$successCount; error_count=$errorCount
                current_package_id=""; current_package_name=""
                log=$logLines.ToArray()
            }
            Remove-CancelFile
            exit 0
        }

        # 2. Doc lai QueueFile de lay cac goi moi vua duoc them vao boi nguoi dung
        try {
            if (Test-Path $QueueFile) {
                $rawJson = [System.IO.File]::ReadAllText($QueueFile, [System.Text.Encoding]::UTF8)
                $queue   = $rawJson | ConvertFrom-Json
                if ($null -ne $queue.package_ids) {
                    $packages = @($queue.package_ids)
                }
                if ($null -ne $queue.catalog_map) {
                    foreach ($prop in $queue.catalog_map.PSObject.Properties) {
                        $names[$prop.Name] = $prop.Value
                    }
                }
            }
        } catch {
            Start-Sleep -Milliseconds 150
        }

        $total = $packages.Count

        # 3. Tim goi tiep theo chua duoc cai dat trong hang doi
        $wid = $null
        foreach ($p in $packages) {
            if (-not $processedIds.Contains($p)) {
                $wid = $p
                break
            }
        }

        # Neu khong con goi nao -> da cai dat tat ca trong hang doi
        if ($null -eq $wid) {
            break
        }

        $processedIds.Add($wid) | Out-Null
        $currentIndex++
        $idx     = $currentIndex
        $pkgName = if ($names.ContainsKey($wid)) { $names[$wid] } else { $wid }
        $startPct = [math]::Max(5, [int]((($idx - 1) / [math]::Max(1, $total)) * 95))

        # Kiem tra huy truoc khi bat dau cai goi nay
        if (Is-Canceled) {
            $logLines.Add("[$(Now)] [HUY] Da dung truoc khi cai $pkgName tai [$idx/$total].")
            Write-Status @{
                is_running=$false; finished=$true; canceled=$true
                status_text="Da dung. Da cai $successCount/$total phan mem thanh cong."
                percentage=$startPct; current_index=$idx; total=$total
                success_count=$successCount; error_count=$errorCount
                current_package_id=$wid; current_package_name=$pkgName
                log=$logLines.ToArray()
            }
            Remove-CancelFile
            exit 0
        }

        # Cap nhat trang thai bat dau goi nay
        Write-Status @{
            is_running=$true; finished=$false; canceled=$false
            status_text="[$idx/$total] Dang tai & cai dat: $pkgName..."
            percentage=$startPct; current_index=$idx; total=$total
            success_count=$successCount; error_count=$errorCount
            current_package_id=$wid; current_package_name=$pkgName
            log=$logLines.ToArray()
        }

        $logLines.Add("[$(Now)] [$idx/$total] Bat dau cai dat: $pkgName ($wid)")

        # ── Ham kiem tra thuc te phan mem da duoc cai vao may hay chua ─────────
        function Test-PackageInstalled {
            param(
                [string]$PackageId,
                [string]$PackageName
            )
            # 1. Kiem tra qua winget list
            try {
                $pinfo = New-Object System.Diagnostics.ProcessStartInfo
                $pinfo.FileName = "winget.exe"
                $pinfo.Arguments = "list --id `"$PackageId`" -e --accept-source-agreements"
                $pinfo.UseShellExecute = $false
                $pinfo.RedirectStandardOutput = $true
                $pinfo.RedirectStandardError = $true
                $pinfo.CreateNoWindow = $true
                $pinfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
                $chkProc = [System.Diagnostics.Process]::Start($pinfo)
                $out = $chkProc.StandardOutput.ReadToEnd()
                $null = $chkProc.WaitForExit(7000)
                if ($chkProc.ExitCode -eq 0 -and $out -match [regex]::Escape($PackageId)) {
                    return $true
                }
            } catch {}

            # 2. Kiem tra qua Windows Uninstall Registry
            $regKeys = @(
                "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
                "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
                "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
            )
            try {
                $cleanName = ($PackageName -replace "\(.*?\)", "").Trim()
                $tokens = $cleanName -split "[\s\-_]+" | Where-Object { $_.Length -ge 3 }
                if ($tokens.Count -gt 0) {
                    $firstToken = $tokens[0]
                    $match = Get-ItemProperty -Path $regKeys -ErrorAction SilentlyContinue |
                        Where-Object { $_.DisplayName -and ($_.DisplayName -match [regex]::Escape($firstToken)) }
                    if ($match -and @($match).Count -gt 0) {
                        return $true
                    }
                }
            } catch {}

            return $false
        }

        # ── Ham goi winget an toan co Timeout va Kiem tra Huy tuc thi ─────────
        function Invoke-WingetPackage {
            param(
                [string]$PackageId,
                [bool]$Exact = $true,
                [bool]$Silent = $true,
                [bool]$LimitSource = $true,
                [int]$TimeoutSeconds = 180
            )
            # Clear any hung winget process from previous run to release file lock 0x80070020
            try { taskkill /f /im winget.exe 2>&1 | Out-Null } catch {}

            $srcArg = if ($LimitSource) { "--source winget" } else { "" }
            $exactArg = if ($Exact) { "-e" } else { "" }
            $silentArg = if ($Silent) { "--silent" } else { "" }

            $pinfo = New-Object System.Diagnostics.ProcessStartInfo
            $pinfo.FileName = "winget.exe"
            # Khong dung --disable-interactivity de tranh bi loi 2147747609 tren cac bo cai dat yeu cau UAC
            $pinfo.Arguments = "install --id `"$PackageId`" $exactArg $srcArg $silentArg --accept-package-agreements --accept-source-agreements --force"
            $pinfo.UseShellExecute = $false
            $pinfo.CreateNoWindow = $true
            $pinfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

            $proc = New-Object System.Diagnostics.Process
            $proc.StartInfo = $pinfo

            try {
                if (-not $proc.Start()) {
                    return @{ Success = $false; ExitCode = -1; TimedOut = $false; Canceled = $false }
                }

                $elapsed = 0
                while (-not $proc.HasExited) {
                    Start-Sleep -Seconds 1
                    $elapsed++

                    # Kiem tra neu nguoi dung bam Dung thi kill ngay lap tuc
                    if (Is-Canceled) {
                        try { taskkill /f /t /pid $proc.Id 2>&1 | Out-Null } catch {}
                        return @{ Success = $false; ExitCode = -999; TimedOut = $false; Canceled = $true }
                    }

                    # Kiem tra Timeout de tranh bi treo mai mai
                    if ($elapsed -ge $TimeoutSeconds) {
                        try { taskkill /f /t /pid $proc.Id 2>&1 | Out-Null } catch {}
                        return @{ Success = $false; ExitCode = -1001; TimedOut = $true; Canceled = $false }
                    }
                }

                $exitCode = $proc.ExitCode
                # 0 = Thanh cong
                # 3010 / 1641 = Thanh cong (can restart may)
                # -1978335189 (0x8A15002B) = Da cai dat ban moi nhat
                # -1978335246 (0x8A150002) = Da cai dat va khong co ban nang cap
                $success = ($exitCode -eq 0) -or ($exitCode -eq 3010) -or ($exitCode -eq 1641) -or ($exitCode -eq -1978335189) -or ($exitCode -eq -1978335246)
                return @{ Success = $success; ExitCode = $exitCode; TimedOut = $false; Canceled = $false }
            } catch {
                return @{ Success = $false; ExitCode = -1; TimedOut = $false; Canceled = $false }
            } finally {
                if (-not $proc.HasExited) {
                    try { $proc.Kill() } catch {}
                }
                $proc.Dispose()
            }
        }

        # Lan 1: Cai dat voi co chuan silent
        $res = Invoke-WingetPackage -PackageId $wid -Exact $true -Silent $true -LimitSource $true -TimeoutSeconds 180

        if ($res.Canceled) {
            $logLines.Add("[$(Now)] [HUY] Da dung theo yeu cau khi dang cai $pkgName.")
            Write-Status @{
                is_running=$false; finished=$true; canceled=$true
                status_text="Da dung theo yeu cau. Da cai $successCount/$total phan mem."
                percentage=$startPct; current_index=$idx; total=$total
                success_count=$successCount; error_count=$errorCount
                current_package_id=$wid; current_package_name=$pkgName
                log=$logLines.ToArray()
            }
            Remove-CancelFile
            exit 0
        }

        # Lan 2 (Fallback): Neu that bai va chua bi Timeout/Huy thi thu lai bo gioi han nguon
        if (-not $res.Success -and -not $res.TimedOut) {
            $logLines.Add("[$(Now)] [$idx/$total] Thu lai lenh du phong cho: $pkgName (exit=$($res.ExitCode))")
            $res = Invoke-WingetPackage -PackageId $wid -Exact $false -Silent $true -LimitSource $false -TimeoutSeconds 180
            if ($res.Canceled) {
                $logLines.Add("[$(Now)] [HUY] Da dung theo yeu cau khi dang cai $pkgName.")
                Write-Status @{
                    is_running=$false; finished=$true; canceled=$true
                    status_text="Da dung theo yeu cau. Da cai $successCount/$total phan mem."
                    percentage=$startPct; current_index=$idx; total=$total
                    success_count=$successCount; error_count=$errorCount
                    current_package_id=$wid; current_package_name=$pkgName
                    log=$logLines.ToArray()
                }
                Remove-CancelFile
                exit 0
            }
        }

        # Xac thuc thuc te xem ung dung da ton tai tren may chua
        $isInstalled = Test-PackageInstalled -PackageId $wid -PackageName $pkgName
        $exitCode = $res.ExitCode

        if ($isInstalled -or $res.Success) {
            $successCount++
            $logLines.Add("[$(Now)] [$idx/$total] [OK] Da cai dat thanh cong: $pkgName")
        } elseif ($res.TimedOut) {
            $errorCount++
            $logLines.Add("[$(Now)] [$idx/$total] [QUA THOI GIAN] Cai dat $pkgName vuot qua thoi gian cho phep.")
        } else {
            $errorCount++
            $logLines.Add("[$(Now)] [$idx/$total] [LOI] That bai: $pkgName (exit=$exitCode, khong tim thay sau khi cai)")
        }

        $endPct = [int](($idx / [math]::Max(1, $total)) * 95)
        Write-Status @{
            is_running=$true; finished=$false; canceled=$false
            status_text="[$idx/$total] Hoan thanh: $pkgName | OK: $successCount | Loi: $errorCount"
            percentage=$endPct; current_index=$idx; total=$total
            success_count=$successCount; error_count=$errorCount
            current_package_id=$wid; current_package_name=$pkgName
            log=$logLines.ToArray()
        }
    }

    # ── Hoan tat toan bo hang doi ─────────────────────────────────────────────
    if ($errorCount -gt 0 -and $successCount -eq 0) {
        $finalStatusText = "That bai: Khong the cai dat $errorCount/$total phan mem. Vui long xem nhat ky!"
    } elseif ($errorCount -gt 0) {
        $finalStatusText = "Hoan tat mot phan: Da cai $successCount/$total thanh cong ($errorCount loi)."
    } else {
        $finalStatusText = "Hoan tat! Da cai $successCount/$total phan mem thanh cong."
    }

    $logLines.Add("[$(Now)] === KET THUC: $successCount/$total thanh cong. $errorCount loi ===")

    Write-Status @{
        is_running=$false; finished=$true; canceled=$false
        status_text=$finalStatusText
        percentage=100; current_index=$total; total=$total
        success_count=$successCount; error_count=$errorCount
        current_package_id=""; current_package_name=""
        log=$logLines.ToArray()
    }
} catch {
    $errStr = $_.ToString()
    Write-Status @{
        is_running=$false; finished=$true; canceled=$false
        status_text="Loi ngoai le: $errStr"
        percentage=100; current_index=0; total=0
        success_count=0; error_count=1
        current_package_id=""; current_package_name=""
        log=@("[$(Now)] [EXCEPTION] $errStr")
    }
} finally {
    Remove-Item $QueueFile -Force -ErrorAction SilentlyContinue
    Remove-CancelFile
}
