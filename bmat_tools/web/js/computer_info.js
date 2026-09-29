/**
 * IT-Tools 2026 - Computer Hardware Info & Diagnostics Module
 */
Object.assign(AppController.prototype, {
  async loadComputerInfo() {
    this.addLog("info", "Đang quét thông tin cấu hình phần cứng hệ thống...");
    
    if (!this.hwClockTimer) {
      this.hwClockTimer = setInterval(() => {
        const clkEl = document.getElementById("hw-system-clock");
        if (clkEl) clkEl.innerText = new Date().toLocaleTimeString('vi-VN');
      }, 1000);
    }
    const clkEl = document.getElementById("hw-system-clock");
    if (clkEl) clkEl.innerText = new Date().toLocaleTimeString('vi-VN');

    let info = null;
    if (window.pywebview && window.pywebview.api) {
      info = await window.pywebview.api.get_computer_info();
    } else {
      info = {
        success: true,
        cpu: {
          name: "Intel Core i5-1135G7 @ 2.40GHz",
          cores_threads: "4 nhân · 8 luồng",
          max_clock: "2.40 GHz",
          cache: "8 MB Cache"
        },
        system: {
          vendor: "Dell Inc.",
          manufacturer: "Dell Inc.",
          model: "Latitude 5520",
          computer_name: "DESKTOP-5VAK9DN",
          system_family: "Latitude",
          chassis_type: "Notebook",
          is_laptop: true
        },
        service_tag: {
          serial: "DYP1BG3",
          service_tag: "DYP1BG3",
          product_id: "DYP1BG3",
          uuid: "4C4C4544-0059-5010-8031-C4C04F424733"
        },
        mainboard: {
          manufacturer: "Dell Inc.",
          model: "063MV5",
          serial: "/DYP1BG3/CNWSC0018M139L/",
          version: "A00"
        },
        bios_info: {
          vendor: "Dell Inc.",
          version: "1.52.0",
          release_date: "29/06/2026"
        },
        battery: {
          is_laptop: true,
          name: "DELL M033W19",
          level_pct: 100,
          wear_pct: 7.1,
          design_mwh: "62366 mWh",
          full_mwh: "57958 mWh",
          status_text: "Đang sạc",
          health_text: "✓ Pin tốt"
        },
        ram_total: "15.7 GB",
        ram_modules: [
          { locator: "Slot 1", details: "8.0 GB DDR4 @ 3200 MHz · Samsung" },
          { locator: "Slot 2", details: "8.0 GB DDR4 @ 3200 MHz · SK Hynix" }
        ],
        gpus: [
          { label: "GPU 1", name: "Intel(R) Iris(R) Xe Graphics", vram: "2.0 GB VRAM", details: "Intel(R) Iris(R) Xe Graphics · 2.0 GB VRAM" }
        ],
        disks: [
          { label: "Ổ 1", model: "NVMe KIOXIA 512GB", size: "512 GB", details: "KIOXIA KXG60ZNV512G · 476 GB NVMe SSD" }
        ],
        partitions: [
          { drive: "C:", free_gb: 74, total_gb: 200, label: "C: 74 GB free / 200 GB" },
          { drive: "D:", free_gb: 118, total_gb: 250, label: "D: 118 GB free / 250 GB" }
        ],
        os: {
          caption: "Windows 11 Pro 64-bit",
          version: "10.0.22631",
          build: "Build 22631",
          arch: "64-bit",
          install_date: "2024-05-10"
        },
        missing_drivers: []
      };
    }

    if (!info) return;
    this.currentSpecsInfo = info;

    // 1. TOP GAUGES
    const isLaptop = info.battery?.is_laptop || info.system?.is_laptop || (info.system?.chassis_type === "Notebook");
    const modelIcon = document.getElementById("hw-gauge-model-icon");
    if (modelIcon) modelIcon.innerText = isLaptop ? "💻" : "🖥️";

    const modelTitle = document.getElementById("hw-gauge-model-title");
    if (modelTitle) modelTitle.innerText = `${info.system?.manufacturer || ''} ${info.system?.model || ''}`.trim() || "N/A";

    const modelSub = document.getElementById("hw-gauge-model-sub");
    if (modelSub) modelSub.innerText = info.system?.chassis_type || (isLaptop ? "Notebook" : "Desktop PC");

    // Gauge CPU
    const cpuNameStr = info.cpu?.name || "N/A";
    const cpuShortName = cpuNameStr.split('@')[0].trim();
    if (document.getElementById("hw-gauge-cpu-name")) document.getElementById("hw-gauge-cpu-name").innerText = cpuShortName;
    if (document.getElementById("hw-gauge-cpu-clock")) document.getElementById("hw-gauge-cpu-clock").innerText = info.cpu?.max_clock || "N/A";
    if (document.getElementById("hw-gauge-cpu-pct")) document.getElementById("hw-gauge-cpu-pct").innerText = "8%";

    // Gauge RAM
    if (document.getElementById("hw-gauge-ram-total")) document.getElementById("hw-gauge-ram-total").innerText = info.ram_total || "N/A";
    if (document.getElementById("hw-gauge-ram-detail")) document.getElementById("hw-gauge-ram-detail").innerText = info.ram_total || "N/A";
    if (document.getElementById("hw-gauge-ram-pct")) document.getElementById("hw-gauge-ram-pct").innerText = "41%";

    // Gauge GPU
    const firstGpu = info.gpus?.[0];
    if (document.getElementById("hw-gauge-gpu-name")) document.getElementById("hw-gauge-gpu-name").innerText = firstGpu?.name || firstGpu?.label || "N/A";
    if (document.getElementById("hw-gauge-gpu-vram")) document.getElementById("hw-gauge-gpu-vram").innerText = firstGpu?.vram || "N/A";
    if (document.getElementById("hw-gauge-gpu-pct")) document.getElementById("hw-gauge-gpu-pct").innerText = "1%";

    // Gauge Network
    if (document.getElementById("hw-gauge-net-name")) document.getElementById("hw-gauge-net-name").innerText = "Ethernet / Wi-Fi";
    if (document.getElementById("hw-gauge-net-speed")) document.getElementById("hw-gauge-net-speed").innerText = "334.3 KB/s";
    if (document.getElementById("hw-gauge-net-pct")) document.getElementById("hw-gauge-net-pct").innerText = "0%";

    // Gauge Disk
    let partitionSummary = "";
    if (info.partitions && info.partitions.length > 0) {
      partitionSummary = info.partitions.map(p => `${p.drive} ${p.free_gb}GB`).join(' | ');
    } else {
      partitionSummary = "N/A";
    }
    if (document.getElementById("hw-gauge-disk-summary")) document.getElementById("hw-gauge-disk-summary").innerText = partitionSummary;
    if (document.getElementById("hw-gauge-disk-pct")) document.getElementById("hw-gauge-disk-pct").innerText = "0%";

    // 2. BOX 1: LOẠI MÁY TÍNH & PIN
    if (document.getElementById("hw-sys-type")) document.getElementById("hw-sys-type").innerText = info.system?.chassis_type || (isLaptop ? "Notebook" : "Desktop");
    if (document.getElementById("hw-sys-vendor")) document.getElementById("hw-sys-vendor").innerText = info.system?.manufacturer || info.system?.vendor || "N/A";
    if (document.getElementById("hw-comp-name")) document.getElementById("hw-comp-name").innerText = info.system?.computer_name || "N/A";
    if (document.getElementById("hw-sys-model")) document.getElementById("hw-sys-model").innerText = info.system?.model || "N/A";
    if (document.getElementById("hw-sys-family")) document.getElementById("hw-sys-family").innerText = info.system?.system_family || "N/A";

    const batPresentEl = document.getElementById("hw-bat-present");
    if (batPresentEl) {
      batPresentEl.innerText = isLaptop ? "✓ Có pin (Laptop)" : "❌ Không có pin (Desktop PC)";
      batPresentEl.style.color = isLaptop ? "#166534" : "#94a3b8";
    }

    if (document.getElementById("hw-bat-name")) document.getElementById("hw-bat-name").innerText = info.battery?.name || "N/A";
    const batLevel = info.battery?.level_pct ?? 0;
    if (document.getElementById("hw-bat-level")) document.getElementById("hw-bat-level").innerText = info.battery?.is_laptop ? `${batLevel}%` : "N/A";
    const batBar = document.getElementById("hw-bat-bar");
    if (batBar) {
      batBar.style.width = info.battery?.is_laptop ? `${batLevel}%` : "0%";
      batBar.style.background = batLevel < 20 ? "#ef4444" : (batLevel < 50 ? "#f59e0b" : "#22c55e");
    }

    if (document.getElementById("hw-bat-wear")) document.getElementById("hw-bat-wear").innerText = info.battery?.is_laptop ? `${info.battery?.wear_pct ?? 0}%` : "N/A";
    if (document.getElementById("hw-bat-design")) document.getElementById("hw-bat-design").innerText = info.battery?.design_mwh || "N/A";
    if (document.getElementById("hw-bat-full")) document.getElementById("hw-bat-full").innerText = info.battery?.full_mwh || "N/A";
    if (document.getElementById("hw-bat-status")) document.getElementById("hw-bat-status").innerText = info.battery?.status_text || "N/A";
    if (document.getElementById("hw-bat-health")) document.getElementById("hw-bat-health").innerText = info.battery?.health_text || "N/A";

    // 3. BOX 2: SERVICE TAG / SERIAL NUMBER
    if (document.getElementById("hw-stag-serial")) document.getElementById("hw-stag-serial").innerText = info.service_tag?.serial || "N/A";
    if (document.getElementById("hw-stag-tag")) document.getElementById("hw-stag-tag").innerText = info.service_tag?.service_tag || "N/A";
    if (document.getElementById("hw-stag-product")) document.getElementById("hw-stag-product").innerText = info.service_tag?.product_id || "N/A";
    if (document.getElementById("hw-stag-uuid")) document.getElementById("hw-stag-uuid").innerText = info.service_tag?.uuid || "N/A";

    // 4. BOX 3: BO MẠCH CHỦ (MAINBOARD)
    if (document.getElementById("hw-mb-vendor")) document.getElementById("hw-mb-vendor").innerText = info.mainboard?.manufacturer || "N/A";
    if (document.getElementById("hw-mb-model")) document.getElementById("hw-mb-model").innerText = info.mainboard?.model || "N/A";
    if (document.getElementById("hw-mb-serial")) document.getElementById("hw-mb-serial").innerText = info.mainboard?.serial || "N/A";
    if (document.getElementById("hw-mb-version")) document.getElementById("hw-mb-version").innerText = info.mainboard?.version || "N/A";

    // 5. BOX 4: BIOS / UEFI
    if (document.getElementById("hw-bios-vendor")) document.getElementById("hw-bios-vendor").innerText = info.bios_info?.vendor || "N/A";
    if (document.getElementById("hw-bios-ver")) document.getElementById("hw-bios-ver").innerText = info.bios_info?.version || "N/A";
    if (document.getElementById("hw-bios-date")) document.getElementById("hw-bios-date").innerText = info.bios_info?.release_date || "N/A";

    // 6. LOWER DETAILED CARDS: CPU, RAM, GPU, DISKS, OS
    if (document.getElementById("hw-cpu-name")) document.getElementById("hw-cpu-name").innerText = info.cpu?.name || "N/A";
    if (document.getElementById("hw-cpu-cores")) document.getElementById("hw-cpu-cores").innerText = info.cpu?.cores_threads || "N/A";
    if (document.getElementById("hw-cpu-clock")) document.getElementById("hw-cpu-clock").innerText = info.cpu?.max_clock || "N/A";
    if (document.getElementById("hw-cpu-cache")) document.getElementById("hw-cpu-cache").innerText = info.cpu?.cache || "N/A";

    if (document.getElementById("hw-ram-total")) document.getElementById("hw-ram-total").innerText = info.ram_total || "N/A";
    
    // RAM modules container
    const ramContainer = document.getElementById("hw-ram-sticks-list");
    if (ramContainer) {
      if (info.ram_modules && info.ram_modules.length > 0) {
        let ramHtml = "";
        info.ram_modules.forEach(m => {
          ramHtml += `
            <div style="display: flex; gap: 6px; align-items: baseline; margin-bottom: 3px;">
              <span style="color: #64748b; font-size: 12px; font-weight: 500;">${m.locator}:</span>
              <strong style="color: #0f172a; font-weight: 600; font-size: 12px;">${m.details || 'N/A'}</strong>
            </div>
          `;
        });
        ramContainer.innerHTML = ramHtml;
      } else {
        ramContainer.innerHTML = `<div class="text-muted text-sm">N/A</div>`;
      }
    }

    // GPU container
    const gpuContainer = document.getElementById("hw-gpus-list");
    if (gpuContainer) {
      if (info.gpus && info.gpus.length > 0) {
        let gpuHtml = "";
        info.gpus.forEach(g => {
          gpuHtml += `
            <div style="display: flex; gap: 6px; align-items: baseline; margin-bottom: 3px;">
              <span style="color: #64748b; font-size: 12px; font-weight: 500;">${g.label}:</span>
              <strong style="color: #0f172a; font-weight: 600; font-size: 12px;">${g.details || 'N/A'}</strong>
            </div>
          `;
        });
        gpuContainer.innerHTML = gpuHtml;
      } else {
        gpuContainer.innerHTML = `<div class="text-muted text-sm">N/A</div>`;
      }
    }

    // Disk & Partition container
    const diskContainer = document.getElementById("hw-disks-list");
    if (diskContainer) {
      let diskHtml = "";
      if (info.disks && info.disks.length > 0) {
        info.disks.forEach(d => {
          diskHtml += `
            <div style="display: flex; gap: 6px; align-items: baseline; margin-bottom: 3px;">
              <span style="color: #64748b; font-size: 12px; font-weight: 500;">${d.label}:</span>
              <strong style="color: #0f172a; font-weight: 600; font-size: 12px;">${d.details || 'N/A'}</strong>
            </div>
          `;
        });
      }
      if (info.partitions && info.partitions.length > 0) {
        diskHtml += `<div style="margin-top: 6px; display: flex; gap: 6px; flex-wrap: wrap;">`;
        info.partitions.forEach(p => {
          diskHtml += `<span style="background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">💾 ${p.label}</span>`;
        });
        diskHtml += `</div>`;
      }
      diskContainer.innerHTML = diskHtml || `<div class="text-muted text-sm">N/A</div>`;
    }

    // OS
    if (document.getElementById("hw-os-caption")) document.getElementById("hw-os-caption").innerText = info.os?.caption || "N/A";
    if (document.getElementById("hw-os-details")) document.getElementById("hw-os-details").innerText = `${info.os?.build ? 'Build ' + info.os?.build : ''} ${info.os?.install_date ? '· Cài: ' + info.os?.install_date : ''}`.trim() || "N/A";

    this.addLog("success", "Đã cập nhật thông tin phần cứng thành công!");
  },

  copyComputerSpecs() {
    if (!this.currentSpecsInfo) {
      alert("Chưa có thông tin phần cứng. Vui lòng bấm Quét lại!");
      return;
    }
    const info = this.currentSpecsInfo;
    const text = `
========================================
       THÔNG TIN CẤU HÌNH MÁY TÍNH
========================================
• Máy tính    : ${info.system?.manufacturer || ''} ${info.system?.model || ''} (${info.system?.chassis_type || 'PC'})
• Tên máy     : ${info.system?.computer_name || '-'}
• Service Tag : ${info.service_tag?.service_tag || '-'}
• CPU         : ${info.cpu?.name || '-'} (${info.cpu?.cores_threads || ''})
• RAM         : ${info.ram_total || '-'}
• Card Đồ Họa : ${info.gpus?.map(g => g.details).join(' | ') || '-'}
• Bo mạch chủ : ${info.mainboard?.manufacturer || ''} ${info.mainboard?.model || ''}
• BIOS / UEFI : ${info.bios_info?.vendor || ''} ${info.bios_info?.version || ''} (${info.bios_info?.release_date || ''})
• Ổ Cứng      : ${info.disks?.map(d => d.details).join(' | ') || '-'}
• Phân vùng   : ${info.partitions?.map(p => p.label).join(' | ') || '-'}
• Pin Laptop  : ${info.battery?.is_laptop ? `${info.battery?.level_pct}% (${info.battery?.health_text}, Chai ${info.battery?.wear_pct}%)` : 'Không có pin (Desktop PC)'}
• Hệ Điều Hành: ${info.os?.caption || '-'} (${info.os?.build || ''})
========================================
`.trim();

    navigator.clipboard.writeText(text).then(() => {
      this.addLog("success", "Đã sao chép cấu hình máy tính vào Clipboard!");
      alert("📋 Đã sao chép cấu hình máy tính vào Clipboard!");
    }).catch(err => {
      console.error(err);
      alert("Nội dung cấu hình:\n\n" + text);
    });
  },

  async exportSpecsFile(formatType) {
    this.addLog("info", `Đang xuất báo cáo cấu hình dạng ${formatType.toUpperCase()}...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.export_specs_file(formatType, this.currentSpecsInfo);
      if (res.success) {
        this.addLog("success", res.message);
        alert(res.message);
      } else {
        this.addLog("error", res.message);
        alert("Lỗi xuất file: " + res.message);
      }
    } else {
      alert(`[Demo Web View] Đã xuất file ${formatType.toUpperCase()} báo cáo cấu hình ra Desktop!`);
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
      alert(`[Demo Web View] Mở trang tải Driver của ${vendor} (Service Tag: ${serviceTag})`);
    }
  },

  checkMissingDrivers() {
    const missing = this.currentSpecsInfo?.missing_drivers || [];
    if (missing.length === 0) {
      alert("✅ Tất cả thiết bị phần cứng đều đã được cài đặt Driver đầy đủ! Không phát hiện Driver bị thiếu hoặc lỗi.");
      this.addLog("success", "Kiểm tra Driver: Tất cả thiết bị hoạt động bình thường.");
    } else {
      let msg = `⚠️ Phát hiện ${missing.length} thiết bị chưa cài hoặc bị lỗi Driver:\n\n`;
      missing.forEach((d, i) => {
        msg += `${i + 1}. ${d.name} (${d.class})\n   ID: ${d.instance}\n\n`;
      });
      alert(msg);
      this.addLog("warn", `Phát hiện ${missing.length} driver thiếu/lỗi.`);
    }
  },

  async runModule(moduleName, action) {
    this.addLog("info", `Đang chạy module ${moduleName} (${action})...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.run_tool_module(moduleName, action);
      this.addLog(res.success ? "success" : "error", res.message);
    }
  }
});
