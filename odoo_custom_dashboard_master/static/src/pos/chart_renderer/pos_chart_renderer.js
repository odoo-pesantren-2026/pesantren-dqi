/** @odoo-module */

import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

export class PosChartRenderer extends Component {
  static props = {
    type: String,
    title: String,
    selectedStore: { type: Number, optional: true },
  };
  setup() {
    this.storeUpdateInterval = null;
    this.chartRef = useRef("chart");
    this.loadingOverlayRef = useRef("loadingOverlay");
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      labels: [],
      datasets: [],
      datasets2: [],
      hasData: null,
      startDate2: null,
      endDate2: null,
      filter1: null,
      filter2: null,
      periodSelection: "month",
    };

    // COUNTDOWN
    this.refreshInterval = null;
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;

    this.isZoomed = false;

    onWillStart(async () => {
      this.showLoading();
      try {
        await loadJS(
          "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"
        );
        await this.fetchStores(); // First fetch stores
        await this.fetchAndProcessData(); // Then fetch data
      } finally {
        this.hideLoading();
      }
    });

    onMounted(() => {
      if (this.props.title === "pie1") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }
      if (this.props.title === "pie2") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }
      if (this.props.title === "line1") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }
      if (this.props.title === "line2") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }
      if (this.props.title === "bar1") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }
      this.renderChart();
      this.startStorePolling();

      // Add escape key listener
      document.addEventListener("keydown", this.handleEscapeKey.bind(this));
    });

    onWillUnmount(() => {
      // COUNTDOWN
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
      }
      if (this.storeUpdateInterval) {
        clearInterval(this.storeUpdateInterval);
      }

      // Remove escape key listener
      document.removeEventListener("keydown", this.handleEscapeKey.bind(this));
    });
  }

  showLoading() {
    // Create loading overlay if it doesn't exist
    if (!this.loadingOverlay) {
      this.loadingOverlay = document.createElement("div");
      this.loadingOverlay.innerHTML = `
        <div class="musyrif-loading-overlay" style="
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.3);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 9999;
        ">
          <div class="loading-spinner">
            <i class="fas fa-sync-alt fa-spin fa-3x text-white"></i>
          </div>
        </div>
      `;
      document.body.appendChild(this.loadingOverlay);
    }
    // Ensure loading overlay is visible
    if (this.loadingOverlay) {
      this.loadingOverlay.style.display = "flex";
    }

    this.state.isLoading = true;
  }

  hideLoading() {
    if (this.loadingOverlay) {
      this.loadingOverlay.style.display = "none";
    }

    this.state.isLoading = false;
  }

  startStorePolling() {
    // Check for store updates every 5 minutes
    this.storeUpdateInterval = setInterval(async () => {
      const newStores = await this.orm.call(
        "pos.config",
        "search_read",
        [[], ["id", "name"]],
        { order: "name asc" }
      );

      const currentStoreIds = this.state.stores.map((store) => store.id).sort();
      const newStoreIds = newStores.map((store) => store.id).sort();

      if (JSON.stringify(currentStoreIds) !== JSON.stringify(newStoreIds)) {
        this.state.stores = newStores;

        const storeFilter = document.getElementById("storeFilter");
        if (storeFilter) {
          const currentValue = storeFilter.value;
          storeFilter.innerHTML = `
            <option value="">All Stores</option>
            ${newStores
              .map(
                (store) => `
              <option value="${store.id}" ${
                  currentValue == store.id ? "selected" : ""
                }>
                ${store.name}
              </option>
            `
              )
              .join("")}
          `;
        }
      }
    }, 300000);
  }

  async fetchStores() {
    try {
      const stores = await this.orm.call(
        "pos.config",
        "search_read",
        [[], ["id", "name"]],
        { order: "name asc" }
      );
      this.state.stores = stores;
    } catch (error) {
      console.error("Error fetching stores:", error);
    }
  }

  // hasDataDeclare(){

  // }

  // FUNC COUNTDOWN
  toggleCountdown() {
    if (this.isCountingDown) {
      // Jika sedang countdown, hentikan
      this.clearIntervals();
      document.getElementById("timerCountdown").textContent = "";
      const clockElement = document.getElementById("timerIcon");
      if (clockElement) {
        clockElement.classList.add("fas", "fa-clock");
      }
    } else {
      // Jika tidak sedang countdown, mulai baru
      this.isCountingDown = true; // Set flag sebelum memulai countdown
      this.startCountdown();
      const clockElement = document.getElementById("timerIcon");
      if (clockElement) {
        clockElement.classList.remove("fas", "fa-clock");
      }
    }
  }

  clearIntervals() {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
    this.countdownTime = 10; // Reset countdown time
    this.isCountingDown = false; // Reset flag
  }

  startCountdown() {
    // Reset dan inisialisasi ulang
    this.countdownTime = 10;
    this.clearIntervals(); // Bersihkan interval yang mungkin masih berjalan
    this.updateCountdownDisplay();

    this.countdownInterval = setInterval(() => {
      this.countdownTime--;

      if (this.countdownTime < 0) {
        this.countdownTime = 10;
        if (this.state.startDate2 && this.state.endDate2) {
          const startDate = this.state.startDate2;
          const endDate = this.state.endDate2;

          this.refreshChart(startDate, endDate);
        } else {
          this.refreshChart();
        }
      }
      this.updateCountdownDisplay();
    }, 1000);

    // Set flag bahwa countdown sedang berjalan
    this.isCountingDown = true;
  }

  updateCountdownDisplay() {
    const countdownElement = document.getElementById("timerCountdown");
    const timerIcon = document.getElementById("timerIcon");
    if (countdownElement) {
      countdownElement.textContent = this.countdownTime;
    }
  }

  async refreshChart(startDate, endDate) {
    this.showLoading();
    try {
      await this.fetchAndProcessData(startDate, endDate);
    } catch (error) {
      console.error("Error refreshing chart:", error);
    } finally {
      this.hideLoading();
    }
  }

  renderChart() {
    // Check if the chart element reference exists
    if (!this.chartRef.el) {
      console.error("Chart element not found");
      return;
    }

    // Check if there is data to render
    const containsData =
      this.state.labels &&
      this.state.labels.length > 0 &&
      this.state.datasets &&
      this.state.datasets.length > 0;
    this.hasData = null;
    // If no data, hide the chart canvas and show "data tidak ditemukan" message
    if (!containsData) {
      this.hasData = false;

      if (this.chartRef.el) {
        this.chartRef.el.style.display = "none"; // Hide the chart canvas
      }

      // Show "data tidak ditemukan" message
      if (!this.noDataMessage) {
        this.noDataMessage = document.createElement("div");
        this.noDataMessage.style.position = "absolute";
        this.noDataMessage.style.top = "50%";
        this.noDataMessage.style.left = "50%";
        this.noDataMessage.style.transform = "translate(-50%, -50%)";
        this.noDataMessage.style.textAlign = "center";
        this.noDataMessage.style.fontSize = "16px";
        this.noDataMessage.style.color = "gray";
        this.noDataMessage.style.backgroundColor = "white"; // Tambahkan background putih
        this.noDataMessage.style.padding = "10px 20px"; // Tambahkan padding
        this.noDataMessage.style.borderRadius = "4px"; // Tambahkan border radius
        this.noDataMessage.style.zIndex = "10"; // Pastikan pesan berada di atas elemen lain
        this.noDataMessage.style.width = "200px"; // Tetapkan lebar specific
        this.noDataMessage.style.height = "50px"; // Tetapkan tinggi specific
        this.noDataMessage.style.display = "flex"; // Gunakan flexbox
        this.noDataMessage.style.alignItems = "center"; // Pusatkan vertikal
        this.noDataMessage.style.justifyContent = "center"; // Pusatkan horizontal
        this.noDataMessage.textContent = "Data tidak ditemukan";

        // Pastikan parent container memiliki posisi relative
        this.chartRef.el.parentNode.style.position = "relative";
        this.chartRef.el.parentNode.style.minHeight = "200px"; // Tambahkan minimum height
        this.chartRef.el.parentNode.appendChild(this.noDataMessage);
      }

      return; // Prevent chart creation if no data
    } else {
      // If there is data, show the chart and remove "no data" message
      this.hasData = true;

      // Ensure "data tidak ditemukan" message is removed if it exists
      if (this.noDataMessage) {
        this.noDataMessage.remove();
        this.noDataMessage = null;
      }
    }

    // Ensure the chart element is visible
    if (this.chartRef.el) {
      this.chartRef.el.style.display = "block"; // Show the chart canvas
    }

    // Destroy the existing chart if it exists
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }
    try {
      if (this.chartInstance) {
        this.chartInstance.destroy(); // Hancurkan chart lama
      }

      const chartConfig = {
        type: this.props.type,
        data: {
          labels: this.state.labels,
          datasets: this.state.datasets,
        },
        options: {
          onClick: (evt) => this.handleChartClick(evt),
          maintainAspectRatio: false, // Allow chart to resize freely
          responsive: true,
          plugins: {
            legend: {
              display:
                this.props.title != "line2" && this.props.title != "bar1",
              position: "top",
            },
          },
        },
      };

      // Tambahkan konfigurasi scales khusus untuk line1
      if (this.props.title === "line1") {
        chartConfig.options.scales = {
          y: {
            type: "linear",
            position: "left",
            title: {
              display: true,
              text: "Jumlah Order",
            },
            ticks: {
              stepSize: 10,
            },
          },
          y1: {
            type: "linear",
            position: "right",
            title: {
              display: true,
              text: "Jumlah Uang",
            },
            grid: {
              drawOnChartArea: false,
            },
            ticks: {
              callback: (value) => `Rp ${value.toLocaleString("id-ID")}`,
              stepSize: 500000,
            },
          },
        };
      }

      this.chartInstance = new Chart(this.chartRef.el, chartConfig);
    } catch (error) {
      console.error("Error rendering chart:", error);
    }
  }

  async fetchAndProcessData(startDate, endDate) {
    this.showLoading();
    try {
      let pie1 = [];
      let pie2 = [];
      let line1 = [];
      let line2 = [];
      const domain1 = [];
      const domain2 = [];
      const domainline = [];
      const domainline2 = [];

      if (!startDate || !endDate) {
        const today = new Date();
        startDate = new Date(
          Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
        );
        endDate = new Date(
          Date.UTC(
            today.getUTCFullYear(),
            today.getUTCMonth(),
            today.getUTCDate(),
            23,
            59,
            59,
            999
          )
        );
      }

      // Base date domains
      domain1.push(["date", ">=", startDate]);
      domain1.push(["date", "<=", endDate]);
      domain2.push(["date", ">=", startDate]);
      domain2.push(["date", "<=", endDate]);
      domainline.push(["date_order", ">=", startDate]);
      domainline.push(["date_order", "<=", endDate]);
      domainline2.push(["date_order", ">=", startDate]);
      domainline2.push(["date_order", "<=", endDate]);

      // Add store filter domain if a store is selected
      const storeFilter = document.getElementById("storeFilter");
      const selectedStoreId = storeFilter ? parseInt(storeFilter.value) : null;

      if (selectedStoreId) {
        domain1.push(["config_id", "=", selectedStoreId]);
        domain2.push(["config_id", "=", selectedStoreId]);
        domainline.push(["config_id", "=", selectedStoreId]);
        domainline2.push(["config_id", "=", selectedStoreId]);
      }

      // Menambah price total untuk menghindari nilai negatif
      domain1.push(["price_total", ">=", 0]);
      domain2.push(["price_total", ">=", 0]);

      // Fetch data with updated domains
      pie1 = await this.orm.call("report.pos.order", "search_read", [
        domain1,
        ["id", "date", "product_categ_id", "price_total"],
      ]);

      pie2 = await this.orm.call("report.pos.order", "search_read", [
        domain2,
        ["id", "date", "pos_categ_id", "price_total"],
      ]);

      line1 = await this.orm.call("pos.order", "search_read", [
        domainline,
        ["id", "date_order", "amount_total"],
      ]);

      line2 = await this.orm.call("pos.order", "search_read", [
        domainline2,
        ["id", "date_order", "margin"],
      ]);

      await this.processData(pie1, pie2, line1, line2);
    } catch (error) {
      console.error("Error fetching data from Odoo:", error);
    } finally {
      this.showLoading();
    }
  }

  async processData(pie1, pie2, line1, line2) {
    const aggregateDataByState = (data) => {
      const stateCounts = {};
      data.forEach((record) => {
        const state = record.product_categ_id[1];
        if (!stateCounts[state]) {
          stateCounts[state] = { count: 0, ids: [] };
        }
        stateCounts[state].count += 1;
        stateCounts[state].ids.push(record.id);
      });
      return stateCounts;
    };

    const aggregateDataByState2 = (data) => {
      const stateCounts = {};
      data.forEach((record) => {
        const state = record.pos_categ_id[1];
        if (!stateCounts[state]) {
          stateCounts[state] = { count: 0, ids: [] };
        }
        stateCounts[state].count += 1;
        stateCounts[state].ids.push(record.id);
      });
      return stateCounts;
    };

    if (this.props.title === "pie1") {
      const stateCounts = aggregateDataByState(pie1);

      this.state.labels = Object.keys(stateCounts);

      this.state.datasets = [
        {
          label: "Count by State",
          data: Object.values(stateCounts).map((item) => item.count),
          backgroundColor: this.state.labels.map((_, index) =>
            this.getDiverseGradientColor(index, this.state.labels.length)
          ),
          borderColor: "#ffffff",
          borderWidth: 3,
          hoverOffset: 4,
          associated_ids: Object.values(stateCounts).map((item) => item.ids),
        },
      ];
    } else if (this.props.title === "pie2") {
      const stateCounts = aggregateDataByState2(pie2);

      this.state.labels = Object.keys(stateCounts);

      this.state.datasets = [
        {
          label: "Count by State",
          data: Object.values(stateCounts).map((item) => item.count),
          backgroundColor: this.state.labels.map((_, index) =>
            this.getDiverseGradientColor(index, this.state.labels.length)
          ),
          borderColor: "#ffffff",
          borderWidth: 3,
          hoverOffset: 4,
          associated_ids: Object.values(stateCounts).map((item) => item.ids),
        },
      ];
    } else if (this.props.title === "line1") {
      const labels = [];
      const totalAmountData = [];
      const recordCountData = [];
      const associatedTotalAmountIds = [];
      const associatedRecordCountIds = [];

      const groupedData = {};

      // Definisi hari dan bulan dalam bahasa Indonesia
      const daysInIndonesian = [
        "Senin",
        "Selasa",
        "Rabu",
        "Kamis",
        "Jumat",
        "Sabtu",
        "Minggu",
      ];
      const monthsInIndonesian = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
      ];

      // Fungsi untuk membuat daftar periode default
      const createDefaultPeriods = (type) => {
        switch (type) {
          case "hourly":
            return Array.from(
              { length: 24 },
              (_, i) => `${i.toString().padStart(2, "0")}:00`
            );
          case "daily":
            return daysInIndonesian;
          case "weekly":
            // Akan diisi dengan week number yang ada di data
            return [];
          case "monthly":
            return monthsInIndonesian;
          case "yearly":
            // Akan diisi dengan tahun yang ada di data
            return [];
          default:
            return Array.from(
              { length: 24 },
              (_, i) => `${i.toString().padStart(2, "0")}:00`
            );
        }
      };

      // Proses data
      line1.forEach((order) => {
        const orderDate = new Date(order.date_order);
        const localDate = new Date(
          orderDate.getTime() - orderDate.getTimezoneOffset() * 60000
        );

        const hour = localDate.getHours(); // Directly use 24-hour format (no AM/PM)
        let dateKey = `${hour.toString().padStart(2, "0")}:00`; // Show only the current hour

        // Sesuaikan pengelompokan berdasarkan periode yang dipilih
        if (this.state.filter1 === "hourly") {
          const hour = localDate.getHours(); // Directly use 24-hour format (no AM/PM)
          dateKey = `${hour.toString().padStart(2, "0")}:00`; // Show only the current hour
        } else if (this.state.filter1 === "daily") {
          // Menggunakan indeks hari untuk memastikan urutan dari Senin
          const dayIndex = (localDate.getDay() + 6) % 7;
          dateKey = daysInIndonesian[dayIndex];
        } else if (this.state.filter1 === "weekly") {
          const startOfYear = new Date(localDate.getFullYear(), 0, 1);
          const weekNumber = Math.ceil(
            ((localDate - startOfYear) / 86400000 + 1) / 7
          );
          dateKey = `Minggu ${weekNumber}`;
        } else if (this.state.filter1 === "monthly") {
          dateKey = monthsInIndonesian[localDate.getMonth()];
        } else if (this.state.filter1 === "yearly") {
          dateKey = `${localDate.getFullYear()}`;
        }

        if (!groupedData[dateKey]) {
          groupedData[dateKey] = {
            totalAmount: 0,
            recordCount: 0,
            totalAmountIds: [],
            recordCountIds: [],
          };
        }

        groupedData[dateKey].totalAmount += order.amount_total;
        groupedData[dateKey].recordCount += 1;
        groupedData[dateKey].totalAmountIds.push(order.id);
        groupedData[dateKey].recordCountIds.push(order.id);
      });

      // Dapatkan periode default
      const defaultPeriods = createDefaultPeriods(this.state.filter1);

      // Gabungkan periode default dengan periode dari data
      const allPeriods = [
        ...new Set([...defaultPeriods, ...Object.keys(groupedData)]),
      ];

      // Urutkan periode
      const sortedPeriods = allPeriods.sort((a, b) => {
        if (this.state.filter1 === "hourly") {
          return a.localeCompare(b);
        } else if (this.state.filter1 === "daily") {
          return daysInIndonesian.indexOf(a) - daysInIndonesian.indexOf(b);
        } else if (this.state.filter1 === "monthly") {
          return monthsInIndonesian.indexOf(a) - monthsInIndonesian.indexOf(b);
        } else if (this.state.filter1 === "weekly") {
          // Untuk weekly, urutkan berdasarkan nomor minggu
          const weekA = parseInt(a.replace("Minggu ", ""));
          const weekB = parseInt(b.replace("Minggu ", ""));
          return weekA - weekB;
        } else if (this.state.filter1 === "yearly") {
          return parseInt(a) - parseInt(b);
        }
        return 0;
      });

      // Proses data untuk chart
      sortedPeriods.forEach((dateKey) => {
        labels.push(dateKey);

        if (groupedData[dateKey]) {
          totalAmountData.push(groupedData[dateKey].totalAmount);
          recordCountData.push(groupedData[dateKey].recordCount);
          associatedTotalAmountIds.push(groupedData[dateKey].totalAmountIds);
          associatedRecordCountIds.push(groupedData[dateKey].recordCountIds);
        } else {
          // Jika tidak ada data untuk periode tertentu
          totalAmountData.push(0);
          recordCountData.push(0);
          associatedTotalAmountIds.push([]);
          associatedRecordCountIds.push([]);
        }
      });

      this.state.labels = labels;
      this.state.datasets = [
        {
          label: "Jumlah Uang",
          data: totalAmountData,
          yAxisID: "y1",
          borderColor: "rgba(22, 163, 74, 1)",
          backgroundColor: "rgba(22, 163, 74, 0.2)",
          tension: 0.3,
          fill: true,
          associated_ids: associatedTotalAmountIds,
        },
        {
          label: "Jumlah Order",
          data: recordCountData,
          yAxisID: "y",
          borderColor: "rgba(8, 145, 178, 1)",
          backgroundColor: "rgba(8, 145, 178, 0.2)",
          tension: 0.3,
          fill: true,
          associated_ids: associatedRecordCountIds,
        },
      ];

      this.hasDatapd = null;
      const containsData =
        this.state.labels &&
        this.state.labels.length > 0 &&
        this.state.datasets &&
        this.state.datasets.length > 0;

      if (!containsData) {
        this.hasDatapd = false;
      } else {
        // If there is data, show the chart and remove "no data" message
        this.hasDatapd = true;
      }
    } else if (this.props.title === "line2") {
      const labels = [];
      const marginData = [];
      const associatedMarginIds = [];

      const groupedData = {};
      const daysInIndonesian = [
        "Senin",
        "Selasa",
        "Rabu",
        "Kamis",
        "Jumat",
        "Sabtu",
        "Minggu",
      ];
      const monthsInIndonesian = [
        "Januari",
        "Februari",
        "Maret",
        "April",
        "Mei",
        "Juni",
        "Juli",
        "Agustus",
        "September",
        "Oktober",
        "November",
        "Desember",
      ];

      // Fungsi untuk membuat daftar periode default (berdasarkan filter2)
      const createDefaultPeriods = (type) => {
        switch (type) {
          case "hourly":
            return Array.from(
              { length: 24 },
              (_, i) => `${i.toString().padStart(2, "0")}:00`
            );
          case "daily":
            return daysInIndonesian;
          case "weekly":
            return []; // Akan diisi dengan nomor minggu yang ada di data
          case "monthly":
            return monthsInIndonesian;
          case "yearly":
            return []; // Akan diisi dengan tahun yang ada di data
          default:
            return Array.from(
              { length: 24 },
              (_, i) => `${i.toString().padStart(2, "0")}:00`
            );
        }
      };

      line2.forEach((order) => {
        // Convert to local timezone for display
        const orderDate = new Date(order.date_order);
        const localDate = new Date(
          orderDate.getTime() - orderDate.getTimezoneOffset() * 60000
        );

        const hour = localDate.getHours(); // Directly use 24-hour format (no AM/PM)
        let dateKey = `${hour.toString().padStart(2, "0")}:00`; // Show only the current hour

        // Sesuaikan pengelompokan berdasarkan periode yang dipilih (menggunakan filter2)
        if (this.state.filter2 === "hourly") {
          const hour = localDate.getHours(); // Directly use 24-hour format (no AM/PM)
          dateKey = `${hour.toString().padStart(2, "0")}:00`; // Show only the current hour
        } else if (this.state.filter2 === "daily") {
          const dayIndex = (localDate.getDay() + 6) % 7;
          dateKey = daysInIndonesian[dayIndex];
        } else if (this.state.filter2 === "weekly") {
          const startOfYear = new Date(localDate.getFullYear(), 0, 1);
          const weekNumber = Math.ceil(
            ((localDate - startOfYear) / 86400000 + 1) / 7
          );
          dateKey = `Minggu ${weekNumber}`;
        } else if (this.state.filter2 === "monthly") {
          dateKey = monthsInIndonesian[localDate.getMonth()];
        } else if (this.state.filter2 === "yearly") {
          dateKey = `${localDate.getFullYear()}`;
        }

        if (!groupedData[dateKey]) {
          groupedData[dateKey] = {
            margin: 0,
            marginIds: [],
          };
        }

        groupedData[dateKey].margin += order.margin;
        groupedData[dateKey].marginIds.push(order.id);
      });

      // Dapatkan periode default berdasarkan filter2
      const defaultPeriods = createDefaultPeriods(this.state.filter2);

      // Gabungkan periode default dengan periode dari data
      const allPeriods = [
        ...new Set([...defaultPeriods, ...Object.keys(groupedData)]),
      ];

      // Urutkan periode
      const sortedPeriods = allPeriods.sort((a, b) => {
        if (this.state.filter2 === "hourly") {
          return a.localeCompare(b);
        } else if (this.state.filter2 === "daily") {
          return daysInIndonesian.indexOf(a) - daysInIndonesian.indexOf(b);
        } else if (this.state.filter2 === "monthly") {
          return monthsInIndonesian.indexOf(a) - monthsInIndonesian.indexOf(b);
        } else if (this.state.filter2 === "weekly") {
          // Untuk weekly, urutkan berdasarkan nomor minggu
          const weekA = parseInt(a.replace("Minggu ", ""));
          const weekB = parseInt(b.replace("Minggu ", ""));
          return weekA - weekB;
        } else if (this.state.filter2 === "yearly") {
          return parseInt(a) - parseInt(b);
        }
        return 0;
      });
      // Proses data untuk chart
      sortedPeriods.forEach((dateKey) => {
        labels.push(dateKey);

        if (groupedData[dateKey]) {
          marginData.push(groupedData[dateKey].margin);
          associatedMarginIds.push(groupedData[dateKey].marginIds);
        } else {
          // Jika tidak ada data untuk periode tertentu
          marginData.push(0);
          associatedMarginIds.push([]);
        }
      });

      this.state.labels = labels;
      this.state.datasets = [
        {
          label: "Margin",
          data: marginData,
          yAxisID: "y",
          borderColor: "rgba(22, 163, 74, 1)",
          backgroundColor: "rgba(21, 128, 61, 0.2)",
          tension: 0.3,
          fill: true,
          associated_ids: associatedMarginIds, // Tambahkan associated_ids
        },
      ];
      this.hasDatapd2 = null;
      const containsData2 =
        this.state.labels &&
        this.state.labels.length > 0 &&
        this.state.datasets &&
        this.state.datasets.length > 0;

      if (!containsData2) {
        this.hasDatapd2 = false;
      } else {
        // If there is data, show the chart and remove "no data" message
        this.hasDatapd = true;
      }
    } else if (this.props.title === "bar1") {
      const labels = [];
      const recordCountData = [];
      const associatedRecordCountIds = [];

      // Function to get Indonesian day name
      const getIndonesianDayName = (date) => {
        const days = [
          "Minggu",
          "Senin",
          "Selasa",
          "Rabu",
          "Kamis",
          "Jumat",
          "Sabtu",
        ];
        return days[date.getDay()];
      };

      const groupedData = {};
      line2.forEach((order) => {
        // Convert to local timezone for display
        const orderDate = new Date(order.date_order);
        const localDate = new Date(
          orderDate.getTime() - orderDate.getTimezoneOffset() * 60000
        );
        const dayName = getIndonesianDayName(localDate);

        if (!groupedData[dayName]) {
          groupedData[dayName] = {
            recordCount: 0,
            recordCountIds: [],
          };
        }
        groupedData[dayName].recordCount += 1;
        groupedData[dayName].recordCountIds.push(order.id);
      });

      // Define the day order for proper sorting
      const dayOrder = [
        "Senin",
        "Selasa",
        "Rabu",
        "Kamis",
        "Jumat",
        "Sabtu",
        "Minggu",
      ];

      // Sort the days according to dayOrder
      Object.keys(groupedData)
        .sort((a, b) => dayOrder.indexOf(a) - dayOrder.indexOf(b))
        .forEach((dayName) => {
          labels.push(dayName);
          recordCountData.push(groupedData[dayName].recordCount);
          associatedRecordCountIds.push(groupedData[dayName].recordCountIds);
        });

      this.state.labels = labels;
      this.state.datasets = [
        {
          label: "Jumlah Order",
          data: recordCountData,
          borderColor: "rgba(8, 145, 178, 1)",
          backgroundColor: "rgba(8, 145, 178, 0.6)",
          tension: 0.3,
          fill: true,
          associated_ids: associatedRecordCountIds,
        },
      ];
    }
    this.renderChart();
  }

  getDiverseGradientColor(index, totalItems) {
    const colors = [
      "rgba(22, 163, 74, 1)",
      "rgba(8, 145, 178, 1)",
      "rgba(34, 197, 94, 1)",
      "rgba(6, 182, 212, 1)",
      "rgba(21, 128, 61, 1)",
      "rgba(14, 116, 144, 1)",
      "rgba(134, 239, 172, 1)",
      "rgba(103, 232, 249, 1)",
      "rgba(22, 101, 52, 1)",
      "rgba(21, 94, 117, 1)",
    ];
    return colors[index % colors.length];
  }

  setState(hasData) {
    if ([true, false].includes(hasData)) {
      this.state.hasData = hasData;
    } else {
      this.state.hasData = false;
    }
  }

  handleChartClick(evt) {
    this.clearIntervals();
    const activePoints = this.chartInstance.getElementsAtEventForMode(
      evt,
      "nearest",
      { intersect: true },
      false
    );
    if (activePoints.length > 0) {
      const firstPoint = activePoints[0];
      const datasetIndex = firstPoint.datasetIndex;
      const label = this.chartInstance.data.labels[firstPoint.index];

      const dataset = this.state.datasets[datasetIndex];
      const associatedIds = dataset.associated_ids
        ? dataset.associated_ids[firstPoint.index]
        : null;

      if (!associatedIds) {
        console.error("No associated IDs for the clicked data point.");
        return;
      }
      let resModel;

      if (this.props.type === "line" || this.props.type === "bar") {
        resModel = "pos.order";
      } else if (this.props.type === "pie") {
        resModel = "report.pos.order";
      }

      // Close the zoomed chart if it's currently zoomed
      if (this.isZoomed) {
        this.toggleZoom();
      }

      if (
        this.actionService &&
        typeof this.actionService.doAction === "function"
      ) {
        this.actionService
          .doAction({
            name: "Record List",
            type: "ir.actions.act_window",
            res_model: resModel,
            view_mode: "list",
            views: [[false, "list"]],
            target: "current",
            domain: [["id", "in", associatedIds]],
          })
          .then(() => {})
          .catch((error) => {
            console.error("Error in actionService.doAction redirect:", error);
          });
      } else {
        console.error(
          "actionService.doAction is not a function or actionService is undefined:",
          this.actionService
        );
      }
    }
  }

  attachEventListeners() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const timerButton = document.getElementById("timerButton");
    const timeFilter = document.getElementById("timeFilter");
    const timeFilter2 = document.getElementById("timeFilter2");
    const storeFilter = document.getElementById("storeFilter");

    if (storeFilter) {
      storeFilter.addEventListener("change", async (event) => {
        this.showLoading();
        try {
          await this.fetchAndProcessData(
            this.state.startDate2,
            this.state.endDate2
          );
        } catch (error) {
          console.error("Error updating chart with store filter:", error);
        } finally {
          this.hideLoading();
        }
      });
    }

    // Update timeFilter event listener
    if (timeFilter) {
      timeFilter.addEventListener("change", async (event) => {
        this.showLoading();
        try {
          const selectedValue = event.target.value;
          switch (selectedValue) {
            case "hourly":
            case "daily":
            case "weekly":
            case "monthly":
            case "yearly":
              this.state.filter1 = selectedValue;
              break;
            default:
              this.state.filter1 = "monthly";
          }
          await this.fetchAndProcessData(
            this.state.startDate2,
            this.state.endDate2
          );
        } catch (error) {
          console.error("Error updating chart with time filter 1:", error);
        } finally {
          this.hideLoading();
        }
      });
    }

    // Update timeFilter2 event listener
    if (timeFilter2) {
      timeFilter2.addEventListener("change", async (event) => {
        this.showLoading();
        try {
          const selectedValue = event.target.value;
          switch (selectedValue) {
            case "hourly":
            case "daily":
            case "weekly":
            case "monthly":
            case "yearly":
              this.state.filter2 = selectedValue;
              break;
            default:
              this.state.filter2 = "monthly";
          }
          await this.fetchAndProcessData(
            this.state.startDate2,
            this.state.endDate2
          );
        } catch (error) {
          console.error("Error updating chart with time filter 2:", error);
        } finally {
          this.hideLoading();
        }
      });
    }

    // Keep existing date input and timer button event listeners
    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", () => this.filterData());
      endDateInput.addEventListener("change", () => this.filterData());
    }

    if (timerButton) {
      timerButton.addEventListener("click", this.toggleCountdown.bind(this));
    }

    // Keep existing date picker button and container logic
    const datePickerButton = document.getElementById("datePickerButton");
    const datePickerContainer = document.getElementById("datePickerContainer");

    if (datePickerButton && datePickerContainer) {
      datePickerButton.addEventListener("click", (event) => {
        event.stopPropagation();
        datePickerContainer.style.display =
          datePickerContainer.style.display === "flex" ? "none" : "flex";
      });
    }

    document.addEventListener("click", (event) => {
      if (
        datePickerContainer &&
        !datePickerContainer.contains(event.target) &&
        !datePickerButton.contains(event.target)
      ) {
        datePickerContainer.style.display = "none";
      }
    });
  }

  async filterData() {
    var startDate = document.getElementById("startDate")?.value;
    var endDate = document.getElementById("endDate")?.value;

    if (startDate && endDate) {
      this.showLoading();
      try {
        this.state.startDate2 = startDate;
        this.state.endDate2 = endDate;
        await this.fetchAndProcessData(
          this.state.startDate2,
          this.state.endDate2
        );
      } catch (error) {
        console.error("Error refreshing chart:", error);
      } finally {
        this.hideLoading();
      }
    }
  }

  filterDataByPeriod() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");

    const today = new Date();
    let startDate;
    let endDate;

    if (periodSelection) {
      periodSelection.addEventListener("change", async () => {
        this.showLoading();
        try {
          switch (periodSelection.value) {
            case "thisweek":
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate() - today.getUTCDay()
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate() + (6 - today.getUTCDay())
                )
              );
              break;
            case "lastweek":
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate() - 14
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate()
                )
              );
              break;
            case "month":
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  1,
                  0,
                  0,
                  1
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate(),
                  23,
                  59,
                  59,
                  999
                )
              );
              break;
            case "yesterday":
              startDate = new Date(
                Date.UTC(
                  today.getFullYear(),
                  today.getMonth(),
                  today.getDate() - 1,
                  0,
                  0,
                  0,
                  0
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getFullYear(),
                  today.getMonth(),
                  today.getDate() - 1,
                  23,
                  59,
                  59,
                  999
                )
              );
              break;
            case "today":
              startDate = new Date(
                Date.UTC(
                  today.getFullYear(),
                  today.getMonth(),
                  today.getDate(),
                  0,
                  0,
                  0,
                  0
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getFullYear(),
                  today.getMonth(),
                  today.getDate(),
                  23,
                  59,
                  59,
                  999
                )
              );
              break;
            case "lastMonth":
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth() - 1,
                  1,
                  0,
                  0,
                  1
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  0,
                  23,
                  59,
                  59,
                  999
                )
              );
              break;
            case "thisyear":
              startDate = new Date(
                Date.UTC(today.getUTCFullYear(), 0, 1, 0, 0, 0)
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate(),
                  23,
                  59,
                  59,
                  999
                )
              );
              break;

            case "lastyear":
              startDate = new Date(
                Date.UTC(today.getUTCFullYear() - 1, 0, 1, 0, 0, 0)
              );
              endDate = new Date(
                Date.UTC(today.getUTCFullYear() - 1, 11, 31, 23, 59, 59, 999)
              );
              break;

            default:
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  1,
                  0,
                  0,
                  1
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate(),
                  23,
                  59,
                  59,
                  999
                )
              );
          }

          if (startDate && endDate) {
            this.state.startDate2 = startDate.toISOString().split("T")[0];
            this.state.endDate2 = endDate.toISOString().split("T")[0];
            startDateInput.value = this.state.startDate2;
            endDateInput.value = this.state.endDate2;

            await this.fetchAndProcessData(
              this.state.startDate2,
              this.state.endDate2
            );
          }
        } catch (error) {
          console.error("Error processing period selection:", error);
        } finally {
          this.hideLoading();
        }
      });
    }
  }

  handleEscapeKey(event) {
    if (event.key === "Escape" && this.isZoomed) {
      this.toggleZoom();
    }
  }

  toggleZoom() {
    console.log("Zoom Ditekan");
  }

  toggleZoom() {
    console.log("Tombol zoom ditekan");
    const chartWrapper = this.chartRef.el.parentElement;
    const zoomBtn = chartWrapper.querySelector(".zoom-btn i");

    if (!this.isZoomed) {
      // Create fullscreen container if it doesn't exist
      if (!this.fullscreenContainer) {
        this.fullscreenContainer = document.createElement("div");
        this.fullscreenContainer.className =
          "position-fixed top-0 start-0 w-100 h-100 bg-white p-4";
        this.fullscreenContainer.style.zIndex = "9999";

        // Add close button
        const closeBtn = document.createElement("button");
        closeBtn.className =
          "btn btn-sm btn-light position-absolute top-0 end-0 m-3";
        closeBtn.innerHTML = '<i class="fas fa-times"></i>';
        closeBtn.onclick = () => this.toggleZoom();
        this.fullscreenContainer.appendChild(closeBtn);

        // Add chart container
        this.zoomedChartContainer = document.createElement("div");
        this.zoomedChartContainer.style.height = "95%";
        this.fullscreenContainer.appendChild(this.zoomedChartContainer);
      }

      // Store original parent and dimensions
      this.originalParent = this.chartRef.el.parentElement;
      this.originalHeight = this.chartRef.el.style.height;
      this.originalWidth = this.chartRef.el.style.width;

      // Show fullscreen
      document.body.appendChild(this.fullscreenContainer);
      this.chartRef.el.style.height = "100%";
      this.zoomedChartContainer.appendChild(this.chartRef.el);

      if (zoomBtn) {
        zoomBtn.className = "fas fa-compress";
      }
    } else {
      // Return to normal view
      const chartCanvas = this.chartRef.el;

      // First, remove the fullscreen container
      if (this.fullscreenContainer && this.fullscreenContainer.parentNode) {
        document.body.removeChild(this.fullscreenContainer);
      }

      // Then reattach the chart to its original container
      if (this.originalParent) {
        // Restore original dimensions
        chartCanvas.style.height = this.originalHeight;
        chartCanvas.style.width = this.originalWidth;
        this.originalParent.appendChild(chartCanvas);
      }

      if (zoomBtn) {
        zoomBtn.className = "fas fa-expand";
      }
    }

    this.isZoomed = !this.isZoomed;

    // Resize chart to fit new container
    if (this.chartInstance) {
      setTimeout(() => {
        this.chartInstance.resize();
      }, 100); // Increased timeout to ensure DOM updates
    }
  }
}
PosChartRenderer.template = "owl.PosChartRenderer";
