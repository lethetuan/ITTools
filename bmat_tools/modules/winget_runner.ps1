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

        # ── Lenh winget chinh (goi truc tiep, khong Start-Process) ───────────
        $success  = $false
        $exitCode = -1

        try {
            $output = & winget install --id "$wid" -e --silent `
                        --accept-package-agreements `
                        --accept-source-agreements 2>&1
            $exitCode = $LASTEXITCODE
            $success  = ($exitCode -eq 0) -or ($exitCode -eq -1978335189)   # -1978335189 = da cai dat roi
        } catch {
            $logLines.Add("[$(Now)] [$idx/$total] Exception lan 1: $_")
            $exitCode = -1
        }

        # ── Fallback: bo co -e neu that bai ─────────────────────────────────
        if (-not $success) {
            $logLines.Add("[$(Now)] [$idx/$total] Thu lai lenh du phong cho: $pkgName (exit=$exitCode)")
            try {
                $output2  = & winget install --id "$wid" --silent `
                              --accept-package-agreements `
                              --accept-source-agreements 2>&1
                $exitCode = $LASTEXITCODE
                $success  = ($exitCode -eq 0) -or ($exitCode -eq -1978335189)
            } catch {
                $logLines.Add("[$(Now)] [$idx/$total] Exception lan 2: $_")
            }
        }

        # Kiem tra huy sau khi cai
        if (Is-Canceled) {
            $logLines.Add("[$(Now)] [HUY] Da dung tai [$idx/$total] sau khi cai.")
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

        if ($success) {
            $successCount++
            $logLines.Add("[$(Now)] [$idx/$total] [OK] Da cai dat thanh cong: $pkgName")
        } else {
            $errorCount++
            $logLines.Add("[$(Now)] [$idx/$total] [LOI] That bai: $pkgName (exit=$exitCode)")
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
    $logLines.Add("[$(Now)] === HOAN TAT: $successCount/$total thanh cong. Loi: $errorCount ===")

    Write-Status @{
        is_running=$false; finished=$true; canceled=$false
        status_text="Hoan tat! Da cai $successCount/$total phan mem thanh cong. Loi: $errorCount"
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
