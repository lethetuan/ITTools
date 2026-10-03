/**
 * IT Tool LTT 2026 - Windows Services Manager Module
 * Author: Lê Thế Tuấn
 */

// Cơ sở tri thức đề xuất & tư vấn tối ưu Windows Services
const SERVICES_RECOMMENDATIONS = {
  // ── NHÓM KHUYÊN TẮT (DISABLED) ──────────────────────────────────────────
  "diagtrack": {
    rec: "Disabled",
    tag: "Khuyên tắt",
    type: "disable",
    short: "Thu thập nhật ký telemetry gửi về Microsoft. Tắt giúp nhẹ máy & tăng bảo mật riêng tư.",
    desc: "Connected User Experiences and Telemetry là dịch vụ ngầm liên tục ghi nhận thói quen sử dụng, lịch sử thao tác và gửi về máy chủ Microsoft. Việc tắt dịch vụ này hoàn toàn an toàn 100%, giúp giải phóng chu kỳ CPU, giảm đọc ghi ổ cứng và bảo vệ quyền riêng tư cá nhân.",
    safety: "Hoàn toàn an toàn (100% Safe)"
  },
  "dmwappushservice": {
    rec: "Disabled",
    tag: "Khuyên tắt",
    type: "disable",
    short: "Định tuyến tin nhắn WAP push & telemetry. Hầu như không cần thiết với người dùng thông thường.",
    desc: "Dịch vụ định tuyến tin nhắn WAP Push và hỗ trợ thu thập dữ liệu telemetry cho các thiết bị di động/doanh nghiệp. Người dùng cá nhân và văn phòng không cần đến.",
    safety: "Hoàn toàn an toàn (100% Safe)"
  },
  "retaildemo": {
    rec: "Disabled",
    tag: "Khuyên tắt",
    type: "disable",
    short: "Chế độ máy trưng bày siêu thị. Hoàn toàn vô ích trên máy tính cá nhân/văn phòng.",
    desc: "Dịch vụ kích hoạt chế độ chạy thử máy mẫu (Demo) cho các siêu thị điện máy trưng bày hàng bán. Trên máy tính người dùng cuối, dịch vụ này hoàn toàn vô ích và lãng phí tài nguyên.",
    safety: "Hoàn toàn an toàn (100% Safe)"
  },
  "remoteregistry": {
    rec: "Disabled",
    tag: "Khuyên tắt",
    type: "disable",
    short: "Cho phép chỉnh sửa Registry từ xa qua mạng. Nên tắt để ngăn chặn hacker nội bộ.",
    desc: "Cho phép người dùng từ máy tính khác trong mạng sửa đổi các khóa cấu hình Registry của máy bạn. Tắt dịch vụ này là khuyến nghị bảo mật hàng đầu của các chuyên gia để ngăn chặn xâm nhập.",
    safety: "Rất an toàn - Tăng bảo mật"
  },
  "fax": {
    rec: "Disabled",
    tag: "Khuyên tắt",
    type: "disable",
    short: "Gửi/nhận máy fax cổ điển. Nếu không cắm máy fax vật lý, nên tắt để giải phóng RAM.",
    desc: "Quản lý việc gửi và nhận tín hiệu Fax qua modem điện thoại. Ngày nay 99.9% người dùng không dùng máy fax, nên tắt để giải phóng RAM.",
    safety: "Rất an toàn (trừ khi dùng máy Fax)"
  },
  "sysmain": {
    rec: "Disabled",
    tag: "Khuyên tắt / Thủ công",
    type: "disable",
    short: "Nạp trước app vào RAM. Trên SSD hay gây 100% Disk kéo dài hoặc giật lag game.",
    desc: "SysMain (trước đây là Superfetch) tự động tải trước các file ứng dụng hay dùng vào bộ nhớ RAM. Trên ổ cứng HDD hoặc SSD giá rẻ, nó thường xuyên gây nghẽn đĩa 100% Disk kéo dài hoặc giật khung hình khi chơi game nặng.",
    safety: "An toàn (Khuyên tắt nếu máy bị 100% Disk)"
  },

  // ── NHÓM KHUYÊN ĐỂ THỦ CÔNG (MANUAL) ────────────────────────────────────
  "wsearch": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Đánh chỉ mục tìm kiếm file. Thường xuyên gây quét đĩa liên tục lúc khởi động.",
    desc: "Windows Search Indexing liên tục chạy ngầm để quét chỉ mục file trên ổ đĩa. Nếu bạn ít khi tìm kiếm file hoặc máy có cấu hình yếu/bị full disk, nên chuyển sang Manual hoặc Disabled để máy thanh thoát hơn.",
    safety: "Khá an toàn (Chỉ làm tìm kiếm file chậm hơn một chút)"
  },
  "wersvc": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Báo cáo lỗi về Microsoft khi crash. Chuyển sang Manual để đỡ chạy ngầm thường trực.",
    desc: "Windows Error Reporting Service ghi nhận các sự cố crash ứng dụng và chuẩn bị gửi về Microsoft. Để Manual giúp dịch vụ chỉ chạy khi có lỗi thật sự xảy ra thay vì chiếm tài nguyên thường trực.",
    safety: "Hoàn toàn an toàn (100% Safe)"
  },
  "mapsbroker": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Quản lý tải bản đồ Windows Maps. Đa số người dùng dùng Google Maps web.",
    desc: "Dịch vụ hỗ trợ tải bản đồ ngoại tuyến cho ứng dụng Maps mặc định của Windows. Đa phần người dùng dùng trình duyệt web để tra cứu bản đồ nên không cần chạy tự động.",
    safety: "Hoàn toàn an toàn"
  },
  "lfsvc": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Dịch vụ định vị vị trí địa lý. Chuyển Manual để tiết kiệm pin & RAM.",
    desc: "Geolocation Service theo dõi vị trí hiện tại của thiết bị để cung cấp cho ứng dụng thời tiết hoặc bản đồ. Để Manual giúp dịch vụ chỉ mở khi bạn chủ động cho phép ứng dụng định vị.",
    safety: "Hoàn toàn an toàn"
  },
  "xboxgipsvc": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Phụ kiện tay cầm Xbox. Để Manual nếu không cắm tay cầm chơi game Xbox.",
    desc: "Xbox Accessory Management Service quản lý tay cầm và phụ kiện Xbox. Nếu không cắm tay cầm chơi game, không cần thiết phải chạy tự động.",
    safety: "An toàn cho máy không cắm tay cầm"
  },
  "xblauthmanager": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Xác thực tài khoản Xbox Live. Nếu không chơi game Xbox, nên để Manual.",
    desc: "Cung cấp dịch vụ đăng nhập và xác thực cho Xbox Live. Người dùng văn phòng hoặc không chơi game Microsoft Store nên để Manual.",
    safety: "An toàn nếu không chơi game Xbox"
  },
  "xblgamesave": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Đồng bộ lưu file game Xbox Live. Nên để Manual nếu không dùng game Xbox.",
    desc: "Đồng bộ save game lên đám mây Xbox Live. Chỉ cần chạy khi bạn mở game Xbox.",
    safety: "An toàn nếu không chơi game Xbox"
  },
  "xboxnetapisvc": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Mạng Xbox Live Networking. Để Manual nếu không chơi game online Xbox.",
    desc: "Hỗ trợ kết nối mạng cho các dịch vụ nhiều người chơi của Xbox.",
    safety: "An toàn nếu không chơi game Xbox"
  },
  "wisvc": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Thử nghiệm bản build mới Windows Insider. Người dùng thường nên để Manual.",
    desc: "Dịch vụ phục vụ người dùng đăng ký nhận các bản cập nhật thử nghiệm Windows Insider Preview.",
    safety: "Hoàn toàn an toàn"
  },
  "walletservice": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Dịch vụ ví điện tử Windows Wallet. Hầu như không sử dụng tại Việt Nam.",
    desc: "Hỗ trợ thanh toán và lưu thẻ qua ứng dụng Wallet của Windows.",
    safety: "Hoàn toàn an toàn"
  },
  "troubleshootingsvc": {
    rec: "Manual",
    tag: "Khuyên để Thủ công",
    type: "manual",
    short: "Tự động chẩn đoán lỗi. Nên để Manual để chỉ chạy khi bạn yêu cầu.",
    desc: "Chạy các tác vụ chẩn đoán tự động của Windows. Để Manual giúp Windows không tự ý chạy ngầm gây lag máy.",
    safety: "Rất an toàn"
  },
  "spooler": {
    rec: "Automatic",
    tag: "Cần cho máy in",
    type: "printer",
    short: "Dịch vụ in ấn. BẮT BUỘC để Automatic nếu có máy in. Không in có thể để Manual.",
    desc: "Print Spooler nạp các lệnh in vào bộ nhớ đệm trước khi gửi đến máy in. Nếu máy tính văn phòng có in ấn tài liệu thì PHẢI giữ Automatic. Nếu là máy cá nhân không bao giờ in thì có thể để Manual.",
    safety: "Cần thiết nếu có máy in"
  },
  "bthserv": {
    rec: "Manual",
    tag: "Cần cho Bluetooth",
    type: "device",
    short: "Dịch vụ Bluetooth. Giữ Automatic nếu dùng tai nghe/chuột Bluetooth.",
    desc: "Hỗ trợ kết nối và khám phá các thiết bị Bluetooth xung quanh. Nếu máy bàn không có Bluetooth có thể để Manual.",
    safety: "Cần thiết nếu dùng Bluetooth"
  },

  // ── NHÓM DỊCH VỤ CỐT LÕI (CRITICAL CORE - BẮT BUỘC GIỮ NGUYÊN) ──────────
  "rpcss": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "Remote Procedure Call - KHÔNG ĐƯỢC TẮT.", desc: "Dịch vụ nền tảng tối quan trọng điều phối giao tiếp giữa các tiến trình của Windows.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "dcomlaunch": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "DCOM Process Launcher - KHÔNG ĐƯỢC TẮT.", desc: "Khởi chạy các máy chủ COM và DCOM cho mọi chương trình trên Windows.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "audiosrv": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "Windows Audio - Quản lý phát âm thanh, loa, tai nghe.", desc: "Nếu tắt dịch vụ này máy tính sẽ bị câm hoàn toàn không có âm thanh.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "dhcp": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "DHCP Client - Nhận IP mạng internet từ Router.", desc: "Nếu tắt dịch vụ này máy tính sẽ không thể nhận địa chỉ IP tự động để vào mạng.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "dnscache": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "DNS Client - Phân giải tên miền website.", desc: "Lưu đệm và phân giải tên miền web (như google.com). Tắt sẽ gây lỗi duyệt web.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "plugplay": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "Plug and Play - Nhận diện phần cứng USB, bàn phím, chuột.", desc: "Tự động nhận diện thiết bị khi cắm vào máy tính.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "eventlog": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "Windows Event Log - Ghi nhật ký bảo mật và lỗi hệ thống.", desc: "Nhiều dịch vụ hệ thống phụ thuộc vào Event Log để hoạt động.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "winmgmt": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "WMI - Quản lý thông tin phần cứng hệ thống.", desc: "Windows Management Instrumentation cung cấp dữ liệu cấu hình cho các ứng dụng.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "cryptsvc": { rec: "Automatic", tag: "Cốt lõi hệ thống", type: "core", short: "Cryptographic Services - Quản lý chứng chỉ số và bảo mật.", desc: "Xác thực chữ ký số của file hệ thống và trình điều khiển driver.", safety: "Bắt buộc giữ nguyên (Critical)" },
  "lanmanworkstation": { rec: "Automatic", tag: "Cốt lõi mạng", type: "core", short: "Workstation - Kết nối chia sẻ dữ liệu và máy in mạng LAN.", desc: "Tạo và duy trì các kết nối mạng máy khách đến các máy chủ chia sẻ tệp và máy in.", safety: "Bắt buộc giữ nguyên (Critical)" }
};

