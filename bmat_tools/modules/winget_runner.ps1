# ============================================================
# winget_runner.ps1  v4 (Dynamic Queue)
# Cai dat am cac goi winget doc lap voi ung dung chinh.
# Ho tro bo sung goi vao hang doi (dynamic queue) trong khi dang chay.
# Script nay chay tach biet - khong bi anh huong khi tat app.
# Tham so: -QueueFile <duong dan json> -StatusFile <duong dan json>
# ============================================================

param(
    [string]$QueueFile = "",
    [string]$StatusFile = ""
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

# ── Ghim & Tao Shortcut Desktop, Start Menu, Programs ─────────────────────────
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class ShellRefreshHelper {
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
    public static void Refresh() {
        try {
            SHChangeNotify(0x08000000, 0, IntPtr.Zero, IntPtr.Zero);
        } catch {}
    }
}
"@ -ErrorAction SilentlyContinue

$GLOBAL:KNOWN_APP_TARGETS = @{
    # Trình duyệt
    "CocCoc.CocCoc"                         = @{ Exes = @("browser.exe"); Title = "Cốc Cốc" }
    "Google.Chrome"                         = @{ Exes = @("chrome.exe"); Title = "Google Chrome" }
    "Microsoft.Edge"                        = @{ Exes = @("msedge.exe"); Title = "Microsoft Edge" }
    "Mozilla.Firefox"                       = @{ Exes = @("firefox.exe"); Title = "Mozilla Firefox" }
    "Brave.Brave"                           = @{ Exes = @("brave.exe"); Title = "Brave Browser" }
    "Opera.Opera"                           = @{ Exes = @("launcher.exe", "opera.exe"); Title = "Opera" }
    "Opera.OperaGX"                         = @{ Exes = @("launcher.exe"); Title = "Opera GX" }
    "Vivaldi.Vivaldi"                       = @{ Exes = @("vivaldi.exe"); Title = "Vivaldi" }

    # Bộ gõ
    "UniKey.UniKey"                         = @{ Exes = @("UniKeyNT.exe", "UniKey.exe"); Title = "UniKey" }
    "lamquangminh.EVKey"                    = @{ Exes = @("EVKey64.exe", "EVKey.exe", "EVKey32.exe"); Title = "EVKey Tiếng Việt" }
    "Tuyenvm.OpenKey"                       = @{ Exes = @("OpenKey.exe", "OpenKey64.exe"); Title = "OpenKey" }

    # Giải nén
    "7zip.7zip"                             = @{ Exes = @("7zFM.exe"); PreferredLnk = "*7-Zip File Manager*.lnk"; Title = "7-Zip" }
    "RARLab.WinRAR"                         = @{ Exes = @("WinRAR.exe"); PreferredLnk = "*WinRAR*.lnk"; Title = "WinRAR" }
    "Giorgiotani.Peazip"                    = @{ Exes = @("peazip.exe"); Title = "PeaZip" }
    "Bandisoft.Bandizip"                    = @{ Exes = @("Bandizip.exe"); Title = "Bandizip" }

    # Download & FTP
    "SoftDeluxe.FreeDownloadManager"        = @{ Exes = @("fdm.exe"); Title = "Free Download Manager" }
    "qBittorrent.qBittorrent"               = @{ Exes = @("qbittorrent.exe"); Title = "qBittorrent" }
    "WinSCP.WinSCP"                         = @{ Exes = @("WinSCP.exe"); Title = "WinSCP" }
    "PuTTY.PuTTY"                           = @{ Exes = @("putty.exe"); PreferredLnk = "*PuTTY*.lnk"; Title = "PuTTY" }
    "Tonec.InternetDownloadManager"         = @{ Exes = @("IDMan.exe"); Title = "Internet Download Manager" }
    "Iterate.Cyberduck"                     = @{ Exes = @("Cyberduck.exe"); Title = "Cyberduck" }

    # PDF & Văn bản
    "Foxit.FoxitReader"                     = @{ Exes = @("FoxitPDFReader.exe", "FoxitReader.exe"); Title = "Foxit PDF Reader" }
    "SumatraPDF.SumatraPDF"                 = @{ Exes = @("SumatraPDF.exe"); Title = "SumatraPDF" }
    "geeksoftwareGmbH.PDF24Creator"         = @{ Exes = @("pdf24.exe", "pdf24-Launcher.exe"); Title = "PDF24 Creator" }
    "Adobe.Acrobat.Reader.64-bit"           = @{ Exes = @("Acrobat.exe", "AcroRd32.exe"); Title = "Adobe Acrobat Reader" }
    "TrackerSoftware.PDF-XChangeEditor"     = @{ Exes = @("PDFXEdit.exe"); Title = "PDF-XChange Editor" }
    "TrackerSoftware.PDF-Tools"             = @{ Exes = @("PDFTools.exe"); Title = "PDF-Tools" }

    # Fonts & Công cụ
    "FontForge.FontForge"                   = @{ Exes = @("fontforge.exe"); Title = "FontForge" }
    "REALiX.HWiNFO"                         = @{ Exes = @("HWiNFO64.exe", "HWiNFO32.exe"); Title = "HWiNFO" }

    # Chat & Liên lạc
    "VNGCorp.Zalo"                          = @{ Exes = @("Zalo.exe"); Title = "Zalo" }
    "Telegram.TelegramDesktop"              = @{ Exes = @("Telegram.exe"); Title = "Telegram" }
    "Zoom.Zoom"                             = @{ Exes = @("Zoom.exe"); Title = "Zoom Meetings" }
    "Discord.Discord"                       = @{ Exes = @("Discord.exe", "Update.exe"); Title = "Discord" }
    "SlackTechnologies.Slack"               = @{ Exes = @("slack.exe"); Title = "Slack" }
    "Microsoft.Teams"                       = @{ Exes = @("msteams.exe", "Teams.exe"); Title = "Microsoft Teams" }
    "Rakuten.Viber"                         = @{ Exes = @("Viber.exe"); Title = "Viber" }
    "Tencent.WeChat"                        = @{ Exes = @("WeChat.exe"); Title = "WeChat" }
    "Caprine.Caprine"                       = @{ Exes = @("Caprine.exe"); Title = "Messenger (Caprine)" }

    # Văn phòng & Soạn thảo
    "TheDocumentFoundation.LibreOffice"     = @{ Exes = @("soffice.exe"); Title = "LibreOffice" }
    "Kingsoft.WPSOffice"                    = @{ Exes = @("wps.exe", "ksolaunch.exe"); Title = "WPS Office" }
    "Notepad++.Notepad++"                   = @{ Exes = @("notepad++.exe"); Title = "Notepad++" }
    "voidtools.Everything"                  = @{ Exes = @("Everything.exe"); Title = "Everything" }
    "Microsoft.PowerToys"                   = @{ Exes = @("PowerToys.exe"); Title = "PowerToys" }
    "Bopsoft.Listary"                       = @{ Exes = @("Listary.exe"); Title = "Listary" }
    "Obsidian.Obsidian"                     = @{ Exes = @("Obsidian.exe"); Title = "Obsidian" }
    "Notion.Notion"                         = @{ Exes = @("Notion.exe"); Title = "Notion" }
    "MarkText.MarkText"                     = @{ Exes = @("MarkText.exe"); Title = "MarkText" }
    "Inkscape.Inkscape"                     = @{ Exes = @("inkscape.exe"); Title = "Inkscape" }

    # Đa phương tiện & Âm nhạc
    "VideoLAN.VLC"                          = @{ Exes = @("vlc.exe"); Title = "VLC Media Player" }
    "Daum.PotPlayer"                        = @{ Exes = @("PotPlayer64.exe", "PotPlayer.exe"); Title = "PotPlayer" }
    "OBSProject.OBSStudio"                  = @{ Exes = @("obs64.exe", "obs32.exe"); Title = "OBS Studio" }
    "GIMP.GIMP"                             = @{ Exes = @("gimp.exe", "gimp-2.10.exe"); Title = "GIMP" }
    "Audacity.Audacity"                     = @{ Exes = @("Audacity.exe"); Title = "Audacity" }
    "Spotify.Spotify"                       = @{ Exes = @("Spotify.exe"); Title = "Spotify" }
    "MPC-BE.MPC-BE"                         = @{ Exes = @("mpc-be64.exe", "mpc-be.exe"); Title = "MPC-BE Player" }
    "HandBrake.HandBrake"                   = @{ Exes = @("HandBrake.exe"); Title = "HandBrake" }
    "KDE.Kdenlive"                          = @{ Exes = @("kdenlive.exe"); Title = "Kdenlive Video Editor" }
    "ByteDance.CapCut"                      = @{ Exes = @("CapCut.exe"); Title = "CapCut" }
    "ShareX.ShareX"                         = @{ Exes = @("ShareX.exe"); Title = "ShareX" }

    # Tiện ích hệ thống
    "AnyDesk.AnyDesk"                       = @{ Exes = @("AnyDesk.exe"); Title = "AnyDesk" }
    "TeamViewer.TeamViewer"                 = @{ Exes = @("TeamViewer.exe"); Title = "TeamViewer" }
    "DucFabulous.UltraViewer"               = @{ Exes = @("UltraViewer_Desktop.exe"); Title = "UltraViewer" }
    "Rufus.Rufus"                           = @{ Exes = @("rufus.exe"); Title = "Rufus" }
    "Piriform.CCleaner"                     = @{ Exes = @("CCleaner64.exe", "CCleaner.exe"); Title = "CCleaner" }
    "Microsoft.WindowsTerminal"             = @{ Exes = @("wt.exe"); Title = "Windows Terminal" }
    "Greenshot.Greenshot"                   = @{ Exes = @("Greenshot.exe"); Title = "Greenshot" }
    "NirSoft.BlueScreenView"                = @{ Exes = @("BlueScreenView.exe"); Title = "BlueScreenView" }

    # Hệ thống & Phần cứng
    "CPUID.CPU-Z"                           = @{ Exes = @("cpuz.exe"); Title = "CPU-Z" }
    "TechPowerUp.GPU-Z"                     = @{ Exes = @("GPU-Z*.exe"); Title = "GPU-Z" }
    "CrystalDewWorld.CrystalDiskInfo"       = @{ Exes = @("DiskInfo64.exe", "DiskInfo32.exe"); Title = "CrystalDiskInfo" }
    "CPUID.HWMonitor"                       = @{ Exes = @("HWMonitor.exe"); Title = "HWMonitor" }
    "Almico.SpeedFan"                       = @{ Exes = @("speedfan.exe"); Title = "SpeedFan" }
    "Piriform.Speccy"                       = @{ Exes = @("Speccy64.exe", "Speccy.exe"); Title = "Speccy" }
    "CrystalDewWorld.CrystalDiskMark"       = @{ Exes = @("DiskMark64.exe", "DiskMark32.exe"); Title = "CrystalDiskMark" }
    "WiseCleaner.WiseRegistryCleaner"       = @{ Exes = @("WiseRegCleaner.exe"); Title = "Wise Registry Cleaner" }

    # Ổ đĩa ảo & Backup
    "EZBSystems.UltraISO"                   = @{ Exes = @("UltraISO.exe"); Title = "UltraISO" }
    "AOMEI.PartitionAssistant"              = @{ Exes = @("PartAssist.exe"); Title = "AOMEI Partition Assistant" }
    "AOMEI.Backupper.Standard"              = @{ Exes = @("Backupper.exe"); Title = "AOMEI Backupper" }
    "EaseUS.TodoBackup"                     = @{ Exes = @("TbBackupUI.exe"); Title = "EaseUS Todo Backup" }
    "EaseUS.PartitionMaster"                = @{ Exes = @("Main.exe"); Title = "EaseUS Partition Master" }

    # Bảo mật & Diệt virus
    "Malwarebytes.Malwarebytes"             = @{ Exes = @("mbam.exe"); Title = "Malwarebytes" }
    "AdGuard.AdGuard"                       = @{ Exes = @("Adguard.exe"); Title = "AdGuard" }
    "Bitdefender.Bitdefender"               = @{ Exes = @("bdagent.exe"); Title = "Bitdefender" }
    "Bitwarden.Bitwarden"                   = @{ Exes = @("Bitwarden.exe"); Title = "Bitwarden" }
    "GlassWire.GlassWire"                   = @{ Exes = @("GlassWire.exe"); Title = "GlassWire" }
    "Proton.ProtonVPN"                      = @{ Exes = @("ProtonVPN.exe"); Title = "Proton VPN" }
    "Cloudflare.Warp"                       = @{ Exes = @("Cloudflare WARP.exe"); Title = "Cloudflare WARP" }
    "NordSecurity.NordVPN"                  = @{ Exes = @("NordVPN.exe"); Title = "NordVPN" }

    # Lập trình & DevTools
    "Microsoft.VisualStudioCode"            = @{ Exes = @("Code.exe"); Title = "Visual Studio Code" }
    "JetBrains.Toolbox"                     = @{ Exes = @("jetbrains-toolbox.exe"); Title = "JetBrains Toolbox" }
    "Git.Git"                               = @{ Exes = @("git-bash.exe"); PreferredLnk = "*Git Bash*.lnk"; Title = "Git Bash" }
    "Python.Python.3.12"                    = @{ Exes = @("python.exe"); Title = "Python 3.12" }
    "OpenJS.NodeJS"                         = @{ Exes = @("node.exe"); Title = "Node.js" }
    "Oracle.JDK.21"                         = @{ Exes = @("java.exe"); Title = "Java JDK 21" }
    "Postman.Postman"                       = @{ Exes = @("Postman.exe"); Title = "Postman" }
    "DBeaver.DBeaver.Community"             = @{ Exes = @("dbeaver.exe"); Title = "DBeaver" }
    "HeidiSQL.HeidiSQL"                     = @{ Exes = @("heidisql.exe"); Title = "HeidiSQL" }
    "Docker.DockerDesktop"                  = @{ Exes = @("Docker Desktop.exe"); Title = "Docker Desktop" }
    "GitHub.GitHubDesktop"                  = @{ Exes = @("GitHubDesktop.exe"); Title = "GitHub Desktop" }
    "Insomnia.Insomnia"                     = @{ Exes = @("Insomnia.exe"); Title = "Insomnia" }
    "Wampserver.Wampserver"                 = @{ Exes = @("wampmanager.exe"); Title = "WampServer" }

    # Mạng xã hội & Giải trí
    "Valve.Steam"                           = @{ Exes = @("steam.exe"); Title = "Steam" }
    "EpicGames.EpicGamesLauncher"           = @{ Exes = @("EpicGamesLauncher.exe"); Title = "Epic Games Launcher" }
    "PeterPawlowski.foobar2000"             = @{ Exes = @("foobar2000.exe"); Title = "foobar2000" }
    "AIMP.AIMP"                             = @{ Exes = @("AIMP.exe"); Title = "AIMP" }
    "Tencent.TencentMeeting"                = @{ Exes = @("wemeetapp.exe"); Title = "Tencent Meeting" }
    "Meltytech.Shotcut"                     = @{ Exes = @("shotcut.exe"); Title = "Shotcut" }

    # Đồ hoạ & Thiết kế
    "Canva.Canva"                           = @{ Exes = @("Canva.exe"); Title = "Canva" }
    "Figma.Figma"                           = @{ Exes = @("Figma.exe"); Title = "Figma" }
    "KDE.Krita"                             = @{ Exes = @("krita.exe"); Title = "Krita" }
    "BlenderFoundation.Blender"             = @{ Exes = @("blender.exe"); Title = "Blender" }
    "IrfanSkiljan.IrfanView"                = @{ Exes = @("i_view64.exe", "i_view32.exe"); Title = "IrfanView" }
    "XnSoft.XnView.Classic"                 = @{ Exes = @("xnview.exe"); Title = "XnView" }

    # Kế toán & Tài chính
    "GnuCash.GnuCash"                       = @{ Exes = @("gnucash.exe"); Title = "GnuCash" }
    "moneymanagerex.moneymanagerex"         = @{ Exes = @("mmex.exe"); Title = "Money Manager Ex" }
    "HomeBank.HomeBank"                     = @{ Exes = @("homebank.exe"); Title = "HomeBank" }
    "Microsoft.PowerBI"                     = @{ Exes = @("PBIDesktop.exe"); Title = "Power BI Desktop" }

    # Cloud & Lưu trữ
    "Google.GoogleDrive"                    = @{ Exes = @("GoogleDriveFS.exe"); Title = "Google Drive" }
    "Dropbox.Dropbox"                       = @{ Exes = @("Dropbox.exe"); Title = "Dropbox" }
    "Microsoft.OneDrive"                    = @{ Exes = @("OneDrive.exe"); Title = "OneDrive" }
    "Mega.MEGASync"                         = @{ Exes = @("MEGAsync.exe"); Title = "MEGAsync" }
    "pCloudAG.pCloudDrive"                  = @{ Exes = @("pCloud.exe"); Title = "pCloud Drive" }
    "Nextcloud.NextcloudDesktop"            = @{ Exes = @("nextcloud.exe"); Title = "Nextcloud" }
    "Box.Box"                               = @{ Exes = @("Box.exe"); Title = "Box Drive" }

    # Công cụ mạng
    "WiresharkFoundation.Wireshark"         = @{ Exes = @("Wireshark.exe"); Title = "Wireshark" }
    "OpenVPNTechnologies.OpenVPN"           = @{ Exes = @("openvpn-gui.exe"); Title = "OpenVPN" }
    "angryziber.AngryIPScanner"             = @{ Exes = @("ipscan.exe"); Title = "Angry IP Scanner" }
    "Insecure.Nmap"                         = @{ Exes = @("zenmap.exe"); Title = "Nmap Zenmap" }
    "mRemoteNG.mRemoteNG"                   = @{ Exes = @("mRemoteNG.exe"); Title = "mRemoteNG" }
}

function Find-InstalledAppTarget {
    param(
        [string]$PackageId,
        [string]$PackageName
    )

    $cleanName = ($PackageName -replace "\(.*?\)", "").Trim()
    $token = ($cleanName -split "[\s\-_]+")[0]

    # Priority 1: Check known targets table if available
    if ($GLOBAL:KNOWN_APP_TARGETS -and $GLOBAL:KNOWN_APP_TARGETS.ContainsKey($PackageId)) {
        $info = $GLOBAL:KNOWN_APP_TARGETS[$PackageId]
        $exes = if ($info -is [hashtable] -and $info.Exes) { $info.Exes } else { @($info) }
        $title = if ($info -is [hashtable] -and $info.Title) { $info.Title } else { $cleanName }

        # If a preferred Start Menu lnk pattern is defined, check it first
        if ($info -is [hashtable] -and $info.PreferredLnk) {
            $startDirs = @([Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('CommonPrograms')) | Where-Object { $_ -and (Test-Path $_) }
            $prefMatch = Get-ChildItem -Path $startDirs -Recurse -Filter $info.PreferredLnk -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($prefMatch) {
                return @{ Type = "Shortcut"; Path = $prefMatch.FullName; Title = $title }
            }
        }

        # Check App Paths for known executables
        foreach ($exe in $exes) {
            $ap = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\$exe" -ErrorAction SilentlyContinue
            if ($ap -and $ap.'(default)' -and (Test-Path $ap.'(default)')) {
                return @{ Type = "Executable"; Path = $ap.'(default)'; Title = $title }
            }
            $apUser = Get-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\$exe" -ErrorAction SilentlyContinue
            if ($apUser -and $apUser.'(default)' -and (Test-Path $apUser.'(default)')) {
                return @{ Type = "Executable"; Path = $apUser.'(default)'; Title = $title }
            }
        }
    }

    # Priority 2: Check Start Menu Programs .lnk files (User and Common)
    $startDirs = @(
        [Environment]::GetFolderPath('Programs'),
        [Environment]::GetFolderPath('CommonPrograms')
    ) | Where-Object { $_ -and (Test-Path $_) }

    $allLnks = Get-ChildItem -Path $startDirs -Recurse -Filter "*.lnk" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -notmatch "uninstall|unins|gỡ|help|readme|doc|update|release|license|install" -and
            ($_.Name -match [regex]::Escape($token) -or $_.DirectoryName -match [regex]::Escape($token))
        }

    if ($allLnks) {
        $bestLnk = $allLnks | Sort-Object {
            if ($_.BaseName -match "^$token") { 0 } else { 1 }
        }, { $_.FullName.Length } | Select-Object -First 1

        if ($bestLnk) {
            return @{
                Type = "Shortcut"
                Path = $bestLnk.FullName
                Title = $bestLnk.BaseName
            }
        }
    }

    # Priority 3: Check Registry Uninstall entries (DisplayIcon & InstallLocation)
    $regKeys = @(
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    $regMatches = Get-ItemProperty -Path $regKeys -ErrorAction SilentlyContinue |
        Where-Object {
            ($_.DisplayName -and $_.DisplayName -match [regex]::Escape($token)) -or
            ($_.PSChildName -and $_.PSChildName -match [regex]::Escape($PackageId))
        }

    foreach ($m in $regMatches) {
        if ($m.DisplayIcon) {
            $rawIcon = ($m.DisplayIcon -split ",")[0].Trim().Trim('"')
            if ($rawIcon.EndsWith(".exe", [System.StringComparison]::OrdinalIgnoreCase) -and (Test-Path $rawIcon)) {
                return @{ Type = "Executable"; Path = $rawIcon; Title = $cleanName }
            }
        }
        if ($m.InstallLocation -and (Test-Path $m.InstallLocation)) {
            $exes = Get-ChildItem -Path $m.InstallLocation -Filter "*.exe" -Depth 1 -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -notmatch "uninstall|unins|helper|update|crash|setup" } |
                Sort-Object { if ($_.BaseName -match [regex]::Escape($token)) { 0 } else { 1 } }, Length -Descending

            if ($exes) {
                return @{ Type = "Executable"; Path = $exes[0].FullName; Title = $cleanName }
            }
        }
        if ($m.UninstallString) {
            $uStr = ($m.UninstallString -split '"')[1]
            if (-not $uStr) { $uStr = ($m.UninstallString -split ' ')[0] }
            if ($uStr -and (Test-Path $uStr)) {
                $uDir = [System.IO.Path]::GetDirectoryName($uStr)
                if ($uDir -and (Test-Path $uDir)) {
                    $exes = Get-ChildItem -Path $uDir -Filter "*.exe" -Depth 1 -ErrorAction SilentlyContinue |
                        Where-Object { $_.Name -notmatch "uninstall|unins|helper|update|crash|setup" } |
                        Sort-Object { if ($_.BaseName -match [regex]::Escape($token)) { 0 } else { 1 } }, Length -Descending
                    if ($exes) {
                        return @{ Type = "Executable"; Path = $exes[0].FullName; Title = $cleanName }
                    }
                }
            }
        }
    }

    # Priority 4: Check Winget Links Shim directory
    $wingetLinks = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links",
        "$env:ProgramFiles\WinGet\Links"
    )
    foreach ($wDir in $wingetLinks) {
        if (Test-Path $wDir) {
            $linkFiles = Get-ChildItem -Path $wDir -Filter "*.exe" -ErrorAction SilentlyContinue |
                Where-Object { $_.BaseName -match [regex]::Escape($token) }
            if ($linkFiles) {
                return @{ Type = "Executable"; Path = $linkFiles[0].FullName; Title = $cleanName }
            }
        }
    }

    return $null
}

