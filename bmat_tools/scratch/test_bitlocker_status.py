import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subprocess
import re
import psutil

def get_bitlocker_drives():
    drives = []
    # Get all disk partitions from psutil first
    partitions = [p for p in psutil.disk_partitions(all=False) if 'cdrom' not in p.opts and p.fstype]
    
    drive_dict = {}
    for p in partitions:
        mp = p.mountpoint.rstrip('\\')
        usage = None
        try:
            usage = psutil.disk_usage(p.mountpoint)
        except Exception:
            pass
        
        total_gb = f"{usage.total / (1024**3):.1f} GB" if usage else "N/A"
        free_gb = f"{usage.free / (1024**3):.1f} GB" if usage else "N/A"
        
        drive_dict[mp.upper()] = {
            "drive": mp.upper(),
            "label": "",
            "size": total_gb,
            "free_space": free_gb,
            "protection_status": "OFF",
            "protection_status_text": "🔓 Đã Tắt (Unprotected)",
            "encryption_pct": 0,
            "conversion_status": "Fully Decrypted",
            "encryption_method": "None",
            "lock_status": "Unlocked"
        }
        
    # Run manage-bde -status to extract accurate BitLocker details
    try:
        res = subprocess.run(["manage-bde", "-status"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout:
            # Parse volumes
            volumes = res.stdout.split("Volume ")
            for vol in volumes[1:]:
                lines = vol.strip().splitlines()
                if not lines: continue
                # First line: "D: [DATA]" or "C: []"
                m_drive = re.match(r'^([A-Z]:)\s*(?:\[(.*?)\])?', lines[0])
                if not m_drive: continue
                
                mp = m_drive.group(1).upper()
                label = m_drive.group(2) or ""
                
                info = drive_dict.get(mp, {
                    "drive": mp,
                    "label": label,
                    "size": "N/A",
                    "free_space": "N/A",
                    "protection_status": "OFF",
                    "protection_status_text": "🔓 Đã Tắt",
                    "encryption_pct": 0,
                    "conversion_status": "Fully Decrypted",
                    "encryption_method": "None",
                    "lock_status": "Unlocked"
                })
                
                if label:
                    info["label"] = label
                    
                vol_text = "\n".join(lines)
                
                # Protection Status
                m_prot = re.search(r'Protection Status:\s*(.*)', vol_text, re.IGNORECASE)
                prot_val = m_prot.group(1).strip() if m_prot else "Protection Off"
                
                # Conversion Status
                m_conv = re.search(r'Conversion Status:\s*(.*)', vol_text, re.IGNORECASE)
                conv_val = m_conv.group(1).strip() if m_conv else "Fully Decrypted"
                
                # Percentage Encrypted
                m_pct = re.search(r'Percentage Encrypted:\s*([\d\,\.]+)\%', vol_text, re.IGNORECASE)
                pct_val = 0
                if m_pct:
                    try:
                        pct_val = float(m_pct.group(1).replace(',', '.'))
                    except:
                        pass
                        
                # Lock Status
                m_lock = re.search(r'Lock Status:\s*(.*)', vol_text, re.IGNORECASE)
                lock_val = m_lock.group(1).strip() if m_lock else "Unlocked"

                # Encryption Method
                m_meth = re.search(r'Encryption Method:\s*(.*)', vol_text, re.IGNORECASE)
                meth_val = m_meth.group(1).strip() if m_meth else "None"
                
                info["conversion_status"] = conv_val
                info["encryption_pct"] = pct_val
                info["encryption_method"] = meth_val
                info["lock_status"] = lock_val
                
                if "Protection On" in prot_val:
                    info["protection_status"] = "ON"
                    info["protection_status_text"] = "🔒 Đã Bật BitLocker (Protected)"
                elif "Decrypt" in conv_val or "Encrypt" in conv_val:
                    info["protection_status"] = "TRANSITION"
                    info["protection_status_text"] = f"⚡ {conv_val} ({pct_val:.1f}%)"
                else:
                    info["protection_status"] = "OFF"
                    info["protection_status_text"] = "🔓 Đã Tắt (Unprotected)"
                    
                drive_dict[mp] = info
    except Exception as e:
        print("Error running manage-bde:", e)
        
    return list(drive_dict.values())

if __name__ == "__main__":
    drives = get_bitlocker_drives()
    for d in drives:
        print(d)
