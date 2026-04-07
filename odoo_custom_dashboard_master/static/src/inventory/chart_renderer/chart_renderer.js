/** @odoo-module */

import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

export class StockChartRenderer extends Component {
  setup() {
    this.chartRef = useRef("chart");
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.default_period = "thisMonth";
    this.state = {
      labels: [],
      datasets: [],
      hasData: true,
      startDate2: null,
      endDate2: null,
    };
    console.log("hasdata onstart: ", this.state.hasData);

    this.hasData = true;
    console.log("thishasdata onstart: ", this.hasData);

    // COUNTDOWN
    this.refreshInterval = null;
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;

    // Contoh lain setup sebelumnya...
    onWillStart(async () => {
      this.showLoading();
      try {
        await loadJS(
          "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"
        );
        await this.fetchAndProcessData();
      } catch {
        console.log("terjadi error");
      } finally {
        this.hideLoading();
      }
    });
    onMounted(() => {
      const periodSelection = document.getElementById("periodSelection");
      if (periodSelection) {
        periodSelection.value = "thisMonth";
      }
      if (this.props.title === "pie1") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }
      if (this.props.title === "pie2") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }
      if (this.props.title === "pie3") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }

      this.renderChart();
    });

    onWillUnmount(() => {
      // COUNTDOWN
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
      }
    });
  }

  showLoading() {
    if (!this.loadingOverlay) {
      this.loadingOverlay = document.createElement("div");
      this.loadingOverlay.innerHTML = ` <div class="musyrif-loading-overlay" style="
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
        </div>`;
      document.body.appendChild(this.loadingOverlay);
    }
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

    // Mulai interval baru
    this.countdownInterval = setInterval(() => {
      this.countdownTime--;

      if (this.countdownTime < 0) {
        this.countdownTime = 10;
        if (this.state.startDate2 && this.state.endDate2) {
          console.log(
            "dates state: ",
            this.state.startDate2,
            "& ",
            this.state.endDate2
          );
          const startDate = this.state.startDate2;
          const endDate = this.state.endDate2;
          console.log("dates: ", startDate, "& ", endDate);
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

  refreshChart(startDate, endDate) {
    // Logika refresh chart
    console.log("Refreshing chart...");
    // Contoh penggunaan data fetching ulang
    this.fetchAndProcessData(startDate, endDate);
  }

  async fetchAndProcessData(startDate, endDate) {
    this.showLoading();
    try {
      let pie1 = [];
      let pie2 = [];
      let pie3 = [];
      const domain1 = [["picking_type_code", "=", "internal"]];
      const domain2 = [["picking_type_code", "=", "incoming"]];
      const domain3 = [["picking_type_code", "=", "outgoing"]];
      // Set default startDate dan endDate jika tidak diisi
      if (!startDate) {
        const today = new Date();
        const firstDayOfMonth = new Date(
          Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
        );
        startDate = firstDayOfMonth.toISOString().split("T")[0];
      }

      if (!endDate) {
        const today = new Date();
        const lastDayOfMonth = new Date(
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
        endDate = lastDayOfMonth.toISOString().split("T")[0];
      }
      domain1.push(["create_date", ">=", startDate]);
      domain1.push(["create_date", "<=", endDate]);
      domain2.push(["create_date", ">=", startDate]);
      domain2.push(["create_date", "<=", endDate]);
      domain3.push(["create_date", ">=", startDate]);
      domain3.push(["create_date", "<=", endDate]);

      pie1 = await this.orm.call("stock.picking", "search_read", [
        domain1,
        ["id", "create_date", "state"],
      ]);

      pie2 = await this.orm.call("stock.picking", "search_read", [
        domain2,
        ["id", "create_date", "state"],
      ]);

      pie3 = await this.orm.call("stock.picking", "search_read", [
        domain3,
        ["id", "create_date", "state"],
      ]);

      console.log("Dom 1 = ", domain1);
      console.log("Dom 2 = ", domain2);
      console.log("Dom 3 = ", domain3);
      console.log("DATA PIE 1 = ", pie1);
      console.log("DATA PIE 2 = ", pie2);
      console.log("DATA PIE 3 = ", pie3);

      // await this.processData(moveData, moveLineData);
      await this.processData(pie1, pie2, pie3);
    } catch (error) {
      console.error("Error fetching data from Odoo:", error);
    } finally {
      this.hideLoading();
    }
  }

  async processData(pie1, pie2, pie3) {
    const aggregateDataByState = (data) => {
      const stateCounts = {};
      data.forEach((record) => {
        const state = record.state;
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

      this.state.labels = Object.keys(stateCounts).map((state) => {
        if (state === "done") return "Selesai";
        if (state === "assigned") return "Proses";
        if (state === "draft") return "Draft";
        if (state === "waiting") return "Menunggu";
        if (state === "cancel") return "Dibatalkan";
        return state;
      });

      this.state.datasets = [
        {
          label: this.state.labels,
          data: Object.values(stateCounts).map((item) => item.count),
          backgroundColor: this.state.labels.map((_, index) =>
            this.getDiverseGradientColor(index, this.state.labels.length)
          ),
          borderColor: "#ffffff",
          borderWidth: 1,
          hoverOffset: 4,
          associated_ids: Object.values(stateCounts).map((item) => item.ids),
        },
      ];

      console.log("Processed Data for pie1:", this.state.datasets);
    } else if (this.props.title === "pie2") {
      const stateCounts = aggregateDataByState(pie2);

      this.state.labels = Object.keys(stateCounts).map((state) => {
        if (state === "done") return "Selesai";
        if (state === "assigned") return "Proses";
        if (state === "draft") return "Draft";
        if (state === "waiting") return "Menunggu";
        if (state === "cancel") return "Dibatalkan";
        return state;
      });

      this.state.datasets = [
        {
          label: "Count by State",
          data: Object.values(stateCounts).map((item) => item.count),
          backgroundColor: this.state.labels.map((_, index) =>
            this.getDiverseGradientColor(index, this.state.labels.length)
          ),
          borderColor: "#ffffff",
          borderWidth: 1,
          hoverOffset: 4,
          associated_ids: Object.values(stateCounts).map((item) => item.ids),
        },
      ];

      console.log("Processed Data for pie2:", this.state.datasets);
    } else if (this.props.title === "pie3") {
      const stateCounts = aggregateDataByState(pie3);

      this.state.labels = Object.keys(stateCounts).map((state) => {
        if (state === "done") return "Selesai";
        if (state === "assigned") return "Proses";
        if (state === "draft") return "Draft";
        if (state === "waiting") return "Menunggu";
        if (state === "cancel") return "Dibatalkan";
        return state;
      });

      this.state.datasets = [
        {
          label: "Count by State",
          data: Object.values(stateCounts).map((item) => item.count),
          backgroundColor: this.state.labels.map((_, index) =>
            this.getDiverseGradientColor(index, this.state.labels.length)
          ),
          borderColor: "#ffffff",
          borderWidth: 1,
          hoverOffset: 4,
          associated_ids: Object.values(stateCounts).map((item) => item.ids),
        },
      ];

      console.log("Processed Data for pie3:", this.state.datasets);
    } else if (this.props.title === "line2") {
      const labels = [];
      const marginData = [];
      const associatedMarginIds = [];

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
            margin: 0,
            marginIds: [],
          };
        }
        groupedData[dayName].margin += order.margin;
        groupedData[dayName].marginIds.push(order.id);
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
          marginData.push(groupedData[dayName].margin);
          associatedMarginIds.push(groupedData[dayName].marginIds);
        });

      this.state.labels = labels;
      this.state.datasets = [
        {
          label: "Margin",
          data: marginData,
          yAxisID: "y",
          borderColor: "rgba(255, 99, 132, 1)",
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          tension: 0.3,
          fill: true,
          associated_ids: associatedMarginIds,
        },
      ];
    }

    this.renderChart();
  }

  getDiverseGradientColor(index, totalItems) {
    const colors = [
      "#16a34a",
      "#0891b2",
      "#22c55e",
      "#06b6d4",
      "#15803d",
      "#0e7490",
      "#86efac",
      "#67e8f9",
      "#166534",
      "#155e75",
    ];
    return colors[index % colors.length];
  }

  setState(hasData) {
    if ([true, false].includes(hasData)) {
      this.state.hasData = hasData;
      console.log("hasdata: ", hasData);
    } else {
      this.state.hasData = false;
      console.log("hasdata else: ", hasData);
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

    // If no data, hide the chart canvas and show "data tidak ditemukan" message
    if (!containsData) {
      this.hasData = false;
      console.log("hasdata: ", this.hasData);

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
      console.log("hasdata: ", this.hasData);

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
      // Create the new chart instance
      this.chartInstance = new Chart(this.chartRef.el, {
        type: this.props.type,
        data: {
          labels: this.state.labels,
          datasets: this.state.datasets,
        },
        options: {
          // Keep aspect ratio fixed
          responsive: true,
          plugins: {
            legend: {
              position: "top",
              display: this.props.type !== "line" && this.props.type !== "bar",
            },
            title: {
              display: false,
              text: this.props.title,
            },
          },
          layout: {
            padding: {
              top: 20, // Jarak atas
              bottom: 20, // Jarak bawah
            },
          },
          onClick: (evt) => this.handleChartClick(evt),
        },
      });
    } catch (error) {
      console.error("Error rendering chart:", error);
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
      const resModel = "stock.picking";

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
          .then(() => {
            console.log(
              `Redirected to list view of ${resModel} for selected IDs.`
            );
          })
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
    this.updateDateRangeText();
    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", () => this.filterData());
      endDateInput.addEventListener("change", () => this.filterData());
    } else {
      console.error("Date input elements not found");
    }

    if (timerButton) {
      timerButton.addEventListener("click", this.toggleCountdown.bind(this));
    } else {
      console.error("Timer button element not found");
    }

    const datePickerButton = document.getElementById("datePickerButton");
    const datePickerContainer = document.getElementById("datePickerContainer");

    if (datePickerButton && datePickerContainer) {
      datePickerButton.addEventListener("click", (event) => {
        event.stopPropagation(); // Prevent event from bubbling up
        // Toggle the display property
        datePickerContainer.style.display =
          datePickerContainer.style.display === "flex" ? "none" : "flex";
      });
    } else {
      console.error("Date picker button or container element not found");
    }

    // Close the date picker if clicking outside of it
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

  filterData() {
    var startDate = document.getElementById("startDate")?.value;
    var endDate = document.getElementById("endDate")?.value;

    if (startDate && endDate) {
      this.showLoading();
      try {
        this.fetchAndProcessData(startDate, endDate);
        this.state.startDate2 = startDate;
        this.state.endDate2 = endDate;
        this.updateDateRangeText();
      } catch {
        console.log("terjadi error");
      } finally {
        this.hideLoading();
      }
    } else {
      this.fetchAndProcessData();
    }
  }

  filterDataByPeriod() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");

    // Langsung eksekusi logic tanpa mendaftarkan event listener baru
    const today = new Date();
    let startDate;
    let endDate;
    const defaultPeriod = "thisMonth"; // Default ke Bulan Ini
    periodSelection.value = defaultPeriod; // Pilih default period pada dropdown

    if (periodSelection) {
      periodSelection.addEventListener("change", () => {
        this.showLoading();
        try {
          switch (periodSelection.value) {
            case "today":
              // Hari Ini
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate(),
                  0,
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
              // Kemarin
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate() - 1,
                  0,
                  0,
                  0,
                  1
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  today.getUTCDate() - 1,
                  23,
                  59,
                  59,
                  999
                )
              );
              break;
            case "thisWeek":
              // Minggu Ini
              const startOfWeek = today.getUTCDate() - today.getUTCDay(); // Set ke hari Minggu
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  startOfWeek,
                  0,
                  0,
                  0,
                  1
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  startOfWeek + 6,
                  23,
                  59,
                  59,
                  999
                )
              );
              break;
            case "lastWeek":
              // Minggu Lalu
              const lastWeekStart = today.getUTCDate() - today.getUTCDay() - 7; // Minggu sebelumnya
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  lastWeekStart,
                  0,
                  0,
                  0,
                  1
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  lastWeekStart + 6,
                  23,
                  59,
                  59,
                  999
                )
              );
              break;
            case "thisMonth":
              // Bulan Ini
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  1,
                  0,
                  0,
                  0,
                  1
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth() + 1,
                  0,
                  23,
                  59,
                  59,
                  999
                )
              );
              break;
            case "lastMonth":
              // Bulan Lalu
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth() - 1,
                  1,
                  0,
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
            case "thisYear":
              // Tahun Ini
              startDate = new Date(
                Date.UTC(today.getUTCFullYear(), 0, 1, 0, 0, 0, 1)
              );
              endDate = new Date(
                Date.UTC(today.getUTCFullYear(), 11, 31, 23, 59, 59, 999)
              );
              break;
            case "lastYear":
              // Tahun Lalu
              startDate = new Date(
                Date.UTC(today.getUTCFullYear() - 1, 0, 1, 0, 0, 0, 1)
              );
              endDate = new Date(
                Date.UTC(today.getUTCFullYear() - 1, 11, 31, 23, 59, 59, 999)
              );
              break;
            default:
              // Default ke Bulan Ini jika tidak ada yang cocok
              startDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth(),
                  1,
                  0,
                  0,
                  0,
                  1
                )
              );
              endDate = new Date(
                Date.UTC(
                  today.getUTCFullYear(),
                  today.getUTCMonth() + 1,
                  0,
                  23,
                  59,
                  59,
                  999
                )
              );
          }

          // Update the input fields and the state
          if (startDate && endDate) {
            this.state.startDate2 = startDate.toISOString().split("T")[0];
            this.state.endDate2 = endDate.toISOString().split("T")[0];
            startDateInput.value = this.state.startDate2;
            endDateInput.value = this.state.endDate2;
            console.log("dates down: ", startDate, "& ", endDate);
            console.log(
              "dates down state: ",
              this.state.startDate2,
              "& ",
              this.state.endDate2
            );
            this.updateDateRangeText();
            this.fetchAndProcessData(startDate, endDate);
          }
        } catch {
          console.log("terjadi error");
        } finally {
          this.hideLoading();
        }
      });
    }
  }

  updateDateRangeText() {
    const dateRangeText = document.getElementById("dateRangeText");
    if (!dateRangeText) return;

    // Jika startDate2 dan endDate2 null, set default ke bulan ini
    if (!this.state.startDate2 && !this.state.endDate2) {
      const today = new Date();
      const startOfMonth = new Date(
        Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1)
      );
      const endOfMonth = new Date(
        Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0)
      );

      this.state.startDate2 = startOfMonth.toISOString().split("T")[0];
      this.state.endDate2 = endOfMonth.toISOString().split("T")[0];
    }

    const startText = this.state.startDate2
      ? new Date(this.state.startDate2).toLocaleDateString("id-ID", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : null;
    const endText = this.state.endDate2
      ? new Date(this.state.endDate2).toLocaleDateString("id-ID", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : null;

    let dateText;

    if (!this.state.startDate2 && !this.state.endDate2) {
      dateText = "Pilih Tanggal";
    } else if (this.state.startDate2 && this.state.endDate2) {
      dateText = `${startText} - ${endText}`;
    } else if (this.state.startDate2) {
      dateText = `${startText} - Pilih`;
    } else if (this.state.endDate2) {
      dateText = `Pilih - ${endText}`;
    }

    dateRangeText.textContent = dateText;
  }
}
StockChartRenderer.template = "owl.StockChartRenderer";

