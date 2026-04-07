/** @odoo-module */
import { registry } from "@web/core/registry";
import { GuruquranKpiCard } from "./kpi_card/kpi_card";
import { GuruquranChartRenderer } from "./chart_renderer/chart_renderer";
import {
  GuruquranTahsinCardList,
  GuruquranTahfidzCardList,
} from "./card_list/card_list";
import { Component, useState } from "@odoo/owl";

export class OwlGuruquranDashboard extends Component {
  setup() {
    // Initialize dates
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);

    // Ensure dates are valid before initializing state
    if (!isNaN(startOfMonth.getTime()) && !isNaN(endOfMonth.getTime())) {
      this.state = useState({
        selectedDateRange: {
          start: this.getLocalDateString(startOfMonth),
          end: this.getLocalDateString(endOfMonth),
        },
        tempDateRange: {
          start: this.getLocalDateString(startOfMonth),
          end: this.getLocalDateString(endOfMonth),
        },
        showDatePicker: false,
        selectedPeriod: "thisMonth",
        isLoading: false,
      });
    } else {
      // Fallback initialization if date creation fails
      const fallbackDate = this.getLocalDateString(new Date());
      this.state = useState({
        selectedDateRange: {
          start: fallbackDate,
          end: fallbackDate,
        },
        tempDateRange: {
          start: fallbackDate,
          end: fallbackDate,
        },
        showDatePicker: false,
        selectedPeriod: "thisMonth",
        isLoading: false,
      });
    }
  }

  toggleDatePicker() {
    this.state.showDatePicker = !this.state.showDatePicker;
    if (this.state.showDatePicker && this.state.selectedDateRange) {
      this.state.tempDateRange = {
        start: this.state.selectedDateRange.start,
        end: this.state.selectedDateRange.end,
      };
    }
  }

  closeDatePicker() {
    this.state.showDatePicker = false;
    this.state.tempDateRange = { start: "", end: "" };
  }

  async applyDateRange() {
    if (this.state.tempDateRange.start && this.state.tempDateRange.end) {
      const start = new Date(this.state.tempDateRange.start);
      const end = new Date(this.state.tempDateRange.end);

      if (start > end) {
        return;
      }

      this.state.selectedDateRange = {
        start: this.state.tempDateRange.start,
        end: this.state.tempDateRange.end,
      };
      this.state.selectedPeriod = "custom";
    }
    this.closeDatePicker();
  }

  formatDate(dateString) {
    if (!dateString) return "";

    const months = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "Mei",
      "Jun",
      "Jul",
      "Ags",
      "Sep",
      "Okt",
      "Nov",
      "Des",
    ];

    const date = new Date(dateString);
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
    const periodLabels = {
      all: "Pilih Periode",
      today: "Hari Ini",
      yesterday: "Kemarin",
      thisWeek: "Minggu Ini",
      lastWeek: "Minggu Lalu",
      thisMonth: "Bulan Ini",
      lastMonth: "Bulan Lalu",
      thisYear: "Tahun Ini",
      lastYear: "Tahun Lalu",
      bawaan: "Default",
      //   testing: "testing",
    };
    return periodLabels[period] || "Pilih Periode";
  }

  isPeriodSelected(period) {
    return this.state.selectedPeriod === period;
  }

  getLocalDateString(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  setPeriod(period) {
    const now = new Date();
    const todayStart = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate()
    );

    let start, end;

    switch (period) {
      case "today":
        start = todayStart;
        end = todayStart;
        break;

      case "yesterday":
        start = new Date(todayStart);
        start.setDate(todayStart.getDate() - 1);
        end = new Date(start);
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
        start = new Date(
          todayStart.getFullYear(),
          todayStart.getMonth() - 1,
          1
        );
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

      case "bawaan":
        start = new Date(
          todayStart.getFullYear(),
          todayStart.getMonth() - 1,
          1
        );
        end = new Date(todayStart.getFullYear(), todayStart.getMonth(), 0);
        console.log(start, end);
        break;

      default:
        console.log("default case");
        break;
    }

    this.state.selectedPeriod = period;
    this.state.selectedDateRange = {
      start: this.getLocalDateString(start),
      end: this.getLocalDateString(end),
    };
  }
}

OwlGuruquranDashboard.template = "owl.OwlGuruquranDashboard";
OwlGuruquranDashboard.components = {
  GuruquranKpiCard,
  GuruquranChartRenderer,
  GuruquranTahsinCardList,
  GuruquranTahfidzCardList,
};

registry
  .category("actions")
  .add("owl.guruquran_dashboard", OwlGuruquranDashboard);
