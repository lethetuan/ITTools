param(
    [string]$VersionCode = "office365",
    [string]$Arch = "x64",
    [string]$Lang = "vi-vn",
    [string]$WorkDir = "C:\ProgramData\ITTools\OfficeSetup"
)

# Ensure WorkDir exists
if (-not (Test-Path $WorkDir)) {
    New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
}

$stateFile = Join-Path $WorkDir "office_install_state.json"
$setupExe = Join-Path $WorkDir "setup.exe"
$configFile = Join-Path $WorkDir "configuration.xml"

# Update state function
function Set-State {
    param(
        [bool]$Active,
        [string]$Status,
        [double]$Percentage,
        [string]$Message,
        [string]$LogLine = ""
    )
    try {
        $state = [ordered]@{}
        if (Test-Path $stateFile) {
            try {
                $raw = Get-Content -Path $stateFile -Raw -Encoding UTF8 -ErrorAction Stop
                if ($raw) {
                    $parsed = $raw | ConvertFrom-Json
                    foreach ($prop in $parsed.PSObject.Properties) {
                        $state[$prop.Name] = $prop.Value
                    }
                }
            } catch {}
        }
        $state["active"] = $Active
        $state["status"] = $Status
        $state["percentage"] = [Math]::Round($Percentage, 1)
        $state["message"] = $Message
        
        $logs = @()
        if ($state["output_log"]) {
            $logs = @($state["output_log"])
        }
        if ($LogLine) {
            $timeStr = (Get-Date).ToString("HH:mm:ss")
            $logs += "[$timeStr] $LogLine"
            if ($logs.Count -gt 200) {
                $logs = $logs[-200..-1]
            }
        }
        $state["output_log"] = $logs
        try {
            $state["updated_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        } catch {
            $state["updated_at"] = [int][double]::Parse((Get-Date -UFormat %s))
        }
        
        $json = $state | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText($stateFile, $json, [System.Text.Encoding]::UTF8)
    } catch {
        try {
            [System.IO.File]::AppendAllText((Join-Path $WorkDir "error.log"), "[$(Get-Date)] Set-State error: $($_.Exception.ToString())`r`n")
        } catch {}
    }
}

# 1. Download & Verify Microsoft Official ODT (setup.exe)
Set-State -Active $true -Status "downloading" -Percentage 10.0 -Message "Đang kiểm tra bộ cài chuẩn Microsoft Office Deployment Tool..." -LogLine "Bắt đầu kiểm tra Microsoft setup.exe..."

$odtUrl = "https://officecdn.microsoft.com/pr/wsus/setup.exe"
$needDownload = $true
if (Test-Path $setupExe) {
    try {
        $size = (Get-Item $setupExe).Length
        if ($size -gt 4000000) {
            $needDownload = $false
            Set-State -Active $true -Status "downloading" -Percentage 25.0 -Message "Đã có sẵn bộ cài Microsoft setup.exe chuẩn." -LogLine "Tìm thấy setup.exe hợp lệ ($([Math]::Round($size/1MB, 2)) MB)."
        }
    } catch {}
}

if ($needDownload) {
    Set-State -Active $true -Status "downloading" -Percentage 15.0 -Message "Đang tải Microsoft setup.exe từ Microsoft CDN..." -LogLine "Bắt đầu tải từ Microsoft CDN: $odtUrl"
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
        $client = New-Object System.Net.WebClient
        $client.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        $client.DownloadFile($odtUrl, $setupExe)
        $size = (Get-Item $setupExe).Length
        Set-State -Active $true -Status "downloading" -Percentage 25.0 -Message "Đã tải xong Microsoft setup.exe ($([Math]::Round($size/1MB, 2)) MB)." -LogLine "Tải thành công setup.exe ($size bytes)."
    } catch {
        Set-State -Active $false -Status "error" -Percentage 100.0 -Message "❌ Không thể tải bộ cài Microsoft ODT: $($_.Exception.Message)" -LogLine "Lỗi tải setup.exe: $($_.Exception.Message)"
        exit 1
    }
}

# 2. Detect existing Office environment to prevent Channel Mismatch errors
$hasCurrentChannel = $false
try {
    $c2rConfig = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration" -ErrorAction SilentlyContinue
    if ($c2rConfig -and ($c2rConfig.UpdateChannel -like "*492350f6-3a01-4f97-b9c0-c7c6ddf67d60*" -or $c2rConfig.UpdateChannel -like "*Current*")) {
        $hasCurrentChannel = $true
    }
} catch {}

# Generate configuration.xml
Set-State -Active $true -Status "configuring" -Percentage 30.0 -Message "Đang khởi tạo cấu hình cài đặt ẩn (Silent Mode)..." -LogLine "Tạo file cấu hình configuration.xml..."

$productId = "O365ProPlusRetail"
$channel = "Current"

