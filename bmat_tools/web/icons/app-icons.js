/**
 * App Icon Registry - Kho phan mem Free
 * Anh xa winget ID -> icon URL hoac SVG inline
 *
 * Nguon icon:
 *   - Simple Icons CDN: https://cdn.simpleicons.org/{slug}
 *   - Inline SVG cho cac app khong co tren Simple Icons
 *
 * De them icon moi:
 *   1. Tim slug tai https://simpleicons.org
 *   2. Them entry: "winget.id": { type: "simpleicons", slug: "slug", color: "#HEX" }
 *      Hoac: "winget.id": { type: "svg", svg: "base64_or_datauri" }
 *      Hoac: "winget.id": { type: "img", url: "https://..." }
 */

window.APP_ICONS = {
  // TRINH DUYET
  "CocCoc.CocCoc":   { type:"letter", letter:"CC", bg:"#3AB4F2", fg:"white" },
  "Google.Chrome":   { type:"simpleicons", slug:"googlechrome",         color:"#4285F4" },
  "Microsoft.Edge":  { type:"simpleicons", slug:"microsoftedge",        color:"#0078D4" },
  "Mozilla.Firefox": { type:"simpleicons", slug:"firefox",              color:"#FF7139" },
  "Brave.Brave":     { type:"simpleicons", slug:"brave",                color:"#FB542B" },
  "Opera.Opera":     { type:"simpleicons", slug:"opera",                color:"#FF1B2D" },
  "Opera.OperaGX":   { type:"simpleicons", slug:"opera",                color:"#9b1fe8" },
  "Vivaldi.Vivaldi": { type:"simpleicons", slug:"vivaldi",              color:"#EF3939" },

  // BO GO
  "UniKey.UniKey":   { type:"letter", letter:"U",  bg:"#d32f2f", fg:"white" },
  "EVKeyVN.EVKey":   { type:"letter", letter:"EV", bg:"#1565C0", fg:"white" },

  // GIAI NEN
  "7zip.7zip":               { type:"simpleicons", slug:"7zip",      color:"#009ACD" },
  "RARLab.WinRAR":           { type:"letter", letter:"RAR", bg:"#8D181A", fg:"white" },
  "Bandisoft.Bandizip":      { type:"letter", letter:"BZ",  bg:"#1A74E0", fg:"white" },

  // DOWNLOAD
  "SoftDeluxe.FreeDownloadManager": { type:"simpleicons", slug:"freedownloadmanager", color:"#00A651" },
  "qBittorrent.qBittorrent":        { type:"simpleicons", slug:"qbittorrent",          color:"#2F67BA" },
  "Tonec.InternetDownloadManager":  { type:"letter", letter:"IDM", bg:"#009900", fg:"white" },

  // PDF
  "Foxit.FoxitReader":             { type:"letter", letter:"FX",  bg:"#E62923", fg:"white" },
  "SumatraPDF.SumatraPDF":         { type:"letter", letter:"SPDF", bg:"#DB0707", fg:"white" },
  "Adobe.Acrobat.Reader.64-bit":   { type:"letter", letter:"PDF", bg:"#EC1C24", fg:"white" },

  // CHAT
  "Telegram.TelegramDesktop": { type:"simpleicons", slug:"telegram",       color:"#26A5E4" },
  "Zoom.Zoom":                 { type:"simpleicons", slug:"zoom",           color:"#2D8CFF" },
  "Discord.Discord":           { type:"simpleicons", slug:"discord",        color:"#5865F2" },
  "Microsoft.Teams":           { type:"letter", letter:"Teams", bg:"#5558AF", fg:"white" },
  "Viber.Viber":               { type:"simpleicons", slug:"viber",          color:"#7360F2" },

  // VAN PHONG
  "TheDocumentFoundation.LibreOffice": { type:"simpleicons", slug:"libreoffice",    color:"#18A303" },
  "Kingsoft.WPSOffice":                { type:"simpleicons", slug:"wpsoffice",       color:"#C92429" },
  "Notepad++.Notepad++":               { type:"simpleicons", slug:"notepadplusplus", color:"#90E59A" },
  "Microsoft.PowerToys":               { type:"letter", letter:"PT",  bg:"#FFB900", fg:"white" },
  "Obsidian.Obsidian":                 { type:"simpleicons", slug:"obsidian",       color:"#7C3AED" },

  // DA PHUONG TIEN
  "VideoLAN.VLC":        { type:"simpleicons", slug:"vlcmediaplayer", color:"#FF8800" },
  "Kakao.PotPlayer":     { type:"letter", letter:"PP", bg:"#1A1A2E", fg:"#E94560" },
  "OBSProject.OBSStudio":{ type:"simpleicons", slug:"obsstudio",      color:"#302E31" },
  "Spotify.Spotify":     { type:"simpleicons", slug:"spotify",        color:"#1DB954" },
  "ShareX.ShareX":       { type:"simpleicons", slug:"sharex",         color:"#1BAAE1" },

  // TIEN ICH
  "AnyDesk.AnyDesk":           { type:"simpleicons", slug:"anydesk",    color:"#EF443B" },
  "TeamViewer.TeamViewer":     { type:"simpleicons", slug:"teamviewer", color:"#0E8EE9" },
  "DucFabulous.UltraViewer":   { type:"letter", letter:"UV", bg:"#1565C0", fg:"white" },
  "Rufus.Rufus":               { type:"letter", letter:"RUF", bg:"#2c2c54", fg:"#706fd3" },
  "Microsoft.WindowsTerminal": { type:"letter", letter:">_", bg:"#0C0C0C", fg:"#0CFF33" },

  // HE THONG
  "CPUID.CPU-Z":                  { type:"letter", letter:"CPU-Z", bg:"#1C2E4A", fg:"#5B9BD5" },
  "TechPowerUp.GPU-Z":            { type:"letter", letter:"GPU-Z", bg:"#1A1A2E", fg:"#E94560" },
  "CrystalDewWorld.CrystalDiskInfo": { type:"letter", letter:"CDI", bg:"#003087", fg:"#00BFFF" },
  "REALiX.HWiNFO":               { type:"letter", letter:"HWi",  bg:"#002B5B", fg:"#00AEEF" },

  // BAO MAT
  "Malwarebytes.Malwarebytes": { type:"simpleicons", slug:"malwarebytes", color:"#00A4BD" },
  "Bitwarden.Bitwarden":       { type:"simpleicons", slug:"bitwarden",    color:"#175DDC" },
  "ProtonVPN.ProtonVPN":       { type:"simpleicons", slug:"protonvpn",    color:"#6D4AFF" },

  // LAP TRINH
  "Microsoft.VisualStudioCode": { type:"simpleicons", slug:"visualstudiocode", color:"#007ACC" },
  "Git.Git":                    { type:"simpleicons", slug:"git",              color:"#F05032" },
  "Python.Python.3.12":         { type:"simpleicons", slug:"python",           color:"#3776AB" },
  "Docker.DockerDesktop":       { type:"simpleicons", slug:"docker",           color:"#2496ED" },

  // MANG XA HOI
  "Valve.Steam":          { type:"simpleicons", slug:"steam",     color:"#1B2838" },
  "Facebook.Messenger":   { type:"simpleicons", slug:"messenger", color:"#00B2FF" },

  // DO HOA
  "Canva.Canva":              { type:"simpleicons", slug:"canva",   color:"#00C4CC" },
  "Figma.Figma":              { type:"simpleicons", slug:"figma",   color:"#F24E1E" },
  "BlenderFoundation.Blender":{ type:"simpleicons", slug:"blender", color:"#F5792A" },

  // KE TOAN
  "GnuCash.GnuCash":   { type:"letter", letter:"$", bg:"#2E7D32", fg:"white" },
  "Microsoft.PowerBI": { type:"simpleicons", slug:"powerbi", color:"#F2C811" },

  // CLOUD
  "Google.GoogleDrive": { type:"simpleicons", slug:"googledrive", color:"#4285F4" },
  "Mega.MEGASync":      { type:"simpleicons", slug:"mega",        color:"#D9272E" },

  // CONG CU MANG
  "Wireshark.Wireshark": { type:"simpleicons", slug:"wireshark",  color:"#1679A7" },
  "Cloudflare.Warp":     { type:"simpleicons", slug:"cloudflare", color:"#F48120" },
};

