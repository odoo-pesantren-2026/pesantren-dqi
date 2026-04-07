/** @odoo-module */

import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

export class KeamananChartRenderer extends Component {
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
    // console.log("hasdata onstart: ", this.state.hasData);

    this.hasData = true;
    // console.log("thishasdata onstart: ", this.hasData);

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
      if (this.props.title === "line1") {
        this.attachEventListeners();
        this.filterDataByPeriod();
      }
      if (this.props.title === "pie2") {
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
          // console.log(
          //   "dates state: ",
          //   this.state.startDate2,
          //   "& ",
          //   this.state.endDate2
          // );
          const startDate = this.state.startDate2;
          const endDate = this.state.endDate2;
          // console.log("dates: ", startDate, "& ", endDate);
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
    this.fetchAndProcessData(startDate, endDate);
  }

  async fetchAndProcessData(startDate, endDate) {
    this.showLoading();
    try {
      // let pie1 = {
      //   Draft: 0,
      //   Check: 0,
      //   Approved: 0,
      //   Rejected: 0,
      //   Permission: 0,
      //   Return: 0,
      // };
      // let bar1 = {};
      let line1 = [];
      let pie2 = [];
      // Set default startDate dan endDate jika tidak diisi
      if (!startDate) {
        const today = new Date();
        const firstDay = new Date(
          Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1)
        );
        startDate = firstDay.toISOString().split("T")[0]; // First day of the current month
      }

      if (!endDate) {
        const today = new Date();
        const lastDay = new Date(
          Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0)
        );
        endDate = lastDay.toISOString().split("T")[0]; // Last day of the current month
      }

      let domain = [
        ["tgl_ijin", ">=", startDate],
        ["tgl_ijin", "<=", endDate],
      ];

      let domain1 = [
        ["tgl_ijin", ">=", startDate],
        ["tgl_ijin", "<=", endDate],
      ];

      domain.push("|", ["state", "=", "Return"], ["state", "=", "Permission"]);

      domain.push();

      line1 = await this.orm.call("cdn.perijinan", "search_read", [
        domain,
        ["id", "tgl_ijin", "state"],
      ]);

      pie2 = await this.orm.call("cdn.perijinan", "search_read", [
        domain1,
        ["id", "tgl_ijin", "state", "keperluan"],
      ]);

      // izinData.forEach((record) => {
      //   if (record.state && pieData.hasOwnProperty(record.state)) {
      //     pieData[record.state]++;
      //   }
      //   if (record.lama_ijin) {
      //     if (!barData[record.lama_ijin]) {
      //       barData[record.lama_ijin] = 0;
      //     }
      //     barData[record.lama_ijin]++;
      //   }
      // });

      // console.log("Pie Data: ", pie1);
      // console.log("Pie Data2", pie2);