switch ($VersionCode.ToLower()) {
    "office365"  { 
        $productId = "O365ProPlusRetail"
        $channel = "Current" 
    }
    "office2024" { 
        $productId = "ProPlus2024Volume"
        $channel = "PerpetualVL2024" 
    }
    "office2021" { 
        $productId = "ProPlus2021Volume"
        $channel = "PerpetualVL2021" 
    }
    "office2019" { 
        $productId = "ProPlus2019Volume"
        $channel = "PerpetualVL2019" 
    }
    "office2016" { 
        $productId = "ProPlusRetail"
        $channel = "Current" 
    }
    "visio"      { 
        if ($hasCurrentChannel) {
            $productId = "VisioProRetail"
            $channel = "Current"
        } else {
            $productId = "VisioPro2021Volume"
            $channel = "PerpetualVL2021"
        }
    }
    "project"    { 
        if ($hasCurrentChannel) {
            $productId = "ProjectProRetail"
            $channel = "Current"
        } else {
            $productId = "ProjectPro2021Volume"
            $channel = "PerpetualVL2021"
        }
    }
    default      { 
        $productId = "O365ProPlusRetail"
        $channel = "Current" 
    }
}

$archNum = if ($Arch -eq "x86") { "32" } else { "64" }

$langXml = "      <Language ID=""$Lang"" />"
if ($Lang.ToLower() -ne "en-us") {
    $langXml += "`r`n      <Language ID=""en-us"" />"
}

$xmlContent = @"
<Configuration>
  <Add OfficeClientEdition="$archNum" Channel="$channel">
    <Product ID="$productId">
$langXml
    </Product>
  </Add>
  <RemoveMSI />
  <Display Level="None" AcceptEULA="TRUE" />
  <Property Name="AUTOACTIVATE" Value="0" />
  <Updates Enabled="TRUE" />
</Configuration>
"@

try {
    [System.IO.File]::WriteAllText($configFile, $xmlContent, [System.Text.Encoding]::UTF8)
    Set-State -Active $true -Status "configuring" -Percentage 35.0 -Message "Đã tạo cấu hình $productId ($archNum-bit, $channel, $Lang)..." -LogLine "Cấu hình cài đặt: Product=$productId, Arch=$archNum, Channel=$channel, Lang=$Lang"
} catch {
    Set-State -Active $false -Status "error" -Percentage 100.0 -Message "❌ Không thể tạo file cấu hình: $($_.Exception.Message)" -LogLine "Lỗi tạo XML: $($_.Exception.Message)"
    exit 1
}

# 3. Execute setup.exe /configure configuration.xml
Set-State -Active $true -Status "installing" -Percentage 40.0 -Message "Đang khởi chạy dịch vụ Microsoft Click-to-Run cài đặt ngầm..." -LogLine "Thực thi: setup.exe /configure configuration.xml"
Set-State -Active $true -Status "installing" -Percentage 42.0 -Message "Đang tải và cài đặt ngầm từ Microsoft CDN (Bạn có thể đóng ITTools bất cứ lúc nào)..." -LogLine "TIẾN TRÌNH CÀI ĐẶT ẨN ĐÃ KÍCH HOẠT: Dù tắt ITTools thì Office vẫn tự động tải & hoàn tất trong nền Windows."

$launchTime = Get-Date

