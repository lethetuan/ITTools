/**
 * IT Tool LTT 2026 - Server Tools Module
 * NIC Teaming SET, DHCP Backup/Restore, Active Directory Tools, iSCSI Manager
 */
Object.assign(AppController.prototype, {

  /**
   * Generic module handler fallback
   */
  async runModule(moduleName, action) {
    this.addLog("info", `Thực thi module: ${moduleName} - ${action}`);
    if (moduleName === 'server_tools') {
      if (action === 'open') {
        this.openServerToolsGui();
      } else {
        this.loadServerTools();
      }
    } else {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.run_module) {
        window.pywebview.api.run_module(moduleName, action);
      }
    }
  },

  /**
   * Loads Server Tools dashboard status (NIC teams, iSCSI, DHCP, AD)
   */
  async loadServerTools() {
    this.addLog("info", "Đang tải dữ liệu Server Tools (NIC Teaming, DHCP, AD, iSCSI)...");
    await this.loadNicTeams();
    await this.loadAdDomainInfo();
  },

  /**
   * Loads active NIC Teams into table
   */
  async loadNicTeams() {
    const tbody = document.getElementById("nic-teams-body");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="5" class="text-center py-3 text-muted">🔄 Đang tải danh sách NIC Teams...</td></tr>`;

    let result = null;
    if (window.pywebview && window.pywebview.api && window.pywebview.api.get_nic_teams) {
      result = await window.pywebview.api.get_nic_teams();
    } else {
      result = {
        success: true,
        teams: [
          { name: "SET-Team-01", mode: "SwitchIndependent", members: "Ethernet 1, Ethernet 2", status: "Up" }
        ]
      };
    }

    if (!result || !result.success || !result.teams || result.teams.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-3 text-muted">Chưa tạo NIC Team nào (hoặc máy tính chưa bật feature NetLbfo).</td></tr>`;
      return;
    }

    tbody.innerHTML = result.teams.map(team => `
      <tr>
        <td style="font-weight: 600; color: #1e293b; padding: 10px;">${this.escapeHtml(team.name)}</td>
        <td style="padding: 10px;">${this.escapeHtml(team.mode)}</td>
        <td style="padding: 10px;">${this.escapeHtml(team.members)}</td>
        <td style="padding: 10px;">
          <span class="badge ${team.status.toLowerCase() === 'up' ? 'badge-success' : 'badge-warning'}">
            ${this.escapeHtml(team.status)}
          </span>
        </td>
        <td style="text-align: right; padding: 10px;">
          <button class="btn btn-xs btn-rose-outline" onclick="app.removeNicTeam('${this.escapeHtml(team.name)}')">
            ❌ Xóa
          </button>
        </td>
      </tr>
    `).join("");
  },

  /**
   * Creates a new NIC Team (SET)
   */
  async createNicTeam() {
    const nameEl = document.getElementById("nic-team-name");
    const adaptersEl = document.getElementById("nic-team-adapters");
    const modeEl = document.getElementById("nic-team-mode");

    const name = nameEl ? nameEl.value.trim() : "";
    const adapters = adaptersEl ? adaptersEl.value.trim() : "";
    const mode = modeEl ? modeEl.value : "SwitchIndependent";

    if (!name || !adapters) {
      alert("Vui lòng nhập tên Team và danh sách Card mạng (phân cách bằng dấu phẩy)!");
      return;
    }

    this.addLog("info", `Đang tạo NIC Team '${name}' với card mạng: ${adapters}...`);

    if (window.pywebview && window.pywebview.api && window.pywebview.api.create_nic_team) {
      const res = await window.pywebview.api.create_nic_team(name, adapters, mode);
      alert(res.message);
    } else {
      alert(`[Mock] Đã gửi lệnh tạo NIC Team '${name}'.`);
    }

    this.loadNicTeams();
  },

  /**
   * Removes a NIC Team
   */
  async removeNicTeam(teamName) {
    if (!confirm(`Bạn có chắc chắn muốn xóa NIC Team '${teamName}' không?`)) return;

    this.addLog("info", `Đang xóa NIC Team '${teamName}'...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.remove_nic_team) {
      const res = await window.pywebview.api.remove_nic_team(teamName);
      alert(res.message);
    } else {
      alert(`[Mock] Đã gửi lệnh xóa NIC Team '${teamName}'.`);
    }

    this.loadNicTeams();
  },

  /**
   * Backup DHCP Server
   */
  async backupDhcpServer() {
    const serverEl = document.getElementById("dhcp-server-ip");
    const server = serverEl ? serverEl.value.trim() : "localhost";

    this.addLog("info", `Đang sao lưu DHCP Server (${server})...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.backup_dhcp_server) {
      const res = await window.pywebview.api.backup_dhcp_server(server, "");
      alert(res.message);
    } else {
      alert("[Mock] Đã sao lưu DHCP Server thành công!");
    }
  },

  /**
   * Restore DHCP Server
   */
  async restoreDhcpServer() {
    const serverEl = document.getElementById("dhcp-server-ip");
    const server = serverEl ? serverEl.value.trim() : "localhost";
    const path = prompt("Nhập đường dẫn thư mục sao lưu DHCP (Ví dụ: C:\\Users\\...\\Desktop\\DHCP_Backup):");
    if (!path) return;

    this.addLog("info", `Đang khôi phục DHCP Server (${server}) từ: ${path}...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.restore_dhcp_server) {
      const res = await window.pywebview.api.restore_dhcp_server(server, path);
      alert(res.message);
    } else {
      alert("[Mock] Đã khôi phục DHCP Server!");
    }
  },

  /**
   * Export DHCP Leases
   */
  async exportDhcpLeases() {
    const serverEl = document.getElementById("dhcp-server-ip");
    const server = serverEl ? serverEl.value.trim() : "localhost";

    this.addLog("info", `Đang xuất danh sách DHCP Leases (${server})...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.export_dhcp_leases) {
      const res = await window.pywebview.api.export_dhcp_leases(server, "");
      alert(res.message);
    } else {
      alert("[Mock] Đã xuất file DHCP Leases ra Desktop!");
    }
  },

  /**
   * Loads AD Domain Info
   */
  async loadAdDomainInfo() {
    const adBox = document.getElementById("ad-domain-info-box");
    if (!adBox) return;

    if (window.pywebview && window.pywebview.api && window.pywebview.api.get_ad_domain_info) {
      const res = await window.pywebview.api.get_ad_domain_info();
      if (res && res.success && res.info) {
        const info = res.info;
        adBox.innerHTML = `
          <div style="font-size: 13px; line-height: 1.6; color: #334155;">
            <div><strong>Tên Domain:</strong> ${this.escapeHtml(info.Name || 'N/A')}</div>
            <div><strong>DNS Root:</strong> ${this.escapeHtml(info.DNSRoot || 'N/A')}</div>
            <div><strong>Domain Mode:</strong> ${this.escapeHtml(info.DomainMode || 'N/A')}</div>
            <div><strong>PDC Emulator:</strong> ${this.escapeHtml(info.PDCEmulator || 'N/A')}</div>
          </div>
        `;
        return;
      }
    }

    adBox.innerHTML = `<span class="text-muted" style="font-size: 13px;">Máy tính cục bộ chưa Join Domain Active Directory hoặc chưa cài đặt RSAT module.</span>`;
  },

  /**
   * Export AD Users
   */
  async exportAdUsers() {
    this.addLog("info", "Đang xuất danh sách Active Directory Users...");
    if (window.pywebview && window.pywebview.api && window.pywebview.api.export_ad_users) {
      const res = await window.pywebview.api.export_ad_users("");
      alert(res.message);
    } else {
      alert("[Mock] Đã xuất file AD Users ra Desktop!");
    }
  },

  /**
   * Connect iSCSI Target Portal
   */
  async connectIscsiTarget() {
    const ipEl = document.getElementById("iscsi-target-ip");
    const portEl = document.getElementById("iscsi-target-port");
    const outputEl = document.getElementById("iscsi-output");

    const ip = ipEl ? ipEl.value.trim() : "";
    const port = portEl ? portEl.value.trim() : "3260";

    if (!ip) {
      alert("Vui lòng nhập IP Target Portal!");
      return;
    }

    this.addLog("info", `Đang kết nối iSCSI Target Portal ${ip}:${port}...`);
    if (window.pywebview && window.pywebview.api && window.pywebview.api.connect_iscsi_target) {
      const res = await window.pywebview.api.connect_iscsi_target(ip, port);
      if (outputEl) outputEl.value = res.output || res.message;
      alert(res.message);
    } else {
      if (outputEl) outputEl.value = `[Mock] Connecting to ${ip}:${port}... Success!`;
      alert("[Mock] Đã kết nối iSCSI Portal!");
    }
  },

  /**
   * List iSCSI Targets
   */
  async listIscsiTargets() {
    const outputEl = document.getElementById("iscsi-output");
    this.addLog("info", "Đang truy vấn danh sách iSCSI Targets...");
    if (window.pywebview && window.pywebview.api && window.pywebview.api.list_iscsi_targets) {
      const res = await window.pywebview.api.list_iscsi_targets();
      if (outputEl) outputEl.value = res.output || res.message;
    } else {
      if (outputEl) outputEl.value = "[Mock] Target Name: iqn.2026-09.com.server:target1\nStatus: Connected";
    }
  },

  /**
   * Open iSCSI Initiator Control Panel
   */
  openIscsiCpl() {
    this.addLog("info", "Mở Windows iSCSI Initiator Properties (iscsicpl.exe)...");
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_iscsi_cpl) {
      window.pywebview.api.open_iscsi_cpl();
    }
  },

  /**
   * Open Tkinter Server Tools GUI window
   */
  openServerToolsGui() {
    this.addLog("info", "Mở cửa sổ Server Tools Tkinter GUI...");
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_server_tools_gui) {
      window.pywebview.api.open_server_tools_gui();
    }
  },

  /**
   * Helper HTML escape
   */
  escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

});
