/** @odoo-module */
import { registry } from "@web/core/registry";
import { GuruKpiCard } from "./kpi_card/kpi_card";
import { GuruChartRenderer } from "./chart_renderer/chart_renderer";
import { EkskulList, GuruList } from "./card_list/card_list";
import { useState, Component, onMounted, onWillUnmount } from "@odoo/owl";

class OwlGuruDashboard extends Component {
  setup() {
    this.state = useState({
      selectedDateRange: null,
      tempDateRange: { start: "", end: "" },
      showDatePicker: false,
      selectedPeriod: "thisMonth",
      isLoading: false,
    });
    console.log("Initial state:", this.state);

    // Event handler untuk klik di luar
    this._handleClickOutside = (ev) => {
      const popup = document.querySelector(".popup-container");
      const button = document.querySelector(".dateButton");

      if (
        popup &&
        !popup.contains(ev.target) &&
        button &&
        !button.contains(ev.target)
      ) {
        this.state.showDatePicker = false;
      }
    };

    onMounted(() => {
      document.addEventListener("click", this._handleClickOutside);
      this.setPeriod(this.state.selectedPeriod);
    });

    onWillUnmount(() => {
      document.removeEventListener("click", this._handleClickOutside);
    });
  }

  toggleDatePicker() {
    this.state.showDatePicker = !this.state.showDatePicker;
    if (this.state.showDatePicker && this.state.selectedDateRange) {
      this.state.tempDateRange = {
        start: this.state.selectedDateRange.start,
        end: this.state.selectedDateRange.end,
      };
    }
    console.log("Toggled date picker, showDatePicker:", this.state.showDatePicker);
  }

  closeDatePicker() {
    this.state.showDatePicker = false;
    console.log("Closed date picker");
  }

  async applyDateRange() {
    if (this.state.tempDateRange.start && this.state.tempDateRange.end) {
      const start = new Date(this.state.tempDateRange.start);
      const end = new Date(this.state.tempDateRange.end);
      console.log("Applying date range:", { start, end });

      // Validate dates
      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        alert("Tanggal tidak valid!");
        return;
      }
      if (start > end) {
        alert("Tanggal mulai tidak boleh lebih besar dari tanggal akhir!");
        return;
      }
      // Warn if start date is in a previous year
      const currentYear = new Date().getFullYear();
      if (start.getFullYear() < currentYear) {
        if (!confirm("Tanggal mulai berada di tahun sebelumnya. Lanjutkan?")) {
          return;
        }
      }

      this.state.selectedDateRange = {
        start: this.state.tempDateRange.start,
        end: this.state.tempDateRange.end,
      };
      this.state.selectedPeriod = "custom";
      this.closeDatePicker();
      console.log("Custom date range applied:", this.state.selectedDateRange);
    } else {
      alert("Harap pilih tanggal mulai dan akhir!");
    }
  }

  formatDate(dateString) {
    if (!dateString) return "";
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "";
    const months = [
      "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
      "Jul", "Ags", "Sep", "Okt", "Nov", "Des",
    ];
    const day = String(date.getDate()).padStart(2, "0");
    const month = months[date.getMonth()];
    const year = date.getFullYear();
    return `${day} ${month} ${year}`;
  }

  formatDateRange(start, end) {
    if (!start || !end) return "";
    if (start === end) {
      return this.formatDate(start);
    }
    return `${this.formatDate(start)} - ${this.formatDate(end)}`;
  }

  getPeriodLabel(period) {
    const labels = {
      today: "Hari Ini",
      yesterday: "Kemarin",
      thisWeek: "Minggu Ini",
      lastWeek: "Minggu Lalu",
      thisMonth: "Bulan Ini",
      lastMonth: "Bulan Lalu",
      thisYear: "Tahun Ini",
      lastYear: "Tahun Lalu",
      custom: "Pilih Periode",
      all: "Semua Data",
    };
    return labels[period] || "Pilih Periode";
  }

  isPeriodSelected(period) {
    return this.state.selectedPeriod === period;
  }

  getLocalDateString(date) {
    if (!date || isNaN(date.getTime())) {
      console.error("Invalid date in getLocalDateString:", date);
      return "";
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  setPeriod(period) {
    console.log("setPeriod called with period:", period);
    if (period === "all") {
      this.state.selectedDateRange = null;
      this.state.selectedPeriod = "all";
      console.log("Set period to 'all', selectedDateRange:", this.state.selectedDateRange);
      return;
    }

    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    let start, end;

    switch (period) {
      case "today":
        start = todayStart;
        end = todayStart;
        break;
      case "yesterday":
        start = new Date(todayStart);
        start.setDate(todayStart.getDate() - 1);
        end = start;
        break;
      case "thisWeek":
        start = new Date(todayStart);
        start.setDate(todayStart.getDate() - todayStart.getDay());
        end = new Date(start);
        end.setDate(start.getDate() + 6);
        break;
      case "lastWeek":
        start = new Date(todayStart);
        start.setDate(todayStart.getDate() - todayStart.getDay() - 7);
        end = new Date(start);
        end.setDate(start.getDate() + 6);
        break;
      case "thisMonth":
        start = new Date(todayStart.getFullYear(), todayStart.getMonth(), 1);
        end = new Date(todayStart.getFullYear(), todayStart.getMonth() + 1, 0);
        break;
      case "lastMonth":
        start = new Date(todayStart.getFullYear(), todayStart.getMonth() - 1, 1);
        end = new Date(todayStart.getFullYear(), todayStart.getMonth(), 0);
        break;
      case "thisYear":
        start = new Date(todayStart.getFullYear(), 0, 1);
        end = new Date(todayStart.getFullYear(), 11, 31);
        break;
      case "lastYear":
        start = new Date(todayStart.getFullYear() - 1, 0, 1);
        end = new Date(todayStart.getFullYear() - 1, 11, 31);
        break;
      default:
        console.warn("Unknown period, defaulting to thisMonth:", period);
        start = new Date(todayStart.getFullYear(), todayStart.getMonth(), 1);
        end = new Date(todayStart.getFullYear(), todayStart.getMonth() + 1, 0);
        period = "thisMonth";
    }

    this.state.selectedPeriod = period;
    this.state.selectedDateRange = {
      start: this.getLocalDateString(start),
      end: this.getLocalDateString(end),
    };

    if (!this.state.selectedDateRange.start || !this.state.selectedDateRange.end) {
      console.error("Failed to set date range, resetting to thisMonth");
      start = new Date(todayStart.getFullYear(), todayStart.getMonth(), 1);
      end = new Date(todayStart.getFullYear(), todayStart.getMonth() + 1, 0);
      this.state.selectedDateRange = {
        start: this.getLocalDateString(start),
        end: this.getLocalDateString(end),
      };
      this.state.selectedPeriod = "thisMonth";
    }

    console.log("Period set:", {
      period: this.state.selectedPeriod,
      startDate: this.state.selectedDateRange.start,
      endDate: this.state.selectedDateRange.end,
      rawStart: start,
      rawEnd: end,
    });
  }

  get dateRangeProps() {
    console.log("Getting dateRangeProps:", this.state.selectedDateRange);
    if (!this.state.selectedDateRange) {
      return { startDate: "", endDate: "" };
    }
    return {
      startDate: this.state.selectedDateRange.start,
      endDate: this.state.selectedDateRange.end,
    };
  }
}

OwlGuruDashboard.template = "owl.OwlGuruDashboard";
OwlGuruDashboard.components = {
  GuruKpiCard,
  GuruChartRenderer,
  GuruList,
  EkskulList,
};

registry.category("actions").add("owl.guru_dashboard", OwlGuruDashboard);