//PENANDAAA

// /** @odoo-module */

// import { registry } from "@web/core/registry";
// import { loadJS } from "@web/core/assets";
// const { Component, onWillStart, useRef, onMounted, onWillUnmount } = owl;
// import { useService } from "@web/core/utils/hooks";

// export class StockChartRenderer extends Component {
//   setup() {
//     this.chartRef = { el: null };
//     this.orm = useService("orm");
//     this.actionService = useService("action");
//     this.default_period = "thisMonth";
//     this.state = {
//       labels: [],
//       datasets: [],
//       hasData: true,
//       startDate2: null,
//       endDate2: null,
//     };

//     this.hasData = true;

//     // COUNTDOWN
//     this.refreshInterval = null;
//     this.countdownInterval = null;
//     this.countdownTime = 10;
//     this.isCountingDown = false;
//     this.chartInstance = null;
//     this.noDataMessage = null;

//     onWillStart(async () => {
//       try {
//         await loadJS("https://cdn.jsdelivr.net/npm/apexcharts");
//         await this.fetchAndProcessData();
//       } catch (error) {
//         console.error("Error loading ApexCharts or fetching data:", error);
//       }
//     });

//     onMounted(() => {
//       const periodSelection = document.getElementById('periodSelection');
//       if (periodSelection) {
//         periodSelection.value = 'thisMonth';
//       }

