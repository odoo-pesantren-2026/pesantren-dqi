/** @odoo-module */

import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

export class WalletChartRenderer extends Component {
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
      let line1 = [];

      if (!startDate) {
        const today = new Date();
        const firstDay = new Date(
          Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1)
        );
        startDate = firstDay.toISOString().split("T")[0];
      }

      if (!endDate) {
        const today = new Date();
        const lastDay = new Date(
          Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0)
        );
        endDate = lastDay.toISOString().split("T")[0];
      }

      // let domain = [
      //   ["tgl_ijin", ">=", startDate],
      //   ["tgl_ijin", "<=", endDate],
      // ];

      // domain.push("|", ["state", "=", "Return"], ["state", "=", "Permission"]);

      line1 = await this.orm.call("cdn.siswa", "search_read", [
        [],
        ["saldo_uang_saku", "name"],
      ]);

      await this.processData(line1);
    } catch (error) {
      console.error("Error fetching data from Odoo:", error);
    } finally {
      this.hideLoading();
    }
  }

  async processData(line1) {
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

    if (this.props.title === "line1") {
      const validData = line1.filter(
        (record) =>
          record.saldo_uang_saku !== null &&
          record.saldo_uang_saku !== undefined &&
          record.saldo_uang_saku > 0
      );
      const top10Students = validData
        .sort((a, b) => b.saldo_uang_saku - a.saldo_uang_saku)
        .slice(0, 10);

      const labels = top10Students.map((student) => student.name);
      const saldoData = top10Students.map((student) => student.saldo_uang_saku);
      const studentIds = top10Students.map((student) => student.id);

      const formattedLabels = labels;

      this.state.labels = formattedLabels;
      this.state.datasets = [
        {
          label: "Saldo Uang Saku",
          data: saldoData,
          // Opsi 1: Gradasi Hijau (Paling Konsisten)
          backgroundColor: saldoData.map((_, index) => {
            const monochromeGreen = [
              "rgba(34, 197, 94, 0.9)", // Hijau primary
              "rgba(34, 197, 94, 0.8)", // Hijau primary (lighter)
              "rgba(34, 197, 94, 0.7)", // Hijau primary (lighter)
              "rgba(34, 197, 94, 0.6)", // Hijau primary (lighter)
              "rgba(34, 197, 94, 0.5)", // Hijau primary (lighter)
              "rgba(22, 163, 74, 0.9)", // Hijau gelap
              "rgba(22, 163, 74, 0.8)", // Hijau gelap (lighter)
              "rgba(74, 222, 128, 0.8)", // Hijau terang
              "rgba(16, 185, 129, 0.8)", // Hijau emerald
              "rgba(132, 204, 22, 0.8)", // Hijau lime
            ];
            return monochromeGreen[index % monochromeGreen.length];
          }),
          borderColor: saldoData.map((_, index) => {
            const monochromeGreen = [
              "rgba(34, 197, 94, 1)", // Hijau primary
              "rgba(34, 197, 94, 1)", // Hijau primary
              "rgba(34, 197, 94, 1)", // Hijau primary
              "rgba(34, 197, 94, 1)", // Hijau primary
              "rgba(34, 197, 94, 1)", // Hijau primary
              "rgba(22, 163, 74, 1)", // Hijau gelap
              "rgba(22, 163, 74, 1)", // Hijau gelap
              "rgba(74, 222, 128, 1)", // Hijau terang
              "rgba(16, 185, 129, 1)", // Hijau emerald
              "rgba(132, 204, 22, 1)", // Hijau lime
            ];
            return monochromeGreen[index % monochromeGreen.length];
          }),
          borderWidth: 1,
          associated_ids: studentIds, // Untuk keperluan click handler
          full_data: top10Students, // Simpan data lengkap untuk referensi
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
          tooltip: {
            callbacks: {
              label: function (context) {
                const value = context.parsed.y;
                return `${context.dataset.label}: Rp ${value.toLocaleString(
                  "id-ID"
                )}`;
              },
            },
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: function (value) {
                  return "Rp " + value.toLocaleString("id-ID");
                },
              },
            },
            x: {
              title: {
                display: true,
                text: "Nama Santri",
              },
              ticks: {
                maxRotation: 45,
                minRotation: 45,
                callback: function (value, index, values) {
                  const label = this.getLabelForValue(value);
                  if (label.length > 12) {
                    return label.substring(0, 12) + "...";
                  }
                  return label;
                },
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

  // handleChartClick(evt) {
  //   this.clearIntervals();
  //   const activePoints = this.chartInstance.getElementsAtEventForMode(
  //     evt,
  //     "nearest",
  //     { intersect: true },
  //     false
  //   );

  //   if (activePoints.length > 0) {
  //     const firstPoint = activePoints[0];
  //     const datasetIndex = firstPoint.datasetIndex;
  //     const pointIndex = firstPoint.index;

  //     // Cek dataset ada
  //     if (!this.state.datasets || !this.state.datasets[datasetIndex]) {
  //       console.error("Dataset not found for index:", datasetIndex);
  //       return;
  //     }

  //     const dataset = this.state.datasets[datasetIndex];

  //     if (
  //       !dataset.associated_ids ||
  //       !dataset.associated_ids[pointIndex] ||
  //       dataset.associated_ids[pointIndex].length === 0
  //     ) {
  //       console.log(
  //         "No associated IDs for this data point. Dataset:",
  //         dataset,
  //         "Point index:",
  //         pointIndex
  //       );
  //       // Jangan menampilkan error ke console, tampilkan pesan ke pengguna
  //       this.env.services.notification.add(
  //         "Tidak ada data terkait untuk titik ini.",
  //         { type: "warning" }
  //       );
  //       return;
  //     }

  //     const associatedIds = dataset.associated_ids[pointIndex];
  //     const resModel = "cdn.perijinan";

  //     if (
  //       this.actionService &&
  //       typeof this.actionService.doAction === "function"
  //     ) {
  //       this.actionService
  //         .doAction({
  //           name: "Record List",
  //           type: "ir.actions.act_window",
  //           res_model: resModel,
  //           view_mode: "list",
  //           views: [[false, "list"]],
  //           target: "current",
  //           domain: [["id", "in", associatedIds]],
  //         })
  //         .then(() => {
  //           console.log(
  //             `Redirected to list view of ${resModel} for selected IDs.`
  //           );
  //         })
  //         .catch((error) => {
  //           console.error("Error in actionService.doAction redirect:", error);
  //         });
  //     } else {
  //       console.error(
  //         "actionService.doAction is not a function or actionService is undefined:",
  //         this.actionService
  //       );
  //     }
  //   }
  // }

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

      if (!this.state.datasets || !this.state.datasets[datasetIndex]) {
        console.error("Dataset not found for index:", datasetIndex);
        return;
      }

      const dataset = this.state.datasets[datasetIndex];

      if (
        !dataset.associated_ids ||
        !dataset.associated_ids[pointIndex] ||
        typeof dataset.associated_ids[pointIndex] !== "number"
      ) {
        console.log(
          "No associated ID for this data point. Dataset:",
          dataset,
          "Point index:",
          pointIndex
        );

        this.env.services.notification.add(
          "Tidak ada data santri untuk bar ini.",
          { type: "warning" }
        );
        return;
      }

      const santriId = dataset.associated_ids[pointIndex];

      const santriName =
        dataset.full_data && dataset.full_data[pointIndex]
          ? dataset.full_data[pointIndex].name
          : "Detail Santri";

      if (
        this.actionService &&
        typeof this.actionService.doAction === "function"
      ) {
        this.actionService
          .doAction({
            name: `Detail Santri - ${santriName}`,
            type: "ir.actions.act_window",
            res_model: "cdn.siswa",
            res_id: santriId,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
          })
          .then(() => {
            console.log(
              `Opened form view for santri ID: ${santriId} (${santriName})`
            );
          })
          .catch((error) => {
            console.error("Error opening santri form:", error);
            this.actionService.doAction({
              name: `Santri - ${santriName}`,
              type: "ir.actions.act_window",
              res_model: "cdn.siswa",
              view_mode: "list,form",
              views: [
                [false, "list"],
                [false, "form"],
              ],
              target: "current",
              domain: [["id", "=", santriId]],
            });
          });
      } else {
        console.error(
          "actionService.doAction is not available:",
          this.actionService
        );

        if (this.actionService) {
          this.actionService.doAction("pesantren_kesantrian.santri_action", {
            additionalContext: {
              search_default_id: santriId,
            },
          });
        }
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
WalletChartRenderer.template = "owl.WalletChartRenderer";