/**
 * Tra ve HTML img hoac span cho mot winget app ID
 * @param {string} appId - Winget Package ID
 * @param {number} size  - Kich thuoc icon (px), mac dinh 28
 * @returns {string} HTML string
 */
window.getAppIconHtml = function(appId, size) {
  if (!size) size = 28;
  var entry = window.APP_ICONS[appId];
  var s = "width:" + size + "px;height:" + size + "px;object-fit:contain;display:inline-block;vertical-align:middle;flex-shrink:0;border-radius:4px;";

  if (!entry) {
    return '<span style="font-size:' + (size * 0.75) + 'px;width:' + size + 'px;height:' + size + 'px;display:inline-flex;align-items:center;justify-content:center;">📦</span>';
  }

  if (entry.type === "simpleicons") {
    var color = (entry.color || "#555555").replace("#", "");
    var url = "https://cdn.simpleicons.org/" + entry.slug + "/" + color;
    return '<img src="' + url + '" alt="' + appId + '" style="' + s + '" loading="lazy" onerror="this.replaceWith(Object.assign(document.createElement(\'span\'),{textContent:\'📦\',style:\'font-size:' + Math.round(size * 0.75) + 'px\'}))">';
  }

  if (entry.type === "letter") {
    var fs = size > 24 ? Math.round(size * 0.35) : Math.round(size * 0.4);
    if (entry.letter.length >= 4) fs = Math.round(size * 0.28);
    else if (entry.letter.length === 3) fs = Math.round(size * 0.32);
    return '<span style="width:' + size + 'px;height:' + size + 'px;display:inline-flex;align-items:center;justify-content:center;background:' + (entry.bg || "#555") + ';color:' + (entry.fg || "white") + ';font-weight:800;font-size:' + fs + 'px;font-family:Arial,sans-serif;border-radius:6px;flex-shrink:0;letter-spacing:-0.5px;">' + entry.letter + '</span>';
  }

  if (entry.type === "img") {
    return '<img src="' + entry.url + '" alt="' + appId + '" style="' + s + '" loading="lazy">';
  }

  return '<span style="font-size:' + (size * 0.75) + 'px;width:' + size + 'px;height:' + size + 'px;display:inline-flex;align-items:center;justify-content:center;">📦</span>';
};