//       if (this.props.title === 'pie1' || this.props.title === 'pie2' || this.props.title === 'pie3') {
//         this.attachEventListeners();
//         this.filterDataByPeriod();
//       }

//       // Ensure chart element exists before rendering
//       this.chartRef.el = document.getElementById('chart');
//       if (!this.chartRef.el) {
//         console.error("Chart element not found. Make sure there's an element with id 'chart'");
//         return;
//       }

//       // Add debugging logs
//       console.log("Current state before rendering:", {
//         labels: this.state.labels,
//         datasets: this.state.datasets
//       });

//       // Render chart even with minimal data
//       this.renderChart();
//     });

//     onWillUnmount(() => {
//       this.clearIntervals();
//       if (this.chartInstance) {
//         try {
//           this.chartInstance.destroy();
//         } catch (error) {
//           console.error("Error destroying chart:", error);
//         }
//       }
//     });
//   }

//   // COUNTDOWN FUNCTIONS
//   toggleCountdown() {
//     if (this.isCountingDown) {
//       this.clearIntervals();
//       document.getElementById("timerCountdown").textContent = "";
//       const clockElement = document.getElementById("timerIcon");
//       if (clockElement) {
//         clockElement.classList.add("fas", "fa-clock");
//       }
//     } else {
//       this.isCountingDown = true;
//       this.startCountdown();
//       const clockElement = document.getElementById("timerIcon");
//       if (clockElement) {
//         clockElement.classList.remove("fas", "fa-clock");
//       }
//     }
//   }

