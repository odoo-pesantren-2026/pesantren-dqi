/** @odoo-module */
import { registry } from "@web/core/registry";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted, onWillUnmount, onWillUpdateProps, onRendered } = owl;
import { useService } from "@web/core/utils/hooks";

export class GuruChartRenderer extends Component {
  static props = {
    type: { type: String },
    title: { type: String },
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };
  static template = "owl.GuruChartRenderer";

  setup() {
    this.chartRef = useRef("chart");
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      chartData: { labels: [], series: [], associated_ids: {} },
      hasData: false,
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
      isFiltered: !!(this.props.startDate && this.props.endDate),
    };
    this.chartInstance = null;
    this.loadingOverlay = null;
    this.isFetching = false;
    this.hasInitialFetch = false;
    this.renderRetryAttempts = 0;
    this.maxRenderRetries = 3; // NEW: Limit retry attempts

    // Bind handler for event listener
    this._handleRefreshEvent = this.handleRefreshEvent.bind(this);

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
          await this.fetchAndProcessData(nextProps.startDate, nextProps.endDate);
        } catch (error) {
          console.error("Error in onWillUpdateProps:", error);
          this.state.hasData = false;
          this.state.chartData = { labels: [], series: [], associated_ids: {} };
        } finally {
          this.hideLoading();
        }
      }
    });

    onWillStart(async () => {
      if (this.hasInitialFetch) return;
      this.showLoading();
      try {
        await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js");
        await this.fetchAndProcessData(
          this.state.currentStartDate,
          this.state.currentEndDate
        );
        this.hasInitialFetch = true;
      } catch (error) {
        console.error("Error in onWillStart:", error);
        this.state.hasData = false;
        this.state.chartData = { labels: [], series: [], associated_ids: {} };
      } finally {
        this.hideLoading();
      }
    });

    onMounted(() => {
      window.addEventListener('guru-dashboard-refresh', this._handleRefreshEvent);
      console.log("✅ GuruChartRenderer: Event listener attached");
    });

    onWillUnmount(() => {
      window.removeEventListener('guru-dashboard-refresh', this._handleRefreshEvent);
      console.log("👋 GuruChartRenderer: Event listener removed");
      this.cleanup();
    });

    onRendered(() => {
      console.log("DOM rendered, hasData:", this.state.hasData, "canvas exists:", !!this.chartRef.el);
      this.renderChart();
    });
  }

  async handleRefreshEvent(event) {
    console.log("🔔 GuruChartRenderer: Received refresh event", event.detail);
    const { startDate, endDate } = event.detail;
    this.showLoading();
    try {
      this.state.currentStartDate = startDate;
      this.state.currentEndDate = endDate;
      await this.fetchAndProcessData(startDate, endDate);
    } catch (error) {
      console.error("Error in handleRefreshEvent:", error);
    } finally {
      this.hideLoading();
    }
  }

  get hasData() {
    return this.state.hasData;
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
  }

  hideLoading() {
    if (this.loadingOverlay) {
      this.loadingOverlay.style.display = "none";
    }
  }

  cleanup() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }
    if (this.loadingOverlay) {
      this.loadingOverlay.remove();
      this.loadingOverlay = null;
    }
    this.renderRetryAttempts = 0; // NEW: Reset retry attempts
  }

  async fetchAndProcessData(startDate = null, endDate = null) {
    if (this.isFetching) {
      console.log("⏭️ Skipping fetch - already fetching");
      return;
    }
    this.isFetching = true;
    console.log("🔍 GuruChartRenderer: Fetching data", {
      title: this.props.title,
      startDate,
      endDate
    });

    try {
      let start, end;
      if (!startDate || !endDate) {
        const today = new Date();
        start = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split("T")[0];
        end = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split("T")[0];
      } else {
        start = new Date(startDate).toISOString().split("T")[0];
        end = new Date(endDate).toISOString().split("T")[0];
      }

      const isValidDate = (dateStr) => {
        const date = new Date(dateStr);
        return date instanceof Date && !isNaN(date);
      };

      if (!isValidDate(start) || !isValidDate(end)) {
        console.error("Invalid date format:", { start, end });
        this.state.hasData = false;
        this.state.chartData = { labels: [], series: [], associated_ids: {} };
        return;
      }

      const domain = [
        ["tanggal", ">=", start],
        ["tanggal", "<=", end],
      ];

      let data = [];
      if (this.props.title === "pie1") {
        data = await this.orm.call(
          "cdn.absensi_siswa_lines",
          "search_read",
          [domain, ["id", "kelas_id", "tanggal", "guru", "kehadiran"]],
          { context: this.env.context }
        );
      } else if (this.props.title === "pie2") {
        data = await this.orm.call(
          "cdn.absen_halaqoh_line",
          "search_read",
          [domain, ["name", "halaqoh_id", "tanggal", "kehadiran", "ustadz_id"]],
          { context: this.env.context }
        );
      }

      console.log("📦 Data fetched:", data.length, "records");

      const statusCount = {};
      const statusIds = {};
      data.forEach((record) => {
        const status = record.kehadiran || "Tidak Ada Status";
        statusCount[status] = (statusCount[status] || 0) + 1;
        if (!statusIds[status]) {
          statusIds[status] = [];
        }
        statusIds[status].push(record.id);
      });

      this.state.chartData = {
        labels: Object.keys(statusCount),
        series: Object.values(statusCount),
        associated_ids: statusIds,
      };

      this.state.hasData = this.state.chartData.labels.length > 0 && this.state.chartData.series.length > 0;
      console.log("✅ Chart data processed:", this.state.chartData.labels, "hasData:", this.state.hasData);
    } catch (error) {
      console.error("Error fetching data from Odoo:", error);
      this.state.hasData = false;
      this.state.chartData = { labels: [], series: [], associated_ids: {} };
    } finally {
      this.isFetching = false;
      this.renderRetryAttempts = 0; // NEW: Reset retry attempts after fetch
    }
  }

  renderChart() {
    // Check if data exists
    if (!this.state.hasData) {
      console.log("No data to render chart.");
      return;
    }

    // Check if canvas exists
    if (!this.chartRef.el) {
      if (this.renderRetryAttempts < this.maxRenderRetries) {
        this.renderRetryAttempts++;
        console.warn(`Chart canvas element not found. Retrying (${this.renderRetryAttempts}/${this.maxRenderRetries})...`);
        setTimeout(() => this.renderChart(), 100); // Retry after 100ms
      } else {
        console.error("Max retry attempts reached. Chart canvas not found.");
      }
      return;
    }

    // Clear previous chart instance
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }

    try {
      this.chartInstance = new Chart(this.chartRef.el, {
        type: this.props.type,
        data: {
          labels: this.state.chartData.labels,
          datasets: [
            {
              label: this.props.title === "pie1" ? "Jumlah" : "Total",
              data: this.state.chartData.series,
              backgroundColor: this.state.chartData.labels.map((_, index) =>
                this.getDiverseColor(index, this.state.chartData.labels.length)
              ),
              borderColor: "#ffffff",
              borderWidth: 1,
              hoverOffset: 4,
              associated_ids: this.state.chartData.associated_ids,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "top",
              display: true,
            },
            title: {
              display: false,
              text: this.props.title,
            },
          },
          layout: {
            padding: {
              top: 20,
              bottom: 20,
            },
          },
          onClick: (evt) => this.handleChartClick(evt),
        },
      });
      console.log("✅ Chart rendered successfully");
      this.renderRetryAttempts = 0; // Reset retries on success
    } catch (error) {
      console.error("Error rendering pie chart:", error);
    }
  }

  getDiverseColor(index, totalItems) {
    const colors = [
      "#16a34a", "#0891b2", "#22c55e", "#06b6d4", "#15803d",
      "#0e7490", "#86efac", "#67e8f9", "#166534", "#155e75",
    ];
    return colors[index % colors.length];
  }

  handleChartClick(evt) {
    const activePoints = this.chartInstance.getElementsAtEventForMode(
      evt,
      "nearest",
      { intersect: true },
      false
    );
    if (activePoints.length === 0) return;

    const firstPoint = activePoints[0];
    const status = this.state.chartData.labels[firstPoint.index];
    const associatedIds = this.state.chartData.associated_ids[status];

    if (!associatedIds || associatedIds.length === 0) {
      console.error("No associated IDs for the clicked data point.");
      return;
    }

    let resModel, nameHeader;
    if (this.props.title === "pie1") {
      resModel = "cdn.absensi_siswa_lines";
      nameHeader = "Absensi Siswa";
    } else if (this.props.title === "pie2") {
      resModel = "cdn.absen_halaqoh_line";
      nameHeader = "Absensi Halaqoh";
    }

    const domain = [["id", "in", associatedIds]];
    if (this.state.currentStartDate && this.state.currentEndDate) {
      domain.push(
        ["tanggal", ">=", this.state.currentStartDate],
        ["tanggal", "<=", this.state.currentEndDate]
      );
    }

    this.actionService.doAction({
      type: "ir.actions.act_window",
      name: `${nameHeader} - ${status}`,
      res_model: resModel,
      view_mode: "list,form",
      domain: domain,
      views: [[false, "list"], [false, "form"]],
      target: "current",
    }).catch((error) => {
      console.error("Error in actionService.doAction:", error);
    });
  }
}

GuruChartRenderer.template = "owl.GuruChartRenderer";