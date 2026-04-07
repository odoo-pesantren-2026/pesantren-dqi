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

export class OrangtuaChartRenderer extends Component {
  static props = {
    type: { type: String },
    title: { type: String },
    period: { type: String, optional: true },
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.chartRef = useRef("chart");
    this.loadingOverlayRef = useRef("loadingOverlay");
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      chartData: { series: [], labels: [], fullData: [] },
    };
    this.chartInstance = null;
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;
    this.isZoomed = false;

    if (this.props.startDate && this.props.endDate) {
      this.state.isFiltered = true;
    }

    this.fetchData(this.props.startDate, this.props.endDate);

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
            await this.fetchData(
              this.state.currentStartDate,
              this.state.currentEndDate
            ),
          ]);
        } catch (error) {
          console.error("Error updating props:", error);
        }
        this.hideLoading();
      }
    });

    onWillStart(async () => {
      this.showLoading();
      try {
        await loadJS("https://cdn.jsdelivr.net/npm/apexcharts");
        await Promise.all([
          await this.fetchData(
            this.state.currentStartDate,
            this.state.currentEndDate
          ),
        ]);
      } catch (error) {
        console.error("Error updating props:", error);
      } finally {
        this.hideLoading();
      }
    });

    onMounted(() => {
      this.renderChart();
      this.attachEventListeners();
    });

    onWillUnmount(() => {
      this.cleanup();
    });
  }

  async fetchData(startDate = null, endDate = null) {
    // Jika tanggal diberikan, format ke format Odoo
    const formattedStartDate = startDate
      ? this.formatDateToOdoo(startDate)
      : null;
    const formattedEndDate = endDate ? this.formatDateToOdoo(endDate) : null;

    if (this.props.title === "Tagihan Santri") {
      await this.fetchTagihanData(formattedStartDate, formattedEndDate);
    }

    if (this.chartInstance) {
      this.updateChart();
      // this.refreshChart();
    } else if (this.chartRef.el) {
      this.renderChart();
    }
  }

  updateChart() {
    if (this.chartInstance) {
      this.chartInstance.updateOptions(
        {
          xaxis: {
            categories: this.state.chartData.labels,
          },
          series: this.state.chartData.series,
        },
        false,
        true
      );
    }

    if (this.donutChartInstance) {
      this.donutChartInstance.updateOptions({
        labels: this.state.donutChartData.labels,
        series: this.state.donutChartData.series,
      });
    }
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
    // Hide loading overlay
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
    this.clearIntervals();
  }

  toggleCountdown() {
    if (this.isCountingDown) {
      this.clearIntervals();
      document.getElementById("timerIcon").className = "fas fa-clock";
      document.getElementById("timerCountdown").textContent = "";
    } else {
      this.startCountdown();
      document.getElementById("timerIcon").className = "fas fa-stop d-none";
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
    document.getElementById("timerCountdown").textContent = this.countdownTime;
  }

  async refreshChart() {
    this.showLoading();
    // Use filtered dates if filtering is active
    const startDate = this.state.isFiltered
      ? this.state.currentStartDate
      : null;
    const endDate = this.state.isFiltered ? this.state.currentEndDate : null;

    try {
      await Promise.all([await this.fetchData(startDate, endDate)]);
      if (this.chartInstance) {
        this.chartInstance.updateOptions(
          {
            series: this.state.chartData.series,
            xaxis: {
              categories: this.state.chartData.labels,
            },
          },
          true,
          true
        );
      }
    } catch (error) {
      console.error("Error refreshing chart:", error);
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
      const timerButton = document.getElementById("timerButton");
      timerButton.addEventListener("click", this.toggleCountdown.bind(this));
    }

    // Add date filter listeners
    const startDateInput = document.querySelector('input[name="start_date"]');
    const endDateInput = document.querySelector('input[name="end_date"]');

    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", () => this.handleDateFilter());
      endDateInput.addEventListener("change", () => this.handleDateFilter());
    }
  }

  handleDateFilter() {
    const startDateInput = document.querySelector('input[name="start_date"]');
    const endDateInput = document.querySelector('input[name="end_date"]');

    if (startDateInput && endDateInput) {
      const startDate = startDateInput.value;
      const endDate = endDateInput.value;

      if (startDate && endDate) {
        // Format dates to match Odoo's expected format
        const formattedStartDate = this.formatDateToOdoo(startDate);
        const formattedEndDate = this.formatDateToOdoo(endDate);

        // Update state with new filter values
        this.state.currentStartDate = formattedStartDate;
        this.state.currentEndDate = formattedEndDate;
        this.state.isFiltered = true;

        // Fetch new data with date range
        this.fetchData(formattedStartDate, formattedEndDate);
      } else {
        // If either date is cleared, remove filtering
        this.state.currentStartDate = null;
        this.state.currentEndDate = null;
        this.state.isFiltered = false;
        this.fetchData();
      }
    }
  }

  formatDateToOdoo(dateString) {
    const date = new Date(dateString);
    return date.toISOString().split(".")[0] + "Z";
  }

  parseDate(dateStr) {
    const date = new Date(dateStr);
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  }

  processDateData(data, field) {
    return data.reduce((acc, record) => {
      const date = this.parseDate(record.create_date);
      const dateStr = date.toLocaleDateString("id-ID", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });

      if (!acc[dateStr]) {
        acc[dateStr] = 0;
      }
      acc[dateStr] += record[field] || 0;
      return acc;
    }, {});
  }

  async fetchTagihanData(startDate = null, endDate = null) {
    try {
      const domain = [
        ["move_type", "in", ["out_invoice", "out_refund"]],
        ["partner_id", "!=", false],
        ["state", "=", "posted"],  // Only show confirmed invoices, exclude draft
        ["orangtua_id", "ilike", session.partner_display_name],
      ];

      if (startDate) domain.push(["invoice_date", ">=", startDate]);
      if (endDate) domain.push(["invoice_date", "<=", endDate]);

      const invoiceData = await this.orm.searchRead("account.move", domain, [
        "name",
        "payment_state",
        "partner_id",
        "orangtua_id",
        "invoice_date",
        "invoice_line_ids",
      ]);

      this.processTagihanData(invoiceData);
    } catch (error) {
      console.error("Error fetching tagihan data:", error);
      this.state.chartData = { series: [], labels: [] };
    }
  }

  processTagihanData(data) {
    if (!Array.isArray(data) || data.length === 0) {
      this.state.chartData = { series: [], labels: [] };
      return;
    }

    // Group by student with complete invoice line information
    const studentStats = data.reduce((acc, record) => {
      const partnerId = record.partner_id[0];
      const partnerName = record.partner_id[1];

      if (!acc[partnerId]) {
        acc[partnerId] = {
          name: partnerName,
          lunas: [],
          belumLunas: [],
          total: 0,
        };
      }

      const lineInfo = {
        line_id: record.id,
        invoice_date: record.invoice_date,
      };

      if (record.payment_state === "paid") {
        acc[partnerId].lunas.push(lineInfo);
      } else {
        acc[partnerId].belumLunas.push(lineInfo);
      }
      acc[partnerId].total += record.quantity || 0;

      return acc;
    }, {});

    const processedData = Object.entries(studentStats)
      .map(([id, stats]) => ({
        id,
        name: stats.name,
        lunas: stats.lunas,
        belumLunas: stats.belumLunas,
        lunasCount: stats.lunas.length,
        belumLunasCount: stats.belumLunas.length,
        total: stats.total,
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 6);

    this.state.chartData = {
      labels: processedData.map((student) => student.name),
      series: [
        {
          name: "Lunas",
          data: processedData.map((student) => student.lunasCount),
        },
        {
          name: "Belum Lunas",
          data: processedData.map((student) => student.belumLunasCount),
        },
      ],
      fullData: processedData, // Store complete data for click handling
    };
  }

  getChartConfig() {
    const hasData = this.state.chartData.series.some(
      (series) => series.data.length > 0
    );

    const baseConfig = {
      chart: {
        type: "bar",
        height: 450,
        stacked: true,
        toolbar: {
          show: false,
          tools: {
            download: false,
            selection: false,
            zoom: false,
            zoomin: false,
            zoomout: false,
            pan: false,
          },
        },
        animations: {
          enabled: true,
          easing: "easeinout",
          speed: 800,
          dynamicAnimation: {
            enabled: true,
            speed: 350,
          },
        },
        events: {
          dataPointSelection: (event, chartContext, config) => {
            this.onChartClick(event, chartContext, config);
          },
        },
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: "70%",
          endingShape: "rounded",
          borderRadius: 4,
          dataLabels: {
            position: "top",
          },
        },
      },
      colors: ["#00E396", "#FF4560"],
      dataLabels: {
        enabled: true,
        formatter: function (val) {
          return val === 0 ? "" : val.toLocaleString("id-ID");
        },
        style: {
          fontSize: "12px",
          colors: ["#333"],
        },
        offsetY: -20,
      },
      title: {
        text: this.props.title,
        align: "center",
        style: {
          fontSize: "18px",
          fontWeight: "600",
          fontFamily: "Inter, sans-serif",
        },
      },
      xaxis: {
        categories: this.state.chartData.labels,
        labels: {
          show: hasData, // Show labels only when data exists
          rotate: -45,
          style: {
            fontSize: "12px",
            fontFamily: "Inter, sans-serif",
          },
        },
        axisBorder: {
          show: hasData, // Show border only when data exists
        },
        axisTicks: {
          show: hasData, // Show ticks only when data exists
        },
        lines: {
          show: hasData, // Show lines only when data exists
        },
      },
      yaxis: {
        labels: {
          show: hasData, // Show labels only when data exists
        },
        min: 0,
        tickAmount: 5,
        forceNiceScale: true,
        lines: {
          show: hasData, // Show lines only when data exists
        },
        axisBorder: {
          show: hasData, // Show border only when data exists
        },
        axisTicks: {
          show: hasData, // Show ticks only when data exists
        },
      },
      grid: {
        show: hasData, // Show grid only when data exists
      },
      legend: {
        position: "top",
        horizontalAlign: "center",
        offsetY: 0,
        itemMargin: {
          horizontal: 10,
          vertical: 5,
        },
      },
      tooltip: {
        shared: true,
        intersect: false,
        y: {
          formatter: function (value) {
            return value === 0 ? "-" : value.toLocaleString("id-ID");
          },
        },
      },
      states: {
        hover: {
          filter: {
            type: "lighten",
            value: 0.15,
          },
        },
        active: {
          allowMultipleDataPointsSelection: false,
          filter: {
            type: "darken",
            value: 0.35,
          },
        },
      },
      noData: {
        text: "Tidak ada data",
        align: "center",
        verticalAlign: "middle",
        style: {
          color: "#1f2937",
          fontSize: "16px",
          fontFamily: "Inter",
        },
      },
    };

    return baseConfig;
  }

  renderChart() {
    if (!this.chartRef.el) return;

    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }

    this.chartRef.el.innerHTML = "";

    const config = {
      ...this.getChartConfig(),
      series: this.state.chartData.series.map((series) => ({
        ...series,
        data: series.data.map((value) => value || 0), // Ensure no undefined values
      })),
    };

    try {
      this.chartInstance = new ApexCharts(this.chartRef.el, config);
      this.chartInstance.render();
    } catch (error) {
      console.error("Error rendering chart:", error);
    }
  }

  // onChartClick(event, chartContext, config) {
  //   const seriesIndex = config.seriesIndex; // 0 for "Lunas", 1 for "Belum Lunas"
  //   const dataPointIndex = config.dataPointIndex; // Index of the student in labels
  //   const studentName = this.state.chartData.labels[dataPointIndex];
  //   const fullData = this.state.chartData.fullData[dataPointIndex];

  //   let filteredInvoices = [];
  //   if (seriesIndex === 0) {
  //     // Clicked on "Lunas" bar
  //     filteredInvoices = fullData.lunas;
  //   } else if (seriesIndex === 1) {
  //     // Clicked on "Belum Lunas" bar
  //     filteredInvoices = fullData.belumLunas;
  //   }

  //   // Here you can navigate or display the filtered invoices
  //   // For example, log or show a popup with invoice details
  //   console.log(
  //     `Clicked on ${
  //       seriesIndex === 0 ? "Lunas" : "Belum Lunas"
  //     } for ${studentName}:`,
  //     filteredInvoices
  //   );

  //   // Example: Navigate to a detail page or open a modal
  //   // this.$router.push({ path: `/tagihan-detail/${studentName}`, query: { invoices: JSON.stringify(filteredInvoices) }});
  //   // Or show a modal with filteredInvoices
  // }

  // async onChartClick(event, chartContext, config) {
  //   const dataPointIndex = config.dataPointIndex;
  //   const seriesIndex = config.seriesIndex;
  //   console.log("DI KLIK", dataPointIndex);
  //   console.log("DI KLIK", se);
  // }

  async onChartClick(event, chartContext, config) {
    const dataPointIndex = config.dataPointIndex;
    const seriesIndex = config.seriesIndex;

    if (dataPointIndex === -1) return;

    // Define the action XML ID from the orangtua module (has create/edit disabled)
    const actionId = "pesantren_orangtua.tagihan_orangtua_action";

    // Get student data
    const studentData = this.state.chartData.fullData[dataPointIndex];
    const seriesName = this.state.chartData.series[seriesIndex].name;

    // Build domain based on the clicked segment
    let domainAction = [
      ["partner_id", "=", parseInt(studentData.id)],
      ["move_type", "=", "out_invoice"],
      ["state", "=", "posted"],  // Only show confirmed invoices
    ];

    if (seriesName === "Lunas") {
      domainAction.push(["payment_state", "=", "paid"]);
    } else {
      domainAction.push(["payment_state", "!=", "paid"]);
    }

    try {
      // Load the action using the correct XML ID
      const action = await this.env.services.action.loadAction(actionId);

      // Create a modified copy of the action
      const newAction = {
        ...action,
        domain: domainAction,
        context: {
          ...action.context,
          default_move_type: "out_invoice",
          search_default_filter_by_blm_lunas: seriesName !== "Lunas" ? 1 : 0,
          create: false,  // Disable create button for parents
          edit: false,    // Disable edit for parents
          delete: false,  // Disable delete for parents
        },
        name: `${this.props.title} - ${studentData.name} - ${seriesName}`,
      };

      // Execute the modified action
      await this.env.services.action.doAction(newAction);
    } catch (error) {
      console.error(`Error loading action ${actionId}:`, error);
      // Show user-friendly error message
      this.env.services.notification.notify({
        title: this.env._t("Error"),
        message: this.env._t(
          "Could not load the requested view. Please contact your administrator."
        ),
        type: "danger",
      });
    }
  }

  toggleZoom = () => {
    const chartWrapper = this.chartRef.el.parentElement;
    const zoomBtn = chartWrapper.querySelector(".zoom-btn i");

    if (!this.isZoomed) {
      // Buat container fullscreen jika belum ada
      if (!this.fullscreenContainer) {
        this.fullscreenContainer = document.createElement("div");
        this.fullscreenContainer.className =
          "position-fixed top-0 start-0 w-100 h-100 bg-white";
        this.fullscreenContainer.style.zIndex = "9999";
        this.fullscreenContainer.style.overflowX =
          window.innerWidth < 768 ? "auto" : "hidden"; // Scroll horizontal untuk HP
        this.fullscreenContainer.style.overflowY = "hidden"; // Cegah scroll vertikal
        this.fullscreenContainer.style.webkitOverflowScrolling = "touch"; // Scroll halus di iOS

        // Tambahkan tombol close
        const closeBtn = document.createElement("button");
        closeBtn.className =
          "btn btn-sm btn-light position-absolute top-0 start-0 m-3"; // Posisikan di kiri atas
        closeBtn.innerHTML = '<i class="fas fa-times"></i>';
        closeBtn.onclick = () => this.toggleZoom();
        closeBtn.style.zIndex = "10000"; // Pastikan tombol berada di atas
        this.fullscreenContainer.appendChild(closeBtn);

        // Tambahkan container chart
        this.zoomedChartContainer = document.createElement("div");
        this.zoomedChartContainer.style.height = "100%";
        this.zoomedChartContainer.style.display = "flex";
        this.zoomedChartContainer.style.justifyContent = "center";
        this.zoomedChartContainer.style.alignItems = "center";

        if (window.innerWidth < 768) {
          // Untuk layar HP
          this.zoomedChartContainer.style.minWidth = "1024px";
          this.zoomedChartContainer.style.paddingRight = "40px";
        }

        this.fullscreenContainer.appendChild(this.zoomedChartContainer);
      }

      // Simpan parent dan dimensi asli
      this.originalParent = this.chartRef.el.parentElement;
      this.originalHeight = this.chartRef.el.style.height;
      this.originalWidth = this.chartRef.el.style.width;

      // Tampilkan fullscreen
      document.body.appendChild(this.fullscreenContainer);
      this.chartRef.el.style.height = window.innerWidth < 768 ? "100%" : "90%";
      this.chartRef.el.style.width = window.innerWidth < 768 ? "100%" : "90%";
      this.zoomedChartContainer.appendChild(this.chartRef.el);

      if (zoomBtn) {
        zoomBtn.className = "fas fa-compress";
      }

      // Tambahkan indikator scroll pada layar HP
      if (window.innerWidth < 768) {
        const scrollIndicator = document.createElement("div");
        scrollIndicator.className = "scroll-indicator";
        scrollIndicator.innerHTML =
          '<i class="fas fa-arrows-left-right"></i> Scroll untuk melihat lebih banyak';
        scrollIndicator.style.cssText = `
                position: absolute;
                bottom: 10px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                opacity: 0.8;
                z-index: 10000;
            `;
        this.fullscreenContainer.appendChild(scrollIndicator);

        // Hilangkan indikator scroll setelah 3 detik
        setTimeout(() => {
          scrollIndicator.style.transition = "opacity 0.5s";
          scrollIndicator.style.opacity = "0";
          setTimeout(() => scrollIndicator.remove(), 500);
        }, 3000);
      }
    } else {
      // Kembali ke tampilan normal
      const chartCanvas = this.chartRef.el;

      // Hapus fullscreen container
      if (this.fullscreenContainer && this.fullscreenContainer.parentNode) {
        document.body.removeChild(this.fullscreenContainer);
      }

      // Kembalikan chart ke container asli
      if (this.originalParent) {
        chartCanvas.style.height = this.originalHeight || "450px";
        chartCanvas.style.width = this.originalWidth || "100%";
        this.originalParent.appendChild(chartCanvas);
      }

      if (zoomBtn) {
        zoomBtn.className = "fas fa-expand";
      }
    }

    this.isZoomed = !this.isZoomed;

    // Perbarui ukuran chart menggunakan ApexCharts
    if (this.chartInstance) {
      setTimeout(() => {
        const height = this.isZoomed ? window.innerHeight * 0.9 : 450;
        const width = this.isZoomed
          ? window.innerWidth < 768
            ? "100%"
            : "90%"
          : "100%";
        const options = {
          chart: {
            height: height,
            width: width,
          },
        };

        this.chartInstance.updateOptions(options, false, true);
      }, 100);
    }
  };
}

OrangtuaChartRenderer.template = "owl.OrangtuaChartRenderer";
