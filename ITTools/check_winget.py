import subprocess

candidates = [
    # Trình duyệt
    ("Cốc Cốc", ["CocCoc.CocCoc", "CocCoc.CocCocBrowser"]),
    ("Google Chrome", ["Google.Chrome"]),
    ("Microsoft Edge", ["Microsoft.Edge"]),
    ("Mozilla Firefox", ["Mozilla.Firefox"]),
    ("Brave Browser", ["Brave.BraveBrowser", "Brave.Brave"]),
    ("Opera", ["Opera.Opera"]),
    ("Opera GX", ["Opera.OperaGX"]),
    ("Vivaldi", ["Vivaldi.Vivaldi"]),

    # Bộ gõ
    ("EVKey 6.0", ["EVKey.EVKey", "EVKey"]),
    ("UniKey", ["UniKey.UniKey", "Unikey.Unikey"]),

    # Giải nén
    ("7-Zip", ["7zip.7zip"]),
    ("WinRAR", ["RARLab.WinRAR"]),
    ("PeaZip", ["PeaZip.PeaZip"]),

    # Download
    ("Free Download Manager", ["SoftDeluxe.FreeDownloadManager"]),
    ("qBittorrent", ["qBittorrent.qBittorrent"]),
    ("WinSCP", ["WinSCP.WinSCP"]),

    # PDF
    ("Foxit PDF Reader", ["Foxit.FoxitReader", "Foxit.FoxitPDFReader"]),
    ("SumatraPDF", ["SumatraPDF.SumatraPDF"]),
    ("PDF24 Creator", ["geeksoftwareGmbH.PDF24Creator"]),

    # Fonts
    ("11000 fonts", ["Fonts.Package"]),
    ("FontForge", ["FontForge.FontForge"]),

    # Chat
    ("Zalo PC", ["VNG.Zalo", "VNG.ZaloPC", "Zalo.Zalo"]),
    ("WeChat PC", ["Tencent.WeChat"]),
    ("Telegram", ["Telegram.TelegramDesktop"]),
    ("Zoom Meetings", ["Zoom.Zoom"]),
    ("Discord", ["Discord.Discord"]),

    # Văn phòng
    ("LibreOffice", ["TheDocumentFoundation.LibreOffice"]),
    ("WPS Office", ["Kingsoft.WPSOffice"]),
    ("Notepad++", ["Notepad++.Notepad++"]),
    ("Everything", ["voidtools.Everything"]),

    # Đa phương tiện
    ("VLC Media Player", ["VideoLAN.VLC"]),
    ("PotPlayer", ["Kakao.PotPlayer"]),
    ("KMPlayer", ["PandoraTV.KMPlayer"]),
    ("OBS Studio", ["OBSProject.OBSStudio"]),
    ("GIMP", ["GIMP.GIMP"]),
    ("Audacity", ["Audacity.Audacity"]),

    # Tiện ích
    ("AnyDesk", ["AnyDeskSoftwareGmbH.AnyDesk"]),
    ("TeamViewer", ["TeamViewer.TeamViewer"]),
    ("UltraViewer", ["UltraViewer.UltraViewer", "DucFami.UltraViewer"]),
    ("Rufus", ["Rufus.Rufus"]),
    ("CCleaner", ["Piriform.CCleaner"]),
    ("Revo Uninstaller", ["VSRevoGroup.RevoUninstaller"]),

    # Hệ thống
    ("CPU-Z", ["CPUID.CPU-Z"]),
    ("GPU-Z", ["TechPowerUp.GPU-Z"]),
    ("CrystalDiskInfo", ["CrystalDewWorld.CrystalDiskInfo"]),
    ("HWiNFO", ["REALiX.HWiNFO"])
]

valid = {}
invalid = []

for name, ids in candidates:
    found_id = None
    for id_str in ids:
        r = subprocess.run(f'winget show --id "{id_str}" -e', shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if r.returncode == 0:
            found_id = id_str
            break
    if not found_id:
        # Search winget
        r = subprocess.run(f'winget search "{name}"', shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        lines = [line for line in r.stdout.splitlines() if line.strip()]
        for line in lines[2:]:  # skip header
            parts = line.split()
            if len(parts) >= 2:
                check_id = parts[1]
                r_check = subprocess.run(f'winget show --id "{check_id}" -e', shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
                if r_check.returncode == 0:
                    found_id = check_id
                    break

    if found_id:
        valid[name] = found_id
        print(f"[OK] {name} -> Winget ID: {found_id}")
    else:
        invalid.append(name)
        print(f"[EXCLUDED - NOT ON WINGET] {name}")

print("\n--- VALID SUMMARY ---")
print(f"Total valid: {len(valid)}")
print("Excluded:", invalid)