try {
    $proc = Start-Process -FilePath $setupExe -ArgumentList "/configure `"$configFile`"" -PassThru -NoNewWindow
} catch {
    Set-State -Active $false -Status "error" -Percentage 100.0 -Message "❌ Không thể khởi chạy setup.exe: $($_.Exception.Message)" -LogLine "Lỗi chạy setup.exe: $($_.Exception.Message)"
    exit 1
}

$startTime = [DateTime]::UtcNow
$pct = 42.0
$loopCount = 0
$lastReportedProgress = 0

while (-not $proc.HasExited) {
    Start-Sleep -Seconds 3
    $loopCount++
    $elapsed = [DateTime]::UtcNow - $startTime
    $minutes = [Math]::Floor($elapsed.TotalMinutes)
    $seconds = [Math]::Floor($elapsed.TotalSeconds % 60)
    $timeStr = "{0:00}:{1:00}" -f $minutes, $seconds
    
    # Try reading real progress from Microsoft log file
    $realProgressFound = $false
    try {
        $recentLogs = Get-ChildItem -Path "$env:TEMP" -Filter "DNI-*.log" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $launchTime.AddMinutes(-1) } | Sort-Object LastWriteTime -Descending
        if ($recentLogs -and $recentLogs.Count -gt 0) {
            $latestLog = $recentLogs[0].FullName
            $match = Select-String -Path $latestLog -Pattern "ScenarioController::UpdateScenarioProgress - total progress is now (\d+)" -ErrorAction SilentlyContinue | Select-Object -Last 1
            if ($match -and $match.Matches) {
                $rawVal = [double]$match.Matches[0].Groups[1].Value
                if ($rawVal -gt 0 -and $rawVal -le 100) {
                    # Map 0-100 real Microsoft download progress to 42% - 95% range
                    $pct = [Math]::Round(42.0 + ($rawVal * 0.53), 1)
                    $realProgressFound = $true
                    if ($rawVal -ne $lastReportedProgress -and $rawVal % 10 -eq 0) {
                        $lastReportedProgress = $rawVal
                        Set-State -Active $true -Status "installing" -Percentage $pct -Message "Dịch vụ ClickToRun đang tải & cài đặt: $rawVal% (Thời gian: $timeStr)..." -LogLine "Tiến độ tải gói Microsoft Office: $rawVal%"
                    }
                }
            }
        }
    } catch {}
    
    if (-not $realProgressFound) {
        if ($pct -lt 92.0) {
            $pct += 0.5
        }
    }
    
    $c2r = Get-Process OfficeClickToRun -ErrorAction SilentlyContinue
    $statusText = if ($c2r) { "Dịch vụ ClickToRun đang tải & cài đặt ngầm" } else { "Đang tiến hành cài đặt ngầm" }
    
    $logLine = ""
    if ($loopCount % 6 -eq 0 -and -not $realProgressFound) {
        if ($c2r) {
            $wsMb = [Math]::Round(($c2r | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB, 1)
            $logLine = "Tiến trình OfficeClickToRun đang tải gói dữ liệu ($wsMb MB RAM, thời gian: $timeStr)..."
        } else {
            $logLine = "Đang xử lý cài đặt gói dữ liệu Office ($timeStr)..."
        }
    }
    
    Set-State -Active $true -Status "installing" -Percentage $pct -Message "$statusText... (Thời gian: $timeStr) - Đang chạy ngầm an toàn." -LogLine $logLine
}

$exitCode = $proc.ExitCode
Set-State -Active $true -Status "finalizing" -Percentage 95.0 -Message "Đang kiểm tra kết quả cài đặt..." -LogLine "Tiến trình setup.exe hoàn tất với mã trả về: $exitCode"

# Determine target binary for verification
$targetExe = "WINWORD.EXE"
switch ($VersionCode.ToLower()) {
    "project" { $targetExe = "WINPROJ.EXE" }
    "visio"   { $targetExe = "VISIO.EXE" }
    default   { $targetExe = "WINWORD.EXE" }
}

$targetPaths = @(
    "C:\Program Files\Microsoft Office\root\Office16\$targetExe",
    "C:\Program Files (x86)\Microsoft Office\root\Office16\$targetExe"
)

$targetInstalled = $false
foreach ($tp in $targetPaths) {
    if (Test-Path $tp) {
        $targetInstalled = $true
        break
    }
}

# Also verify in Registry
$regInstalled = $false
try {
    $c2rInstalled = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration" -ErrorAction SilentlyContinue
    if ($c2rInstalled) {
        $regInstalled = $true
    }
} catch {}

if ($exitCode -eq 0 -or $exitCode -eq 17002 -or ($targetInstalled -and $exitCode -ge 0)) {
    Set-State -Active $false -Status "completed" -Percentage 100.0 -Message "🎉 Đã hoàn tất cài đặt thành công $productId vào máy tính!" -LogLine "Cài đặt thành công 100%! Bạn có thể mở ứng dụng để sử dụng."
} else {
    # Extract detailed error message from Microsoft log if available
    $errDetail = ""
    try {
        $recentLogs = Get-ChildItem -Path "$env:TEMP" -Filter "DNI-*.log" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $launchTime.AddMinutes(-2) } | Sort-Object LastWriteTime -Descending
        if ($recentLogs -and $recentLogs.Count -gt 0) {
            $latestLog = $recentLogs[0].FullName
            $prereq = Select-String -Path $latestLog -Pattern 'ShowPrereqFailureDialog.*"Body":"([^"]+)"' -ErrorAction SilentlyContinue | Select-Object -Last 1
            if ($prereq -and $prereq.Matches) {
                $rawBody = $prereq.Matches[0].Groups[1].Value
                $cleanBody = [regex]::Unescape($rawBody).Trim().Replace("`r`n", " ").Replace("`n", " ")
                $errDetail = "Xung đột cài đặt: $cleanBody"
            } else {
                $errLine = Select-String -Path $latestLog -Pattern 'ErrorMessage":\s*"([^"]+)"' -ErrorAction SilentlyContinue | Select-Object -Last 1
                if ($errLine -and $errLine.Matches) {
                    $errDetail = $errLine.Matches[0].Groups[1].Value
                }
            }
        }
    } catch {}

    if (-not $errDetail) {
        $errDetail = "Quá trình cài đặt kết thúc với mã lỗi: $exitCode. Vui lòng kiểm tra lại kết nối mạng hoặc thử phiên bản khác."
    }

    Set-State -Active $false -Status "error" -Percentage 100.0 -Message "❌ $errDetail" -LogLine "LỖI TỪ MICROSOFT: $errDetail"
}
