param(
    [string]$VersionCode = "office365",
    [string]$Arch = "x64",
    [string]$Lang = "vi-vn",
    [string]$WorkDir = "C:\ProgramData\BMAT_Tools\OfficeSetup"
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
                $parsed = $raw | ConvertFrom-Json
                foreach ($prop in $parsed.PSObject.Properties) {
                    $state[$prop.Name] = $prop.Value
                }
            } catch {}
        }
        $state["active"] = $Active
        $state["status"] = $Status
        $state["percentage"] = [Math]::Round($Percentage, 1)
        $state["message"] = $Message
        
        $logs = @()
        if ($state.ContainsKey("output_log") -and $state["output_log"]) {
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
        $state["updated_at"] = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        
        $json = $state | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText($stateFile, $json, [System.Text.Encoding]::UTF8)
    } catch {}
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

# 2. Generate configuration.xml
Set-State -Active $true -Status "configuring" -Percentage 30.0 -Message "Đang khởi tạo cấu hình cài đặt ẩn (Silent Mode)..." -LogLine "Tạo file cấu hình configuration.xml..."

$productId = "O365ProPlusRetail"
$channel = "Current"

switch ($VersionCode.ToLower()) {
    "office365"  { $productId = "O365ProPlusRetail"; $channel = "Current" }
    "office2024" { $productId = "ProPlus2024Volume"; $channel = "PerpetualVL2024" }
    "office2021" { $productId = "ProPlus2021Volume"; $channel = "PerpetualVL2021" }
    "office2019" { $productId = "ProPlus2019Volume"; $channel = "PerpetualVL2019" }
    "office2016" { $productId = "ProPlusRetail";      $channel = "Current" }
    "visio"      { $productId = "VisioPro2021Volume"; $channel = "PerpetualVL2021" }
    "project"    { $productId = "ProjectPro2021Volume"; $channel = "PerpetualVL2021" }
    default      { $productId = "O365ProPlusRetail"; $channel = "Current" }
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
Set-State -Active $true -Status "installing" -Percentage 42.0 -Message "Đang tải và cài đặt ngầm từ Microsoft CDN (Bạn có thể đóng BMAT Tools bất cứ lúc nào)..." -LogLine "ĐÃ KÍCH HOẠT TIẾN TRÌNH CÀI ĐẶT ẨN: Cho dù có tắt ứng dụng BMAT Tools thì Office vẫn tự động tải & hoàn tất trong nền Windows."

try {
    $proc = Start-Process -FilePath $setupExe -ArgumentList "/configure `"$configFile`"" -PassThru -NoNewWindow
} catch {
    Set-State -Active $false -Status "error" -Percentage 100.0 -Message "❌ Không thể khởi chạy setup.exe: $($_.Exception.Message)" -LogLine "Lỗi chạy setup.exe: $($_.Exception.Message)"
    exit 1
}

$startTime = [DateTime]::UtcNow
$pct = 45.0

while (-not $proc.HasExited) {
    Start-Sleep -Seconds 3
    $elapsed = [DateTime]::UtcNow - $startTime
    
    if ($pct -lt 92.0) {
        $pct += 1.0
    }
    
    $minutes = [Math]::Floor($elapsed.TotalMinutes)
    $seconds = [Math]::Floor($elapsed.TotalSeconds % 60)
    $timeStr = "{0:00}:{1:00}" -f $minutes, $seconds
    
    $c2r = Get-Process OfficeClickToRun -ErrorAction SilentlyContinue
    $statusText = if ($c2r) { "Dịch vụ ClickToRun đang tải & cài đặt ngầm" } else { "Đang tiến hành cài đặt ngầm" }
    
    Set-State -Active $true -Status "installing" -Percentage $pct -Message "$statusText... (Thời gian: $timeStr) - Đang chạy ngầm an toàn."
}

$exitCode = $proc.ExitCode
Set-State -Active $true -Status "finalizing" -Percentage 95.0 -Message "Đang kiểm tra kết quả cài đặt..." -LogLine "Tiến trình setup.exe hoàn tất với mã trả về: $exitCode"

$wordPaths = @(
    "C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE"
)
$installed = $false
foreach ($wp in $wordPaths) {
    if (Test-Path $wp) {
        $installed = $true
        break
    }
}

if ($exitCode -eq 0 -or $installed) {
    Set-State -Active $false -Status "completed" -Percentage 100.0 -Message "🎉 Đã hoàn tất cài đặt thành công Office vào máy tính!" -LogLine "Cài đặt thành công 100%! Bạn có thể mở Word, Excel, PowerPoint để sử dụng."
} else {
    Set-State -Active $false -Status "error" -Percentage 100.0 -Message "❌ Quá trình cài đặt kết thúc với mã lỗi: $exitCode. Vui lòng kiểm tra lại kết nối mạng hoặc thử phiên bản khác." -LogLine "Lỗi mã: $exitCode"
}