//   clearIntervals() {
//     if (this.countdownInterval) {
//       clearInterval(this.countdownInterval);
//       this.countdownInterval = null;
//     }
//     if (this.refreshInterval) {
//       clearInterval(this.refreshInterval);
//       this.refreshInterval = null;
//     }
//     this.countdownTime = 10;
//     this.isCountingDown = false;
//   }

//   startCountdown() {
//     this.countdownTime = 10;
//     this.clearIntervals();
//     this.updateCountdownDisplay();

//     this.countdownInterval = setInterval(() => {
//       this.countdownTime--;

//       if (this.countdownTime < 0) {
//         this.countdownTime = 10;
//         if (this.state.startDate2 && this.state.endDate2) {
//           this.refreshChart(this.state.startDate2, this.state.endDate2);
//         } else {
//           this.refreshChart();
//         }
//       }

//       this.updateCountdownDisplay();
//     }, 1000);

//     this.isCountingDown = true;
//   }

//   updateCountdownDisplay() {
//     const countdownElement = document.getElementById("timerCountdown");
//     if (countdownElement) {
//       countdownElement.textContent = this.countdownTime;
//     }
//   }

//   refreshChart(startDate, endDate) {
//     console.log("Refreshing chart...");
//     this.fetchAndProcessData(startDate, endDate);
//   }