      // Process and render the chart data
      // this.renderPieChart(pieData);
      // this.renderBarChart(barData);
      await this.processData(line1, pie2);
    } catch (error) {
      console.error("Error fetching data from Odoo:", error);
    } finally {
      this.hideLoading();
    }
  }

  async processData(line1, pie2) {
    // Fungsi agregasi tetap dipertahankan
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

    const aggregateDataByKeperluan = (data) => {
      const stateCounts = {};
      data.forEach((record) => {
        const state = record.keperluan;
        if (!stateCounts[state]) {
          stateCounts[state] = { count: 0, ids: [] };
        }
        stateCounts[state].count += 1;
        stateCounts[state].ids.push(record.id);
      });
      return stateCounts;
    };

    // Contoh untuk line1 (Masuk/Keluar)
    if (this.props.title === "line1") {
      const kembaliData = line1.filter((record) => record.state === "Return");
      const keluarData = line1.filter(
        (record) => record.state === "Permission"
      );

      // Tambahkan fungsi untuk mengumpulkan ID berdasarkan periode
      const groupIdsByDate = (data) => {
        const result = {};
        data.forEach((record) => {
          // Ambil tanggal dari tgl_ijin dan format sebagai string
          const date = new Date(record.tgl_ijin);
          const adjustedDate = new Date(date);
          adjustedDate.setDate(date.getDate() + 1);

          // Format sebagai YYYY-MM-DD
          const dateStr = adjustedDate.toISOString().split("T")[0];

          console.log("Data setelah penyesuaian:", dateStr);
          if (!result[dateStr]) {
            result[dateStr] = [];
          }
          result[dateStr].push(record.id);
        });
        return result;
      };

      const kembaliCounts = this.groupDataByPeriod(kembaliData);
      const keluarCounts = this.groupDataByPeriod(keluarData);

      // Grup ID berdasarkan periode
      const kembaliIds = groupIdsByDate(kembaliData);
      const keluarIds = groupIdsByDate(keluarData);

      const allPeriods = [
        ...new Set([
          ...Object.keys(kembaliCounts),
          ...Object.keys(keluarCounts),
        ]),
      ].sort();

      const formattedLabels = allPeriods.map((dateStr) => {
        // Parse tanggal dengan menambahkan offset untuk Indonesia
        const [year, month, day] = dateStr.split("-").map(Number);
        const date = new Date(Date.UTC(year, month - 1, day));
        date.setTime(date.getTime() + 7 * 60 * 60 * 1000); // Tambahkan 7 jam (WIB)

        const dayNum = date.getUTCDate();
        const monthName = date.toLocaleString("id-ID", {
          month: "long",
          timeZone: "Asia/Jakarta",
        });
        const yearNum = date.getUTCFullYear();

        return `${dayNum} ${monthName} ${yearNum}`;
      });

      this.state.labels = formattedLabels;
      this.state.datasets = [
        {
          label: "Masuk",
          data: allPeriods.map((period) => kembaliCounts[period] || 0),
          borderColor: "rgba(54, 162, 235, 1)",
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          tension: 0.3,
          fill: true,

          associated_ids: allPeriods.map((period) => kembaliIds[period] || []),
        },
        {
          label: "Keluar",
          data: allPeriods.map((period) => keluarCounts[period] || 0),
          borderColor: "rgba(75, 192, 75, 1)",
          backgroundColor: "rgba(75, 192, 75, 0.2)",
          tension: 0.3,
          fill: true,
          // Tambahkan ID yang terkait untuk setiap titik data
          associated_ids: allPeriods.map((period) => keluarIds[period] || []),
        },
      ];
    } else if (this.props.title === "pie2") {
      const stateCounts = aggregateDataByKeperluan(pie2);

      this.state.labels = Object.keys(stateCounts).map((label) =>
        label.replace(/^\d+,\s*/, "")
      );

      this.state.datasets = [
        {
          label: "Total Siswa Ijin",
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

      // console.log("Processed Data for pie2:", this.state.datasets);s
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

      // console.log("Processed Data for pie3:", this.state.datasets);
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

  // groupDataByPeriod(data) {
  //   const result = {};

  //   data.forEach((record) => {
  //     const date = new Date(record.tgl_ijin);
  //     let periodKey;

  //     let periodSelection = document.getElementById("periodSelection");

  //     if (!periodSelection) {
  //       periodSelection = "thisMonth";
  //     }

  //     if (periodSelection) {
  //       periodKey = date.toISOString().split("T")[0];
  //     }

  //     console.log("Periode yang dipilih", periodSelection.value);

  //     if (!result[periodKey]) {
  //       result[periodKey] = 0;
  //     }

  //     result[periodKey] += 1;
  //   });

  //   return result;
  // }

  groupDataByPeriod(data) {
    const result = {};

    data.forEach((record) => {
      // Ambil tanggal dari tgl_ijin
      const utcDate = new Date(record.tgl_ijin);

      // Konversi ke zona waktu Indonesia (WIB = UTC+7)
      const wibOffset = 7 * 60 * 60 * 1000; // 7 jam dalam milidetik
      const wibDate = new Date(utcDate.getTime() + wibOffset);

      // Format sebagai YYYY-MM-DD
      const year = wibDate.getUTCFullYear();
      const month = String(wibDate.getUTCMonth() + 1).padStart(2, "0");
      const day = String(wibDate.getUTCDate()).padStart(2, "0");
      const periodKey = `${year}-${month}-${day}`;

      if (!result[periodKey]) {
        result[periodKey] = 0;
      }
      result[periodKey] += 1;
    });

    return result;
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
    } else {
      this.state.hasData = false;
    }
  }

  renderChart() {
    if (!this.chartRef.el) {
      console.error("Chart element not found");
      return;
    }

    const containsData =
      this.state.labels &&
      this.state.labels.length > 0 &&
      this.state.datasets &&
      this.state.datasets.length > 0;
    this.hasData = null;

    if (!containsData) {
      this.hasData = false;
      // Kode penanganan tidak ada data
      if (this.chartRef.el) {
        this.chartRef.el.style.display = "none";
      }

      if (!this.noDataMessage) {
        this.noDataMessage = document.createElement("div");
        // Styling pesan tidak ada data
        this.noDataMessage.style.position = "absolute";
        this.noDataMessage.style.top = "50%";
        this.noDataMessage.style.left = "50%";
        this.noDataMessage.style.transform = "translate(-50%, -50%)";
        this.noDataMessage.style.textAlign = "center";
        this.noDataMessage.style.fontSize = "16px";
        this.noDataMessage.style.color = "gray";
        this.noDataMessage.style.backgroundColor = "white";
        this.noDataMessage.style.padding = "10px 20px";
        this.noDataMessage.style.borderRadius = "4px";
        this.noDataMessage.style.zIndex = "10";
        this.noDataMessage.style.width = "200px";
        this.noDataMessage.style.height = "50px";
        this.noDataMessage.style.display = "flex";
        this.noDataMessage.style.alignItems = "center";
        this.noDataMessage.style.justifyContent = "center";
        this.noDataMessage.textContent = "Data tidak ditemukan";

        this.chartRef.el.parentNode.style.position = "relative";
        this.chartRef.el.parentNode.style.minHeight = "200px";
        this.chartRef.el.parentNode.appendChild(this.noDataMessage);
      }
      return;
    } else {
      this.hasData = true;
      if (this.noDataMessage) {
        this.noDataMessage.remove();
        this.noDataMessage = null;
      }
    }

    if (this.chartRef.el) {
      this.chartRef.el.style.display = "block";
    }

    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }

    try {
      const chartConfig = {
        type: this.props.type,
        data: {
          labels: this.state.labels,
          datasets: this.state.datasets,
        },
        options: {
          onClick: (evt) => this.handleChartClick(evt),
          maintainAspectRatio: false,
          responsive: true,
          plugins: {
            legend: {
              display: true,
              position: "top",
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                stepSize: 1,
                precision: 0,
              },
            },
          },
        },
      };

      this.chartInstance = new Chart(this.chartRef.el, chartConfig);
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
      const pointIndex = firstPoint.index;

      // Cek dataset ada
      if (!this.state.datasets || !this.state.datasets[datasetIndex]) {
        console.error("Dataset not found for index:", datasetIndex);
        return;
      }

      const dataset = this.state.datasets[datasetIndex];

      // Cek apakah associated_ids ada dan valid untuk index titik data ini
      if (
        !dataset.associated_ids ||
        !dataset.associated_ids[pointIndex] ||
        dataset.associated_ids[pointIndex].length === 0
      ) {
        console.log(
          "No associated IDs for this data point. Dataset:",
          dataset,
          "Point index:",
          pointIndex
        );
        // Jangan menampilkan error ke console, tampilkan pesan ke pengguna
        this.env.services.notification.add(
          "Tidak ada data terkait untuk titik ini.",
          { type: "warning" }
        );
        return;
      }

      const associatedIds = dataset.associated_ids[pointIndex];
      const resModel = "cdn.perijinan";

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
        // console.log("terjadi error");s
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
            // console.log("dates down: ", startDate, "& ", endDate);
            // console.log(
            //   "dates down state: ",
            //   this.state.startDate2,
            //   "& ",
            //   this.state.endDate2
            // );
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
KeamananChartRenderer.template = "owl.KeamananChartRenderer";
