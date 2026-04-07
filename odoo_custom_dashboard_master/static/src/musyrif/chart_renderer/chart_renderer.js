/** @odoo-module */
import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
const {
  Component,
  onWillStart,
  useRef,
  onMounted,
  onWillUnmount,
  onWillUpdateProps,
} = owl;
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class MusyrifChartRenderer extends Component {
  static props = {
    type: { type: String },
    period: { type: String, optional: true },
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.chartRef = useRef("chart");
    this.areaChartRef = useRef("areaChart");
    this.loadingOverlayRef = useRef("loadingOverlay");
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      chartData: { series: [], labels: [], stateIds: {} },
      uangSakuData: { dates: [], masuk: [], keluar: [], rawData: {} },
      selectedPeriod: this.props.period || "all",
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
      isLoading: false,
      totalPermissions: 0,
      isFiltered: !!(this.props.startDate && this.props.endDate),
    };
    this.refreshInterval = null;
    this.countdownInterval = null;
    this.areaChartInstance = null;
    this.countdownTime = 10;
    this.isCountingDown = false;

    if (this.props.startDate && this.props.endDate) {
      this.state.currentStartDate = this.props.startDate;
      this.state.currentEndDate = this.props.endDate;
    }

    onWillUpdateProps(async (nextProps) => {
      if (
        nextProps.startDate !== this.props.startDate ||
        nextProps.endDate !== this.props.endDate
      ) {
        this.showLoading();
        try {
          this.state.currentStartDate = nextProps.startDate;
          this.state.currentEndDate = nextProps.endDate;
          this.state.isFiltered = !!(nextProps.startDate && nextProps.endDate);

          await Promise.all([
            this.fetchData(
              this.state.currentStartDate,
              this.state.currentEndDate
            ),
            this.fetchUangSakuData(
              this.state.currentStartDate,
              this.state.currentEndDate
            ),
          ]);
        } catch (error) {
          console.error("Error updating props:", error);
        } finally {
          this.hideLoading();
        }
      }
    });


    onWillStart(async () => {
      this.showLoading();
      try {
        await loadJS("https://cdn.jsdelivr.net/npm/apexcharts");
        await Promise.all([
          this.fetchData(
            this.state.currentStartDate,
            this.state.currentEndDate
          ),
          this.fetchUangSakuData(
            this.state.currentStartDate,
            this.state.currentEndDate
          ),
        ]);
      } catch (error) {
        console.error("Error in initial data fetch:", error);
      } finally {
        this.hideLoading();
      }
    });

    onMounted(() => {
      this.renderChart();
      this.renderAreaChart();
      this.attachEventListeners();
    });

    onWillUnmount(() => {
      this.cleanup();
      if (this.loadingOverlay && document.body.contains(this.loadingOverlay)) {
        document.body.removeChild(this.loadingOverlay);
      }
    });
  }

  showLoading() {
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
    this.loadingOverlay.style.display = "flex";
    this.state.isLoading = true;
  }

  hideLoading() {
    if (this.loadingOverlay) {
      this.loadingOverlay.style.display = "none";
    }
    this.state.isLoading = false;
  }

  cleanup() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }
    if (this.areaChartInstance) {
      this.areaChartInstance.destroy();
      this.areaChartInstance = null;
    }
    this.clearIntervals();

    if (this.loadingOverlay && document.body.contains(this.loadingOverlay)) {
      document.body.removeChild(this.loadingOverlay);
      this.loadingOverlay = null;
    }
  }

  toggleCountdown() {
    if (this.isCountingDown) {
      this.clearIntervals();
      const timerIcon = document.getElementById("timerIcon");
      const timerCountdown = document.getElementById("timerCountdown");
      if (timerIcon) timerIcon.className = "fas fa-clock";
      if (timerCountdown) timerCountdown.textContent = "";
    } else {
      this.startCountdown();
      const timerIcon = document.getElementById("timerIcon");
      if (timerIcon) timerIcon.className = "fas fa-stop";
    }
    this.isCountingDown = !this.isCountingDown;
  }

  startCountdown() {
    this.countdownTime = 10;
    this.updateCountdownDisplay();

    this.countdownInterval = setInterval(() => {
      this.countdownTime--;
      if (this.countdownTime < 0) {
        this.countdownTime = 10;
        this.refreshChart();
      }
      this.updateCountdownDisplay();
    }, 1000);
  }

  updateCountdownDisplay() {
    const timerCountdown = document.getElementById("timerCountdown");
    if (timerCountdown) timerCountdown.textContent = this.countdownTime;
  }

  async refreshChart() {
    this.showLoading();

    const startDate = this.state.isFiltered ? this.state.currentStartDate : null;
    const endDate = this.state.isFiltered ? this.state.currentEndDate : null;

    try {
      await Promise.all([
        this.fetchData(startDate, endDate),
        this.fetchUangSakuData(startDate, endDate),
      ]);

      // Update donut chart
      if (this.chartInstance) {
        this.chartInstance.updateOptions({
          series: this.state.chartData.series,
          labels: this.state.chartData.labels,
        });
      }

      // Update area chart
      if (this.areaChartInstance) {
        const masuk = this.state.uangSakuData.masuk.map((v) => Number(v) || 0);
        const keluar = this.state.uangSakuData.keluar.map((v) => Number(v) || 0);

        this.areaChartInstance.updateOptions({
          series: [
            { name: "Uang Masuk", data: masuk },
            { name: "Uang Keluar", data: keluar },
          ],
          xaxis: {
            categories: this.state.uangSakuData.dates.map((date) =>
              this.formatDate(date)
            ),
          },
        });
      }
    } catch (error) {
      console.error("Error refreshing charts:", error);
    } finally {
      this.hideLoading();
    }
  }

  clearIntervals() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);
    if (this.refreshInterval) clearInterval(this.refreshInterval);
  }

  attachEventListeners() {
    const timerButton = document.getElementById("timerButton");
    if (timerButton) {
      timerButton.addEventListener("click", this.toggleCountdown.bind(this));
    }

    const startDateInput = document.querySelector('input[name="start_date"]');
    const endDateInput = document.querySelector('input[name="end_date"]');

    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", () => this.handleDateFilter());
      endDateInput.addEventListener("change", () => this.handleDateFilter());
    }
  }

  async handleDateFilter() {
    this.clearIntervals();
    this.showLoading();

    const startDateInput = document.querySelector('input[name="start_date"]');
    const endDateInput = document.querySelector('input[name="end_date"]');

    if (startDateInput && endDateInput) {
      const startDate = startDateInput.value;
      const endDate = endDateInput.value;

      if (startDate && endDate) {
        const formattedStartDate = this.formatDateToOdoo(startDate);
        const formattedEndDate = this.formatDateToOdoo(endDate);

        this.state.currentStartDate = formattedStartDate;
        this.state.currentEndDate = formattedEndDate;
        this.state.isFiltered = true;

        try {
          await Promise.all([
            this.fetchData(formattedStartDate, formattedEndDate),
            this.fetchUangSakuData(formattedStartDate, formattedEndDate),
          ]);
        } catch (error) {
          console.error("Error in date filter:", error);
        } finally {
          this.hideLoading();
        }
      }
    }

    if (this.isCountingDown) {
      this.startCountdown();
    }
  }

  formatDateToOdoo(dateString) {
    const date = new Date(dateString);
    return date.toISOString().split(".")[0] + "Z";
  }

  formatDate(dateString) {
    const date = new Date(dateString);
    const months = [
      "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
      "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
    ];
    const day = String(date.getDate()).padStart(2, "0");
    const month = months[date.getMonth()];
    const year = date.getFullYear();
    return `${day} ${month} ${year}`;
  }

  getStateColor(state) {
    const colorMap = {
      Draft: "#16a34a",
      Check: "#dc2626",
      Approved: "#737373",
      Rejected: "#3b82f6",
    };
    return colorMap[state] || "#cbd5e1";
  }

  getChartConfig() {
    const states = ["Draft", "Check", "Approved", "Rejected"];
    const colors = states.map((state) => this.getStateColor(state));

    return {
      chart: {
        type: "donut",
        height: "80%",
        fontFamily: "Inter, sans-serif",
        background: "transparent",
        animations: {
          enabled: true,
          easing: "easeinout",
          speed: 800,
          animateGradually: { enabled: true, delay: 150 },
          dynamicAnimation: { enabled: true, speed: 350 },
        },
        events: {
          dataPointSelection: (event, chartContext, config) => {
            const dataPointIndex = config.dataPointIndex;
            if (dataPointIndex === -1) return;

            const selectedLabel = this.state.chartData.labels[dataPointIndex];
            const associatedIds = this.state.chartData.stateIds[selectedLabel];

            if (!associatedIds || associatedIds.length === 0) return;

            this.actionService.doAction({
              type: "ir.actions.act_window",
              target: "current",
              name: "Perijinan",
              res_model: "cdn.perijinan",
              view_mode: "list,form",
              views: [[false, "list"], [false, "form"]],
              domain: [["id", "in", associatedIds]],
            });
          },
        },
      },
      series: [],
      labels: states.map((state) => this.getStateLabel(state)),
      colors: colors,
      plotOptions: {
        pie: {
          donut: {
            size: "65%",
            labels: {
              show: true,
              name: { show: true, fontSize: "22px", offsetY: -10, color: "#1f2937" },
              value: { show: true, fontSize: "16px", color: "#1f2937", formatter: (val) => `${val} Siswa` },
              total: {
                show: true,
                label: "Total Siswa",
                formatter: (w) => `${w.globals.seriesTotals.reduce((a, b) => a + b, 0)} Siswa`,
              },
            },
          },
        },
      },
      stroke: { width: 0 },
      legend: { position: "bottom", horizontalAlign: "center", fontSize: "14px" },
      tooltip: { enabled: true, y: { formatter: (value) => `${value} Siswa` } },
      noData: {
        text: "Tidak ada data",
        style: { fontSize: "16px", fontFamily: "Inter" },
      },
    };
  }

  getAreaChartConfig() {
    return {
      chart: {
        type: "area",
        height: "100%",
        stacked: true,
        toolbar: { show: false },
        events: {
          click: (event, chartContext, config) => {
            if (config.dataPointIndex === undefined) return;
            const date = this.state.uangSakuData.dates[config.dataPointIndex];
            if (!date) return;

            const start = new Date(date);
            start.setHours(0, 0, 0, 0);
            const end = new Date(date);
            end.setHours(23, 59, 59, 999);

            const domain = [
              ["tgl_transaksi", ">=", start.toISOString().split(".")[0]],
              ["tgl_transaksi", "<=", end.toISOString().split(".")[0]],
              ["jns_transaksi", "=", config.seriesIndex === 0 ? "masuk" : "keluar"],
            ];

            this.actionService.doAction({
              type: "ir.actions.act_window",
              name: `Data Uang ${config.seriesIndex === 0 ? "Masuk" : "Keluar"}`,
              res_model: "cdn.uang_saku",
              view_mode: "list,form",
              views: [[false, "list"], [false, "form"]],
              target: "current",
              domain: domain,
              context: { create: false },
            });
          },
        },
      },
      colors: ["#16a34a", "#dc2626"],
      series: [
        { name: "Uang Masuk", data: this.state.uangSakuData.masuk || [] },
        { name: "Uang Keluar", data: this.state.uangSakuData.keluar || [] },
      ],
      xaxis: {
        categories: (this.state.uangSakuData.dates || []).map((d) => this.formatDate(d)),
      },
      yaxis: {
        labels: {
          formatter: (value) =>
            new Intl.NumberFormat("id-ID", {
              style: "currency",
              currency: "IDR",
              minimumFractionDigits: 0,
            }).format(value),
        },
      },
      fill: { type: "gradient", gradient: { opacityFrom: 0.6, opacityTo: 0.3 } },
      tooltip: {
        shared: true,
        y: {
          formatter: (value) =>
            new Intl.NumberFormat("id-ID", {
              style: "currency",
              currency: "IDR",
              minimumFractionDigits: 0,
            }).format(value),
        },
      },
      noData: { text: "Tidak ada data" },
    };
  }

  // ================== FETCH DATA TANPA FILTER USER ==================

  async fetchData(startDate = null, endDate = null) {
    // Hapus filter musyrif_id → semua data perijinan ditampilkan
    let domain = [["state", "not in", ["Return", "Permission"]]];
    if (startDate) domain.push(["create_date", ">=", startDate]);
    if (endDate) domain.push(["create_date", "<=", endDate]);

    try {
      const data = await this.orm.call("cdn.perijinan", "search_read", [
        domain,
        ["state", "id"],
      ]);

      const stateGroups = {};
      const stateIds = {};

      data.forEach((record) => {
        const state = this.getStateLabel(record.state);
        if (!stateGroups[state]) {
          stateGroups[state] = 0;
          stateIds[state] = [];
        }
        stateGroups[state]++;
        stateIds[state].push(record.id);
      });

      this.state.chartData = {
        series: Object.values(stateGroups),
        labels: Object.keys(stateGroups),
        stateIds,
      };

      this.renderChart();
    } catch (error) {
      console.error("Error fetching perijinan data:", error);
    }
  }

  async fetchUangSakuData(startDate = null, endDate = null) {
    // Hapus filter musyrif_id → semua data uang saku ditampilkan
    let domain = [];
    if (startDate) {
      const start = new Date(startDate);
      start.setHours(0, 0, 0, 0);
      domain.push(["tgl_transaksi", ">=", start.toISOString().split(".")[0]]);
    }
    if (endDate) {
      const end = new Date(endDate);
      end.setHours(23, 59, 59, 999);
      domain.push(["tgl_transaksi", "<=", end.toISOString().split(".")[0]]);
    }

    try {
      const data = await this.orm.call("cdn.uang_saku", "search_read", [
        domain,
        ["tgl_transaksi", "amount_in", "amount_out", "jns_transaksi", "id"],
      ]);

      const processed = data.reduce(
        (acc, record) => {
          const date = record.tgl_transaksi?.split("T")[0];
          if (!date) return acc;

          if (!acc.dates.includes(date)) {
            acc.dates.push(date);
            acc.masuk.push(0);
            acc.keluar.push(0);
            acc.rawData[date] = [];
          }

          const idx = acc.dates.indexOf(date);
          acc.rawData[date].push(record);

          if (record.jns_transaksi === "masuk") {
            acc.masuk[idx] += Number(record.amount_in) || 0;
          } else if (record.jns_transaksi === "keluar") {
            acc.keluar[idx] += Number(record.amount_out) || 0;
          }

          return acc;
        },
        { dates: [], masuk: [], keluar: [], rawData: {} }
      );

      this.state.uangSakuData = processed;

      if (this.areaChartInstance) {
        this.areaChartInstance.updateOptions({
          series: [
            { name: "Uang Masuk", data: processed.masuk },
            { name: "Uang Keluar", data: processed.keluar },
          ],
          xaxis: { categories: processed.dates.map((d) => this.formatDate(d)) },
        });
      }
    } catch (error) {
      console.error("Error fetching uang saku data:", error);
    }
  }

  renderChart() {
    if (!this.chartRef.el) return;
    if (this.chartInstance) this.chartInstance.destroy();

    const hasData = this.state.chartData.series.length > 0;
    const config = {
      ...this.getChartConfig(),
      series: hasData ? this.state.chartData.series : [],
      labels: hasData ? this.state.chartData.labels : [],
    };

    this.chartInstance = new ApexCharts(this.chartRef.el, config);
    this.chartInstance.render();
  }

  renderAreaChart() {
    if (!this.areaChartRef.el) return;
    if (this.areaChartInstance) this.areaChartInstance.destroy();

    const config = this.getAreaChartConfig();
    this.areaChartInstance = new ApexCharts(this.areaChartRef.el, config);
    this.areaChartInstance.render();
  }

  getStateLabel(state) {
    const map = { Draft: "Pengajuan", Check: "Diperiksa", Approved: "Disetujui", Rejected: "Ditolak" };
    return map[state] || state;
  }
}

MusyrifChartRenderer.template = "owl.MusyrifChartRenderer";