Object.assign(AppController.prototype, {
  async loadServices() {
    const badgeEl = document.getElementById("services-count-badge");
    const bodyEl = document.getElementById("services-list-body");

    if (bodyEl) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-4 text-muted">
            <span class="spinner-border spinner-border-sm text-primary"></span>
            Đang quét danh sách các dịch vụ Windows...
          </td>
        </tr>
      `;
    }

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.get_windows_services();
        if (res && res.success) {
          this.allServices = res.services || [];
          if (badgeEl) badgeEl.innerText = `${res.total} Services`;
          this.renderServicesList(this.allServices);
        } else {
          if (bodyEl) {
            bodyEl.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-danger">Lỗi quét Services: ${res ? res.message : 'Unknown'}</td></tr>`;
          }
        }
      } catch (err) {
        console.error("Lỗi get_windows_services:", err);
      }
    } else {
      const mockServices = [
        { name: "DiagTrack", display: "Connected User Experiences and Telemetry", status: "Running", start_type: "Automatic" },
        { name: "SysMain", display: "SysMain (Superfetch)", status: "Running", start_type: "Automatic" },
        { name: "WSearch", display: "Windows Search", status: "Running", start_type: "Automatic" },
        { name: "Spooler", display: "Print Spooler", status: "Running", start_type: "Automatic" },
        { name: "wuauserv", display: "Windows Update", status: "Stopped", start_type: "Manual" },
        { name: "RpcSs", display: "Remote Procedure Call (RPC)", status: "Running", start_type: "Automatic" },
        { name: "RemoteRegistry", display: "Remote Registry", status: "Stopped", start_type: "Disabled" },
        { name: "Fax", display: "Fax Service", status: "Stopped", start_type: "Manual" }
      ];
      this.allServices = mockServices;
      if (badgeEl) badgeEl.innerText = `${mockServices.length} Services (MOCK)`;
      this.renderServicesList(mockServices);
    }
  },

  renderServicesList(services) {
    const bodyEl = document.getElementById("services-list-body");
    if (!bodyEl) return;

    if (!services || services.length === 0) {
      bodyEl.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-4 text-muted">
            Không tìm thấy dịch vụ nào phù hợp với bộ lọc.
          </td>
        </tr>
      `;
      return;
    }

    bodyEl.innerHTML = services.map((item, index) => {
      const isRunning = (item.status && item.status.toLowerCase() === 'running');
      const statusBadge = isRunning
        ? `<span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); font-weight:700; font-size:11px; padding:3px 8px; border-radius:12px;">🟢 Running</span>`
        : `<span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); font-size:11px; padding:3px 8px; border-radius:12px;">🔴 Stopped</span>`;

      const startType = item.start_type || 'Manual';
      const sKey = (item.name || '').toLowerCase();
      const rec = SERVICES_RECOMMENDATIONS[sKey];

      // Xây dựng nhãn tư vấn & đề xuất tối ưu
      let adviceHtml = '';
      if (rec) {
        let isAlreadyOptimized = false;
        let badgeStyle = '';
        let badgeText = '';

        if (rec.type === 'disable') {
          isAlreadyOptimized = startType.toLowerCase().includes('disabled');
          if (isAlreadyOptimized) {
            badgeStyle = 'background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4);';
            badgeText = '✓ Đã tối ưu (Disabled)';
          } else {
            badgeStyle = 'background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4);';
            badgeText = '💡 Khuyên tắt (Disabled)';
          }
        } else if (rec.type === 'manual') {
          isAlreadyOptimized = startType.toLowerCase().includes('manual') || startType.toLowerCase().includes('demand');
          if (isAlreadyOptimized) {
            badgeStyle = 'background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4);';
            badgeText = '✓ Đã tối ưu (Manual)';
          } else {
            badgeStyle = 'background: rgba(2, 132, 199, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4);';
            badgeText = '✋ Khuyên để Thủ công (Manual)';
          }
        } else if (rec.type === 'core') {
          badgeStyle = 'background: rgba(100, 116, 139, 0.2); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.4);';
          badgeText = '🛡️ Cốt lõi (Giữ nguyên)';
        } else if (rec.type === 'printer') {
          badgeStyle = 'background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.4);';
          badgeText = '🖨️ Cần cho máy in';
        } else if (rec.type === 'device') {
          badgeStyle = 'background: rgba(139, 92, 246, 0.15); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4);';
          badgeText = '🎧 Cần cho Bluetooth';
        }

        adviceHtml = `
          <div>
            <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
              <span class="badge" style="${badgeStyle} font-size: 10.5px; font-weight: 700; padding: 2px 7px; border-radius: 4px;">
                ${badgeText}
              </span>
              <button class="btn btn-xs btn-sky-outline" onclick="app.showServiceAdvice('${item.name}')" style="padding: 1px 6px; font-size: 10px; font-weight: 600;" title="Xem giải thích chi tiết & tư vấn an toàn">
                ℹ️ Chi tiết
              </button>
            </div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px; line-height: 1.35;">
              ${rec.short}
            </div>
          </div>
        `;
      } else {
        adviceHtml = `
          <span style="font-size: 11px; color: var(--text-muted); font-style: italic;">
            ⚖️ Mặc định (Tùy nhu cầu người dùng)
          </span>
        `;
      }

      return `
        <tr style="border-bottom: 1px solid #f1f5f9;">
          <td style="text-align: center; font-weight: 600; color: #64748b; padding: 8px;">${index + 1}</td>
          <td style="padding: 8px;">
            <strong style="font-family: monospace; color: #0284c7; font-size: 12.5px;">${item.name}</strong>
          </td>
          <td style="padding: 8px; color: #1e293b; font-weight: 600; font-size: 12.5px;">
            ${item.display || item.name}
          </td>
          <td style="padding: 8px;">
            ${adviceHtml}
          </td>
          <td style="text-align: center; padding: 8px;">
            ${statusBadge}
          </td>
          <td style="text-align: center; padding: 8px;">
            <select class="form-control" onchange="app.changeServiceStartup('${item.name}', this)" style="padding: 3px 6px; font-size: 12px; border-radius: 6px; border: 1px solid #cbd5e1; width: 130px; margin: 0 auto; display: inline-block;">
              <option value="Automatic" ${startType.toLowerCase().includes('auto') ? 'selected' : ''}>⚡ Automatic</option>
              <option value="Manual" ${startType.toLowerCase().includes('manual') || startType.toLowerCase().includes('demand') ? 'selected' : ''}>✋ Manual</option>
              <option value="Disabled" ${startType.toLowerCase().includes('disabled') ? 'selected' : ''}>🚫 Disabled</option>
            </select>
          </td>
          <td style="text-align: right; padding: 8px;">
            <div style="display: flex; gap: 4px; justify-content: flex-end;">
              ${!isRunning ? `
                <button class="btn btn-success-solid btn-sm" onclick="app.manageService('${item.name}', 'start')" title="Bật dịch vụ" style="padding: 2px 8px; font-size: 11px;">
                  ▶ Start
                </button>
              ` : `
                <button class="btn btn-danger-solid btn-sm" onclick="app.manageService('${item.name}', 'stop')" title="Tắt dịch vụ" style="padding: 2px 8px; font-size: 11px;">
                  ⏹ Stop
                </button>
              `}
              <button class="btn btn-sky-outline btn-sm" onclick="app.manageService('${item.name}', 'restart')" title="Restart dịch vụ" style="padding: 2px 8px; font-size: 11px;">
                🔄 Restart
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  },

  searchServices() {
    const query = document.getElementById("services-search-input")?.value.toLowerCase().trim() || "";
    if (!this.allServices) return;

    if (!query) {
      this.renderServicesList(this.allServices);
      return;
    }

    const filtered = this.allServices.filter(s =>
      (s.name && s.name.toLowerCase().includes(query)) ||
      (s.display && s.display.toLowerCase().includes(query)) ||
      (s.status && s.status.toLowerCase().includes(query)) ||
      (s.start_type && s.start_type.toLowerCase().includes(query)) ||
      (SERVICES_RECOMMENDATIONS[s.name?.toLowerCase()]?.short?.toLowerCase().includes(query))
    );
    this.renderServicesList(filtered);
  },

  filterServicesCategory(category, btnEl) {
    if (btnEl) {
      btnEl.parentElement.querySelectorAll(".btn").forEach(b => {
        b.classList.remove("btn-primary");
        b.classList.add("btn-slate-light");
      });
      btnEl.classList.remove("btn-slate-light");
      btnEl.classList.add("btn-primary");
    }

    if (!this.allServices) return;

    if (category === 'all') {
      this.renderServicesList(this.allServices);
    } else if (category === 'recommended') {
      // Lọc các dịch vụ có đề xuất tối ưu (Khuyên tắt hoặc Khuyên để thủ công)
      const list = this.allServices.filter(s => {
        const key = (s.name || '').toLowerCase();
        const r = SERVICES_RECOMMENDATIONS[key];
        return r && (r.type === 'disable' || r.type === 'manual');
      });
      this.renderServicesList(list);
    } else if (category === 'core') {
      // Lọc các dịch vụ cốt lõi không được tắt
      const list = this.allServices.filter(s => {
        const key = (s.name || '').toLowerCase();
        const r = SERVICES_RECOMMENDATIONS[key];
        return r && r.type === 'core';
      });
      this.renderServicesList(list);
    } else if (category === 'running') {
      this.renderServicesList(this.allServices.filter(s => s.status && s.status.toLowerCase() === 'running'));
    } else if (category === 'stopped') {
      this.renderServicesList(this.allServices.filter(s => !s.status || s.status.toLowerCase() !== 'running'));
    } else if (category === 'auto') {
      this.renderServicesList(this.allServices.filter(s => s.start_type && s.start_type.toLowerCase().includes('auto')));
    }
  },

  showServiceAdvice(serviceName) {
    const sKey = (serviceName || '').toLowerCase();
    const rec = SERVICES_RECOMMENDATIONS[sKey];
    const sItem = (this.allServices || []).find(s => (s.name || '').toLowerCase() === sKey) || {
      name: serviceName,
      display: serviceName,
      status: 'Unknown',
      start_type: 'Unknown'
    };

    const modalBody = document.getElementById("service-advice-modal-body");
    const modalEl = document.getElementById("service-advice-modal");
    if (!modalBody || !modalEl) return;

    if (!rec) {
      modalBody.innerHTML = `
        <div style="font-size: 13px; color: #334155; line-height: 1.6;">
          <p>Dịch vụ: <strong>${serviceName}</strong></p>
          <p class="text-muted">Đây là dịch vụ bình thường hoặc của phần mềm bên thứ 3. Hệ thống giữ nguyên theo cấu hình mặc định của bạn.</p>
        </div>
      `;
      modalEl.style.display = "flex";
      return;
    }

    const isCurrentMatch = sItem.start_type && sItem.start_type.toLowerCase().includes(rec.rec.toLowerCase());

    modalBody.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 12px; font-size: 13px;">
        <div style="background: rgba(2, 132, 199, 0.08); border: 1px solid rgba(2, 132, 199, 0.25); border-radius: 8px; padding: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <strong style="font-family: monospace; font-size: 14px; color: #0284c7;">${sItem.name}</strong>
            <span class="badge" style="background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-weight: 700;">
              Hiện tại: ${sItem.start_type || 'Manual'}
            </span>
          </div>
          <div style="color: var(--text-muted); font-size: 12px;">
            ${sItem.display}
          </div>
        </div>

        <div>
          <strong style="color: #0284c7; display: block; margin-bottom: 4px;">🎯 Lời Khuyên Tối Ưu Của IT Tool LTT:</strong>
          <div style="padding: 10px 12px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; font-weight: 600; color: #d97706; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 18px;">💡</span>
            <span>Khuyên dùng kiểu: <u>${rec.rec}</u> — ${rec.tag}</span>
          </div>
        </div>

        <div>
          <strong style="color: #0284c7; display: block; margin-bottom: 4px;">📋 Chức Năng Dịch Vụ:</strong>
          <p style="margin: 0; line-height: 1.6; color: var(--text-main);">
            ${rec.desc}
          </p>
        </div>

        <div>
          <strong style="color: #0284c7; display: block; margin-bottom: 4px;">🛡️ Đánh Giá Độ An Toàn:</strong>
          <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); font-size: 12px; padding: 4px 10px; border-radius: 6px; font-weight: 700;">
            ${rec.safety}
          </span>
        </div>

        <div style="background: rgba(239, 68, 68, 0.08); border-left: 3px solid #ef4444; padding: 8px 12px; border-radius: 4px; font-size: 12px; color: var(--text-muted); line-height: 1.5;">
          ⚠️ <strong>Lưu ý:</strong> IT Tool LTT tuyệt đối <strong>không tự ý thay đổi</strong> dịch vụ của bạn. Bạn hãy cân nhắc nhu cầu và tự bấm nút bên dưới nếu đồng ý áp dụng.
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 6px; border-top: 1px solid rgba(0,0,0,0.08); padding-top: 12px;">
          <button class="btn btn-slate-light" onclick="app.closeServiceAdviceModal()">
            Đóng / Giữ Nguyên
          </button>
          ${!isCurrentMatch && rec.type !== 'core' ? `
            <button class="btn btn-primary-solid" onclick="app.applyRecommendedStartup('${sItem.name}', '${rec.rec}')">
              ⚡ Chuyển sang ${rec.rec}
            </button>
          ` : `
            <button class="btn btn-success-solid" disabled style="opacity: 0.7;">
              ✓ Đã ở trạng thái tối ưu
            </button>
          `}
        </div>
      </div>
    `;

    modalEl.style.display = "flex";
  },

  closeServiceAdviceModal() {
    const modalEl = document.getElementById("service-advice-modal");
    if (modalEl) modalEl.style.display = "none";
  },

  async applyRecommendedStartup(serviceName, targetStartupType) {
    const confirmed = confirm(`Bạn có chắc chắn muốn chuyển kiểu khởi động của dịch vụ "${serviceName}" sang "${targetStartupType}" để tối ưu không?\n\n(Lưu ý: Thao tác này chỉ áp dụng cho riêng dịch vụ này theo chỉ định của bạn)`);
    if (!confirmed) return;

    this.closeServiceAdviceModal();
    this.addLog("info", `Người dùng yêu cầu đổi kiểu khởi động '${serviceName}' sang ${targetStartupType}...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.set_service_startup_type(serviceName, targetStartupType);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadServices();
      } catch (err) {
        alert(`Lỗi đổi kiểu khởi động: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã đổi kiểu khởi động '${serviceName}' sang ${targetStartupType}!`);
      this.loadServices();
    }
  },

  async manageService(serviceName, action) {
    this.addLog("info", `Đang thực hiện ${action} trên dịch vụ '${serviceName}'...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.manage_windows_service(serviceName, action);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadServices();
      } catch (err) {
        alert(`Lỗi quản lý dịch vụ: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã thực hiện ${action} trên dịch vụ '${serviceName}'!`);
      this.loadServices();
    }
  },

  async changeServiceStartup(serviceName, selectEl) {
    const startupType = selectEl.value;
    this.addLog("info", `Đang đổi kiểu khởi động '${serviceName}' sang ${startupType}...`);

    if (window.pywebview && window.pywebview.api) {
      try {
        const res = await window.pywebview.api.set_service_startup_type(serviceName, startupType);
        this.addLog(res.success ? "success" : "error", res.message);
        alert(res.message);
        this.loadServices();
      } catch (err) {
        alert(`Lỗi đổi kiểu khởi động: ${err.message}`);
      }
    } else {
      alert(`[MOCK] Đã đổi kiểu khởi động '${serviceName}' sang ${startupType}!`);
    }
  },

  async openServicesMsc() {
    if (window.pywebview && window.pywebview.api) {
      try {
        await window.pywebview.api.open_services_msc();
      } catch (err) {
        console.error("Lỗi mở services.msc:", err);
      }
    } else {
      alert("[MOCK] Đã mở Services.msc!");
    }
  }
});