//   async fetchAndProcessData(startDate, endDate) {
//     try {
//       let pie1 = [];
//       let pie2 = [];
//       let pie3 = [];
//       const domain1 = [['picking_type_code', '=', 'internal']];
//       const domain2 = [['picking_type_code', '=', 'incoming']];
//       const domain3 = [['picking_type_code', '=', 'outgoing']];

//       // Set default startDate and endDate if not provided
//       if (!startDate) {
//         const today = new Date();
//         const firstDayOfMonth = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1));
//         startDate = firstDayOfMonth.toISOString().split('T')[0];
//       }

//       if (!endDate) {
//         const today = new Date();
//         const lastDayOfMonth = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate(), 23, 59, 59, 999));
//         endDate = lastDayOfMonth.toISOString().split('T')[0];
//       }

//       // Add date filters to domains
//       domain1.push(["create_date", ">=", startDate]);
//       domain1.push(["create_date", "<=", endDate]);
//       domain2.push(["create_date", ">=", startDate]);
//       domain2.push(["create_date", "<=", endDate]);
//       domain3.push(["create_date", ">=", startDate]);
//       domain3.push(["create_date", "<=", endDate]);

//       // Fetch data for each pie chart
//       pie1 = await this.orm.call("stock.picking", "search_read", [
//         domain1,
//         ["id", "create_date", "state"]
//       ]);

//       pie2 = await this.orm.call("stock.picking", "search_read", [
//         domain2,
//         ["id", "create_date", "state"]
//       ]);

//       pie3 = await this.orm.call("stock.picking", "search_read", [
//         domain3,
//         ["id", "create_date", "state"]
//       ]);

//       console.log("Fetched Data:", { pie1, pie2, pie3 });

//       await this.processData(pie1, pie2, pie3);
//     } catch (error) {
//       console.error("Error fetching data from Odoo:", error);
//       this.handleEmptyChart();
//     }
//   }

//   async processData(pie1, pie2, pie3) {
//     const aggregateDataByState = (data) => {
//       const stateCounts = {};
//       data.forEach((record) => {
//         const state = record.state;
//         if (!stateCounts[state]) {
//           stateCounts[state] = { count: 0, ids: [] };
//         }
//         stateCounts[state].count += 1;
//         stateCounts[state].ids.push(record.id);
//       });
//       return stateCounts;
//     };

//     if (this.props.title === "pie1") {
//       const stateCounts = aggregateDataByState(pie1);

//       this.state.labels = Object.keys(stateCounts).map(state => {
//         if (state === 'done') return 'Selesai';
//         if (state === 'assigned') return 'Proses';
//         if (state === 'draft') return 'Draft';
//         if (state === 'waiting') return 'Menunggu';
//         if (state === 'cancel') return 'Dibatalkan';
//         return state;
//       });

