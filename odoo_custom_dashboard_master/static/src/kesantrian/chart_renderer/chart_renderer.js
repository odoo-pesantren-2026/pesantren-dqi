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
  onPatched,
} = owl;
import { useService } from "@web/core/utils/hooks";

export class ChartRenderer extends Component {
  static props = {
    type: { type: String }, // 'chart' atau 'donutChart'
    period: { type: String, optional: true },
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.chartRef = useRef("chart");
    this.donutChartRef = useRef("donutChart");
    this.orm = useService("orm");
    this.actionService = useService("action");

    this.state = {
      chartData: { series: [], labels: [] },
      donutChartData: { labels: [], series: [] },
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
      isFiltered: !!(this.props.startDate && this.props.endDate),
      hasData: false, // Track if data exists
    };

    this.chartInstance = null;
    this.donutChartInstance = null;
    this.pendingRender = false;

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
          await this.fetchHalaqohAttendanceData(
            nextProps.startDate,
            nextProps.endDate
          );
        } finally {
          this.hideLoading();
        }
      }
    });

    onWillStart(async () => {
      this.showLoading();
      try {
        // Load Chart.js
        await loadJS("https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js");
        await this.fetchHalaqohAttendanceData(
          this.state.currentStartDate,
          this.state.currentEndDate
        );
      } finally {
        this.hideLoading();
      }
    });

    onMounted(() => {
      this.renderChartIfNeeded();
    });

    // Re-render chart after DOM is patched (when state.hasData changes)
    onPatched(() => {
      if (this.pendingRender) {
        this.pendingRender = false;
        this.renderChartIfNeeded();
      }
    });

    onWillUnmount(() => {
      this.cleanup();
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
    if (this.donutChartInstance) {
      this.donutChartInstance.destroy();
      this.donutChartInstance = null;
    }
  }

  async fetchHalaqohAttendanceData(startDate = null, endDate = null) {
    // Tentukan rentang default (7 hari terakhir)
    let start, end;
    if (!startDate && !endDate) {
      const today = new Date();
      const weekAgo = new Date();
      weekAgo.setDate(today.getDate() - 6);
      start = weekAgo.toISOString().split("T")[0];
      end = today.toISOString().split("T")[0];
    } else {
      start = new Date(startDate).toISOString().split("T")[0];
      end = new Date(endDate).toISOString().split("T")[0];
    }

    const domain = [
      ["tanggal", ">=", start],
      ["tanggal", "<=", end],
    ];

    try {
      const data = await this.orm.call(
        "cdn.absen_halaqoh_line",
        "search_read",
        [domain, ["name", "halaqoh_id", "tanggal", "kehadiran"]]
      );

      // Check if data exists
      this.state.hasData = data && data.length > 0;

      if (!this.state.hasData) {
        this.state.chartData = { series: [], labels: [] };
        this.state.donutChartData = { labels: [], series: [] };
        this.pendingRender = true;
        return;
      }

      // Group by halaqoh
      const halaqohMap = {};
      const statusCount = {};

      data.forEach((record) => {
        const halaqohName = record.halaqoh_id ? record.halaqoh_id[1] : "Tanpa Halaqoh";
        const status = record.kehadiran || "Tidak Ada Status";

        // Hitung per halaqoh
        if (!halaqohMap[halaqohName]) {
          halaqohMap[halaqohName] = { count: 0, ids: [] };
        }
        halaqohMap[halaqohName].count += 1;
        halaqohMap[halaqohName].ids.push(record.id);

        // Hitung status kehadiran
        statusCount[status] = (statusCount[status] || 0) + 1;
      });

      // Siapkan data untuk chart batang (per halaqoh)
      const halaqohNames = Object.keys(halaqohMap).sort();
      this.state.chartData = {
        labels: ["Total"],
        series: halaqohNames.map((name) => ({
          name: name,
          data: [halaqohMap[name].count],
          associated_ids: halaqohMap[name].ids,
        })),
      };

      // Siapkan data untuk donat (status kehadiran)
      this.state.donutChartData = {
        labels: Object.keys(statusCount),
        series: Object.values(statusCount),
      };

      // Mark pending render - chart will be rendered in onPatched hook after DOM updates
      this.pendingRender = true;
    } catch (error) {
      console.error("Error fetching halaqoh attendance data:", error);
      this.state.hasData = false;
      this.state.chartData = { series: [], labels: [] };
      this.state.donutChartData = { labels: [], series: [] };
    }
  }

  renderChartIfNeeded() {
    // Clean up existing charts first before any rendering decision
    if (!this.state.hasData) {
      // Clear chart containers when no data
      this.cleanup();
      if (this.chartRef.el) {
        this.chartRef.el.innerHTML = '<div style="display: flex; justify-content: center; align-items: center; height: 100%; color: #666;">Tidak ada data untuk periode ini</div>';
      }
      if (this.donutChartRef.el) {
        this.donutChartRef.el.innerHTML = '<div style="display: flex; justify-content: center; align-items: center; height: 100%; color: #666;">Tidak ada data untuk periode ini</div>';
      }
      return;
    }

    if (this.props.type === "chart") {
      this.renderChart();
    } else if (this.props.type === "donutChart") {
      this.renderDonutChart();
    }
  }

  getChartColors() {
    return [
      "#16a34a", "#0891b2", "#22c55e", "#06b6d4", "#15803d",
      "#0e7490", "#86efac", "#67e8f9", "#166534", "#155e75"
    ];
  }

  renderChart() {
    if (!this.chartRef.el) return;
    this.cleanupChartOnly();

    const canvas = document.createElement('canvas');
    this.chartRef.el.innerHTML = '';
    this.chartRef.el.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    const colors = this.getChartColors();
    const datasets = this.state.chartData.series.map((series, index) => ({
      label: series.name,
      data: series.data,
      backgroundColor: colors[index % colors.length],
      borderColor: colors[index % colors.length],
      borderWidth: 1,
      borderRadius: 4,
      associated_ids: series.associated_ids,
    }));

    try {
      this.chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: this.state.chartData.labels,
          datasets: datasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            mode: 'index',
            intersect: false,
          },
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 15,
                font: {
                  size: 12,
                  family: 'Inter, sans-serif',
                },
                boxWidth: 15,
                boxHeight: 15,
              },
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              titleFont: {
                size: 13,
              },
              bodyFont: {
                size: 12,
              },
              callbacks: {
                label: function (context) {
                  return context.dataset.label + ': ' + Math.round(context.parsed.y);
                }
              }
            },
          },
          scales: {
            x: {
              grid: {
                display: false,
              },
              ticks: {
                font: {
                  size: 12,
                  family: 'Inter, sans-serif',
                },
              },
            },
            y: {
              beginAtZero: true,
              ticks: {
                callback: function (value) {
                  return Math.round(value);
                },
                font: {
                  size: 12,
                },
              },
              grid: {
                color: 'rgba(0, 0, 0, 0.05)',
              },
            },
          },
          onClick: (event, elements) => {
            if (elements.length > 0) {
              const element = elements[0];
              const datasetIndex = element.datasetIndex;
              const associatedIds = datasets[datasetIndex].associated_ids;

              if (associatedIds && associatedIds.length > 0) {
                this.actionService.doAction({
                  type: "ir.actions.act_window",
                  name: "Detail Absensi Halaqoh",
                  res_model: "cdn.absen_halaqoh_line",
                  view_mode: "list,form",
                  domain: [["id", "in", associatedIds]],
                  views: [[false, "list"], [false, "form"]],
                  target: "current",
                });
              }
            }
          },
        },
      });
    } catch (error) {
      console.error("Error rendering bar chart:", error);
    }
  }

  renderDonutChart() {
    if (!this.donutChartRef.el) return;
    this.cleanupDonutOnly();

    const canvas = document.createElement('canvas');
    this.donutChartRef.el.innerHTML = '';
    this.donutChartRef.el.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    const colors = this.getChartColors();

    try {
      this.donutChartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: this.state.donutChartData.labels,
          datasets: [{
            data: this.state.donutChartData.series,
            backgroundColor: colors.slice(0, this.state.donutChartData.labels.length),
            borderColor: '#ffffff',
            borderWidth: 2,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: {
                padding: 15,
                font: {
                  size: 12,
                  family: 'Inter, sans-serif',
                },
                boxWidth: 15,
                boxHeight: 15,
              },
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              titleFont: {
                size: 13,
              },
              bodyFont: {
                size: 12,
              },
              callbacks: {
                label: function (context) {
                  const label = context.label || '';
                  const value = context.parsed || 0;
                  return label + ': ' + value + ' orang';
                }
              }
            },
          },
          onClick: (event, elements) => {
            if (elements.length > 0) {
              const element = elements[0];
              const index = element.index;
              const status = this.state.donutChartData.labels[index];

              const domain = [["kehadiran", "=", status]];

              if (this.state.currentStartDate && this.state.currentEndDate) {
                domain.push(
                  ["tanggal", ">=", this.state.currentStartDate],
                  ["tanggal", "<=", this.state.currentEndDate]
                );
              }

              this.actionService.doAction({
                type: "ir.actions.act_window",
                name: `Absensi Halaqoh - ${status}`,
                res_model: "cdn.absen_halaqoh_line",
                view_mode: "list,form",
                domain: domain,
                views: [[false, "list"], [false, "form"]],
                target: "current",
              });
            }
          },
        },
      });
    } catch (error) {
      console.error("Error rendering pie chart:", error);
    }
  }

  cleanupChartOnly() {
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }
  }

  cleanupDonutOnly() {
    if (this.donutChartInstance) {
      this.donutChartInstance.destroy();
      this.donutChartInstance = null;
    }
  }
}

ChartRenderer.template = "owl.ChartRenderer";