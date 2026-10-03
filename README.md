# 🛠️ IT TOOL LTT 2026 - BỘ CÔNG CỤ QUẢN TRỊ & TỐI ƯU WINDOWS TẤT-CẢ-TRONG-MỘT

<div align="center">

![IT Tool LTT Logo](bmat_tools/web/logo.png)

### **GIẢI PHÁP TẤT CẢ TRONG MỘT CHO KỸ THUẬT VIÊN CNTT & QUẢN TRỊ VIÊN WINDOWS**
*Tác giả & Phát triển: **Lê Thế Tuấn** | Hotline/Zalo: **0352 194 195***

[![Author](https://img.shields.io/badge/T%C3%A1c%20Gi%E1%BA%A3-L%C3%AA%20Th%E1%BA%BF%20Tu%E1%BA%A5n-0284c7.svg)](https://lethetuanpc.blogspot.com)
[![Hotline/Zalo](https://img.shields.io/badge/Zalo-0352%20194%20195-0068ff.svg)](https://zalo.me/0352194195)
[![Website](https://img.shields.io/badge/Website-lethetuanpc.blogspot.com-f59e0b.svg)](https://lethetuanpc.blogspot.com)
[![Telegram](https://img.shields.io/badge/Telegram-@lethetuanpc-229ED9.svg)](https://t.me/lethetuanpc)
[![Version](https://img.shields.io/badge/Phi%C3%AAn%20B%E1%BA%A3n-1.0.0%20(2026)-10b981.svg)]()
[![Platform](https://img.shields.io/badge/N%E1%BB%81n%20T%E1%BA%A3ng-Windows%2010%20%7C%2011%20%7C%20Server-blue.svg)]()
[![Single File](https://img.shields.io/badge/Build-Single%20Portable%20.EXE-purple.svg)]()

</div>

---

## 📖 GIỚI THIỆU TỔNG QUAN

**IT Tool LTT 2026** là phần mềm quản trị, bảo trì, cứu hộ và tối ưu hóa hệ thống Windows chuyên nghiệp. Phần mềm được thiết kế nhằm hỗ trợ tối đa cho các kỹ thuật viên IT, kỹ sư máy tính, quản trị viên mạng doanh nghiệp và người dùng nâng cao.

Ứng dụng được đóng gói thành **duy nhất 1 file `.exe` (Portable)**, dung lượng tinh gọn (~43 MB), tích hợp sẵn toàn bộ engine Python, C-runtime, giao diện Webview hiện đại và tài nguyên hệ thống sạch. Người dùng có thể copy vào USB hoặc tải về chạy trực tiếp trên bất kỳ máy tính Windows nào (Windows 10, Windows 11, Windows Server) mà **hoàn toàn không cần cài đặt thêm bất kỳ phần mềm hay thư viện phụ trợ nào**.

---

## 🌟 ĐẶC ĐIỂM NỔI BẬT

- **📦 1 File Thực Thi Duy Nhất (100% Standalone Portable):** Không cần cài đặt Python, Node.js hay Visual C++. Chạy trực tiếp từ USB hoặc ổ cứng trên mọi máy tính.
- **⚡ Tự Động Yêu Cầu Quyền Quản Trị (UAC Elevation Manifest):** Nhúng sẵn manifest `requireAdministrator`. Khi mở ở bất kỳ máy tính nào, Windows sẽ tự động kích hoạt quyền Admin, đảm bảo mọi can thiệp hệ thống (Registry, Service, Firewall, Takeown tệp hệ thống) thực thi thành công 100%.
- **🚀 Quản Lý Khởi Động Cùng Windows Tiện Lợi:** Tích hợp nút gạt bật/tắt tự khởi động ngay trên Header, cấu hình trực tiếp vào Registry `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- **🔍 Quản Lý Đơn Tiến Trình Thông Minh (Single Instance IPC):** Sử dụng socket IPC cục bộ (`127.0.0.1:49285`). Khi ứng dụng đang chạy (hoặc ẩn dưới khay), việc mở lại file exe sẽ ngay lập tức đánh thức và đưa cửa sổ hiện tại lên trên cùng màn hình mà không mở trùng lặp tiến trình thừa.
- **🔽 Khay Hệ Thống Thông Minh (System Tray):** Khi nhấn dấu X đỏ, ứng dụng tự động thu nhỏ xuống khay Taskbar để giải phóng màn hình làm việc. Menu chuột phải ở khay hỗ trợ: Hiện giao diện, Mở Website, Gọi Zalo, Mở Telegram, Thoát hoàn toàn.
- **⚡ Vận Hành Không Nhấp Nháy (Zero-Flicker):** Cơ chế hook cấp thấp triệt tiêu hoàn toàn các cửa sổ đen dòng lệnh (`CREATE_NO_WINDOW`) cho toàn bộ các lệnh PowerShell, CMD, netsh, sc, reg ngầm.
- **🌓 Giao Diện Chuẩn Web Đỉnh Cao:** Render bằng Microsoft Edge WebView2 mượt mà, hỗ trợ giao diện Sáng / Tối (Light / Dark Mode), phóng to/thu nhỏ tỷ lệ hiển thị linh hoạt (Zoom 70% - 100%).
- **📋 Nhật Ký Hệ Thống Thời Gian Thực (Live Terminal & Drawer Log):** Hiển thị chi tiết từng câu lệnh DOS/PowerShell đang chạy, mã lệnh, thời gian và trạng thái trực quan.

---

## 📑 BẢN ĐỒ TÍNH NĂNG CHI TIẾT (27 PHÂN HỆ)

Phần mềm được phân loại khoa học thành **4 nhóm chuyên đề chính** với **27 phân hệ tính năng chuyên sâu**:

```
IT Tool LTT 2026
├── 🖥️ 1. HỆ THỐNG & CẤU HÌNH
│   ├── 💻 Check Cấu Hình (Computer Info & Audit)
│   ├── 🩺 Test Computer (Bộ Chẩn Đoán Phần Cứng Toàn Diện)
│   ├── 💿 Cài Win & Update (Windows Setup & Update Manager)
│   ├── 🚀 Startup Manager (Quản Lý Khởi Động)
│   ├── 🗑️ Uninstall Manager (Gỡ Cài Đặt Nhanh Ứng Dụng)
│   └── 🔒 Tắt BitLocker & EFS (BitLocker & Drive Encryption)
│
├── 🖨️ 2. MẠNG & MÁY IN
│   ├── 🖨️ Fix Máy In - Share LAN (Chuyên Trị Lỗi In Mạng LAN & USB)
│   │   └── ★ ONE CLICK FIX TẤT CẢ LỖI MÁY IN (Quy Trình 4 Bước Chuẩn)
│   ├── 🌐 IP Manager & Subnet (Cấu Hình IP & Tính Dải Mạng)
│   ├── 🔍 IP Scanner (Quét Thiết Bị Mạng LAN Đa Luồng)
│   ├── 🛡️ Firewall Manager (Quản Lý Tường Lửa)
│   └── 🖧 Server Tools (Công Cụ Máy Chủ & Dịch Vụ Mạng)
│
├── 🛠️ 3. TIỆN ÍCH WINDOWS
│   ├── 🔍 Zoom Screen (Phóng To, Vẽ Chú Thích, Quay Chụp & Break Timer)
│   ├── ⏻ Auto Shutdown (Hẹn Giờ Tắt / Bật / Khởi Động Lại)
│   ├── 📝 Hosts File Editor (Chỉnh Sửa File Hosts Hệ Thống)
│   ├── 📤 SendTo Editor (Tùy Biến Menu Chuột Phải Send To)
│   ├── 🪟 Classic Win10 Menu (Bật Menu Chuột Phải Win 10 trên Win 11)
│   ├── 🖥️ Desktop Icon (Bật / Tắt Icon Màn Hình Chính)
│   ├── 🕐 Date Time Config (Cấu Hình Ngày Giờ & Đồng Bộ NTP)
│   ├── ⚙️ Boot Manager (Quản Lý Menu Khởi Động BCD)
│   ├── ⚙️ Services Manager (Quản Trị Dịch Vụ Windows)
│   ├── 📁 Folder Size Analyzer (Phân Tích Dung Lượng Ổ Đĩa)
│   ├── 💰 Currency Converter (Quy Đổi Ngoại Tệ Trực Tuyến)
│   └── 🔧 Other System Tweaks (Tinh Chỉnh & Tối Ưu Hệ Thống)
│
└── 🔄 4. SAO LƯU & PHẦN MỀM
    ├── 📊 Cài Đặt Office (Office Silent Installer Tự Động)
    ├── 🔑 Kích Hoạt - Gỡ Crack (Bản Quyền & Gỡ Mã Độc Crack)
    ├── 💾 Backup Restore Driver (Sao Lưu & Phục Hồi Driver)
    ├── 🔄 Browser Backup Restore (Sao Lưu Dữ Liệu Trình Duyệt)
    └── 📦 Kho Phần Mềm Free (Winget Package Manager)
```

---

### 🖥️ KHỐI 1: HỆ THỐNG & CẤU HÌNH

#### 1.1. Check Cấu Hình (Computer Info & Audit)
- **Kiểm tra thông số phần cứng & hệ điều hành chuyên sâu:** Tên máy (Hostname), phiên bản Windows (Edition, Version, OS Build, Architecture), vi xử lý (CPU Model, số nhân Core, số luồng Thread, xung nhịp hiện tại), dung lượng RAM (Tổng RAM, RAM khả dụng, Bus, số khe cắm), Mainboard (Hãng sản xuất, Model, Serial Number), Card đồ họa (GPU Model, VRAM, Driver Version), BIOS (Phiên bản, Ngày phát hành, Chuẩn UEFI hoặc Legacy).
- **Phân vùng ổ cứng:** Dung lượng tổng, dung lượng đã dùng, dung lượng trống của từng phân vùng (C, D, E...).
- **Xuất báo cáo:** Xuất thông tin cấu hình ra định dạng văn bản để gửi khách hàng hoặc dán vào phiếu bảo hành máy tính.

#### 1.2. 🩺 Test Computer (Bộ Chẩn Đoán Phần Cứng Toàn Diện)
Tích hợp bộ công cụ kiểm tra sức khỏe thiết bị trực quan bằng công nghệ Web Audio, Web Canvas và Vue 3 Engine:
1. **Kiểm tra bàn phím (Keyboard Diagnostics):** Hỗ trợ đầy đủ layout Fullsize 100%, TKL 80%, Compact 60%, layout Windows và Mac. Ghi nhận lịch sử phím bấm, kiểm tra kẹt phím, đo chỉ số APM (Actions Per Minute) và CPS (Clicks Per Second).
2. **Kiểm tra chuột & switch (Mouse & Switch Test):** Đo tốc độ bấm, kiểm tra hiện tượng double-click switch trái/phải, bài test giữ chuột liên tục (Hold Test) và điều chỉnh ngưỡng debounce ms.
3. **Kiểm tra màn hình & điểm chết (Screen Pixel Checker):** Kiểm tra điểm chết (Dead/Stuck Pixel) toàn màn hình qua 5 dải màu thuần khiết (Đỏ, Lục, Lam, Trắng, Đen) và dải màu tương phản.
4. **Kiểm tra Webcam:** Quét danh sách thiết bị ghi hình kết nối vào máy và hiển thị luồng video preview trực tiếp với độ phân giải thực.
5. **Kiểm tra Microphone:** Bộ phân tích cường độ âm thanh thời gian thực (Audio Level VU Meter), điều chỉnh Gain Control và ghi âm phát lại tức thì để kiểm tra chất lượng mic.
6. **Kiểm tra Loa & Bộ tổng hợp âm thanh (Speaker Synthesizer):** Phát tần số âm trầm Bass (80Hz), âm trung Mid (1KHz), âm cao Treble (8KHz), quét dải tần (Frequency Sweep) và kiểm tra cân bằng 2 kênh Stereo trái / phải.
7. **Kiểm tra Pin Laptop (Battery State & Health):** Báo cáo tình trạng pin, tỷ lệ dung lượng thiết kế so với dung lượng thực tế, mức độ chai pin và trạng thái cắm sạc.
8. **Đo tần số quét màn hình (Display FPS & Refresh Rate):** Đo đạc FPS thực tế, độ trễ khung hình (Jank test), độ mượt cuộn trang và bài test vệt bóng ma màn hình (Ghosting test).

#### 1.3. Cài Win & Update (Windows Setup & Update Manager)
- Bật / Tắt triệt để dịch vụ cập nhật tự động Windows Update chỉ với 1 click.
- Dọn sạch bộ nhớ đệm cập nhật hệ thống (`C:\Windows\SoftwareDistribution\Download`) giúp giải phóng hàng chục GB ổ C.
- Tích hợp hướng dẫn và đường dẫn công cụ tải file ISO Windows chính thức từ Microsoft.

#### 1.4. Startup Manager (Quản Lý Khởi Động)
- Quét toàn diện các vị trí khởi động trên Windows:
  - Registry người dùng: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
  - Registry hệ thống: `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
  - Khởi động 1 lần: `RunOnce (HKCU / HKLM)`
  - Thư mục Startup người dùng: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
  - Thư mục Startup toàn hệ thống: `%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
- Tự động trích xuất icon gốc từ file thực thi `.exe`.
- Bật/Tắt tức thì, Thêm mới (`Add New`), Chỉnh sửa (`Edit`), Xóa (`Delete`) hoặc Chạy thử ngay (`Run Now`).
- **Nút gạt Bật/Tắt tự động mở IT Tool LTT khi bật máy tính.**

#### 1.5. Uninstall Manager (Gỡ Cài Đặt Nhanh)
- Quét nhanh và đầy đủ tất cả phần mềm đã cài đặt trên máy tính (cả ứng dụng 32-bit và 64-bit).
- Tìm kiếm tức thời theo tên phần mềm, lọc theo ngày cài, kích thước chiếm dụng, nhà phát hành và phiên bản.
- Hỗ trợ gỡ cài đặt tiêu chuẩn hoặc kích hoạt chế độ gỡ âm thầm (`Silent Uninstall`).

#### 1.6. Tắt BitLocker & EFS (BitLocker & Drive Encryption)
- Quét trạng thái mã hóa BitLocker trên từng ổ đĩa (Mức độ mã hóa, Trạng thái bảo vệ, Tình trạng khóa).
- Cung cấp tính năng tắt mã hóa BitLocker chỉ với 1 click, giải phóng ổ đĩa bị khóa, tránh mất dữ liệu do quên khóa khôi phục (Recovery Key).
- Giải mã nhanh các tập tin / thư mục bị mã hóa bởi chứng chỉ EFS.

---

### 🖨️ KHỐI 2: MẠNG & MÁY IN

#### 2.1. Fix Máy In - Share LAN (Chuyên Trị Lỗi In Mạng LAN & USB)
- **★ ONE CLICK FIX TẤT CẢ LỖI MÁY IN MẠNG LAN (Quy trình 4 bước chuẩn):**
  1. *Bước 1:* Chiếm quyền sở hữu (`takeown /A /F`) và cấp toàn quyền (`icacls administrators:F SYSTEM:F`), sao lưu các tệp hiện tại thành đuôi `.old` (`spoolsv.exe.old`, `win32spl.dll.old`, `localspl.dll.old`). Nạp các khóa Registry cốt lõi: `RpcAuthnLevelPrivacyEnabled = 0`, `RpcOverNamedPipes = 1`, `RpcOverTcp = 1`, `PointAndPrint`, `forceguest = 0`, `AllowInsecureGuestAuth = 1`.
  2. *Bước 2:* Nạp bộ 3 tệp hệ thống sạch chuẩn (`win32spl.dll`, `localspl.dll`, `spoolsv.exe`) trích xuất trực tiếp từ bundle vào thư mục `C:\Windows\System32`.
  3. *Bước 3:* Cấu hình chế độ khởi động tự động (`Automatic`) cho Print Spooler và các dịch vụ mạng liên quan (`LanmanWorkstation`, `LanmanServer`, `fdPHost`, `FDResPub`, `SSDPSRV`, `upnphost`), khởi động lại dịch vụ Print Spooler.
  4. *Bước 4:* Hoàn tất, giao diện hiển thị thông báo thành công và cho phép in ngay qua mạng LAN.
  - *Giao diện trực quan:* Modal tiến trình hiển thị 4 thẻ bước (Pending / Running / Done), thanh tiến trình % và Terminal hiển thị trực tiếp từng dòng lệnh DOS/PowerShell thực thi theo thời gian thực.
- **Sửa các mã lỗi kinh điển:**
  - Sửa lỗi **0x0000011b** (PrintNightmare sau các bản vá KB Windows).
  - Sửa lỗi **0x00000709** (Không kết nối được tên máy in chia sẻ).
  - Sửa lỗi **0x0000007c**, **0x00000bcb**, **0x000006ba**, **0x000006d9**.
- **Chuyên trị máy in Canon LBP 2900 / 3300:** Reset toàn diện hàng đợi in, xóa USB Monitor trong Registry, xóa cổng mạng CNBJNP, sao chép `mscms.dll` và hướng dẫn nhận lại máy in sau 10 giây.
- **Tiện ích mở rộng:**
  - Tự động gỡ sạch hàng đợi in bị kẹt (`%SystemRoot%\System32\spool\PRINTERS`).
  - Gỡ bỏ driver máy in cũ thông qua công cụ hệ thống `pnputil`.
  - Mở khóa chia sẻ máy in (Unlock Share Printer).
  - Thêm Windows Credentials đăng nhập mạng LAN không cần nhập lại mật khẩu.
  - Mở tường lửa (Firewall) cho nhóm File and Printer Sharing và Network Discovery.

#### 2.2. IP Manager & Subnet (Quản Lý Địa Chỉ IP Card Mạng)
- Liệt kê toàn bộ các card mạng có dây (Ethernet) và không dây (Wi-Fi).
- Chuyển đổi siêu tốc giữa **IP Động (DHCP)** và **IP Tĩnh (Static IP)** chỉ bằng 1 thao tác.
- Tùy chọn nhanh các cặp DNS thông dụng ổn định: Google DNS (`8.8.8.8` / `8.8.4.4`), Cloudflare DNS (`1.1.1.1` / `1.0.0.1`), Quad9, OpenDNS.
- Tích hợp công cụ tính toán dải mạng Subnet Mask (CIDR, Network Address, Broadcast Address, Tổng số IP khả dụng).

#### 2.3. IP Scanner (Quét Thiết Bị Mạng LAN Đa Luồng)
- Tự động nhận diện dải IP hiện tại của mạng nội bộ (ví dụ: `192.168.1.1/24`).
- Quét đồng thời toàn bộ dải 254 địa chỉ IP với tốc độ cực nhanh bằng kỹ thuật đa luồng (Multithreaded).
- Báo cáo rõ ràng: Trạng thái Online, Địa chỉ IP, Tên thiết bị (Hostname), Địa chỉ MAC và Nhà sản xuất card mạng (Vendor OUI).
- Tích hợp nút Ping kiểm tra độ trễ (Latency) trực tiếp trên từng thiết bị.

#### 2.4. Firewall Manager (Quản Lý Tường Lửa Windows)
- Bật / Tắt tường lửa cho cả 3 chế độ (Domain, Private, Public).
- Cho phép mở nhanh (Whitelist) các cổng dịch vụ cần thiết (Port 80 HTTP, 443 HTTPS, 3389 RDP, 445 SMB File Sharing...).
- Khôi phục tường lửa về cài đặt mặc định gốc của Windows.

#### 2.5. Server Tools (Công Cụ Quản Trị Máy Chủ & Dịch Vụ Mạng)
- **Remote Desktop (RDP):** Bật / Tắt tính năng cho phép máy tính khác điều khiển từ xa qua cổng 3389, cấu hình xác thực cấp độ mạng NLA.
- **File Sharing Server:** Quản lý danh sách các thư mục đang được chia sẻ trên máy (Shares List), xem số lượng người dùng đang kết nối.
- **Dịch vụ mạng Windows:** Kích hoạt hoặc vô hiệu hóa các dịch vụ: IIS Web Server, FTP Service, Telnet Client, NetBIOS qua TCP/IP.

---

### 🛠️ KHỐI 3: TIỆN ÍCH WINDOWS

#### 3.1. 🔍 Zoom Screen (Trình Chiếu, Zoom & Ghi Chú Đa Năng)
Giải pháp thay thế và nâng cấp toàn diện cho ZoomIt của Microsoft Sysinternals:
- **Phóng to màn hình (Zoom):** Phóng to mượt mà tại vị trí con trỏ chuột, hỗ trợ cuộn chuột tăng/giảm tỷ lệ phóng.
- **Vẽ & Viết chữ trực tiếp (LiveDraw & Annotate):** Vẽ tự do, đường thẳng, mũi tên, hình chữ nhật, hình elip; gõ văn bản trực tiếp lên màn hình; chuyển đổi nhanh màn hình bảng đen (`K`) hoặc bảng trắng (`W`).
- **Đồng hồ giải lao (Break Timer):** Đếm ngược thời gian nghỉ giải lao với thanh tiến trình và thông báo kết thúc trực quan.
- **LiveZoom:** Phóng to màn hình nhưng vẫn cho phép thao tác chuột và bàn phím tương tác với các ứng dụng bên dưới.
- **Quay & Chụp màn hình (Record & Snip):** Quay video màn hình với định dạng MP4 hoặc chụp ảnh vùng chọn sao chép thẳng vào Clipboard / lưu ra file ảnh.
- **DemoType:** Tự động gõ từng ký tự từ văn bản chuẩn bị trước phục vụ giảng dạy, thuyết trình demo kỹ thuật.
- **Chế độ gương lật & Toàn cảnh (Mirror & Panorama):** Hỗ trợ lật ngược màn hình khi trình chiếu qua máy chiếu ngược hoặc cuộn xem màn hình toàn cảnh.
- **Hệ thống phím tắt toàn cục (Global Hotkeys):**
  - Mặc định: `Ctrl + 1` (Zoom), `Ctrl + 2` (Vẽ), `Ctrl + 3` (Break Timer), `Ctrl + 4` (LiveZoom), `Ctrl + 5` (Record), `Ctrl + 6` (Snip), `Ctrl + 7` (DemoType), `Ctrl + 8` (Panorama), `Ctrl + 9` (Mirror).
  - Cho phép tùy biến phím tắt theo ý muốn.
  - **Tự động kích hoạt ngầm:** Lắng nghe phím tắt ngay từ lúc mở tool hoặc khi thu nhỏ xuống khay Taskbar.

#### 3.2. Auto Shutdown (Hẹn Giờ Tắt / Bật Máy)
- Đa dạng chế độ: Tắt máy (`Shutdown`), Khởi động lại (`Restart`), Ngủ (`Sleep`), Ngủ đông (`Hibernate`).
- Phương thức đặt lịch phong phú: Hẹn giờ đếm ngược (sau số phút / giờ) hoặc hẹn giờ theo mốc thời gian cố định trong ngày (ví dụ: đúng 18:00 hàng ngày).
- Tích hợp nút hủy hẹn giờ nhanh chỉ với 1 click.

#### 3.3. Hosts File Editor (Chỉnh Sửa File Hosts Trực Quan)
- Trực tiếp đọc và chỉnh sửa file hosts hệ thống (`C:\Windows\System32\drivers\etc\hosts`) mà không bị lỗi phân quyền bảo vệ của Windows.
- Thêm nhanh bản ghi Tên miền -> IP tương ứng.
- Khóa / Chặn tên miền quảng cáo hoặc website độc hại.
- Sao lưu dự phòng và khôi phục file hosts gốc của Microsoft khi cần thiết.

#### 3.4. SendTo Editor (Tùy Biến Menu Send To)
- Quản lý danh sách các lối tắt xuất hiện trong menu `Chuột phải -> Send to`.
- Dễ dàng thêm thư mục lưu trữ thường dùng (Google Drive, Dropbox, Ổ D, Ổ E...) vào menu để sao chép dữ liệu nhanh.
- Xóa bỏ các mục thừa không dùng đến giúp menu gọn gàng, tăng tốc chuột phải.

#### 3.5. Classic Win10 Menu (Menu Chuột Phải Cổ Điển Cho Win 11)
- Chuyển đổi menu chuột phải trên Windows 11 về giao diện đầy đủ quen thuộc của Windows 10 (không còn phải bấm *Show more options* hay *Shift + F10*).
- Hỗ trợ khôi phục về menu mặc định của Windows 11 bất kỳ lúc nào chỉ bằng 1 click.

#### 3.6. Desktop Icon (Bật / Tắt Biểu Tượng Hệ Thống)
- Ẩn / Hiện các icon hệ thống quan trọng trên màn hình Desktop:
  - 🖥️ This PC (Computer)
  - 📁 Thư mục người dùng (User's Files)
  - 🌐 Mạng (Network)
  - 🗑️ Thùng rác (Recycle Bin)
  - ⚙️ Control Panel
- Tự động làm mới Explorer để icon hiển thị ngay lập tức mà không cần khởi động lại máy.

#### 3.7. Date Time Config (Cấu Hình Ngày Giờ & Đồng Bộ NTP)
- Đặt múi giờ chuẩn Việt Nam: `(UTC+07:00) Bangkok, Hanoi, Jakarta`.
- Tự động bật dịch vụ Windows Time (`w32time`) và đồng bộ giờ chuẩn xác theo các máy chủ NTP uy tín: `time.windows.com`, `time.google.com`, `pool.ntp.org`.
- Sửa lỗi máy tính bị sai giờ sau khi cài lại Windows hoặc do pin CMOS yếu.

#### 3.8. Boot Manager (Quản Lý Khởi Động BCD)
- Xem danh sách các hệ điều hành đang có trong menu Boot BCD.
- Chỉnh sửa thời gian chờ hiển thị menu Boot (`Boot Timeout`).
- Bật/Tắt chế độ khởi động an toàn (`Safe Mode`) và giao diện kiểm tra cấu hình `msconfig`.

#### 3.9. Services Manager (Quản Trị Dịch Vụ Hệ Thống)
- Liệt kê toàn bộ các dịch vụ hệ thống Windows với tên hiển thị, tên nội bộ, trạng thái đang chạy (`Running`) hay dừng (`Stopped`), và kiểu khởi động (`Automatic`, `Manual`, `Disabled`).
- Tìm kiếm dịch vụ thông minh.
- Cho phép Bắt đầu, Tạm dừng, Khởi động lại dịch vụ hoặc đổi kiểu khởi động trực tiếp.

#### 3.10. Folder Size Analyzer (Phân Tích Dung Lượng Ổ Đĩa)
- Quét và trực quan hóa dung lượng của các thư mục trên ổ cứng.
- Phát hiện các thư mục hoặc tập tin có dung lượng lớn bất thường đang chiếm dụng bộ nhớ để người dùng xem xét dọn dẹp.

#### 3.11. Currency Converter (Quy Đổi Ngoại Tệ Trực Tuyến)
- Chuyển đổi qua lại giữa đồng Việt Nam (VNĐ) và các loại ngoại tệ phổ biến trên thế giới: USD, EUR, JPY, GBP, CNY, KRW, SGD...
- Cập nhật tỷ giá trực tiếp, hỗ trợ tính toán tài chính nhanh chóng ngay trong công việc.

#### 3.12. Other System Tweaks (Bộ Tinh Chỉnh Nâng Cao)
- Kích hoạt gói năng lượng hiệu suất cao nhất: **Ultimate Performance Power Plan**.
- Bật / Tắt chế độ ngủ đông (`Hibernate - hiberfil.sys`) để giải phóng hàng chục GB ổ C.
- Xóa sạch rác tạm hệ thống: `%TEMP%`, `Prefetch`, `C:\Windows\Temp`.
- Tắt hiệu ứng làm mờ / hoạt ảnh thừa để tăng tốc tối đa cho các máy tính cấu hình yếu.

---

### 🔄 KHỐI 4: SAO LƯU & PHẦN MỀM

#### 4.1. Cài Đặt Office (Office Silent Installer)
- Hỗ trợ tải và cài đặt tự động không cần thao tác các phiên bản Office phổ biến:
  - Microsoft Office 2016
  - Microsoft Office 2019
  - Microsoft Office 2021
  - Microsoft Office 365
- Cho phép người dùng tùy chọn chỉ cài các ứng dụng cần thiết (Word, Excel, PowerPoint, Outlook...) để tiết kiệm dung lượng ổ cứng.

#### 4.2. Kích Hoạt - Gỡ Crack (Bản Quyền & An Toàn Hệ Thống)
- Cung cấp giải pháp kích hoạt Windows & Office bản quyền hợp pháp (Digital License / KMS chính thống).
- Tích hợp công cụ quét và gỡ bỏ triệt để các phần mềm bẻ khóa (KMSPico, KMSAuto, tool crack chứa mã độc trojan/miner) khỏi hệ thống.

#### 4.3. Backup Restore Driver (Sao Lưu & Phục Hồi Driver)
- Tự động xuất toàn bộ Driver bên thứ ba (Driver mạng, âm thanh, đồ họa, chipset...) ra một thư mục lưu trữ độc lập.
- Khôi phục (Restore) lại toàn bộ Driver chỉ với 1 click sau khi cài mới lại Windows, giúp tiết kiệm thời gian tìm kiếm driver thủ công.

#### 4.4. Browser Backup Restore (Sao Lưu Dữ Liệu Trình Duyệt)
- Hỗ trợ các trình duyệt thông dụng: **Google Chrome, Microsoft Edge, Cốc Cốc, Brave, Mozilla Firefox**.
- Tùy chọn sao lưu các dữ liệu quan trọng:
  - 🔖 Dấu trang (Bookmarks / Favorites)
  - 🕒 Lịch sử duyệt web (Browsing History)
  - 🔑 Mật khẩu đã lưu (Saved Passwords)
- Khôi phục nhanh chóng khi chuyển đổi sang máy tính mới hoặc cài lại hệ điều hành.

#### 4.5. Kho Phần Mềm Free (Winget & One-Click Installer)
- Tích hợp trình quản lý gói chính thức của Microsoft: **Windows Package Manager (Winget)**.
- Danh mục phần mềm miễn phí thiết yếu được tuyển chọn:
  - **Bộ gõ & Văn phòng:** Unikey, EVKey, Foxit Reader, Adobe Acrobat Reader...
  - **Nén & Giải nén:** WinRAR, 7-Zip...
  - **Trình duyệt web:** Google Chrome, Cốc Cốc, Firefox, Brave...
  - **Hỗ trợ từ xa:** UltraViewer, AnyDesk, TeamViewer...
  - **Chat & Làm việc:** Zalo, Telegram, Skype...
  - **Đa phương tiện:** VLC Media Player, K-Lite Codec Pack...
- Cài đặt âm thầm (`Silent Install`), tự động bỏ qua các câu hỏi xác nhận rườm rà.

---

## 🛠️ CÔNG NGHỆ & KIẾN TRÚC PHÁT TRIỂN

| Thành Phần | Công Nghệ Sử Dụng | Mục Đích & Vai Trò |
| :--- | :--- | :--- |
| **Ngôn ngữ lõi** | Python 3.10+ / 3.14 (Embedded Engine) | Xử lý toàn bộ logic nghiệp vụ, gọi Windows API, đa luồng |
| **Giao diện người dùng** | PyWebView + HTML5 / CSS3 / ES6 / Vue 3 | Giao diện hiện đại, mượt mà, hỗ trợ Responsive |
| **Hệ thống Web Engine** | Microsoft Edge Chromium (WebView2) | Render giao diện chuẩn web hiện đại, tiêu thụ cực ít RAM |
| **Tương tác Windows** | .NET CLR (Pythonnet) + Win32 ctypes | Điều khiển System Tray, Windows Forms, Registry, Services |
| **Giao tiếp liên tiến trình**| TCP Socket IPC (`127.0.0.1:49285`) | Kiểm tra đơn tiến trình & đánh thức cửa sổ khi chạy ngầm |
| **Bảo mật & Phân quyền** | Windows Manifest (`requireAdministrator`) | Tự động kích hoạt UAC Admin khi chạy trên máy lạ |
| **Bộ tệp sạch máy in** | Assets Spooler Clean Repository | Nhúng sẵn `win32spl.dll`, `localspl.dll`, `spoolsv.exe` sạch |
| **Đóng gói** | PyInstaller 6.x (`--onefile`) | Đóng gói thành 1 file `.exe` duy nhất không cần cài đặt |

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG

### 1. Dành Cho Kỹ Thuật Viên & Người Dùng Cuối (Khuyên dùng)
1. Tải bản build đóng gói sẵn: **`IT Tool LTT.exe`** tại thư mục `dist\` hoặc `dist_release\`.
2. Click đúp vào file để khởi chạy (phần mềm sẽ tự động yêu cầu quyền Quản trị viên `Administrator` để thực hiện các can thiệp hệ thống).
3. Sử dụng các tính năng qua menu 4 khối bên trái.
4. Nếu muốn phần mềm luôn sẵn sàng mỗi khi bật máy: Hãy gạt công tắc **"Khởi Động Cùng Win: BẬT"** ở thanh trên cùng.

### 2. Dành Cho Lập Trình Viên (Chạy từ mã nguồn)
Yêu cầu: Máy đã cài đặt **Python 3.8+** và thư viện **Microsoft Edge WebView2 Runtime**.

```bash
# 1. Di chuyển vào thư mục dự án
cd d:\AllinOne

# 2. Cài đặt các thư viện cần thiết
pip install -r bmat_tools/requirements.txt
pip install pywebview pythonnet pillow psutil openpyxl bottle

# 3. Khởi chạy ứng dụng
python bmat_tools/main.py
```
Hoặc click đúp trực tiếp vào file **`IT-Tools.bat`**.

### 3. Hướng Dẫn Tự Biên Dịch (Build Exe Độc Lập)
Để đóng gói lại toàn bộ ứng dụng thành 1 file `.exe` độc lập duy nhất:
```bash
cd d:\AllinOne
pyinstaller IT-Tools.spec --clean --noconfirm
```
File thực thi sau khi hoàn tất sẽ nằm tại: **`d:\AllinOne\dist\IT Tool LTT.exe`** (~43 MB).

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

```
d:\AllinOne
├── IT-Tools.spec              # Cấu hình đóng gói PyInstaller 1 file duy nhất
├── IT-Tools.bat               # File khởi động nhanh từ mã nguồn Python
├── README.md                  # Tài liệu hướng dẫn sử dụng chi tiết
├── dist\                      # Thư mục chứa file IT Tool LTT.exe hoàn chỉnh
│   └── IT Tool LTT.exe        # File thực thi Portable duy nhất (~43 MB)
├── dist_release\              # Thư mục lưu bản sao lưu phát hành
│   └── IT Tool LTT.exe
└── bmat_tools\                # Mã nguồn chính của dự án
    ├── main.py                # Điểm khởi động, Single Instance IPC, Webview loader
    ├── web_api.py             # Cầu nối API giữa JavaScript và Python (200+ methods)
    ├── constants.py           # Thông tin phần mềm, màu sắc, cổng IPC
    ├── tray_manager.py        # Quản lý khay hệ thống Taskbar (System Tray)
    ├── requirements.txt       # Danh sách thư viện Python
    ├── assets\                # Tài nguyên đồ họa & tệp hệ thống sạch
    │   ├── tray_icon.ico      # Icon khay hệ thống & icon ứng dụng
    │   ├── tray_icon.png
    │   └── spooler_clean\     # Bộ 3 tệp hệ thống sạch sửa lỗi máy in
    │       ├── localspl.dll
    │       ├── spoolsv.exe
    │       └── win32spl.dll
    ├── config\                # Cấu hình lưu trữ
    │   └── zoom_screen.json   # Cấu hình phím tắt và tham số Zoom Screen
    ├── modules\               # 27 module xử lý logic Windows chuyên sâu
    │   ├── auto_shutdown.py
    │   ├── backup_driver.py
    │   ├── bitlocker.py
    │   ├── boot_manager.py
    │   ├── browser_backup.py
    │   ├── classic_menu.py
    │   ├── computer_info.py
    │   ├── currency.py
    │   ├── datetime_tool.py
    │   ├── desktop_icon.py
    │   ├── firewall.py
    │   ├── folder_size.py
    │   ├── hosts_editor.py
    │   ├── install_office_silent.ps1
    │   ├── ip_manager.py
    │   ├── ip_scanner.py
    │   ├── office_opt.py
    │   ├── other_tools.py
    │   ├── printer_fix.py     # Module sửa lỗi máy in & One Click Fix LAN
    │   ├── sendto_editor.py
    │   ├── server_tools.py
    │   ├── services_manager.py
    │   ├── startup_manager.py
    │   ├── uninstall_manager.py
    │   ├── win_update.py
    │   ├── wincheck.py
    │   ├── winget_runner.ps1
    │   ├── zoom_screen.py     # Trình quản lý Zoom Screen & phím tắt toàn cục
    │   └── zoom_screen_gui.py # Bộ công cụ vẽ và phóng to màn hình native GUI
    ├── ui\                    # Giao diện bổ trợ Tkinter (Boot Manager, Server Tools)
    │   └── main_window.py
    └── web\                   # Toàn bộ giao diện Webview hiện đại
        ├── index.html         # Giao diện chính và các Modal tương tác
        ├── style.css          # Hệ thống CSS Design System chuẩn mực
        ├── app.js             # Logic điều hướng chính và binding sự kiện
        ├── test_computer.css  # CSS cho bộ công cụ Test Computer
        ├── zoom_screen.css    # CSS cho bộ công cụ Zoom Screen
        ├── js\                # 18 tập tin JavaScript điều khiển từng phân hệ
        │   ├── app_manager.js
        │   ├── auto_shutdown.js
        │   ├── backup_driver.js
        │   ├── boot_manager.js
        │   ├── browser_backup.js
        │   ├── computer_info.js
        │   ├── currency_converter.js
        │   ├── datetime.js
        │   ├── network_tools.js
        │   ├── printer_fix.js # Điều khiển One Click Fix & Modal tiến trình
        │   ├── sendto_editor.js
        │   ├── server_tools.js
        │   ├── services_manager.js
        │   ├── system_drives.js
        │   ├── test_computer.js
        │   ├── vue.global.prod.js
        │   ├── win_security.js
        │   └── zoom_screen.js
        └── icons\             # Thư viện icon SVG của các ứng dụng phổ biến
```

---

## 👤 THÔNG TIN TÁC GIẢ & HỖ TRỢ KỸ THUẬT

- **Tác giả & Phát triển:** **Lê Thế Tuấn**
- **Hotline / Zalo:** **[0352 194 195](https://zalo.me/0352194195)**
- **Website chính thức:** [https://lethetuanpc.blogspot.com](https://lethetuanpc.blogspot.com)
- **Kênh Telegram hỗ trợ:** [https://t.me/lethetuanpc](https://t.me/lethetuanpc)
- **Bản quyền:** © 2026 **IT Tool LTT**. Phát hành phục vụ cộng đồng kỹ thuật viên CNTT Việt Nam.

---

> 💡 *Nếu công cụ này hữu ích cho công việc hàng ngày của bạn, hãy chia sẻ cho đồng nghiệp và bạn bè cùng trải nghiệm nhé!*