//       this.state.datasets = [
//         {
//           name: 'Status Count',
//           data: Object.values(stateCounts).map(item => item.count)
//         }
//       ];

//       console.log("Processed Data for pie1:", this.state.datasets);
//     }
//     else if (this.props.title === "pie2") {
//       const stateCounts = aggregateDataByState(pie2);

//       this.state.labels = Object.keys(stateCounts).map(state => {
//         if (state === 'done') return 'Selesai';
//         if (state === 'assigned') return 'Proses';
//         if (state === 'draft') return 'Draft';
//         if (state === 'waiting') return 'Menunggu';
//         if (state === 'cancel') return 'Dibatalkan';
//         return state;
//       });

//       this.state.datasets = [
//         {
//           name: 'Status Count',
//           data: Object.values(stateCounts).map(item => item.count)
//         }
//       ];

//       console.log("Processed Data for pie2:", this.state.datasets);
//     }
//     else if (this.props.title === "pie3") {
//       const stateCounts = aggregateDataByState(pie3);

//       this.state.labels = Object.keys(stateCounts).map(state => {
//         if (state === 'done') return 'Selesai';
//         if (state === 'assigned') return 'Proses';
//         if (state === 'draft') return 'Draft';
//         if (state === 'waiting') return 'Menunggu';
//         if (state === 'cancel') return 'Dibatalkan';
//         return state;
//       });

//       this.state.datasets = [
//         {
//           name: 'Status Count',
//           data: Object.values(stateCounts).map(item => item.count)
//         }
//       ];

//       console.log("Processed Data for pie3:", this.state.datasets);
//     }

//     // Always call renderChart, even if data is empty
//     this.renderChart();
//   }

//   getDiverseGradientColor(index, totalItems) {
//     const colors = [
//       "#16a34a", "#0891b2", "#22c55e", "#06b6d4",
//       "#15803d", "#0e7490", "#86efac", "#67e8f9",
//       "#166534", "#155e75"
//     ];
//     return colors[index % colors.length];
//   }

//   renderChart() {
//     // Debugging: Log chart rendering conditions
//     console.log("Rendering Chart Conditions:", {
//       chartRefEl: this.chartRef.el,
//       labels: this.state.labels,
//       labelLength: this.state.labels.length,
//       datasets: this.state.datasets,
//       datasetsValid: this.state.datasets.some(dataset => dataset.data && dataset.data.length > 0)
//     });

//     if (!this.chartRef.el) {
//       console.error("Chart element not found. Cannot render chart.");
//       this.handleEmptyChart();
//       return;
//     }

//     // Destroy existing chart instance
//     if (this.chartInstance) {
//       try {
//         this.chartInstance.destroy();
//       } catch (error) {
//         console.error("Error destroying previous chart:", error);
//       }
//     }

//     try {
//       const chartOptions = this.getChartOptions();
//       this.chartInstance = new ApexCharts(this.chartRef.el, chartOptions);
//       this.chartInstance.render();
//     } catch (error) {
//       console.error("Error rendering chart. Check data and configuration.", error);
//       this.handleEmptyChart();
//     }
//   }

//   getChartOptions() {
//     const baseOptions = {
//       series: this.state.datasets[0].data,
//       labels: this.state.labels,
//       chart: {
//         type: 'pie',
//         height: 350,
//         events: {
//           dataPointSelection: (event, chartContext, config) => {
//             this.handleChartClick(config);
//           }
//         }
//       },
//       colors: this.state.labels.map((_, index) =>
//         this.getDiverseGradientColor(index, this.state.labels.length)
//       ),
//       legend: {
//         position: this.props.type === 'bar' ? 'bottom' : 'top',
//         show: this.props.type !== 'line'
//       },
//       responsive: [
//         {
//           breakpoint: 480,
//           options: {
//             chart: {
//               width: '100%'
//             },
//             legend: {
//               position: 'bottom'
//             }
//           }
//         }
//       ]
//     };

//     // Customize options based on chart type
//     switch (this.props.type) {
//       case 'line':
//         baseOptions.stroke = { curve: 'smooth' };
//         baseOptions.fill = { type: 'solid' };
//         break;
//       case 'bar':
//         baseOptions.plotOptions = {
//           bar: {
//             horizontal: false
//           }
//         };
//         break;
//     }

//     return baseOptions;
//   }

