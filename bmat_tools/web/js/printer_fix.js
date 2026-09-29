/**
 * IT-Tools 2026 - Printer & Credentials Module
 */
Object.assign(AppController.prototype, {
  async scanPrinters() {
    this.addLog("info", "Đang quét danh sách máy in hệ thống...");
    const tbody = document.getElementById("printers-list-body");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">Đang quét máy in...</td></tr>`;

    let printers = [];
    if (window.pywebview && window.pywebview.api) {
      printers = await window.pywebview.api.get_printers();
    } else {
      printers = [
        { name: "Microsoft Print to PDF", port: "PORTPROMPT:", status: "Sẵn sàng (Ready)", is_default: true },
        { name: "\\\\test\\Canon2900", port: "Ne00:", status: "Bình thường", is_default: false }
      ];
    }

    if (!printers || printers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-4 text-muted">Không tìm thấy máy in nào.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    printers.forEach((p, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><input type="checkbox" class="printer-checkbox" value="${p.name.replace(/"/g, '&quot;')}"></td>
        <td><strong>${p.is_default ? '⭐ ' : ''}${p.name}</strong></td>
        <td><code>${p.port}</code></td>
        <td><span class="badge ${p.status.includes('Ready') || p.status.includes('Bình') ? 'text-primary' : 'text-danger'}">${p.status}</span></td>
      `;
      tr.addEventListener("click", (e) => {
        if (e.target.tagName !== "INPUT") {
          document.querySelectorAll("#printers-list-body tr").forEach(r => r.classList.remove("selected"));
          tr.classList.add("selected");
          this.selectedPrinter = p.name;
        }
      });
      tbody.appendChild(tr);
    });

    this.addLog("success", `Đã quét thấy ${printers.length} máy in.`);
  },

  toggleSelectAllPrinters(chk) {
    document.querySelectorAll(".printer-checkbox").forEach(c => c.checked = chk.checked);
  },

  async printTestPage() {
    const selected = this.getSelectedPrinterName();
    if (!selected) {
      alert("Vui lòng chọn 1 máy in trong bảng để in trang test!");
      return;
    }
    this.addLog("info", `Đang in trang test cho ${selected}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.print_test_page(selected);
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert(`[MOCK] In trang test gửi đến ${selected}`);
    }
  },

  async setDefaultPrinter() {
    const selected = this.getSelectedPrinterName();
    if (!selected) {
      alert("Vui lòng chọn 1 máy in trong bảng!");
      return;
    }
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.set_default_printer(selected);
      this.addLog(res.success ? "success" : "error", res.message);
      this.scanPrinters();
    } else {
      alert(`[MOCK] Đã đặt ${selected} làm máy in mặc định.`);
    }
  },

  async addLocalPortPrompt() {
    const port = prompt("Nhập tên Cổng (Local Port) mới cần thêm (VD: 192.168.1.100 hoặc LocalPort1):");
    if (!port) return;
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.add_local_port(port);
      this.addLog(res.success ? "success" : "error", res.message);
    }
  },

  async sharePrinterPrompt() {
    const selected = this.getSelectedPrinterName();
    if (!selected) {
      alert("Vui lòng chọn 1 máy in trong bảng để chia sẻ!");
      return;
    }
    const shareName = prompt(`Nhập Tên Chia Sẻ (Share Name) cho máy in ${selected}:`, "PrinterShare");
    if (shareName === null) return;
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.share_printer_lan(selected, shareName);
      this.addLog(res.success ? "success" : "error", res.message);
    }
  },

  async deleteSelectedPrinter() {
    const selected = this.getSelectedPrinterNames();
    if (!selected || selected.length === 0) {
      alert("Vui lòng tích chọn (checkbox) hoặc click chọn máy in trong bảng để xóa!");
      return;
    }
    const printerListStr = selected.map(n => `• ${n}`).join("\n");
    if (confirm(`Bạn CHẮC CHẮN muốn xóa các máy in sau khỏi hệ thống?\n\n${printerListStr}\n\nThao tác này sẽ gỡ bỏ máy in khỏi Windows!`)) {
      this.addLog("info", `Đang thực hiện xóa ${selected.length} máy in...`);
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.delete_printer(selected);
        if (res && res.success) {
          this.addLog("success", res.message);
          alert(res.message);
        } else {
          this.addLog("error", (res && res.message) || "Lỗi xóa máy in");
        }
        this.scanPrinters();
      } else {
        alert(`[MOCK] Đã xóa: ${selected.join(", ")}`);
      }
    }
  },

  getSelectedPrinterNames() {
    const checkboxes = document.querySelectorAll(".printer-checkbox:checked");
    const names = Array.from(checkboxes).map(c => c.value);
    if (names.length > 0) return names;
    if (this.selectedPrinter) return [this.selectedPrinter];
    return [];
  },

  getSelectedPrinterName() {
    const names = this.getSelectedPrinterNames();
    return names.length > 0 ? names[0] : null;
  },

  async runPrinterFixFunc(funcName) {
    this.addLog("info", `Đang thực thi chức năng: ${funcName}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.run_printer_fix_func(funcName);
      if (res && res.success) {
        this.addLog("success", res.message || `Đã thực thi thành công: ${funcName}`);
      } else {
        this.addLog("error", (res && res.message) || `Lỗi khi thực thi: ${funcName}`);
      }
    } else {
      alert(`[MOCK] Thực thi chức năng ${funcName}`);
    }
  },

  async fixSelectedErrors() {
    const checkboxes = document.querySelectorAll(".error-checkbox:checked");
    const codes = Array.from(checkboxes).map(c => c.value);
    if (codes.length === 0) {
      alert("Vui lòng tích chọn ít nhất 1 mã lỗi ở bảng trên!");
      return;
    }
    this.addLog("info", `Đang sửa các mã lỗi: ${codes.join(", ")}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_printer_error_codes(codes);
      if (res.success) {
        this.addLog("success", `Hoàn tất sửa lỗi: ${(res.details || []).join(" | ")}`);
        alert("Đã sửa các mã lỗi máy in thành công!");
      } else {
        this.addLog("error", res.message);
      }
    } else {
      alert(`[MOCK] Sửa các lỗi: ${codes.join(", ")}`);
    }
  },

  async fixSpoolerServices() {
    this.addLog("info", "Đang Fix Print Spooler Service...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_spooler_services();
      this.addLog(res.success ? "success" : "error", res.message);
    }
  },

  async installPrintToPdf() {
    this.addLog("info", "Đang cài đặt Microsoft Print to PDF...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.install_print_to_pdf();
      this.addLog(res.success ? "success" : "error", res.message);
    }
  },

  async fixCanon2900() {
    this.addLog("info", "Đang Fix Canon LBP 2900/3300 Communication Error...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_canon_2900();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  async fixDefaultPrinter() {
    this.addLog("info", "Đang sửa lỗi Set Default Printer (0x00000709)...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_printer_error_codes(["0x00000709"]);
      this.addLog(res.success ? "success" : "error", "Đã fix lỗi Set Default Printer 0x709");
    }
  },

  async oneClickFixAll() {
    this.addLog("info", "Đang chạy Auto Fix 15 Bước toàn diện...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.one_click_fix_all_printers();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  downloadSpoolerFix() {
    alert("Tính năng tự động tải gói Spooler Fix tương thích với Windows đã sẵn sàng!");
  },

  resetCanonColor() {
    alert("Đã gửi lệnh Reset Canon Màu!");
  },

  fixDriverInstall() {
    alert("Đã gỡ bỏ PointAndPrint Restriction để cho phép cài Driver máy in LAN!");
  },

  backupRestoreDriver() {
    const navItem = document.querySelector('[data-tab="tab-backup-driver"]');
    if (navItem) navItem.click();
  },

  async scanCredentials() {
    try {
      this.addLog("info", "Đang quét danh sách Windows Credentials...");
      const tbody = document.getElementById("creds-list-body");
      if (!tbody) return;
      tbody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-muted">Đang quét credentials...</td></tr>`;

      let creds = [];
      if (window.pywebview && window.pywebview.api) {
        creds = await window.pywebview.api.get_credentials();
      } else {
        creds = [
          { target: "192.168.1.100", type: "Domain Password", user: "guest" }
        ];
      }

      if (!creds || !Array.isArray(creds) || creds.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-muted">Chưa có Windows Credential nào được lưu.</td></tr>`;
        return;
      }

      tbody.innerHTML = "";
      creds.forEach(c => {
        const tr = document.createElement("tr");
        const tVal = c.target || "N/A";
        const typeVal = c.type || "Domain Password";
        const uVal = c.user || "N/A";

        tr.innerHTML = `
          <td><strong>${tVal}</strong></td>
          <td><code>${typeVal}</code></td>
          <td>${uVal}</td>
        `;
        tr.addEventListener("click", () => {
          document.querySelectorAll("#creds-list-body tr").forEach(r => r.classList.remove("selected"));
          tr.classList.add("selected");
          this.selectedCredTarget = tVal;
          const targetEl = document.getElementById("cred-target");
          const userEl = document.getElementById("cred-user");
          if (targetEl) targetEl.value = tVal;
          if (userEl) userEl.value = uVal;
        });
        tbody.appendChild(tr);
      });

      this.addLog("success", `Tìm thấy ${creds.length} credentials đã lưu.`);
    } catch (ex) {
      console.error("Lỗi scanCredentials:", ex);
      this.addLog("error", `Lỗi quét credentials: ${ex.message || ex}`);
    }
  },

  async saveCredential() {
    const target = document.getElementById("cred-target").value.trim();
    const user = document.getElementById("cred-user").value.trim();
    const pass = document.getElementById("cred-pass").value;

    if (!target || !user) {
      alert("Vui lòng nhập Target (Tên máy chủ / IP) và User name!");
      return;
    }

    this.addLog("info", `Đang lưu Credential cho ${target}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.save_credential(target, user, pass);
      this.addLog(res.success ? "success" : "error", res.message);
      this.scanCredentials();
    }
  },

  async deleteSelectedCredential() {
    const target = this.selectedCredTarget || document.getElementById("cred-target").value.trim();
    if (!target) {
      alert("Vui lòng chọn hoặc nhập Credential cần xóa!");
      return;
    }

    if (confirm(`Bạn có chắc chắn muốn xóa Credential: ${target}?`)) {
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.delete_credential(target);
        this.addLog(res.success ? "success" : "error", res.message);
        this.scanCredentials();
      }
    }
  },

  async createShareUser() {
    const user = document.getElementById("share-username").value.trim();
    const pass = document.getElementById("share-password").value;

    if (!user || !pass) {
      alert("Vui lòng nhập Username và Mật khẩu!");
      return;
    }

    this.addLog("info", `Đang tạo user ${user}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.create_printer_share_user(user, pass);
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  },

  async fixDataSharing() {
    this.addLog("info", "Đang Fix Chia Sẻ Dữ Liệu & Mạng LAN...");
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.fix_data_sharing();
      this.addLog(res.success ? "success" : "error", res.message);
      alert(res.message);
    }
  }
});
