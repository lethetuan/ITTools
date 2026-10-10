# 🛠️ IT TOOL LTT 2026 - BỘ CÔNG CỤ QUẢN TRỊ & TỐI ƯU WINDOWS TẤT-CẢ-TRONG-MỘT

<div align="center">

![IT Tool LTT Logo](ITTools/web/logo.png)

### **GIẢI PHÁP TẤT CẢ TRONG MỘT CHO KỸ THUẬT VIÊN CNTT & QUẢN TRỊ VIÊN WINDOWS**
*Tác giả & Phát triển: **Lê Thế Tuấn** | Hotline/Zalo: **0352 194 195***

[![Author](https://img.shields.io/badge/T%C3%A1c%20Gi%E1%BA%A3-L%C3%AA%20Th%E1%BA%BF%20Tu%E1%BA%A5n-0284c7.svg)](https://lethetuanpc.blogspot.com)
[![Hotline/Zalo](https://img.shields.io/badge/Zalo-0352%20194%20195-0068ff.svg)](https://zalo.me/0352194195)
[![Website](https://img.shields.io/badge/Website-lethetuanpc.blogspot.com-f59e0b.svg)](https://lethetuanpc.blogspot.com)
[![Telegram](https://img.shields.io/badge/Telegram-@lethetuanpc-229ED9.svg)](https://t.me/lethetuanpc)
[![Version](https://img.shields.io/badge/Phi%C3%AAn%20B%E1%BA%A3n-1.0.0%20(2026)-10b981.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/N%E1%BB%81n%20T%E1%BA%A3ng-Windows%2010%20%7C%2011%20%7C%20Server-blue.svg)]()
[![Single File](https://img.shields.io/badge/Build-Single%20Portable%20.EXE-purple.svg)]()

</div>

---

## 📖 GIỚI THIỆU TỔNG QUAN

**IT Tool LTT 2026** là phần mềm quản trị, bảo trì, cứu hộ và tối ưu hóa hệ thống Windows chuyên nghiệp dành riêng cho kỹ thuật viên CNTT, kỹ sư máy tính, quản trị viên mạng doanh nghiệp và người dùng nâng cao.

Ứng dụng được đóng gói thành **duy nhất 1 file `.exe` (Portable)**, dung lượng tinh gọn (~43 MB), tích hợp sẵn toàn bộ engine Python, C-runtime, giao diện Webview Edge Chromium hiện đại và bộ tài nguyên hệ thống sạch. Người dùng có thể copy vào USB hoặc tải về chạy trực tiếp trên bất kỳ máy tính Windows nào (Windows 10, Windows 11, Windows Server) mà **hoàn toàn không cần cài đặt thêm bất kỳ phần mềm hay thư viện phụ trợ nào**.

---

## 🌟 ĐẶC ĐIỂM NỔI BẬT

- **📦 1 File Thực Thi Duy Nhất (100% Standalone Portable):** Không cần cài đặt Python, Node.js hay Visual C++. Chạy trực tiếp từ USB hoặc ổ cứng trên mọi máy tính.
- **⚡ Tự Động Kích Hoạt Quyền Quản Trị (UAC Elevation Manifest):** Nhúng sẵn manifest `requireAdministrator`. Khi mở ở bất kỳ máy tính nào, Windows sẽ tự động kích hoạt quyền Administrator, đảm bảo mọi can thiệp hệ thống (Registry, Service, Firewall, Takeown tệp hệ thống) thực thi thành công 100%.
- **🚀 Quản Lý Khởi Động Cùng Windows Tiện Lợi:** Tích hợp nút gạt bật/tắt tự khởi động ngay trên Header, cấu hình trực tiếp vào Registry `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
- **🔍 Quản Lý Đơn Tiến Trình Thông Minh (Single Instance IPC):** Sử dụng socket IPC cục bộ (`127.0.0.1:49285`). Khi ứng dụng đang chạy (hoặc ẩn dưới khay), việc mở lại file exe sẽ ngay lập tức đánh thức và đưa cửa sổ hiện tại lên trên cùng màn hình mà không mở trùng lặp tiến trình thừa.
- **🔽 Khay Hệ Thống Thông Minh (System Tray):** Khi nhấn dấu X, ứng dụng tự động thu nhỏ xuống khay Taskbar để giải phóng màn hình làm việc. Menu chuột phải ở khay hỗ trợ: Hiện giao diện, Mở Website, Gọi Zalo, Mở Telegram, Thoát hoàn toàn.
- **⚡ Vận Hành Không Nhấp Nháy (Zero-Flicker):** Cơ chế hook cấp thấp triệt tiêu hoàn toàn các cửa sổ đen dòng lệnh (`CREATE_NO_WINDOW`) cho toàn bộ các lệnh PowerShell, CMD, netsh, sc, reg ngầm.
- **🌓 Giao Diện Chuẩn Web Đỉnh Cao:** Render bằng Microsoft Edge WebView2 mượt mà, hỗ trợ giao diện Sáng / Tối (Light / Dark Mode), phóng to/thu nhỏ tỷ lệ hiển thị linh hoạt (Zoom 70% - 100%).
- **📋 Nhật Ký Hệ Thống Thời Gian Thực (Live Terminal & Drawer Log):** Hiển thị chi tiết từng câu lệnh DOS/PowerShell đang chạy, mã lệnh, thời gian và trạng thái trực quan.

---

## 📑 BẢN ĐỒ TÍNH NĂNG CHI TIẾT (28 PHÂN HỆ)

Phần mềm được phân loại khoa học thành **4 nhóm chuyên đề chính** với **28 phân hệ tính năng chuyên sâu**:

```
IT Tool LTT 2026
├── 🖥️ 1. HỆ THỐNG & CẤU HÌNH
│   ├── 💻 Check Cấu Hình (Computer Info & Audit)
│   ├── 🩺 Test Computer (Bộ Chẩn Đoán Phần Cứng Toàn Diện 8 Công Cụ)
│   ├── 💿 Cài Win & Update (Windows Setup & Update Manager)
│   ├── 🚀 Startup Manager (Quản Lý Khởi Động Đa Vị Trí)
│   ├── 🗑️ Uninstall Manager (Gỡ Cài Đặt Nhanh & Silent Uninstall)
│   └── 🔒 Tắt BitLocker & EFS (BitLocker & Drive Encryption)
│
├── 🖨️ 2. MẠNG & MÁY IN
│   ├── 🖨️ Fix Máy In - Share LAN (Chuyên Trị Lỗi In Mạng LAN & USB)
│   │   ├── ★ ONE CLICK FIX TẤT CẢ LỖI MÁY IN (Quy Trình 4 Bước Chuẩn)
│   │   ├── Sửa Lỗi 0x0000011b, 0x00000709, 0x0000007c, 0x00000bcb
│   │   └── Chuyên Trị Máy In Canon LBP 2900 / 3300
│   ├── 🌐 IP Manager & Subnet (Cấu Hình IP, DNS & Tính Dải Mạng)
│   ├── 🔍 IP Scanner (Quét Thiết Bị Mạng LAN Đa Luồng Siêu Tốc)
│   ├── 🛡️ Firewall Manager (Quản Lý Tường Lửa & Mở Port Nhanh)
│   └── 🖧 Server Tools (Công Cụ Quản Trị Máy Chủ & Dịch Vụ Mạng)
│
├── 🛠️ 3. TIỆN ÍCH WINDOWS
│   ├── 🔍 Zoom Screen (Phóng To, Vẽ Chú Thích, Quay Chụp & Break Timer)
│   ├── ⏻ Auto Shutdown (Hẹn Giờ Tắt / Bật, Nhật Ký Event Log & Xuất Excel)
│   ├── 📝 Hosts File Editor (Chỉnh Sửa File Hosts Trực Quan & Backup)
│   ├── 📤 SendTo Editor (Tùy Biến Menu Chuột Phải Send To)
│   ├── 🪟 Classic Win10 Menu (Bật Menu Chuột Phải Cổ Điển Trên Win 11)
│   ├── 🖥️ Desktop Icon (Bật / Tắt Biểu Tượng Hệ Thống Trên Desktop)
│   ├── 🕐 Date Time Config (Đồng Bộ Giờ Chuẩn NTP & Múi Giờ VN)
│   ├── ⚙️ Boot Manager (Quản Lý Khởi Động BCD & Tích Hợp WinPE)
│   ├── ⚙️ Services Manager (Quản Trị Dịch Vụ Hệ Thống Windows)
│   ├── 📁 Folder Size Analyzer (Phân Tích Dung Lượng Ổ Đĩa & Thư Mục)
│   ├── 💰 Currency Converter (Quy Đổi Ngoại Tệ Trực Tuyến Đa Đồng Tiền)
│   └── 🔧 Other System Tweaks (Ultimate Performance, Tắt Hibernate, Dọn Rác)
│
└── 🔄 4. SAO LƯU & PHẦN MỀM
    ├── 📊 Cài Đặt Office (Office Silent Installer Tự Động Từ Microsoft CDN)
    ├── 🔑 Kích Hoạt - Gỡ Crack (Bản Quyền Hợp Pháp & Quét Sạch Mã Độc Crack)
    ├── 💾 Backup Restore Driver (Sao Lưu & Phục Hồi Driver 1 Click)
    ├── 🔄 Browser Backup Restore (Sao Lưu Bookmarks, History, Passwords)
    └── 📦 Kho Phần Mềm Free (Winget Package Manager Tải & Cài Đặt Tự Động)
```

---

## 🔍 CHI TIẾT TỪNG PHÂN HỆ TÍNH NĂNG

### 🖥️ KHỐI 1: HỆ THỐNG & CẤU HÌNH

#### 1.1. 💻 Check Cấu Hình (Computer Info & Audit)
- **Kiểm tra thông số phần cứng & hệ điều hành chuyên sâu:**
  - **Máy tính:** Hostname, Username, Tên hãng sản xuất, Model, Serial Number / Service Tag.
  - **Hệ điều hành:** Edition (Home, Pro, Enterprise), Phiên bản Version, OS Build, Kiến trúc 32-bit/64-bit, Ngày cài đặt hệ điều hành, Thời gian hoạt động liên tục (Uptime).
  - **Bộ vi xử lý (CPU):** Tên đầy đủ, số nhân vật lý (Cores), số luồng (Threads), xung nhịp cơ bản và tối đa, tập lệnh hỗ trợ.
  - **Bộ nhớ trong (RAM):** Tổng dung lượng, dung lượng khả dụng, Bus RAM, chuẩn RAM (DDR3/DDR4/DDR5), số khe cắm RAM đang sử dụng / còn trống.
  - **Bo mạch chủ (Mainboard):** Hãng sản xuất, Model, Serial, Phiên bản BIOS, Ngày phát hành BIOS, Chuẩn khởi động (UEFI hoặc Legacy).
  - **Card đồ họa (GPU):** Model GPU rời & GPU onboard, dung lượng bộ nhớ đồ họa (VRAM), phiên bản Driver màn hình.
  - **Ổ cứng & Phân vùng:** Danh sách ổ cứng vật lý (SSD/HDD, dung lượng tổng, serial), chi tiết từng phân vùng (C, D, E... tổng dung lượng, đã dùng, còn trống, định dạng NTFS/FAT32).
  - **Card mạng (Network):** Địa chỉ IPv4/IPv6, MAC Address, Gateway, DNS server.
- **Xuất báo cáo cấu hình:** Hỗ trợ sao chép nhanh vào Clipboard hoặc xuất file văn bản `.txt` phục vụ báo cáo khách hàng hoặc in phiếu bảo hành máy tính.

#### 1.2. 🩺 Test Computer (Bộ Chẩn Đoán Phần Cứng Toàn Diện 8 Công Cụ)
Tích hợp trọn bộ 8 công cụ kiểm tra sức khỏe thiết bị trực quan bằng công nghệ Web Audio, Web Canvas và Vue 3 Engine:
1. **⌨️ Kiểm tra bàn phím (Keyboard Diagnostics):**
   - Hỗ trợ đầy đủ các layout phổ biến: Fullsize 100%, TKL 80%, Compact 60%, layout Windows và macOS.
   - Ghi nhận lịch sử nhấn phím, phát hiện kẹt phím, liệt phím.
   - Đo chỉ số tốc độ gõ: APM (Actions Per Minute) và CPS (Clicks Per Second).
2. **🖱️ Kiểm tra chuột & switch (Mouse & Switch Test):**
   - Kiểm tra chuột trái, chuột phải, chuột giữa và con lăn cuộn.
   - Đo tốc độ click chuột (CPS).
   - **Phát hiện lỗi Double-Click:** Tự động phát hiện hiện tượng bounce switch nảy kép bất thường với thanh điều chỉnh ngưỡng debounce ms linh hoạt.
   - **Bài test giữ chuột liên tục (Hold Test):** Kiểm tra switch có bị nhả giữa chừng khi đang kéo thả hay không.
3. **🖥️ Kiểm tra màn hình & điểm chết (Screen Pixel Checker):**
   - Kiểm tra điểm chết (Dead/Stuck Pixel) toàn màn hình qua 5 dải màu thuần khiết: Đỏ, Xanh lá, Xanh dương, Trắng, Đen.
   - Bổ sung màn hình kiểm tra dải màu tương phản và độ chuyển màu (Gradient test).
4. **📷 Kiểm tra Webcam:**
   - Tự động quét và liệt kê danh sách thiết bị camera kết nối vào máy.
   - Hiển thị luồng video preview trực tiếp với độ phân giải và tỷ lệ khung hình thực tế.
5. **🎙️ Kiểm tra Microphone:**
   - Bộ phân tích cường độ âm thanh thời gian thực (Audio Level VU Meter).
   - Điều chỉnh Gain Control và tính năng ghi âm - phát lại tức thì để kiểm tra chất lượng thu âm, lọc nhiễu, chống rè.
6. **🔊 Kiểm tra Loa & Bộ tổng hợp âm thanh (Speaker Synthesizer):**
   - Phát các tần số âm thanh chuẩn: Âm trầm Bass (80Hz), Âm trung Mid (1KHz), Âm cao Treble (8KHz).
   - Chế độ quét dải tần liên tục (Frequency Sweep 20Hz - 20,000Hz).
   - Kiểm tra cân bằng âm thanh độc lập 2 kênh Stereo: Loa Trái (Left) / Loa Phải (Right).
7. **🔋 Kiểm tra Pin Laptop (Battery State & Health):**
   - Trạng thái nguồn điện cắm sạc (AC Online / Battery).
   - Dung lượng thiết kế gốc (Design Capacity) so với dung lượng sạc đầy thực tế (Full Charge Capacity).
   - Mức độ chai pin (Wear Level %), điện áp hiện tại và số chu kỳ sạc (Cycle Count).
8. **🎬 Đo tần số quét & FPS màn hình (Display FPS & Refresh Rate):**
   - Đo đạc chính xác tần số quét thực tế của màn hình (Hz) và chỉ số khung hình (FPS).
   - Kiểm tra độ giật khung hình (Jank test), độ mượt khi cuộn trang và bài test vệt bóng ma màn hình (Ghosting test).

#### 1.3. 💿 Cài Win & Update (Windows Setup & Update Manager)
- **Bật / Tắt Windows Update:** Vô hiệu hóa hoặc kích hoạt triệt để dịch vụ cập nhật tự động của Windows chỉ với 1 click, ngăn Windows tự tải bản cập nhật gây chậm máy hoặc lỗi máy in.
- **Dọn sạch cache Windows Update:** Xóa sạch thư mục bộ nhớ đệm `C:\Windows\SoftwareDistribution\Download` giúp giải phóng hàng chục GB dung lượng ổ C bị chiếm dụng bởi các file cập nhật cũ.
- **Tải file ISO Windows chính thức:** Tích hợp hướng dẫn và đường dẫn trực tiếp đến các công cụ tải file ISO Windows 10/11 nguyên gốc từ máy chủ Microsoft.

#### 1.4. 🚀 Startup Manager (Quản Lý Khởi Động Đa Vị Trí)
- Quét toàn diện 5 vị trí khởi động trên hệ thống Windows:
  - Registry người dùng hiện tại: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
  - Registry hệ thống toàn cục: `HKLM\Software\Microsoft\Windows\CurrentVersion\Run`
  - Khởi động một lần: `RunOnce (HKCU / HKLM)`
  - Thư mục Startup người dùng: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
  - Thư mục Startup toàn hệ thống: `%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup`
- Tự động trích xuất icon gốc từ file thực thi `.exe` để hiển thị trực quan.
- Thao tác nhanh: Bật/Tắt tức thì, Thêm mới (`Add New`), Chỉnh sửa đường dẫn/tham số (`Edit`), Xóa (`Delete`) hoặc Chạy thử ngay (`Run Now`).
- **Nút gạt Bật/Tắt tự động mở IT Tool LTT cùng Windows:** Cấu hình trực tiếp vào Registry giúp phần mềm luôn sẵn sàng khi bật máy.

#### 1.5. 🗑️ Uninstall Manager (Gỡ Cài Đặt Nhanh & Silent Uninstall)
- Quét nhanh và đầy đủ danh mục phần mềm đã cài đặt trên máy tính (hỗ trợ cả ứng dụng 32-bit và 64-bit trong Registry).
- Tìm kiếm tức thời theo tên phần mềm, lọc theo ngày cài đặt, kích thước chiếm dụng, nhà phát hành và phiên bản.
- Hỗ trợ gỡ cài đặt tiêu chuẩn (mở trình gỡ mặc định của ứng dụng) hoặc kích hoạt chế độ **Gỡ âm thầm (`Silent Uninstall`)** tự động bỏ qua các bước xác nhận.

#### 1.6. 🔒 Tắt BitLocker & EFS (BitLocker & Drive Encryption)
- Quét trạng thái mã hóa BitLocker trên từng ổ đĩa (Mức độ mã hóa %, Trạng thái bảo vệ, Tình trạng khóa Lock/Unlock).
- Cung cấp tính năng tắt mã hóa BitLocker chỉ với 1 click, giải mã ổ đĩa, phòng tránh rủi ro mất dữ liệu vĩnh viễn do quên khóa khôi phục (Recovery Key).
- Giải mã nhanh các tập tin / thư mục bị mã hóa bởi chứng chỉ EFS (Encrypting File System).

---

### 🖨️ KHỐI 2: MẠNG & MÁY IN

#### 2.1. 🖨️ Fix Máy In - Share LAN (Chuyên Trị Lỗi In Mạng LAN & USB)
- **★ ONE CLICK FIX TẤT CẢ LỖI MÁY IN MẠNG LAN (Quy trình 4 bước chuẩn hóa):**
  1. *Bước 1:* Chiếm quyền sở hữu (`takeown /A /F`) và cấp toàn quyền (`icacls administrators:F SYSTEM:F`), sao lưu các tệp hiện tại thành đuôi `.old` (`spoolsv.exe.old`, `win32spl.dll.old`, `localspl.dll.old`). Nạp các khóa Registry cốt lõi: `RpcAuthnLevelPrivacyEnabled = 0`, `RpcOverNamedPipes = 1`, `RpcOverTcp = 1`, `PointAndPrint`, `forceguest = 0`, `AllowInsecureGuestAuth = 1`.
  2. *Bước 2:* Nạp bộ 3 tệp hệ thống sạch chuẩn (`win32spl.dll`, `localspl.dll`, `spoolsv.exe`) trích xuất trực tiếp từ bundle vào thư mục `C:\Windows\System32`.
  3. *Bước 3:* Cấu hình chế độ khởi động tự động (`Automatic`) cho Print Spooler và các dịch vụ mạng liên quan (`LanmanWorkstation`, `LanmanServer`, `fdPHost`, `FDResPub`, `SSDPSRV`, `upnphost`), khởi động lại dịch vụ Print Spooler.
  4. *Bước 4:* Hoàn tất, giao diện hiển thị thông báo thành công và cho phép in ngay qua mạng LAN.
  - *Giao diện trực quan:* Modal tiến trình hiển thị 4 thẻ bước (Pending / Running / Done), thanh tiến trình % và Live Terminal hiển thị trực tiếp từng dòng lệnh DOS/PowerShell thực thi theo thời gian thực.
- **Sửa triệt để các mã lỗi in mạng LAN kinh điển:**
  - Sửa lỗi **0x0000011b** (Lỗi bảo mật RPC PrintNightmare sau các bản vá cập nhật KB Windows).
  - Sửa lỗi **0x00000709** (Không kết nối được tên máy in chia sẻ hoặc xung đột Registry).
  - Sửa lỗi **0x0000007c**, **0x00000bcb**, **0x000006ba**, **0x000006d9**.
- **Chuyên trị máy in Canon LBP 2900 / 3300:** Reset toàn diện hàng đợi in, xóa USB Monitor trong Registry, xóa cổng mạng ảo CNBJNP, sao chép thư viện chuẩn `mscms.dll` và hướng dẫn nhận lại máy in sau 10 giây.
- **Bộ tiện ích mở rộng cho máy in:**
  - Dọn sạch hàng đợi in bị kẹt (xóa toàn bộ file rác trong `%SystemRoot%\System32\spool\PRINTERS`).
  - Gỡ bỏ driver máy in cũ bị lỗi thông qua công cụ hệ thống `pnputil`.
  - Mở khóa chia sẻ máy in (Unlock Share Printer).
  - Thêm Windows Credentials đăng nhập máy chủ in trong mạng LAN mà không bị hỏi lại mật khẩu.
  - Tự động mở tường lửa (Firewall) cho nhóm File and Printer Sharing và Network Discovery.

#### 2.2. 🌐 IP Manager & Subnet (Cấu Hình IP, DNS & Tính Dải Mạng)
- Liệt kê toàn bộ các card mạng có dây (Ethernet) và không dây (Wi-Fi) đang có trên máy kèm thông số IP, Subnet Mask, Default Gateway và DNS hiện tại.
- Chuyển đổi siêu tốc giữa **IP Động (DHCP)** và **IP Tĩnh (Static IP)** chỉ bằng 1 thao tác.
- Tùy chọn nhanh các cặp DNS tin cậy và ổn định:
  - Google DNS: `8.8.8.8` / `8.8.4.4`
  - Cloudflare DNS: `1.1.1.1` / `1.0.0.1`
  - Quad9 DNS: `9.9.9.9` / `149.112.112.112`
  - OpenDNS: `208.67.222.222` / `208.67.220.220`
- **Công cụ tính toán dải mạng (Subnet Calculator):** Nhập IP và tiền tố CIDR (ví dụ `/24`, `/28`...) tính toán ngay lập tức Subnet Mask, Network Address, Broadcast Address, First Usable IP, Last Usable IP và Tổng số thiết bị (Host) khả dụng.

#### 2.3. 🔍 IP Scanner (Quét Thiết Bị Mạng LAN Đa Luồng Siêu Tốc)
- Tự động nhận diện dải IP hiện tại của mạng nội bộ (ví dụ: `192.168.1.1/24`).
- Quét đồng thời toàn bộ dải 254 địa chỉ IP với tốc độ cực nhanh bằng kỹ thuật đa luồng (Multithreaded).
- Báo cáo rõ ràng: Trạng thái Online/Offline, Địa chỉ IP, Tên thiết bị (Hostname), Địa chỉ MAC và Nhà sản xuất card mạng (Vendor OUI lookup: Apple, Samsung, Intel, TP-Link, Asus, Dell...).
- Tích hợp nút Ping kiểm tra độ trễ (Latency ms) trực tiếp trên từng thiết bị trong bảng kết quả.

#### 2.4. 🛡️ Firewall Manager (Quản Lý Tường Lửa & Mở Port Nhanh)
- Bật / Tắt tường lửa độc lập cho cả 3 chế độ mạng: **Domain**, **Private**, **Public**.
- Cho phép mở nhanh (Whitelist) các cổng dịch vụ cần thiết qua tường lửa:
  - Port 80 (HTTP Web)
  - Port 443 (HTTPS Web)
  - Port 3389 (Remote Desktop RDP)
  - Port 445 (SMB File Sharing / Chia sẻ máy in)
- Khôi phục tường lửa Windows về cài đặt mặc định gốc của Microsoft.

#### 2.5. 🖧 Server Tools (Công Cụ Quản Trị Máy Chủ & Dịch Vụ Mạng)
- **Remote Desktop (RDP):** Bật / Tắt tính năng cho phép máy tính khác điều khiển từ xa qua cổng 3389, cấu hình xác thực cấp độ mạng (NLA - Network Level Authentication).
- **File Sharing Server:** Quản lý danh sách các thư mục đang được chia sẻ trên máy (Shares List), xem số lượng người dùng mạng LAN đang kết nối.
- **Dịch vụ mạng Windows:** Kích hoạt hoặc vô hiệu hóa các dịch vụ: IIS Web Server, FTP Service, Telnet Client, NetBIOS qua TCP/IP.

---

### 🛠️ KHỐI 3: TIỆN ÍCH WINDOWS

#### 3.1. 🔍 Zoom Screen (Trình Chiếu, Zoom & Ghi Chú Đa Năng)
Giải pháp thay thế và nâng cấp toàn diện cho ZoomIt của Microsoft Sysinternals:
- **Phóng to màn hình (Zoom):** Phóng to mượt mà tại vị trí con trỏ chuột, hỗ trợ cuộn chuột tăng/giảm tỷ lệ phóng từ 1.25x đến 5.0x.
- **Vẽ & Viết chú thích trực tiếp (LiveDraw & Annotate):**
  - Chế độ vẽ tự do, vẽ đường thẳng (giữ `Shift`), mũi tên (giữ `Ctrl + Shift`), hình chữ nhật (giữ `Ctrl`), hình elip (giữ `Tab`).
  - Gõ văn bản trực tiếp lên màn hình tại vị trí nhấp chuột (`T`).
  - Chuyển đổi màn hình bảng đen (`K`) hoặc bảng trắng (`W`).
  - Chọn nhanh màu bút: `R` (Đỏ), `G` (Xanh lá), `B` (Xanh dương), `Y` (Vàng), `O` (Cam), `P` (Hồng).
  - Hoàn tác nét vẽ (`Ctrl + Z`), xóa toàn bộ bảng (`E`), thoát vẽ (`Esc` hoặc chuột phải).
- **Đồng hồ giải lao (Break Timer):** Đếm ngược thời gian nghỉ giải lao với thanh tiến trình đồ họa và thông báo khi hết giờ.
- **LiveZoom:** Phóng to màn hình nhưng vẫn cho phép thao tác chuột và bàn phím tương tác bình thường với các ứng dụng bên dưới.
- **Quay & Chụp màn hình (Record & Snip):** Quay video màn hình với định dạng MP4 hoặc chụp ảnh vùng chọn sao chép thẳng vào Clipboard / lưu ra file ảnh.
- **DemoType:** Tự động gõ từng ký tự từ văn bản chuẩn bị trước phục vụ giảng dạy, thuyết trình demo kỹ thuật mượt mà.
- **Chế độ gương lật & Toàn cảnh (Mirror & Panorama):** Hỗ trợ lật ngược màn hình khi trình chiếu qua máy chiếu ngược hoặc cuộn xem màn hình toàn cảnh.
- **Hệ thống phím tắt toàn cục (Global Hotkeys):**
  - Mặc định: `Ctrl + 1` (Zoom), `Ctrl + 2` (Vẽ), `Ctrl + 3` (Break Timer), `Ctrl + 4` (LiveZoom), `Ctrl + 5` (Record), `Ctrl + 6` (Snip), `Ctrl + 7` (DemoType), `Ctrl + 8` (Panorama), `Ctrl + 9` (Mirror).
  - Cho phép tùy biến mọi tổ hợp phím tắt theo ý muốn.
  - **Tự động kích hoạt ngầm:** Lắng nghe phím tắt ngay từ lúc mở tool hoặc khi thu nhỏ xuống khay Taskbar.

#### 3.2. ⏻ Auto Shutdown (Hẹn Giờ Tắt / Bật, Nhật Ký Event Log & Xuất Excel)
- **Đa dạng chế độ đặt lịch:** Tắt máy (`Shutdown`), Khởi động lại (`Restart`), Ngủ (`Sleep`), Ngủ đông (`Hibernate`).
- **Phương thức đặt lịch phong phú:** Hẹn giờ đếm ngược (sau số phút / giờ) hoặc hẹn giờ theo mốc thời gian cố định trong ngày (ví dụ: đúng 18:00 hàng ngày).
- Tích hợp nút hủy hẹn giờ nhanh chỉ với 1 click.
- **Tra cứu nhật ký Windows Event Log thời gian thực:**
  - Truy vấn tự động các sự kiện tắt / mở / sập nguồn máy tính:
    - **Event ID 1074:** Tắt máy hoặc khởi động lại có kiểm soát (hiển thị rõ User tài khoản nào thực hiện, tiến trình nào yêu cầu, lý do Shutdown).
    - **Event ID 6008:** Tắt nguồn đột ngột (mất điện, rút phích cắm, sập nguồn bất thường).
    - **Event ID 41:** Sự kiện Kernel-Power (máy tính bị treo, khởi động lại đột ngột do màn hình xanh BSOD hoặc lỗi phần cứng).
  - Dashboard thống kê KPI: Tổng số sự kiện, tỷ lệ tắt bình thường vs sập nguồn/crash, thời gian máy hoạt động (Uptime).
- **Xuất báo cáo Excel (.xlsx) chuyên nghiệp:** Xuất bảng nhật ký lịch sử tắt mở máy ra file Excel có định dạng tiêu đề, màu sắc nhận diện, thông tin thiết bị và chữ ký kỹ thuật viên.

#### 3.3. 📝 Hosts File Editor (Chỉnh Sửa File Hosts Trực Quan)
- Trực tiếp đọc và chỉnh sửa file hosts hệ thống (`C:\Windows\System32\drivers\etc\hosts`) mà không bị lỗi phân quyền bảo vệ của Windows.
- Thêm nhanh bản ghi Tên miền ➔ IP tương ứng.
- Khóa / Chặn tên miền quảng cáo, mã độc hoặc website giải trí không mong muốn.
- Sao lưu dự phòng và khôi phục file hosts gốc của Microsoft khi cần thiết.

#### 3.4. 📤 SendTo Editor (Tùy Biến Menu Send To)
- Quản lý danh sách các lối tắt xuất hiện trong menu `Chuột phải -> Send to`.
- Dễ dàng thêm thư mục lưu trữ thường dùng (Google Drive, Dropbox, OneDrive, Ổ D, Ổ E...) vào menu để sao chép dữ liệu nhanh chóng.
- Xóa bỏ các mục thừa không dùng đến giúp menu gọn gàng, tăng tốc độ phản hồi chuột phải.

#### 3.5. 🪟 Classic Win10 Menu (Menu Chuột Phải Cổ Điển Cho Win 11)
- Chuyển đổi menu chuột phải trên Windows 11 về giao diện đầy đủ quen thuộc của Windows 10 (không còn phải bấm *Show more options* hay *Shift + F10*).
- Hỗ trợ khôi phục về menu mặc định của Windows 11 bất kỳ lúc nào chỉ bằng 1 click mà không cần khởi động lại máy tính.

#### 3.6. 🖥️ Desktop Icon (Bật / Tắt Biểu Tượng Hệ Thống)
- Ẩn / Hiện các icon hệ thống quan trọng trên màn hình Desktop chỉ bằng các nút gạt:
  - 🖥️ This PC (Computer)
  - 📁 Thư mục người dùng (User's Files)
  - 🌐 Mạng (Network)
  - 🗑️ Thùng rác (Recycle Bin)
  - ⚙️ Control Panel
- Tự động làm mới Explorer để icon hiển thị ngay lập tức mà không cần đăng xuất hay khởi động lại máy.

#### 3.7. 🕐 Date Time Config (Cấu Hình Ngày Giờ & Đồng Bộ NTP)
- Đặt múi giờ chuẩn Việt Nam: `(UTC+07:00) Bangkok, Hanoi, Jakarta`.
- Tự động bật dịch vụ Windows Time (`w32time`) và đồng bộ giờ chuẩn xác theo các máy chủ NTP uy tín:
  - `time.windows.com`
  - `time.google.com`
  - `pool.ntp.org`
- Sửa triệt để lỗi máy tính bị sai giờ sau khi cài lại Windows hoặc do pin CMOS trên bo mạch chủ bị yếu.

#### 3.8. ⚙️ Boot Manager (Quản Lý Khởi Động BCD & Tích Hợp WinPE)
- Xem danh sách các hệ điều hành và mục khởi động đang có trong menu BCD của Windows.
- Chỉnh sửa thời gian chờ hiển thị menu Boot (`Boot Timeout`).
- Bật/Tắt chế độ khởi động an toàn (`Safe Mode`) và mở giao diện cấu hình `msconfig`.
- **Tích hợp WinPE Boot trực tiếp vào ổ cứng:** Cho phép tích hợp file cứu hộ WinPE từ file ảnh `.iso` hoặc `.wim` trực tiếp vào ổ cứng C. Khi máy tính gặp sự cố, người dùng có thể khởi động ngay vào WinPE để cứu hộ dữ liệu mà không cần cắm USB boot.
- Hỗ trợ đổi tên mục boot, xóa mục boot thừa hoặc mở giao diện đồ họa nâng cao (GUI Boot Manager).

#### 3.9. ⚙️ Services Manager (Quản Trị Dịch Vụ Hệ Thống)
- Liệt kê toàn bộ các dịch vụ hệ thống Windows với Tên hiển thị, Tên nội bộ, Trạng thái (`Running` / `Stopped`) và Kiểu khởi động (`Automatic`, `Manual`, `Disabled`).
- Tìm kiếm dịch vụ thông minh theo từ khóa.
- Thao tác nhanh: Khởi động (Start), Dừng (Stop), Khởi động lại (Restart) dịch vụ hoặc đổi kiểu khởi động trực tiếp.

#### 3.10. 📁 Folder Size Analyzer (Phân Tích Dung Lượng Ổ Đĩa)
- Quét và trực quan hóa dung lượng của các thư mục trên ổ cứng.
- Phát hiện các thư mục hoặc tập tin có dung lượng lớn bất thường đang chiếm dụng bộ nhớ để người dùng xem xét dọn dẹp an toàn.

#### 3.11. 💰 Currency Converter (Quy Đổi Ngoại Tệ Trực Tuyến)
- Chuyển đổi qua lại giữa đồng Việt Nam (VNĐ) và các loại ngoại tệ phổ biến trên thế giới: USD, EUR, JPY, GBP, CNY, KRW, SGD, AUD, CAD, THB...
- Cập nhật tỷ giá trực tiếp, hỗ trợ tính toán tài chính nhanh chóng ngay trong công việc kỹ thuật.

#### 3.12. 🔧 Other System Tweaks (Bộ Tinh Chỉnh Nâng Cao)
- **Ultimate Performance Power Plan:** Kích hoạt gói năng lượng hiệu năng tối đa (Ultimate Performance) ẩn của Windows giúp CPU và phần cứng phát huy 100% công suất.
- **Bật / Tắt chế độ ngủ đông (Hibernate):** Xóa file bộ nhớ đệm `hiberfil.sys` để giải phóng hàng chục GB ổ C khi không sử dụng tính năng ngủ đông.
- **Dọn rác tạm thời hệ thống:** Xóa sạch các file rác tạm chiếm dụng ổ đĩa: `%TEMP%`, `Prefetch`, `C:\Windows\Temp`.
- **Tối ưu hóa giao diện cho máy yếu:** Tắt hiệu ứng mờ và hoạt ảnh chuyển động để tăng tốc độ phản hồi cho máy tính cấu hình thấp.

---

### 🔄 KHỐI 4: SAO LƯU & PHẦN MỀM

#### 4.1. 📊 Cài Đặt Office (Office Silent Installer)
- Tải và cài đặt tự động ngầm không cần thao tác các phiên bản Office chính thức từ máy chủ Microsoft CDN thông qua bộ công cụ chính thức Office Deployment Tool (ODT):
  - **Microsoft Office 365** (Microsoft 365 Apps for Enterprise)
  - **Microsoft Office 2024** Professional Plus
  - **Microsoft Office 2021** Professional Plus
  - **Microsoft Office 2019** Professional Plus
  - **Microsoft Office 2016** Professional Plus
  - **Microsoft Visio** Professional 2021
  - **Microsoft Project** Professional 2021
- Hỗ trợ tùy chọn kiến trúc 64-bit hoặc 32-bit và gói ngôn ngữ (Tiếng Việt `vi-vn` hoặc Tiếng Anh `en-us`).
- **Cơ chế chạy ngầm độc lập:** Sau khi bấm bắt đầu, tiến trình cài đặt chạy hoàn toàn ngầm trong nền Windows. Người dùng có thể tắt ứng dụng IT Tool LTT mà Office vẫn tiếp tục tải và hoàn tất cài đặt tự động.

#### 4.2. 🔑 Kích Hoạt - Gỡ Crack (Bản Quyền & An Toàn Hệ Thống)
- Cung cấp giải pháp kích hoạt Windows & Office bản quyền hợp pháp (Digital License vĩnh viễn / KMS hợp lệ).
- Tích hợp công cụ quét và gỡ bỏ triệt để các phần mềm bẻ khóa nguy hiểm (KMSPico, KMSAuto, tool crack chứa mã độc trojan/miner) khỏi hệ thống.

#### 4.3. 💾 Backup Restore Driver (Sao Lưu & Phục Hồi Driver 1 Click)
- **Sao lưu Driver:** Tự động trích xuất toàn bộ Driver bên thứ ba (Driver card mạng LAN, Wi-Fi, Card âm thanh, Card màn hình, Chipset...) ra một thư mục lưu trữ độc lập do người dùng chọn.
- **Phục hồi Driver:** Khôi phục lại toàn bộ Driver chỉ với 1 click sau khi cài mới lại Windows, giúp tiết kiệm hàng giờ đồng hồ tìm kiếm và cài đặt driver thủ công.

#### 4.4. 🔄 Browser Backup Restore (Sao Lưu Dữ Liệu Trình Duyệt)
- Hỗ trợ các trình duyệt thông dụng nhất: **Google Chrome, Microsoft Edge, Cốc Cốc, Brave, Mozilla Firefox**.
- Tùy chọn sao lưu các dữ liệu quan trọng:
  - 🔖 Dấu trang (Bookmarks / Favorites)
  - 🕒 Lịch sử duyệt web (Browsing History)
  - 🔑 Mật khẩu đã lưu (Saved Passwords)
- Đóng gói dữ liệu sao lưu thành tệp `.zip` an toàn và khôi phục nhanh chóng khi chuyển đổi sang máy tính mới hoặc cài lại hệ điều hành.

#### 4.5. 📦 Kho Phần Mềm Free (Winget & One-Click Installer)
- Tích hợp trình quản lý gói chính thức của Microsoft: **Windows Package Manager (Winget)**.
- Danh mục phần mềm miễn phí thiết yếu được tuyển chọn kỹ lưỡng:
  - **Bộ gõ & Văn phòng:** Unikey, EVKey, Foxit Reader, Adobe Acrobat Reader, LibreOffice...
  - **Nén & Giải nén:** 7-Zip, WinRAR...
  - **Trình duyệt web:** Google Chrome, Cốc Cốc, Firefox, Brave...
  - **Hỗ trợ từ xa:** UltraViewer, AnyDesk, TeamViewer...
  - **Chat & Làm việc:** Zalo, Telegram, Skype...
  - **Đa phương tiện:** VLC Media Player, K-Lite Codec Pack...
  - **Công cụ lập trình & Kỹ thuật:** Notepad++, Visual Studio Code, Git...
- Cài đặt âm thầm hàng loạt (`Batch Silent Install`), tự động bỏ qua các câu hỏi xác nhận rườm rà.

---

## 🛠️ CÔNG NGHỆ & KIẾN TRÚC PHÁT TRIỂN

| Thành Phần | Công Nghệ Sử Dụng | Mục Đích & Vai Trò |
| :--- | :--- | :--- |
| **Ngôn ngữ lõi** | Python 3.10+ / 3.14 (Embedded Engine) | Xử lý toàn bộ logic nghiệp vụ, gọi Windows API, xử lý đa luồng |
| **Giao diện người dùng** | PyWebView + HTML5 / CSS3 / ES6 / Vue 3 | Giao diện hiện đại, mượt mà, hỗ trợ Responsive và Dark Mode |
| **Hệ thống Web Engine** | Microsoft Edge Chromium (WebView2) | Render giao diện chuẩn web hiện đại, tiêu thụ cực ít RAM |
| **Tương tác Windows** | .NET CLR (Pythonnet) + Win32 ctypes | Điều khiển System Tray, Windows Forms, Registry, Services |
| **Giao tiếp liên tiến trình**| TCP Socket IPC (`127.0.0.1:49285`) | Kiểm tra đơn tiến trình & đánh thức cửa sổ khi chạy ngầm |
| **Bảo mật & Phân quyền** | Windows Manifest (`requireAdministrator`) | Tự động kích hoạt quyền UAC Administrator khi khởi chạy |
| **Bộ tệp sạch máy in** | Assets Spooler Clean Repository | Nhúng sẵn `win32spl.dll`, `localspl.dll`, `spoolsv.exe` sạch |
| **Đóng gói** | PyInstaller 6.x (`--onefile`) | Đóng gói thành 1 file `.exe` duy nhất không cần cài đặt |

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG

### 1. Dành Cho Kỹ Thuật Viên & Người Dùng Cuối (Khuyên dùng)
1. Tải bản build đóng gói sẵn: **`IT Tool LTT.exe`** tại thư mục `dist\` hoặc `dist_release\`.
2. Click đúp vào file để khởi chạy (phần mềm sẽ tự động yêu cầu quyền Quản trị viên `Administrator` để thực hiện các can thiệp hệ thống).
3. Sử dụng các tính năng qua menu 4 khối bên trái.
4. Nếu muốn phần mềm luôn sẵn sàng mỗi khi bật máy: Hãy gạt công tắc **"Khởi Động Cùng Win: BẬT"** ở thanh tiêu đề trên cùng.

### 2. Dành Cho Lập Trình Viên (Chạy từ mã nguồn)
Yêu cầu: Máy đã cài đặt **Python 3.8+** và thư viện **Microsoft Edge WebView2 Runtime**.

```bash
# 1. Di chuyển vào thư mục dự án
cd d:\GitHubDesktop\ITTools

# 2. Cài đặt các thư viện cần thiết
pip install -r ITTools/requirements.txt
pip install pywebview pythonnet pillow psutil openpyxl bottle

# 3. Khởi chạy ứng dụng
python ITTools/main.py
```
Hoặc click đúp trực tiếp vào file **`IT-Tools.bat`**.

### 3. Hướng Dẫn Tự Biên Dịch (Build Exe Độc Lập)
Để đóng gói lại toàn bộ ứng dụng thành 1 file `.exe` độc lập duy nhất:
```bash
# Cách 1: Sử dụng file build_exe.bat
build_exe.bat

# Cách 2: Chạy trực tiếp PyInstaller từ thư mục gốc
python -m PyInstaller IT-Tools.spec --clean --noconfirm
```
File thực thi sau khi hoàn tất sẽ nằm tại: **`ITTools\dist\IT_Tool_LTT.exe`** hoặc **`dist\IT Tool LTT.exe`** (~43 MB).

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

```
ITTools\
├── IT-Tools.bat               # File khởi động nhanh từ mã nguồn Python
├── IT-Tools.spec              # Cấu hình đóng gói PyInstaller 1 file duy nhất
├── build_exe.bat              # Kịch bản tự động build file EXE
├── README.md                  # Tài liệu hướng dẫn sử dụng chi tiết
└── ITTools\                   # Mã nguồn chính của dự án
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
    ├── modules\               # 28 module xử lý logic Windows chuyên sâu
    │   ├── auto_shutdown.py   # Hẹn giờ tắt máy & xuất báo cáo Event Log
    │   ├── backup_driver.py   # Sao lưu & phục hồi driver
    │   ├── bitlocker.py       # Quản lý BitLocker & EFS
    │   ├── boot_manager.py    # Quản trị BCD Boot & tích hợp WinPE
    │   ├── browser_backup.py  # Sao lưu dữ liệu trình duyệt
    │   ├── classic_menu.py    # Menu chuột phải Windows 10
    │   ├── computer_info.py   # Thu thập thông số phần cứng & OS
    │   ├── currency.py        # Quy đổi ngoại tệ trực tuyến
    │   ├── datetime_tool.py   # Đồng bộ ngày giờ NTP & múi giờ
    │   ├── desktop_icon.py    # Bật/tắt icon Desktop
    │   ├── firewall.py        # Quản trị tường lửa Windows
    │   ├── folder_size.py     # Phân tích dung lượng thư mục
    │   ├── hosts_editor.py    # Chỉnh sửa file hosts hệ thống
    │   ├── install_office_silent.ps1 # Kịch bản tải & cài đặt ngầm Office
    │   ├── ip_manager.py      # Đổi IP Tĩnh/DHCP & DNS
    │   ├── ip_scanner.py      # Quét IP mạng LAN đa luồng
    │   ├── office_opt.py      # Tối ưu hóa bộ ứng dụng Office
    │   ├── other_tools.py     # Ultimate Performance, Hibernate, dọn rác
    │   ├── printer_fix.py     # Module sửa lỗi máy in & One Click Fix LAN
    │   ├── sendto_editor.py   # Tùy biến menu Send To
    │   ├── server_tools.py    # Quản trị RDP, Shares, dịch vụ mạng
    │   ├── services_manager.py# Quản trị Windows Services
    │   ├── startup_manager.py # Quản trị ứng dụng khởi động
    │   ├── uninstall_manager.py # Gỡ cài đặt phần mềm
    │   ├── win_update.py      # Bật/tắt Windows Update
    │   ├── wincheck.py        # Kích hoạt bản quyền & gỡ phần mềm crack
    │   ├── winget_runner.ps1  # Bộ thực thi cài đặt âm thầm Winget
    │   ├── zoom_screen.py     # Trình quản lý Zoom Screen & phím tắt toàn cục
    │   └── zoom_screen_gui.py # Bộ công cụ vẽ và phóng to màn hình native GUI
    ├── ui\                    # Giao diện đồ họa bổ trợ (Boot Manager GUI)
    │   └── main_window.py
    └── web\                   # Toàn bộ giao diện Webview hiện đại
        ├── index.html         # Giao diện chính và các Modal tương tác
        ├── style.css          # Hệ thống CSS Design System chuẩn mực
        ├── app.js             # Logic điều hướng chính và binding sự kiện
        ├── test_computer.css  # CSS cho bộ công cụ Test Computer
        ├── zoom_screen.css    # CSS cho bộ công cụ Zoom Screen
        ├── js\                # 18 tập tin JavaScript điều khiển từng phân hệ
        │   ├── app_manager.js # Quản lý phần mềm, Office, kích hoạt
        │   ├── auto_shutdown.js # Hẹn giờ & bảng Event Log
        │   ├── backup_driver.js # Điều khiển sao lưu driver
        │   ├── boot_manager.js# Điều khiển menu boot
        │   ├── browser_backup.js # Điều khiển sao lưu trình duyệt
        │   ├── computer_info.js # Hiển thị thông số cấu hình
        │   ├── currency_converter.js # Bộ chuyển đổi ngoại tệ
        │   ├── datetime.js    # Cấu hình ngày giờ
        │   ├── network_tools.js # IP Manager, Scanner, Firewall
        │   ├── printer_fix.js # One Click Fix & Modal tiến trình máy in
        │   ├── sendto_editor.js # Quản lý SendTo
        │   ├── server_tools.js# Quản lý RDP, Shares, Server
        │   ├── services_manager.js # Quản lý Services
        │   ├── system_drives.js # Phân tích dung lượng ổ đĩa
        │   ├── test_computer.js # Bộ 8 công cụ chẩn đoán phần cứng
        │   ├── vue.global.prod.js # Thư viện Vue 3 runtime
        │   ├── win_security.js# BitLocker, Classic Menu, Desktop Icon
        │   └── zoom_screen.js # Điều khiển Zoom Screen
        └── icons\             # Thư viện icon SVG của các ứng dụng phổ biến
```

---

## ⌨️ BẢNG PHÍM TẮT ZOOM SCREEN (MẶC ĐỊNH)

| Phím Tắt | Chức Năng | Mô Tả Chi Tiết |
| :---: | :--- | :--- |
| **`Ctrl + 1`** | **Zoom (Phóng to)** | Phóng to tại vị trí con trỏ chuột. Cuộn chuột để tăng/giảm tỷ lệ phóng. |
| **`Ctrl + 2`** | **LiveDraw (Vẽ trực tiếp)** | Vào chế độ vẽ chú thích lên màn hình. Hỗ trợ nhiều màu và hình khối. |
| **`Ctrl + 3`** | **Break Timer (Nghỉ giải lao)** | Bật đồng hồ đếm ngược giải lao với thanh tiến trình đồ họa. |
| **`Ctrl + 4`** | **LiveZoom** | Phóng to màn hình nhưng vẫn tương tác được chuột/phím bên dưới. |
| **`Ctrl + 5`** | **Record (Quay video)** | Bắt đầu / Dừng quay video màn hình định dạng MP4. |
| **`Ctrl + 6`** | **Snip (Chụp màn hình)** | Chụp ảnh vùng chọn sao chép vào Clipboard hoặc lưu file. |
| **`Ctrl + 7`** | **DemoType** | Tự động gõ văn bản chuẩn bị trước phục vụ giảng dạy demo. |
| **`Ctrl + 8`** | **Panorama** | Cuộn xem toàn cảnh màn hình khi thu phóng. |
| **`Ctrl + 9`** | **Mirror** | Lật ngược gương màn hình khi chiếu qua máy chiếu ngược. |
| **`T`** *(khi vẽ)* | **Gõ chữ** | Nhập văn bản trực tiếp lên màn hình tại vị trí trỏ chuột. |
| **`R / G / B / Y`** *(khi vẽ)* | **Đổi màu bút** | Đỏ (R), Xanh lá (G), Xanh dương (B), Vàng (Y), Cam (O), Hồng (P). |
| **`Shift`** *(khi vẽ)* | **Đường thẳng** | Giữ Shift khi kéo chuột để vẽ đường thẳng hoàn hảo. |
| **`Ctrl`** *(khi vẽ)* | **Hình chữ nhật** | Giữ Ctrl khi kéo chuột để vẽ khung chữ nhật. |
| **`Tab`** *(khi vẽ)* | **Hình Elip** | Giữ Tab khi kéo chuột để vẽ hình tròn / elip. |
| **`Ctrl + Shift`** *(khi vẽ)*| **Mũi tên** | Giữ Ctrl + Shift khi kéo chuột để vẽ mũi tên chỉ dẫn. |
| **`K / W`** *(khi vẽ)* | **Bảng đen / Bảng trắng** | Chuyển toàn bộ màn hình thành bảng phấn đen (`K`) hoặc bảng trắng (`W`). |
| **`Ctrl + Z`** | **Undo** | Hoàn tác nét vẽ vừa thực hiện gần nhất. |
| **`E`** *(khi vẽ)* | **Erase All** | Xóa sạch tất cả các nét vẽ đang có trên màn hình. |
| **`Esc / Chuột phải`** | **Thoát vẽ** | Thoát khỏi chế độ vẽ và trả lại màn hình làm việc bình thường. |

---

## 👤 THÔNG TIN TÁC GIẢ & HỖ TRỢ KỸ THUẬT

- **Tác giả & Phát triển:** **Lê Thế Tuấn**
- **Hotline / Zalo:** **[0352 194 195](https://zalo.me/0352194195)**
- **Website chính thức:** [https://lethetuanpc.blogspot.com](https://lethetuanpc.blogspot.com)
- **Kênh Telegram hỗ trợ:** [https://t.me/lethetuanpc](https://t.me/lethetuanpc)
- **Bản quyền:** © 2026 **IT Tool LTT**. Phát hành phục vụ cộng đồng kỹ thuật viên CNTT & quản trị viên mạng Việt Nam.

---

## 📄 GIẤY PHÉP BẢN QUYỀN (LICENSE)

Dự án này được phân phối dưới giấy phép **[MIT License](LICENSE)**. Bạn được toàn quyền sử dụng, sửa đổi, phân phối cho mục đích cá nhân.

---

> 💡 *Nếu công cụ này hữu ích cho công việc hàng ngày của bạn, hãy chia sẻ cho đồng nghiệp và bạn bè cùng trải nghiệm nhé!*
