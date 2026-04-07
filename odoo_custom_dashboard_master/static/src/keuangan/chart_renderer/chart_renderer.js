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

export class KeuanganChartRenderer extends Component {
  static props = {
    type: { type: String },
    title: { type: String },
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.chartRef = useRef("chart");
    this.loadingOverlayRef = useRef("loadingOverlay");
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      chartData: { series: [], labels: [] },
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
          console.error("Error fetching data:", error);
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
          await this.fetchData(
            this.state.currentStartDate,
            this.state.currentEndDate
          ),
        ]);
      } catch (error) {
        console.error("Error fetching data:", error);
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
      console.error("Error fetching data:", error);
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

      // Cek apakah tanggal yang dimasukkan valid
      if (this.isValidDate(startDate) && this.isValidDate(endDate)) {
        // Format tanggal agar sesuai dengan format yang diharapkan oleh Odoo
        const formattedStartDate = this.formatDateToOdoo(startDate);
        const formattedEndDate = this.formatDateToOdoo(endDate);

        // Update state dengan nilai filter baru
        this.state.currentStartDate = formattedStartDate;
        this.state.currentEndDate = formattedEndDate;
        this.state.isFiltered = true;

        // Ambil data baru berdasarkan rentang tanggal
        this.fetchData(formattedStartDate, formattedEndDate);
      } else {
        // Jika tanggal tidak valid atau kosong, reset filter dan ambil data tanpa filter
        this.state.currentStartDate = null;
        this.state.currentEndDate = null;
        this.state.isFiltered = false;
        this.fetchData();
      }
    }
  }

  // Fungsi untuk memeriksa apakah tanggal valid
  isValidDate(date) {
    const regex = /^\d{4}-\d{2}-\d{2}$/; // Format YYYY-MM-DD
    return regex.test(date); // Cek apakah tanggal sesuai dengan format
  }

  // Fungsi untuk format tanggal ke format Odoo (misalnya, YYYY-MM-DD)
  formatDateToOdoo(date) {
    const parsedDate = new Date(date);
    const year = parsedDate.getFullYear();
    const month = (parsedDate.getMonth() + 1).toString().padStart(2, "0"); // Menambahkan leading zero jika bulan kurang dari 10
    const day = parsedDate.getDate().toString().padStart(2, "0"); // Menambahkan leading zero jika hari kurang dari 10

    return `${year}-${month}-${day}`;
  }

  formatDateToOdoo(dateString) {
    const date = new Date(dateString);
    return date.toISOString().split(".")[0] + "Z";
  }

  async fetchData(startDate = null, endDate = null) {
    try {
      // Reset chartData to a safe state before fetching
      this.state.chartData = { series: [], labels: [] };

      // Existing fetch logic remains the same
      switch (this.props.title) {
        case "Tagihan Santri":
          await this.fetchTagihanData(startDate, endDate);
          break;
        case "Uang Saku Masuk":
          await this.fetchUangSakuMasukData(startDate, endDate);
          break;
        case "Uang Saku Keluar":
          await this.fetchUangSakuKeluarData(startDate, endDate);
          break;
      }

      // Aggressive validation and fallback
      const isEmptyData =
        !this.state.chartData.series ||
        this.state.chartData.series.length === 0 ||
        this.state.chartData.series.every(
          (series) =>
            !series.data ||
            series.data.length === 0 ||
            series.data.every((value) => value === 0)
        );

      if (isEmptyData) {
        this.state.chartData = {
          labels: [],
          series: [
            {
              name: this.props.title,
              type: this.props.type === "bar" ? "bar" : "area",
              data: [],
            },
          ],
        };
      }

      // Consistent rendering logic
      if (this.chartRef.el) {
        this.renderChart();
      }
    } catch (error) {
      console.error("Error in fetchData:", error);

      // Ensure a clean, fallback chart state
      this.state.chartData = {
        labels: [],
        series: [
          {
            name: this.props.title,
            type: this.props.type === "bar" ? "bar" : "area",
            data: [],
          },
        ],
      };

      if (this.chartRef.el) {
        this.renderChart();
      }
    }
  }
  // Add this new method to validate chart data
  isValidChartData(chartData) {
    return (
      chartData &&
      Array.isArray(chartData.series) &&
      chartData.series.length > 0 &&
      Array.isArray(chartData.labels) &&
      chartData.labels.length > 0
    );
  }

  // Add this new method to reset the chart
  resetChart() {
    this.state.chartData = { series: [], labels: [] };
    if (this.chartInstance) {
      this.chartInstance.destroy();
      this.chartInstance = null;
    }
  }

  updateChart() {
    if (!this.isValidChartData(this.state.chartData)) {
      console.warn("Attempting to update chart with invalid data");
      return;
    }

    if (this.chartInstance) {
      const updatedSeries = this.state.chartData.series.map((series) => ({
        ...series,
        data: series.data.map((value) => value || 0), // Ensure all values are numbers
      }));

      this.chartInstance.updateOptions(
        {
          xaxis: {
            categories: this.state.chartData.labels,
          },
          series: updatedSeries,
        },
        true,
        true
      );
    }
  }

  formatDate(date) {
    return date.toISOString().split(".")[0] + "Z";
  }

  parseDate(dateStr) {
    const date = new Date(dateStr);
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  }

  processDateData(data, field) {
    return data.reduce((acc, record) => {
      const date = this.parseDate(record.create_date);
      // Gunakan format YYYY-MM-DD untuk konsistensi
      const dateStr = date.toISOString().split('T')[0];

      if (!acc[dateStr]) {
        acc[dateStr] = 0;
      }
      acc[dateStr] += record[field] || 0;
      return acc;
    }, {});
  }

  async fetchTagihanData(startDate = null, endDate = null) {
    try {
      // Set default date range if not provided
      const today = new Date();
      const defaultStartDate =
        startDate ||
        new Date(today.getFullYear(), today.getMonth(), 1)
          .toISOString()
          .split("T")[0];
      const defaultEndDate =
        endDate ||
        new Date(today.getFullYear(), today.getMonth() + 1, 0)
          .toISOString()
          .split("T")[0];

      // First, fetch account.move (invoices) to get payment_state
      const invoiceDomain = [
        ["move_type", "in", ["out_invoice", "out_refund"]],
        ["state", "=", "posted"],
        ["invoice_date", ">=", defaultStartDate],
        ["invoice_date", "<=", defaultEndDate],
      ];

      const invoices = await this.orm.searchRead(
        "account.move",
        invoiceDomain,
        ["id", "name", "payment_state", "state", "amount_total", "amount_residual"],
        { order: "invoice_date asc" }
      );

      if (!invoices || invoices.length === 0) {
        this.state.chartData = { series: [], labels: [] };
        return;
      }

      // Create a map of invoice_id -> payment_state
      const invoicePaymentStateMap = {};
      invoices.forEach(inv => {
        invoicePaymentStateMap[inv.id] = inv.payment_state;
      });

      // Now fetch invoice lines
      const invoiceIds = invoices.map(inv => inv.id);
      const lineDomain = [
        ["move_id", "in", invoiceIds],
        ["display_type", "in", ["product"]],
        ["product_id", "!=", false],
      ];

      const result = await this.orm.searchRead(
        "account.move.line",
        lineDomain,
        [
          "date",
          "product_id",
          "move_id",
          "parent_state",
          "name",
          "quantity",
          "credit",
        ],
        { order: "date asc" }
      );

      if (!result || result.length === 0) {
        this.state.chartData = { series: [], labels: [] };
        return;
      }

      // Attach payment_state to each line from the invoice map
      result.forEach(line => {
        const moveId = line.move_id && line.move_id[0];
        line.payment_state = invoicePaymentStateMap[moveId] || 'not_paid';
      });

      // Store current date range in state
      this.state.currentStartDate = defaultStartDate;
      this.state.currentEndDate = defaultEndDate;

      const processedData = this.processTagihanData(result);
      this.state.chartData = processedData;
      this.renderChart();
    } catch (error) {
      console.error("Error fetching tagihan data:", error);
      this.state.chartData = { series: [], labels: [] };
      this.renderChart();
    }
  }

  async fetchUangSakuMasukData(startDate = null, endDate = null) {
    try {
      console.log("Fetching Uang Saku Masuk data...");
      if (this.loading) return;
      this.loading = true;

      const today = new Date();
      startDate =
        startDate ||
        new Date(today.getFullYear(), today.getMonth(), 1).toISOString();
      endDate =
        endDate ||
        new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString();

      const domain = [
        ["amount_in", ">", 0],
        ["create_date", ">=", startDate],
        ["create_date", "<=", endDate],
      ];

      const result = await this.orm.searchRead(
        "cdn.uang_saku",
        domain,
        ["create_date", "amount_in", "state"],
        { order: "create_date asc", limit: 1000 }
      );

      console.log("Raw data result:", result);


      if (!result || result.length === 0) {
        console.log("No data found for Uang Saku Masuk");
        this.state.chartData = {
          labels: [],
          series: [{
            name: "Uang Masuk",
            type: "area",
            data: [],
          }],
        };
      } else {
        console.log("Processing", result.length, "records");
        this.processUangSakuData(result, "amount_in", "Uang Masuk");
        console.log("Processed chart data:", this.state.chartData);
      }

      this.state.currentViewRange = {
        startDate,
        endDate,
        viewType: "masuk",
      };
    } catch (error) {
      console.error("Error in fetch Uang Saku Masuk Data:", error);
      this.state.chartData = {
        labels: [],
        series: [
          {
            name: "Uang Masuk",
            type: "area",
            data: [],
          },
        ],
      };

      if (this.chartInstance) {
        this.renderChart(); // Force render to show "No Data" state
      }
    } finally {
      this.loading = false; // Reset loading flag
    }
  }

  async fetchUangSakuKeluarData(startDate = null, endDate = null) {
    try {
      // Validate dates to ensure they are not null
      const safeStartDate = startDate || this.getFirstDayOfMonth();
      const safeEndDate = endDate || this.getLastDayOfMonth();

      const domain = [
        ["amount_out", ">", 0],
        ["create_date", ">=", safeStartDate],
        ["create_date", "<=", safeEndDate],
      ];

      const result = await this.orm.searchRead(
        "cdn.uang_saku",
        domain,
        ["create_date", "amount_out", "state"],
        { order: "create_date asc", limit: 1000 } // Add a reasonable limit
      );

      // Handle empty result explicitly
      if (!result || result.length === 0) {
        this.state.chartData = {
          labels: [],
          series: [
            {
              name: "Uang Keluar",
              type: "area",
              data: [],
            },
          ],
        };

        if (this.chartInstance) {
          this.renderChart(); // Force render to show "No Data" state
        }
      } else {
        this.processUangSakuData(result, "amount_out", "Uang Keluar");
      }

      // Store view range in state
      this.state.currentViewRange = {
        startDate: safeStartDate,
        endDate: safeEndDate,
        viewType: "keluar",
      };
    } catch (error) {
      console.error("Error fetching uang saku keluar data:", error);
      this.state.chartData = {
        labels: [],
        series: [
          {
            name: "Uang Keluar",
            type: "area",
            data: [],
          },
        ],
      };

      if (this.chartInstance) {
        this.renderChart(); // Force render to show "No Data" state
      }
    } finally {
      this.loading = false;
    }
  }

  // Helper to get first day of current month
  getFirstDayOfMonth() {
    const date = new Date();
    date.setDate(1);
    return date.toISOString().split("T")[0]; // Format YYYY-MM-DD
  }

  // Helper to get last day of current month
  getLastDayOfMonth() {
    const date = new Date();
    date.setMonth(date.getMonth() + 1);
    date.setDate(0);
    return date.toISOString().split("T")[0]; // Format YYYY-MM-DD
  }

  processTagihanData(data) {
    if (!Array.isArray(data) || data.length === 0) {
      return { series: [], labels: [] };
    }

    const lunasData = new Map();
    const belumLunasData = new Map();
    const kreditLunasData = new Map(); // Credit untuk yang Lunas
    const kreditBelumLunasData = new Map(); // Credit untuk yang Belum Lunas

    data.forEach((record) => {
      const productName =
        record.product_id && record.product_id[1]
          ? record.product_id[1]
          : "Unknown Product";
      const quantity = record.quantity || 1;
      const credit = record.credit || 0;

      // Skip cancelled invoices
      if (record.parent_state === "cancel") {
        return;
      }

      // Use payment_state to determine Lunas vs Belum Lunas
      // payment_state: 'paid' = Lunas, 'not_paid'/'partial'/'in_payment' = Belum Lunas
      const paymentState = record.payment_state || 'not_paid';
      const isLunas = paymentState === 'paid';

      if (isLunas) {
        // Data untuk status Lunas (sudah dibayar penuh)
        lunasData.set(
          productName,
          (lunasData.get(productName) || 0) + quantity
        );
        if (credit > 0) {
          kreditLunasData.set(
            productName,
            (kreditLunasData.get(productName) || 0) + credit
          );
        }
      } else {
        // Data untuk status Belum Lunas (not_paid, partial, in_payment)
        belumLunasData.set(
          productName,
          (belumLunasData.get(productName) || 0) + quantity
        );
        if (credit > 0) {
          kreditBelumLunasData.set(
            productName,
            (kreditBelumLunasData.get(productName) || 0) + credit
          );
        }
      }
    });

    // Combine and sort products
    const allProducts = new Set([
      ...lunasData.keys(),
      ...belumLunasData.keys(),
    ]);

    const sortedProducts = Array.from(allProducts)
      .map((product) => ({
        name: product,
        total:
          (lunasData.get(product) || 0) + (belumLunasData.get(product) || 0),
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 10)
      .map((item) => item.name);

    return {
      labels: sortedProducts,
      series: [
        {
          name: "Lunas",
          data: sortedProducts.map((product) => lunasData.get(product) || 0),
          type: "bar",
        },
        {
          name: "Belum Lunas",
          data: sortedProducts.map(
            (product) => belumLunasData.get(product) || 0
          ),
          type: "bar",
        },
        {
          name: "Dibayar",
          data: sortedProducts.map(
            (product) => kreditLunasData.get(product) || 0
          ),
          type: "line",
        },
        {
          name: "Belum Bayar",
          data: sortedProducts.map(
            (product) => kreditBelumLunasData.get(product) || 0
          ),
          type: "line",
        },
      ],
    };
  }

  processUangSakuData(data, field, label) {
    if (!data || !Array.isArray(data) || data.length === 0) {
      console.warn("No data available for chart rendering");
      this.state.chartData = {
        labels: [],
        series: [{
          name: label,
          type: "area",
          data: [],
        }],
      };
      return;
    }

    try {
      const dateData = this.processDateData(data, field);

      // Urutkan tanggal secara kronologis
      const sortedDates = Object.keys(dateData).sort((a, b) => {
        return new Date(a) - new Date(b);
      });

      const processedData = sortedDates.map((date) =>
        Math.max(0, Number(dateData[date]) || 0)
      );

      // Format label tanggal untuk display (bisa dalam format yang lebih user-friendly)
      const displayLabels = sortedDates.map(date => {
        const d = new Date(date);
        return d.toLocaleDateString('id-ID', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric'
        });
      });

      this.state.chartData = {
        labels: displayLabels, // Untuk display di chart
        originalDates: sortedDates, // Simpan format asli YYYY-MM-DD untuk referensi
        series: [{
          name: label,
          type: "area",
          data: processedData,
        }],
      };
    } catch (error) {
      console.error("Error processing Uang Saku data:", error);
      this.state.chartData = {
        labels: [],
        series: [{
          name: label,
          type: "area",
          data: [],
        }],
      };
    }
  }

  getChartConfig() {
    const baseConfig = {
      chart: {
        height: 450,
        type: this.props.type === "bar" ? "bar" : "area",
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
        stacked: this.props.type === "bar" ? true : false,
      },
      plotOptions: {
        bar: {
          horizontal: false,
          columnWidth: "50%",
          endingShape: "rounded",
          borderRadius: 4,
        },
      },
      stroke: {
        show: true,
        width:
          this.props.title === "Tagihan Santri"
            ? [0, 0, 3, 3] // For Tagihan (2 bars, 2 lines)
            : [2], // For Uang Saku (single area)
        curve: "smooth",
      },
      colors:
        this.props.title === "Tagihan Santri"
          ? ["#0c8351", "#d14343", "#2a7a9c", "#c79832"] // Updated all colors to match theme
          : ["#0c8351"],
      dataLabels: {
        enabled: true,
        formatter: function (val) {
          return val.toLocaleString("id-ID");
        },
        background: {
          enabled: true,
          borderColor: "#000000", // Warna border hitam
        },
        style: {
          colors: this.props.type === "bar" ? ["#000000"] : ["#000000"],
        },
        dropShadow: {
          enabled: true,
          top: 1,
          left: 1,
          blur: 1,
          opacity: 0.3,
        },
      },
      xaxis: {
        categories: this.state.chartData.labels.map((label) =>
          label.length > 10 ? label.substring(0, 10) + "..." : label
        ),
        labels: {
          rotate: -45,
          style: {
            fontSize: "12px",
          },
        },
      },
      yaxis:
        this.props.title === "Tagihan Santri"
          ? [
            {
              title: {
                text: "Total",
              },
              labels: {
                formatter: function (value) {
                  return Math.round(value).toLocaleString("id-ID");
                },
              },
            },
            {
              title: {
                text: "Quantity",
              },
              show: false,
            },
            {
              opposite: true,
              title: {
                text: "Nominal",
              },
              labels: {
                formatter: function (value) {
                  return value.toLocaleString("id-ID", {
                    style: "currency",
                    currency: "IDR",
                    maximumFractionDigits: 0,
                  });
                },
              },
            },
            {
              opposite: true,
              show: false,
            },
          ]
          : [
            {
              title: {
                text: "Nominal",
              },
              labels: {
                formatter: function (value) {
                  return value.toLocaleString("id-ID", {
                    style: "currency",
                    currency: "IDR",
                    maximumFractionDigits: 0,
                  });
                },
              },
            },
          ],
      tooltip: {
        shared: true,
        intersect: false,
        y:
          this.props.title === "Tagihan Santri"
            ? [
              {
                formatter: function (value) {
                  return `${Math.round(value).toLocaleString("id-ID")}`;
                },
              },
              {
                formatter: function (value) {
                  return `${Math.round(value).toLocaleString("id-ID")}`;
                },
              },
              {
                formatter: function (value) {
                  return `${value.toLocaleString("id-ID", {
                    style: "currency",
                    currency: "IDR",
                    maximumFractionDigits: 0,
                  })}`;
                },
              },
              {
                formatter: function (value) {
                  return `${value.toLocaleString("id-ID", {
                    style: "currency",
                    currency: "IDR",
                    maximumFractionDigits: 0,
                  })}`;
                },
              },
            ]
            : [
              {
                formatter: function (value) {
                  return value.toLocaleString("id-ID", {
                    style: "currency",
                    currency: "IDR",
                    maximumFractionDigits: 0,
                  });
                },
              },
            ],
      },
      title: {
        text: this.props.title,
        align: "center",
        style: {
          fontSize: "16px",
          fontWeight: "bold",
        },
      },
      legend: {
        position: "top",
        horizontalAlign: "center",
      },
      fill: {
        opacity: this.props.type === "bar" ? 1 : 0.7,
        type: this.props.type === "bar" ? "solid" : "gradient",
        gradient:
          this.props.type === "bar"
            ? undefined
            : {
              shadeIntensity: 1,
              opacityFrom: 0.7,
              opacityTo: 0.9,
              stops: [0, 90, 100],
            },
      },
    };

    return baseConfig;
  }

  renderChart() {
    // Validate chart reference and data
    if (!this.chartRef.el) {
      console.warn("Cannot render chart: invalid chart element");
      return;
    }

    if (this.chartInstance) {
      this.chartInstance.destroy();
    }

    this.chartRef.el.innerHTML = "";

    const isEmptyData =
      !this.state.chartData.series ||
      this.state.chartData.series.length === 0 ||
      this.state.chartData.series.every(
        (series) =>
          !series.data ||
          series.data.length === 0 ||
          series.data.every((value) => value === 0)
      );

    const config = {
      ...this.getChartConfig(),
      series: isEmptyData
        ? []
        : this.state.chartData.series.map((series) => ({
          ...series,
          data: series.data
            ? series.data.map((value) => Number(value) || 0)
            : [],
        })),
      chart: {
        ...this.getChartConfig().chart,
        events: {
          dataPointSelection: (event, chartContext, config) => {
            this.onChartClick(event, chartContext, config);
          },
        },
      },
      noData: {
        text: "Tidak ada data untuk ditampilkan",
        align: "center",
        verticalAlign: "middle",
        style: {
          color: "#6b7280",
          fontSize: "18px",
          fontWeight: "bold",
        },
      },
      yaxis: isEmptyData
        ? {
          show: false,
        }
        : this.getChartConfig().yaxis,
      // Menyembunyikan xaxis ketika tidak ada data
      xaxis: {
        ...this.getChartConfig().xaxis,
        labels: {
          ...this.getChartConfig().xaxis.labels,
          show: !isEmptyData,
        },
        axisBorder: {
          show: !isEmptyData,
        },
        axisTicks: {
          show: !isEmptyData,
        },
      },
      // Menyembunyikan grid ketika tidak ada data
      grid: {
        show: !isEmptyData,
      },
    };
    try {
      this.chartInstance = new ApexCharts(this.chartRef.el, config);
      this.chartInstance.render();
    } catch (error) {
      console.error("Error rendering chart:", error);
      // Potentially add fallback handling or user notification
    }
  }

  onChartClick(event, chartContext, config) {
    // Debounce to prevent duplicate clicks from dataPointSelection and click events
    const now = Date.now();
    if (this._lastClickTime && (now - this._lastClickTime) < 300) {
      return;
    }
    this._lastClickTime = now;

    const dataPointIndex = config.dataPointIndex;
    const seriesIndex = config.seriesIndex;

    if (dataPointIndex === -1 || seriesIndex === -1) return;

    if (!this.state?.chartData?.labels || !this.state?.chartData?.series) {
      console.error("Chart data is not properly initialized");
      return;
    }

    // Validate seriesIndex is within bounds
    if (seriesIndex >= this.state.chartData.series.length) {
      console.error("Invalid seriesIndex:", seriesIndex, "series length:", this.state.chartData.series.length);
      return;
    }

    const label = this.state.chartData.labels[dataPointIndex];
    const seriesName = this.state.chartData.series[seriesIndex]?.name || "";

    // Debug: log all series to verify correct index
    console.log("Available series:", this.state.chartData.series.map((s, i) => ({ index: i, name: s.name })));
    console.log("Clicked seriesIndex:", seriesIndex, "seriesName:", seriesName);

    if (!label) {
      console.error("Label not found for dataPointIndex:", dataPointIndex);
      return;
    }

    let actionConfig = {
      type: "ir.actions.act_window",
      name: `${this.props.title} - ${seriesName}`,
      view_mode: "list,form",
      target: "current",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      res_model: "",
      domain: [],
      context: {},
    };

    switch (this.props.title) {
      case "Tagihan Santri": {
        // Use account.move (invoice) directly for better filtering
        actionConfig.res_model = "account.move";
        actionConfig.name = `Tagihan ${label} - ${seriesName}`;

        // Create a fresh domain array (deep copy to prevent reference issues)
        let domain = JSON.parse(JSON.stringify([
          ["move_type", "in", ["out_invoice", "out_refund"]],
          ["state", "=", "posted"],
        ]));

        // Add date filter from current dashboard selection
        if (this.state.currentStartDate && this.state.currentEndDate) {
          domain.push(["invoice_date", ">=", this.state.currentStartDate]);
          domain.push(["invoice_date", "<=", this.state.currentEndDate]);
        }

        // ========================================
        // FIX: Add product/komponen filter based on clicked label
        // Ini yang menyebabkan bug sebelumnya - tidak ada filter product
        // ========================================
        if (label) {
          // Filter by product name in invoice lines
          // Label adalah nama product dari chart (contoh: "Baju Olahraga", "SPP", dll)
          domain.push(["invoice_line_ids.product_id.name", "ilike", label]);
        }

        // Filter berdasarkan status pembayaran (payment_state)
        console.log("Chart clicked - seriesName:", seriesName, "label (product):", label);

        if (seriesName === "Lunas") {
          // Lunas = invoice sudah dibayar penuh
          domain.push(["payment_state", "=", "paid"]);
        } else if (seriesName === "Belum Lunas") {
          // Belum Lunas = invoice belum dibayar atau partial
          domain.push(["payment_state", "in", ["not_paid", "partial", "in_payment"]]);
        } else if (seriesName === "Dibayar") {
          // Dibayar = sudah ada pembayaran (paid atau partial)
          domain.push(["payment_state", "in", ["paid", "partial", "in_payment"]]);
        } else if (seriesName === "Belum Bayar") {
          // Belum Bayar = tidak ada pembayaran sama sekali
          domain.push(["payment_state", "=", "not_paid"]);
        }

        console.log("Domain filter with product:", JSON.stringify(domain));
        actionConfig.domain = domain;
        break;
      }

      case "Uang Saku Masuk": {
        actionConfig.res_model = "cdn.uang_saku";
        actionConfig.domain = [["amount_in", ">", 0]];

        // Gunakan originalDate yang sudah dalam format YYYY-MM-DD
        if (this.state.chartData.originalDates && this.state.chartData.originalDates[dataPointIndex]) {
          const originalDate = this.state.chartData.originalDates[dataPointIndex];
          actionConfig.domain.push(["create_date", ">=", originalDate]);
          actionConfig.domain.push(["create_date", "<", this.getNextDay(originalDate)]);
        }
        break;
      }

      case "Uang Saku Keluar": {
        actionConfig.res_model = "cdn.uang_saku";
        actionConfig.domain = [["amount_out", ">", 0]];

        // Gunakan originalDate yang sudah dalam format YYYY-MM-DD
        if (this.state.chartData.originalDates && this.state.chartData.originalDates[dataPointIndex]) {
          const originalDate = this.state.chartData.originalDates[dataPointIndex];
          actionConfig.domain.push(["create_date", ">=", originalDate]);
          actionConfig.domain.push(["create_date", "<", this.getNextDay(originalDate)]);
        }
        break;
      }
    }

    this.actionService.doAction(actionConfig);
  }

  // Tambahkan method helper untuk mendapatkan hari berikutnya
  getNextDay(dateString) {
    try {
      const date = new Date(dateString);
      date.setDate(date.getDate() + 1);
      return date.toISOString().split('T')[0];
    } catch (error) {
      console.error("Error getting next day:", error);
      return dateString;
    }
  }

  toggleZoom = () => {
    console.log("Tombol zoom ditekan");
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

KeuanganChartRenderer.template = "owl.KeuanganChartRenderer";