//   convertChartType(chartjsType) {
//     const typeMap = {
//       'pie': 'pie',
//       'doughnut': 'donut',
//       'line': 'line',
//       'bar': 'bar'
//     };
//     return typeMap[chartjsType] || 'pie';
//   }

//   handleEmptyChart() {
//     if (this.chartRef.el) {
//       this.chartRef.el.style.display = 'none';
//     }

//     if (!this.noDataMessage) {
//       this.noDataMessage = document.createElement('div');
//       this.noDataMessage.style.position = 'absolute';
//       this.noDataMessage.style.top = '50%';
//       this.noDataMessage.style.left = '50%';
//       this.noDataMessage.style.transform = 'translate(-50%, -50%)';
//       this.noDataMessage.style.textAlign = 'center';
//       this.noDataMessage.style.fontSize = '16px';
//       this.noDataMessage.style.color = 'gray';
//       this.noDataMessage.style.backgroundColor = 'white';
//       this.noDataMessage.style.padding = '10px 20px';
//       this.noDataMessage.style.borderRadius = '4px';
//       this.noDataMessage.style.zIndex = '10';
//       this.noDataMessage.style.width = '200px';
//       this.noDataMessage.style.height = '50px';
//       this.noDataMessage.style.display = 'flex';
//       this.noDataMessage.style.alignItems = 'center';
//       this.noDataMessage.style.justifyContent = 'center';
//       this.noDataMessage.textContent = 'Data tidak ditemukan';

//       this.chartRef.el.parentNode.style.position = 'relative';
//       this.chartRef.el.parentNode.style.minHeight = '200px';
//       this.chartRef.el.parentNode.appendChild(this.noDataMessage);
//     }
//   }

//   handleChartClick(config) {
//     this.clearIntervals();
//     const datasetIndex = config.seriesIndex;
//     const dataPointIndex = config.dataPointIndex;

//     const dataset = this.state.datasets[0];
//     const associatedIds = dataset.associatedIds ? dataset.associatedIds[dataPointIndex] : null;

//     if (!associatedIds) {
//       console.error("No associated IDs for the clicked data point.");
//       return;
//     }
//     const resModel = 'stock.picking';

//     if (this.actionService && typeof this.actionService.doAction === 'function') {
//       this.actionService.doAction({
//         name: "Record List",
//         type: "ir.actions.act_window",
//         res_model: resModel,
//         view_mode: "list",
//         views: [[false, "list"]],
//         target: "current",
//         domain: [["id", "in", associatedIds]],
//       }).then(() => {
//         console.log(`Redirected to list view of ${resModel} for selected IDs.`);
//       }).catch(error => {
//         console.error("Error in actionService.doAction redirect:", error);
//       });
//     } else {
//       console.error('actionService.doAction is not a function or actionService is undefined:', this.actionService);
//     }
//   }

//   attachEventListeners() {
//     const startDateInput = document.getElementById("startDate");
//     const endDateInput = document.getElementById("endDate");
//     const timerButton = document.getElementById("timerButton");
//     this.updateDateRangeText();
//     if (startDateInput && endDateInput) {
//       startDateInput.addEventListener("change", () => this.filterData());
//       endDateInput.addEventListener("change", () => this.filterData());
//     } else {
//       console.error("Date input elements not found");
//     }

//     if (timerButton) {
//       timerButton.addEventListener("click", this.toggleCountdown.bind(this));
//     } else {
//       console.error("Timer button element not found");
//     }

//     const datePickerButton = document.getElementById("datePickerButton");
//     const datePickerContainer = document.getElementById("datePickerContainer");

//     if (datePickerButton && datePickerContainer) {
//       datePickerButton.addEventListener("click", (event) => {
//         event.stopPropagation(); // Prevent event from bubbling up
//         // Toggle the display property
//         datePickerContainer.style.display = datePickerContainer.style.display === "flex" ? "none" : "flex";
//       });
//     } else {
//       console.error("Date picker button or container element not found");
//     }

//     // Close the date picker if clicking outside of it
//     document.addEventListener("click", (event) => {
//       if (
//         datePickerContainer &&
//         !datePickerContainer.contains(event.target) &&
//         !datePickerButton.contains(event.target)
//       ) {
//         datePickerContainer.style.display = "none";
//       }
//     });

//   }

//   filterData() {
//     var startDate = document.getElementById("startDate")?.value;
//     var endDate = document.getElementById("endDate")?.value;

//     if (startDate && endDate) {
//       this.fetchAndProcessData(startDate, endDate);
//       this.state.startDate2 = startDate;
//       this.state.endDate2 = endDate;
//       this.updateDateRangeText(); // Perbarui teks pada tombol
//     } else {
//       this.fetchAndProcessData();
//     }
//   }

