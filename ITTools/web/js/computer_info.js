/**
 * IT Tool LTT 2026 - Computer Hardware Info & Real-time Diagnostics Module
 */
Object.assign(AppController.prototype, {

  async loadComputerInfo() {
    this.addLog("info", "Dang quet thong tin cau hinh phan cung he thong...");

    if (!this.hwClockTimer) {
      this.hwClockTimer = setInterval(() => {
        const clkEl = document.getElementById("hw-system-clock");
        if (clkEl) clkEl.innerText = new Date().toLocaleTimeString("vi-VN");
      }, 1000);
    }
    const clkEl = document.getElementById("hw-system-clock");
    if (clkEl) clkEl.innerText = new Date().toLocaleTimeString("vi-VN");

    let info = null;
    if (window.pywebview && window.pywebview.api) {
      info = await window.pywebview.api.get_computer_info();
    } else {
      info = {
        success: true,
        cpu: { name: "Intel Core i5-1135G7 @ 2.40GHz", cores_threads: "4 nhan 8 luong", max_clock: "2.40 GHz", cache: "8 MB Cache" },
        system: { vendor: "Dell Inc.", manufacturer: "Dell Inc.", model: "Latitude 5520", computer_name: "DESKTOP-5VAK9DN", system_family: "Latitude", chassis_type: "Notebook", is_laptop: true },
        service_tag: { serial: "DYP1BG3", service_tag: "DYP1BG3", product_id: "DYP1BG3", uuid: "4C4C4544-0059-5010-8031-C4C04F424733" },
        mainboard: { manufacturer: "Dell Inc.", model: "063MV5", serial: "/DYP1BG3/CNWSC0018M139L/", version: "A00" },
        bios_info: { vendor: "Dell Inc.", version: "1.52.0", release_date: "29/06/2026" },
        battery: { is_laptop: true, name: "DELL M033W19", level_pct: 100, wear_pct: 7.1, design_mwh: "62366 mWh", full_mwh: "57958 mWh", status_text: "Dang sac", health_text: "Pin tot" },
        ram_total: "15.7 GB",
        ram_modules: [{ locator: "Slot 1", details: "8.0 GB DDR4 @ 3200 MHz" }],
        gpus: [{ label: "GPU 1", name: "Intel Iris Xe Graphics", vram: "2.0 GB VRAM", details: "Intel Iris Xe Graphics 2.0 GB VRAM" }],
        disks: [{ label: "O 1", model: "NVMe KIOXIA 512GB", size: "512 GB", details: "KIOXIA KXG60ZNV512G 476 GB NVMe SSD" }],
        partitions: [{ drive: "C:", free_gb: 74, total_gb: 200, label: "C: 74 GB free / 200 GB" }],
        os: { caption: "Windows 11 Pro 64-bit", version: "10.0.22631", build: "Build 22631", arch: "64-bit", install_date: "2024-05-10" },
        missing_drivers: []
      };
    }

    if (!info) return;
    this.currentSpecsInfo = info;

    const isLaptop = info.battery?.is_laptop || info.system?.is_laptop || (info.system?.chassis_type === "Notebook");

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val ?? "N/A"; };

    // Model gauge
    const modelIcon = document.getElementById("hw-gauge-model-icon");
    if (modelIcon) modelIcon.innerText = isLaptop ? "?" : "?";
    set("hw-gauge-model-title", `${info.system?.manufacturer || ""} ${info.system?.model || ""}`.trim() || "N/A");
    set("hw-gauge-model-sub", info.system?.chassis_type || (isLaptop ? "Notebook" : "Desktop PC"));

    // CPU gauge (% updated by real-time)
    const cpuShortName = (info.cpu?.name || "N/A").split("@")[0].trim();
    set("hw-gauge-cpu-name", cpuShortName);
    set("hw-gauge-cpu-clock", info.cpu?.max_clock || "N/A");

    // RAM gauge (% updated by real-time)
    set("hw-gauge-ram-total", info.ram_total || "N/A");
    set("hw-gauge-ram-detail", info.ram_total || "N/A");

    // GPU gauge (static)
    const firstGpu = info.gpus?.[0];
    set("hw-gauge-gpu-name", firstGpu?.name || firstGpu?.label || "N/A");
    set("hw-gauge-gpu-vram", firstGpu?.vram || "N/A");
    set("hw-gauge-gpu-pct", firstGpu?.vram || "N/A");

    // Network / Disk gauges (updated by real-time)
    set("hw-gauge-net-name", "Ethernet / Wi-Fi");

    // Box 1: May tinh & Pin
    set("hw-sys-type", info.system?.chassis_type || (isLaptop ? "Notebook" : "Desktop"));
    set("hw-sys-vendor", info.system?.manufacturer || info.system?.vendor || "N/A");
    set("hw-comp-name", info.system?.computer_name || "N/A");
    set("hw-sys-model", info.system?.model || "N/A");
    set("hw-sys-family", info.system?.system_family || "N/A");

    const batPresentEl = document.getElementById("hw-bat-present");
    if (batPresentEl) {
      batPresentEl.innerText = isLaptop ? "🔋 Có pin (Laptop)" : "🖥️ Không có pin (Desktop PC)";
      batPresentEl.style.color = isLaptop ? "#22c55e" : "var(--text-muted)";
    }

    // Battery section visibility
    const batSection = document.getElementById("hw-bat-section");
    if (batSection) batSection.style.display = isLaptop ? "" : "none";

    if (isLaptop) {
      const bat = info.battery || {};
      const batLevel = bat.level_pct ?? 0;
      set("hw-bat-name", bat.name || "Standard Battery");
      set("hw-bat-level", `${batLevel}%`);
      const batBar = document.getElementById("hw-bat-bar");
      if (batBar) {
        batBar.style.width = `${batLevel}%`;
        batBar.style.background = bat.is_ac ? "#38bdf8" : (batLevel < 20 ? "#ef4444" : batLevel < 40 ? "#f59e0b" : "#22c55e");
      }
      // Health bar
      const healthPct = bat.health_pct ?? (bat.wear_pct !== undefined ? Math.max(0, 100 - bat.wear_pct) : 0);
      const healthBarEl = document.getElementById("hw-bat-health-bar");
      if (healthBarEl) {
        healthBarEl.style.width = `${healthPct}%`;
        healthBarEl.style.background = healthPct > 80 ? "#22c55e" : healthPct > 60 ? "#f59e0b" : "#ef4444";
      }
      // Wear + health
      const wearPct = bat.wear_pct ?? 0;
      set("hw-bat-wear", wearPct > 0 ? `${wearPct}%` : "0%");
      const healthEl = document.getElementById("hw-bat-health");
      if (healthEl) {
        healthEl.textContent = bat.health_text || "✓ Hoạt động tốt";
        healthEl.style.color = wearPct < 15 ? "#22c55e" : wearPct < 35 ? "#f59e0b" : "#ef4444";
      }
      // Capacities
      set("hw-bat-design", bat.design_mwh || "N/A");
      set("hw-bat-full", bat.full_mwh || "N/A");
      set("hw-bat-remaining", bat.remaining_mwh || "N/A");
      // Extra details
      set("hw-bat-cycles", bat.cycle_text || "N/A");
      set("hw-bat-voltage", bat.voltage_v || "N/A");
      set("hw-bat-chemistry", bat.chemistry || "N/A");
      set("hw-bat-mfg", bat.manufacturer || "N/A");
      set("hw-bat-serial", bat.serial_number || "N/A");
      // New realtime fields
      set("hw-bat-discharge-rate", bat.discharge_rate || "N/A");
      set("hw-bat-charge-rate", bat.charge_rate || "N/A");
      set("hw-bat-time-remaining", bat.time_remaining || "N/A");
      set("hw-bat-power-source", bat.power_source || (bat.is_ac ? "Nguồn AC" : "Nguồn Pin"));
      // Status + pulse
      set("hw-bat-status", bat.status_text || "N/A");
      set("hw-bat-updated", bat.last_updated || "—");
      const pulseEl = document.getElementById("hw-bat-pulse");
      if (pulseEl) {
        pulseEl.style.display = "block";
        pulseEl.style.background = bat.is_ac ? "#38bdf8" : "#22c55e";
      }
    }

    // Box 2: Service Tag
    set("hw-stag-serial", info.service_tag?.serial || "N/A");
    set("hw-stag-tag", info.service_tag?.service_tag || "N/A");
    set("hw-stag-product", info.service_tag?.product_id || "N/A");
    set("hw-stag-uuid", info.service_tag?.uuid || "N/A");

    // Box 3: Mainboard
    set("hw-mb-vendor", info.mainboard?.manufacturer || "N/A");
    set("hw-mb-model", info.mainboard?.model || "N/A");
    set("hw-mb-serial", info.mainboard?.serial || "N/A");
    set("hw-mb-version", info.mainboard?.version || "N/A");

    // Box 4: BIOS
    set("hw-bios-vendor", info.bios_info?.vendor || "N/A");
    set("hw-bios-ver", info.bios_info?.version || "N/A");
    set("hw-bios-date", info.bios_info?.release_date || "N/A");

    // Detail: CPU
    set("hw-cpu-name", info.cpu?.name || "N/A");
    set("hw-cpu-cores", info.cpu?.cores_threads || "N/A");
    set("hw-cpu-clock", info.cpu?.max_clock || "N/A");
    set("hw-cpu-cache", info.cpu?.cache || "N/A");
    set("hw-ram-total", info.ram_total || "N/A");

    // RAM modules
    const ramContainer = document.getElementById("hw-ram-sticks-list");
    if (ramContainer) {
      if (info.ram_modules && info.ram_modules.length > 0) {
        ramContainer.innerHTML = info.ram_modules.map(m => `<div style="display:flex;gap:6px;align-items:baseline;margin-bottom:3px;"><span class="hw-label">${m.locator}:</span><strong class="hw-val">${m.details || "N/A"}</strong></div>`).join("");
      } else {
        ramContainer.innerHTML = `<div class="hw-val-muted text-sm">N/A</div>`;
      }
    }

    // GPU list
    const gpuContainer = document.getElementById("hw-gpus-list");
    if (gpuContainer) {
      if (info.gpus && info.gpus.length > 0) {
        gpuContainer.innerHTML = info.gpus.map(g => `<div style="display:flex;gap:6px;align-items:baseline;margin-bottom:3px;"><span class="hw-label">${g.label}:</span><strong class="hw-val">${g.details || "N/A"}</strong></div>`).join("");
      } else {
        gpuContainer.innerHTML = `<div class="hw-val-muted text-sm">N/A</div>`;
      }
    }

    // Disk + Partition list
    const diskContainer = document.getElementById("hw-disks-list");
    if (diskContainer) {
      let diskHtml = (info.disks || []).map(d => `<div style="display:flex;gap:6px;align-items:baseline;margin-bottom:3px;"><span class="hw-label">${d.label}:</span><strong class="hw-val">${d.details || "N/A"}</strong></div>`).join("");
      if (info.partitions && info.partitions.length > 0) {
        diskHtml += `<div style="margin-top:6px;display:flex;gap:6px;flex-wrap:wrap;">` + info.partitions.map(p => `<span class="badge badge-location-subtle">💽 ${p.label}</span>`).join("") + `</div>`;
      }
      diskContainer.innerHTML = diskHtml || `<div class="hw-val-muted text-sm">N/A</div>`;
    }

    // OS
    set("hw-os-caption", info.os?.caption || "N/A");
    set("hw-os-details", `${info.os?.build ? "Build " + info.os.build : ""} ${info.os?.install_date ? "· Cài: " + info.os.install_date : ""}`.trim() || "N/A");

    this.addLog("success", "Da cap nhat thong tin phan cung thanh cong!");

    // Start real-time monitoring
    this.startRealtimeMonitoring();
  },


  // ── REAL-TIME PERFORMANCE MONITOR ────────────────────────────────────────
  startRealtimeMonitoring() {
    // Always stop existing timer first (allow restart on re-enter tab)
    this.stopRealtimeMonitoring();

    const pollStats = async () => {
      // Check if still on computer-info tab via app's own tracking
      const activeId = (window.app && window.app.currentActiveTabId) ? window.app.currentActiveTabId : this.currentActiveTabId;
      if (activeId && activeId !== "tab-computer-info") return;

      // Wait for pywebview to be ready
      if (!window.pywebview || !window.pywebview.api || typeof window.pywebview.api.get_realtime_stats !== "function") return;

      try {
        const s = await window.pywebview.api.get_realtime_stats();
        if (!s || !s.success) return;

        const setEl = (id, val) => {
          const el = document.getElementById(id);
          if (el && val !== undefined && val !== null) el.innerText = String(val);
        };
        const setBar = (id, pct, color) => {
          const el = document.getElementById(id);
          if (el) {
            el.style.width = `${Math.min(100, Math.max(0, pct || 0))}%`;
            if (color) el.style.background = color;
          }
        };

        // ── CPU ──────────────────────────────────────────────────────────
        const cpuPct = s.cpu_pct ?? 0;
        setEl("hw-gauge-cpu-pct", `${cpuPct}%`);
        const cpuColor = cpuPct > 80 ? "#ef4444" : cpuPct > 50 ? "#f59e0b" : "#3b82f6";
        setBar("hw-gauge-cpu-bar", cpuPct, cpuColor);

        // ── RAM ──────────────────────────────────────────────────────────
        const ramPct = s.ram_pct ?? 0;
        setEl("hw-gauge-ram-pct", `${ramPct}%`);
        if (s.ram_used && s.ram_total) setEl("hw-gauge-ram-detail", `${s.ram_used} / ${s.ram_total}`);
        const ramColor = ramPct > 85 ? "#ef4444" : ramPct > 60 ? "#f59e0b" : "#06b6d4";
        setBar("hw-gauge-ram-bar", ramPct, ramColor);

        // ── Network ──────────────────────────────────────────────────────
        const netTotal = (s.net_rx_kb || 0) + (s.net_tx_kb || 0);
        const netBarPct = Math.min(100, netTotal / 10240 * 100);
        setEl("hw-gauge-net-pct", s.net_rx || "0 KB/s");
        setEl("hw-gauge-net-speed", (s.net_rx && s.net_tx) ? `↓ ${s.net_rx}  ↑ ${s.net_tx}` : "0 KB/s");
        setBar("hw-gauge-net-bar", Math.max(2, netBarPct), null);

        // ── Disk I/O ─────────────────────────────────────────────────────
        const diskTotal = (s.disk_read_kb || 0) + (s.disk_write_kb || 0);
        const diskBarPct = Math.min(100, diskTotal / 51200 * 100);
        setEl("hw-gauge-disk-pct", (s.disk_read && s.disk_write) ? `R:${s.disk_read} W:${s.disk_write}` : "0 KB/s");
        if (s.partitions_usage && s.partitions_usage.length > 0) {
          setEl("hw-gauge-disk-summary", s.partitions_usage.map(p => `${p.drive} ${p.free_gb}G`).join(" · "));
        }
        setBar("hw-gauge-disk-bar", Math.max(2, diskBarPct), null);

        // ── Battery Real-time ─────────────────────────────────────────────
        const bat = s.battery;
        if (!bat) return;

        const isLaptopBat = !!(bat.is_laptop || bat.has_battery);

        // Show/hide battery section
        const batSection = document.getElementById("hw-bat-section");
        if (batSection) batSection.style.display = isLaptopBat ? "" : "none";

        // Battery presence indicator
        const batPresentEl = document.getElementById("hw-bat-present");
        if (batPresentEl) {
          batPresentEl.innerText = isLaptopBat ? "🔋 Có pin (Laptop)" : "🖥️ Không có pin (Desktop PC)";
          batPresentEl.style.color = isLaptopBat ? "#22c55e" : "var(--text-muted)";
        }

        if (!isLaptopBat) return;

        // Level + main bar
        const bLevel = bat.level_pct ?? 0;
        setEl("hw-bat-level", `${bLevel}%`);
        const batBarEl = document.getElementById("hw-bat-bar");
        if (batBarEl) {
          batBarEl.style.width = `${bLevel}%`;
          batBarEl.style.background = bat.is_ac
            ? "#38bdf8"
            : (bLevel < 20 ? "#ef4444" : bLevel < 40 ? "#f59e0b" : "#22c55e");
        }

        // Health bar
        const healthPct = bat.health_pct ?? (bat.wear_pct !== undefined ? Math.max(0, 100 - bat.wear_pct) : 0);
        const healthBarEl = document.getElementById("hw-bat-health-bar");
        if (healthBarEl) {
          healthBarEl.style.width = `${healthPct}%`;
          healthBarEl.style.background = healthPct > 80 ? "#22c55e" : healthPct > 60 ? "#f59e0b" : "#ef4444";
        }

        // Health text
        const healthEl = document.getElementById("hw-bat-health");
        if (healthEl) {
          const wearPct = bat.wear_pct ?? 0;
          healthEl.textContent = bat.health_text || "✓ Hoạt động tốt";
          healthEl.style.color = wearPct < 15 ? "#22c55e" : wearPct < 35 ? "#f59e0b" : "#ef4444";
        }

        // All detail fields — always update (don't skip N/A for dynamic values)
        setEl("hw-bat-name",           bat.name           || "Standard Battery");
        setEl("hw-bat-status",         bat.status_text    || "N/A");
        setEl("hw-bat-wear",           bat.wear_pct !== undefined ? `${bat.wear_pct}%` : "N/A");
        setEl("hw-bat-cycles",         bat.cycle_text     || "N/A");
        setEl("hw-bat-design",         bat.design_mwh     || "N/A");
        setEl("hw-bat-full",           bat.full_mwh       || "N/A");
        setEl("hw-bat-remaining",      bat.remaining_mwh  || "N/A");
        setEl("hw-bat-voltage",        bat.voltage_v      || "N/A");
        setEl("hw-bat-chemistry",      bat.chemistry      || "N/A");
        setEl("hw-bat-mfg",            bat.manufacturer   || "N/A");
        setEl("hw-bat-serial",         bat.serial_number  || "N/A");
        setEl("hw-bat-discharge-rate", bat.discharge_rate || "N/A");
        setEl("hw-bat-charge-rate",    bat.charge_rate    || "N/A");
        setEl("hw-bat-time-remaining", bat.time_remaining || "N/A");
        setEl("hw-bat-power-source",   bat.power_source   || (bat.is_ac ? "Nguồn AC" : "Nguồn Pin"));
        setEl("hw-bat-updated",        bat.last_updated   || new Date().toLocaleTimeString("vi-VN"));

        // Pulse indicator
        const pulseEl = document.getElementById("hw-bat-pulse");
        if (pulseEl) {
          pulseEl.style.display = "block";
          pulseEl.style.background = bat.is_ac ? "#38bdf8" : "#22c55e";
        }

      } catch (err) {
        console.warn("[ComputerInfo] Realtime poll error:", err);
      }
    };

    // Run immediately then every 2s
    pollStats();
    this._realtimeTimer = setInterval(pollStats, 2000);
  },

  stopRealtimeMonitoring() {
    if (this._realtimeTimer) {
      clearInterval(this._realtimeTimer);
      this._realtimeTimer = null;
    }
  },

  copyComputerSpecs() {
    if (!this.currentSpecsInfo) { alert("Chua co thong tin phan cung. Vui long bam Quet lai!"); return; }
    const info = this.currentSpecsInfo;
    const text = [
      "========================================",
      "       THONG TIN CAU HINH MAY TINH",
      "========================================",
      `? May tinh    : ${info.system?.manufacturer || ""} ${info.system?.model || ""} (${info.system?.chassis_type || "PC"})`,
      `? Ten may     : ${info.system?.computer_name || "-"}`,
      `? Service Tag : ${info.service_tag?.service_tag || "-"}`,
      `? CPU         : ${info.cpu?.name || "-"} (${info.cpu?.cores_threads || ""})`,
      `? RAM         : ${info.ram_total || "-"}`,
      `? Card Do Hoa : ${info.gpus?.map(g => g.details).join(" | ") || "-"}`,
      `? Bo mach chu : ${info.mainboard?.manufacturer || ""} ${info.mainboard?.model || ""}`,
      `? BIOS / UEFI : ${info.bios_info?.vendor || ""} ${info.bios_info?.version || ""} (${info.bios_info?.release_date || ""})`,
      `? O Cung      : ${info.disks?.map(d => d.details).join(" | ") || "-"}`,
      `? Phan vung   : ${info.partitions?.map(p => p.label).join(" | ") || "-"}`,
      `? Pin Laptop  : ${info.battery?.is_laptop ? `${info.battery.level_pct}% (${info.battery.health_text}, Chai ${info.battery.wear_pct}%)` : "Khong co pin (Desktop PC)"}`,
      `? He Dieu Hanh: ${info.os?.caption || "-"} (${info.os?.build || ""})`,
      "========================================"
    ].join("\n");

    navigator.clipboard.writeText(text).then(() => {
      this.addLog("success", "Da sao chep cau hinh may tinh vao Clipboard!");
      alert("?? Da sao chep cau hinh may tinh vao Clipboard!");
    }).catch(err => { alert("Noi dung cau hinh:\n\n" + text); });
  },

  async exportSpecsFile(formatType) {
    this.addLog("info", `Dang xuat bao cao cau hinh dang ${formatType.toUpperCase()}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.export_specs_file(formatType, this.currentSpecsInfo);
      if (res.success) { this.addLog("success", res.message); alert(res.message); }
      else { this.addLog("error", res.message); alert("Loi xuat file: " + res.message); }
    } else {
      alert(`[Demo] Da xuat file ${formatType.toUpperCase()} ra Desktop!`);
    }
  },

  async openVendorDriverSite() {
    const vendor = this.currentSpecsInfo?.system?.manufacturer || this.currentSpecsInfo?.system?.vendor || "";
    const serviceTag = this.currentSpecsInfo?.service_tag?.service_tag || "";
    this.addLog("info", `Đang mở trang Driver của hãng ${vendor}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.open_vendor_driver_site(vendor, serviceTag);
      this.addLog(res.success ? "success" : "info", res.message);
    } else {
      window.open("https://www.google.com/search?q=" + encodeURIComponent(`driver download ${vendor}`), "_blank");
    }
  },

  async openDeviceManager() {
    this.addLog("info", "Đang mở Trình quản lý thiết bị Device Manager (devmgmt.msc)...");
    if (window.pywebview && window.pywebview.api && window.pywebview.api.open_device_manager) {
      const res = await window.pywebview.api.open_device_manager();
      this.addLog(res.success ? "success" : "error", res.message);
    } else {
      alert("[MOCK] Đã mở Trình quản lý thiết bị (devmgmt.msc)!");
    }
  },

  closeDriverCheckModal() {
    const modalEl = document.getElementById("driver-check-modal");
    if (modalEl) modalEl.style.display = "none";
  },

  async checkMissingDrivers(forceScan = true) {
    const modalEl = document.getElementById("driver-check-modal");
    const modalBody = document.getElementById("driver-check-modal-body");

    if (modalBody && modalEl) {
      modalBody.innerHTML = `
        <div style="text-align: center; padding: 30px 15px;">
          <span class="spinner-border spinner-border-lg text-primary" style="width: 32px; height: 32px; margin-bottom: 12px;"></span>
          <div style="font-weight: 700; color: #1e293b; font-size: 14px;">Đang quét toàn bộ thiết bị & Driver thời gian thực...</div>
          <div style="font-size: 12px; color: #64748b; margin-top: 4px;">Kiểm tra mã trạng thái phần cứng chuẩn Device Manager...</div>
        </div>
      `;
      modalEl.style.display = "flex";
    }

    let missing = [];

    if (window.pywebview && window.pywebview.api && window.pywebview.api.check_missing_drivers) {
      try {
        const res = await window.pywebview.api.check_missing_drivers();
        if (res && res.success) {
          missing = res.missing_drivers || [];
          if (this.currentSpecsInfo) {
            this.currentSpecsInfo.missing_drivers = missing;
          }
        }
      } catch (err) {
        console.error("Lỗi quét driver:", err);
      }
    } else {
      missing = this.currentSpecsInfo?.missing_drivers || [];
    }

    if (!modalBody || !modalEl) return;

    if (missing.length === 0) {
      this.addLog("success", "Kiểm tra Driver: 100% thiết bị phần cứng đều có Driver đầy đủ và hoạt động tốt.");
      modalBody.innerHTML = `
        <div style="text-align: center; padding: 14px 10px;">
          <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
          <h4 style="font-size: 16px; font-weight: 700; color: #10b981; margin-bottom: 8px;">
            Tất Cả Thiết Bị Đều Hoạt Động Hoàn Hảo!
          </h4>
          <p style="font-size: 13px; color: #475569; line-height: 1.6; max-width: 470px; margin: 0 auto 18px auto;">
            Hệ thống đã đối soát trực tiếp theo thời gian thực: <strong>100% phần cứng hiện tại</strong> đều đã được cài đặt Driver đầy đủ, không có xung đột, không có chấm than vàng hay lỗi mã nào (Khớp hoàn toàn với Device Manager).
          </p>
          <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 8px; padding: 10px 14px; margin-bottom: 18px; font-size: 12px; color: #047857; text-align: left;">
            ✓ <strong>Trạng thái:</strong> Khỏe mạnh (0 thiết bị cảnh báo)<br>
            ✓ <strong>Mã lỗi loại trừ:</strong> Đã bỏ qua các thiết bị ngoại vi đã rút (Phantom USB/Bluetooth) và thiết bị tự tắt.
          </div>
          <div style="display: flex; gap: 8px; justify-content: center; flex-wrap: wrap;">
            <button class="btn btn-primary-solid btn-sm" onclick="app.openDeviceManager()">
              ⚙️ Mở Device Manager (devmgmt.msc)
            </button>
            <button class="btn btn-slate-light btn-sm" onclick="app.checkMissingDrivers(true)">
              🔄 Quét lại
            </button>
            <button class="btn btn-slate-light btn-sm" onclick="app.closeDriverCheckModal()">
              Đóng
            </button>
          </div>
        </div>
      `;
    } else {
      this.addLog("warn", `Phát hiện ${missing.length} driver bị lỗi hoặc thiếu.`);
      modalBody.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 12px;">
          <div style="background: rgba(239, 68, 68, 0.08); border-left: 4px solid #ef4444; border-radius: 6px; padding: 10px 14px;">
            <div style="font-weight: 700; color: #dc2626; font-size: 14px; display: flex; align-items: center; gap: 6px;">
              <span>⚠️</span> Phát hiện ${missing.length} thiết bị chưa cài hoặc bị lỗi Driver:
            </div>
            <div style="font-size: 12px; color: #64748b; margin-top: 3px;">
              Dưới đây là danh sách thiết bị gặp sự cố được ghi nhận trực tiếp từ Device Manager:
            </div>
          </div>

          <div style="max-height: 280px; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px;">
            ${missing.map((d, i) => `
              <div style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; background: ${i % 2 === 0 ? '#fafafa' : '#fff'};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
                  <div>
                    <strong style="color: #1e293b; font-size: 13px;">${i + 1}. ${d.name}</strong>
                    <span class="badge" style="background: #f1f5f9; color: #64748b; font-size: 10.5px; margin-left: 6px; padding: 2px 6px; border-radius: 4px;">${d.class || 'Phần cứng'}</span>
                  </div>
                  <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #ef4444; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; white-space: nowrap;">
                    ${d.error_desc || 'Lỗi Driver'}
                  </span>
                </div>
                <div style="font-family: monospace; font-size: 10.5px; color: #64748b; margin-top: 5px; word-break: break-all;">
                  ID: ${d.instance}
                </div>
              </div>
            `).join('')}
          </div>

          <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 6px; border-top: 1px solid #f1f5f9; padding-top: 12px;">
            <button class="btn btn-primary-solid btn-sm" onclick="app.openDeviceManager()">
              ⚙️ Mở Device Manager để cập nhật
            </button>
            <button class="btn btn-gold-light btn-sm" onclick="app.openVendorDriverSite()">
              🔗 Tìm Driver Hãng
            </button>
            <button class="btn btn-slate-light btn-sm" onclick="app.closeDriverCheckModal()">
              Đóng
            </button>
          </div>
        </div>
      `;
    }
  },

  async runModule(moduleName, action) {
    this.addLog("info", `Dang chay module ${moduleName} (${action})...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.run_tool_module(moduleName, action);
      this.addLog(res.success ? "success" : "error", res.message);
    }
  }
});