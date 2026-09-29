/**
 * IT-Tools 2026 - Date & Time Config Module
 */
Object.assign(AppController.prototype, {
  async loadDateTimeInfo() {
    this.addLog("info", "Đang kiểm tra trạng thái Date & Time hệ thống...");
    if (window.pywebview && window.pywebview.api) {
      const info = await window.pywebview.api.get_datetime_info();
      if (info && info.success) {
        if (document.getElementById("dt-live-clock")) document.getElementById("dt-live-clock").innerText = info.current_time;
        if (document.getElementById("dt-live-date")) document.getElementById("dt-live-date").innerText = `${info.day_of_week}, ${info.current_date}`;
        if (document.getElementById("dt-current-tz")) document.getElementById("dt-current-tz").innerText = info.timezone;
        if (document.getElementById("dt-short-format")) document.getElementById("dt-short-format").innerText = info.short_date_format;
        this.addLog("success", `Trạng thái: ${info.timezone} (${info.current_date})`);
      }
    } else {
      const now = new Date();
      if (document.getElementById("dt-live-clock")) document.getElementById("dt-live-clock").innerText = now.toLocaleTimeString('vi-VN');
      if (document.getElementById("dt-live-date")) document.getElementById("dt-live-date").innerText = now.toLocaleDateString('vi-VN');
      if (document.getElementById("dt-current-tz")) document.getElementById("dt-current-tz").innerText = "SE Asia Standard Time (UTC+7)";
      if (document.getElementById("dt-short-format")) document.getElementById("dt-short-format").innerText = "dd/MM/yyyy";
    }
  },

  async configureDateTime(action) {
    this.addLog("info", `Đang thực hiện cấu hình Date & Time (${action})...`);
    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.configure_datetime(action);
      if (res && res.success) {
        this.addLog("success", res.message);
        alert(res.message);
        this.loadDateTimeInfo();
      } else {
        this.addLog("error", res ? res.message : "Lỗi cấu hình Date Time!");
        alert("Lỗi: " + (res ? res.message : "Lỗi cấu hình Date Time!"));
      }
    } else {
      alert(`[Demo Web View] Đã thực hiện thao tác Date Time: ${action}`);
    }
  }
});