//   filterDataByPeriod() {
//     const startDateInput = document.getElementById('startDate');
//     const endDateInput = document.getElementById('endDate');
//     const periodSelection = document.getElementById('periodSelection');

//     // Langsung eksekusi logic tanpa mendaftarkan event listener baru
//     const today = new Date();
//     let startDate;
//     let endDate;
//     const defaultPeriod = 'thisMonth'; // Default ke Bulan Ini
//     periodSelection.value = defaultPeriod; // Pilih default period pada dropdown

//     if (periodSelection) {
//       periodSelection.addEventListener('change', () => {
//         switch (periodSelection.value) {
//           case 'today':
//             // Hari Ini
//             startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate(), 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate(), 23, 59, 59, 999));
//             break;
//           case 'yesterday':
//             // Kemarin
//             startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - 1, 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - 1, 23, 59, 59, 999));
//             break;
//           case 'thisWeek':
//             // Minggu Ini
//             const startOfWeek = today.getUTCDate() - today.getUTCDay(); // Set ke hari Minggu
//             startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), startOfWeek, 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), startOfWeek + 6, 23, 59, 59, 999));
//             break;
//           case 'lastWeek':
//             // Minggu Lalu
//             const lastWeekStart = today.getUTCDate() - today.getUTCDay() - 7; // Minggu sebelumnya
//             startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), lastWeekStart, 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), lastWeekStart + 6, 23, 59, 59, 999));
//             break;
//           case 'thisMonth':
//             // Bulan Ini
//             startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0, 23, 59, 59, 999));
//             break;
//           case 'lastMonth':
//             // Bulan Lalu
//             startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() - 1, 1, 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 0, 23, 59, 59, 999));
//             break;
//           case 'thisYear':
//             // Tahun Ini
//             startDate = new Date(Date.UTC(today.getUTCFullYear(), 0, 1, 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear(), 11, 31, 23, 59, 59, 999));
//             break;
//           case 'lastYear':
//             // Tahun Lalu
//             startDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 0, 1, 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 11, 31, 23, 59, 59, 999));
//             break;
//           default:
//             // Default ke Bulan Ini jika tidak ada yang cocok
//             startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 0, 1));
//             endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0, 23, 59, 59, 999));
//         }

//         // Update the input fields and the state
//         if (startDate && endDate) {
//           this.state.startDate2 = startDate.toISOString().split('T')[0];
//           this.state.endDate2 = endDate.toISOString().split('T')[0];
//           startDateInput.value = this.state.startDate2;
//           endDateInput.value = this.state.endDate2;
//           console.log("dates down: ", startDate, "& ", endDate);
//           console.log("dates down state: ", this.state.startDate2, "& ", this.state.endDate2);
//           this.updateDateRangeText();
//           this.fetchAndProcessData(startDate, endDate);
//         }
//       });
//     }
//   }

//   updateDateRangeText() {
//     const dateRangeText = document.getElementById("dateRangeText");
//     if (!dateRangeText) return;

//     // Jika startDate2 dan endDate2 null, set default ke bulan ini
//     if (!this.state.startDate2 && !this.state.endDate2) {
//       const today = new Date();
//       const startOfMonth = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1));
//       const endOfMonth = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0));

//       this.state.startDate2 = startOfMonth.toISOString().split('T')[0];
//       this.state.endDate2 = endOfMonth.toISOString().split('T')[0];
//     }

//     const startText = this.state.startDate2
//       ? new Date(this.state.startDate2).toLocaleDateString('id-ID', {
//         day: 'numeric',
//         month: 'short',
//         year: 'numeric',
//       })
//       : null;
//     const endText = this.state.endDate2
//       ? new Date(this.state.endDate2).toLocaleDateString('id-ID', {
//         day: 'numeric',
//         month: 'short',
//         year: 'numeric',
//       })
//       : null;

//     let dateText;

//     if (!this.state.startDate2 && !this.state.endDate2) {
//       dateText = "Pilih Tanggal";
//     } else if (this.state.startDate2 && this.state.endDate2) {
//       dateText = `${startText} - ${endText}`;
//     } else if (this.state.startDate2) {
//       dateText = `${startText} - Pilih`;
//     } else if (this.state.endDate2) {
//       dateText = `Pilih - ${endText}`;
//     }

//     dateRangeText.textContent = dateText;
//   }

// }

// StockChartRenderer.template = "owl.StockChartRenderer";