function Pin-AppShortcuts {
    param(
        [string]$PackageId,
        [string]$PackageName
    )

    $targetInfo = Find-InstalledAppTarget -PackageId $PackageId -PackageName $PackageName
    if (-not $targetInfo) {
        return @{
            Success = $false
            Message = "Khong tim thay tap tin thuc thi (.exe) hoac shortcut goc cua ung dung."
            CreatedCount = 0
            Paths = @()
        }
    }

    $title = if ($targetInfo.Title) { $targetInfo.Title } else { $PackageName }
    $cleanTitle = ($title -replace '[\\/:*?"<>|]', '').Trim()
    if ([string]::IsNullOrWhiteSpace($cleanTitle)) { $cleanTitle = $PackageId }
    $lnkFileName = "$cleanTitle.lnk"

    # 3 Must-Have Locations:
    # 1. Desktop: [Environment]::GetFolderPath('Desktop')
    $desktopFolder = [Environment]::GetFolderPath('Desktop')
    # 2. Programs (Start Menu Programs): [Environment]::GetFolderPath('Programs')
    $programsFolder = [Environment]::GetFolderPath('Programs')
    # 3. Start Menu (Root): [Environment]::GetFolderPath('StartMenu')
    $startMenuFolder = [Environment]::GetFolderPath('StartMenu')

    $destinations = @($desktopFolder, $programsFolder, $startMenuFolder) | Where-Object { $_ -and (Test-Path $_) }

    $createdPaths = @()
    $ws = New-Object -ComObject WScript.Shell

    try {
        if ($targetInfo.Type -eq "Shortcut") {
            foreach ($dest in $destinations) {
                $destLnk = Join-Path $dest $lnkFileName
                if ($destLnk -ne $targetInfo.Path) {
                    Copy-Item -Path $targetInfo.Path -Destination $destLnk -Force -ErrorAction SilentlyContinue
                }
                if (Test-Path $destLnk) { $createdPaths += $destLnk }
            }
        } else {
            $exePath = $targetInfo.Path
            $workDir = [System.IO.Path]::GetDirectoryName($exePath)

            foreach ($dest in $destinations) {
                $destLnk = Join-Path $dest $lnkFileName
                $sc = $ws.CreateShortcut($destLnk)
                $sc.TargetPath = $exePath
                $sc.WorkingDirectory = $workDir
                $sc.IconLocation = "$exePath,0"
                $sc.Save()
                if (Test-Path $destLnk) { $createdPaths += $destLnk }
            }
        }
    } catch {
        # Continue even if single shortcut fails
    } finally {
        try { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ws) | Out-Null } catch {}
    }

    # Attempt Pin to Start Menu via shell verbs if supported
    try {
        $sh = New-Object -ComObject Shell.Application
        foreach ($lnk in $createdPaths) {
            $pDir = [System.IO.Path]::GetDirectoryName($lnk)
            $fName = [System.IO.Path]::GetFileName($lnk)
            $ns = $sh.Namespace($pDir)
            if ($ns) {
                $it = $ns.ParseName($fName)
                if ($it) {
                    foreach ($v in $it.Verbs()) {
                        $vName = $v.Name.Replace('&', '').ToLower()
                        if ($vName -match "pin to start|ghim vào start|pintostartscreen") {
                            $v.DoIt()
                        }
                    }
                }
            }
        }
    } catch {}

    # Refresh Windows Shell Icon Cache
    try { [ShellRefreshHelper]::Refresh() } catch {}

    return @{
        Success = ($createdPaths.Count -gt 0)
        Target = $targetInfo.Path
        Title = $cleanTitle
        CreatedCount = $createdPaths.Count
        Paths = $createdPaths
    }
}

# Neu chi dot-source de dung ham hoac khong truyen tham so hang doi thi dung tai day
if ([string]::IsNullOrWhiteSpace($QueueFile) -and [string]::IsNullOrWhiteSpace($StatusFile)) {
    return
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

            # Tu dong ghim & tao shortcut chinh xac ra Desktop, Start Menu, Programs
            $pinRes = Pin-AppShortcuts -PackageId $wid -PackageName $pkgName
            if ($pinRes.Success) {
                $logLines.Add("[$(Now)] [$idx/$total] [GHIM] Da ghim chinh xac ung dung '$($pinRes.Title)' ra Desktop, Start Menu va Programs ($($pinRes.CreatedCount) vi tri)")
            } else {
                $logLines.Add("[$(Now)] [$idx/$total] [CANH BAO] Khong the tu dong ghim ${pkgName}: $($pinRes.Message)")
            }
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
