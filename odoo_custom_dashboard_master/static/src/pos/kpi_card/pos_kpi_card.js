/** @odoo-module **/
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, onMounted, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

export class PosKpiCard extends Component {
  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      labels: [],
      datasets: [],
      startDate: null,
      endDate: null,
      periodSelection: "month",
      kpiData: [],
    };
    this.refreshInterval = null;
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;

    onWillStart(async () => {
      await loadJS(
        "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"
      );
      await this.updateKpiData();
    });

    onMounted(() => {
      this.render();
      this.attachEventListeners();
      const periodSelection = document.getElementById("periodSelection");
      if (periodSelection) {
        periodSelection.value = "month";
      }
    });

    onWillUnmount(() => {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
      }
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
      }
    });
  }

  toggleCountdown() {
    if (this.isCountingDown) {
      // Jika sedang countdown, hentikan
      this.clearIntervals();
      //   document.getElementById("timerCountdown").innerHTML = "<i class='fas fa-clock'><   /i>";
    } else {
      // Jika tidak sedang countdown, mulai baru
      this.isCountingDown = true; // Set flag sebelum memulai countdown
      document.getElementById("timerCountdown").innerHTML = "";
      this.startCountdown();
    }
  }

  startCountdown() {
    this.countdownTime = 10;
    this.updateCountdownDisplay();
    this.countdownInterval = setInterval(() => {
      this.countdownTime--;
      if (this.countdownTime < 0) {
        this.countdownTime = 10;
        this.refreshChart(); // Refresh with current filter dates
      }
      this.updateCountdownDisplay();
    }, 1000);
  }

  updateCountdownDisplay() {
    document.getElementById("timerCountdown").innerHTML = this.countdownTime;
  }

  refreshChart() {
    const period = document.getElementById("periodSelection")?.value;
    const today = new Date();
    let startDate, endDate;

    if (period === "today") {
      // Today
      // Set startDate and endDate to today's date in UTC
      startDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate(),
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
          59
        )
      );
    } else if (period === "yesterday") {
      // Yesterday
      // Set startDate and endDate to yesterday's date in UTC
      startDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - 1,
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
          59
        )
      );
    } else if (period === "thisweek") {
      // thisweeek
      // Set startDate to 7 days ago from today in UTC, and endDate to the end of today
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
    } else if (period === "lastweek") {
      // Lastweek
      // Set startDate to 15 days ago from today in UTC, and endDate to the end of today
      startDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - (today.getDay() + 7),
          0,
          0,
          0
        )
      );
      endDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - (today.getDay() + 1),
          23,
          59,
          59
        )
      );
    } else if (period === "month") {
      // Current month to date
      // Set startDate to the first day of the current month in UTC, and endDate to the current day in UTC
      startDate = new Date(
        Date.UTC(today.getFullYear(), today.getMonth(), 1, 0, 0, 0)
      );
      endDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate(),
          23,
          59,
          59
        )
      );
    } else if (period === "lastMonth") {
      // Last month
      // Set startDate to the first day of the previous month in UTC, and endDate to the last day of the previous month in UTC
      startDate = new Date(
        Date.UTC(today.getFullYear(), today.getMonth() - 1, 1, 0, 0, 0)
      );
      endDate = new Date(
        Date.UTC(today.getFullYear(), today.getMonth(), 0, 23, 59, 59)
      );
    } else if (period === "thisyear") {
      startDate = new Date(Date.UTC(today.getUTCFullYear(), 0, 1, 0, 0, 0));
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
    } else if (period === "lastyear") {
      startDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 0, 1, 0, 0, 0));
      endDate = new Date(
        Date.UTC(today.getUTCFullYear() - 1, 11, 31, 23, 59, 59, 999)
      );
    }

    if (startDate && endDate) {
      console.log(
        "Refreshing chart with filtered data from",
        startDate,
        "to",
        endDate
      );
      this.updateKpiData(startDate.toISOString(), endDate.toISOString());
    }
  }

  clearIntervals() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);
    if (this.refreshInterval) clearInterval(this.refreshInterval);
  }

  async updateKpiData(startDate = null, endDate = null) {
    const today = new Date();
    if (!startDate || !endDate) {
      startDate = new Date(today.getFullYear(), today.getMonth(), 1, 0, 0, 0);
      endDate = new Date(
        today.getFullYear(),
        today.getMonth() + 1,
        0,
        23,
        59,
        59
      );
    }

    try {
      const dateDomain = [
        ["date_order", ">=", startDate],
        ["date_order", "<=", endDate],
      ];
      const storeFilter =
        document.getElementById("storeFilter")?.value || "all";
      if (storeFilter && storeFilter !== "all") {
        dateDomain.push(["config_id", "=", parseInt(storeFilter)]);
      }

      // Get all products with type 'consu'
      const consuProducts = await this.orm.call(
        "product.product",
        "search_read",
        [[["type", "=", "consu"]], ["id"]]
      );

      const consuProductIds = consuProducts.map((product) => product.id);

      // Get current period orders
      const currentPeriodOrders = await this.orm.call(
        "pos.order",
        "search_read",
        [dateDomain, ["id", "amount_total", "name", "date_order", "lines"]]
      );

      // Get order lines for 'consu' products
      const currentOrderLines = await this.orm.call(
        "pos.order.line",
        "search_read",
        [
          [
            ["order_id", "in", currentPeriodOrders.map((order) => order.id)],
            ["product_id", "in", consuProductIds],
          ],
          ["product_id", "qty"],
        ]
      );

      // Calculate total quantity of 'consu' products sold
      const totalConsuSold = currentOrderLines.reduce(
        (total, line) => total + line.qty,
        0
      );

      // Get active POS sessions
      const activeSessions = await this.orm.call("pos.session", "search_read", [
        [["state", "=", "opened"]],
        ["name", "start_at"],
      ]);

      // Get previous period data
      const previousPeriodStartDate = this.getStartOfPreviousPeriod(
        startDate,
        endDate
      );
      const previousPeriodEndDate = this.getEndOfPreviousPeriod(
        startDate,
        endDate
      );

      const previousPeriodOrders = await this.orm.call(
        "pos.order",
        "search_read",
        [
          [
            ["date_order", ">=", previousPeriodStartDate],
            ["date_order", "<=", previousPeriodEndDate],
          ],
          ["id", "amount_total", "name", "date_order", "lines"],
        ]
      );

      const previousOrderLines = await this.orm.call(
        "pos.order.line",
        "search_read",
        [
          [
            ["order_id", "in", previousPeriodOrders.map((order) => order.id)],
            ["product_id", "in", consuProductIds],
          ],
          ["product_id", "qty"],
        ]
      );

      const totalPreviousConsuSold = previousOrderLines.reduce(
        (total, line) => total + line.qty,
        0
      );

      console.log("Total Produk Terjual", currentOrderLines);

      this.processData(
        currentPeriodOrders,
        previousPeriodOrders,
        currentOrderLines,
        previousOrderLines,
        activeSessions,
        { totalConsuSold, totalPreviousConsuSold }
      );
    } catch (error) {
      console.error("Error fetching POS data:", error);
    }
  }

  formatLargeNumber(number) {
    if (number >= 1000000) {
      return (number / 1000000).toFixed(1).replace(/\.0$/, "") + " jt";
    } else if (number >= 1000) {
      return (number / 1000).toFixed(0) + "rb";
    }
    return number.toFixed(0);
  }

  getStartOfPreviousPeriod(startDate, endDate) {
    const currentStart = new Date(startDate);
    const currentEnd = new Date(endDate);
    const periodDays = Math.max(
      1,
      Math.ceil((currentEnd - currentStart) / (1000 * 60 * 60 * 24)) + 1
    );
    const previousStart = new Date(currentStart);
    previousStart.setDate(currentStart.getDate() - periodDays);
    return previousStart.toISOString().split("T")[0];
  }

  getEndOfPreviousPeriod(startDate) {
    const currentStart = new Date(startDate);
    const previousEnd = new Date(currentStart);
    previousEnd.setDate(currentStart.getDate() - 1);
    return previousEnd.toISOString().split("T")[0];
  }

  processData(
    currentPeriodOrders,
    previousPeriodOrders,
    currentOrderLines,
    previousOrderLines,
    activeSessions
  ) {
    // Calculate totals
    const totalOrdersCurrent = currentPeriodOrders.length || 0;
    const totalOrdersPrevious = previousPeriodOrders.length || 0;

    const revenueCurrent = currentPeriodOrders.reduce(
      (sum, order) => sum + order.amount_total,
      0
    );
    const revenuePrevious = previousPeriodOrders.reduce(
      (sum, order) => sum + order.amount_total,
      0
    );

    const totalProductsCurrent = currentOrderLines.length;

    const totalProductsPrevious = previousOrderLines.reduce(
      (sum, line) => sum + line.qty,
      0
    );

    const percentageChange = (current, previous) => {
      if (previous === 0 && current > 0) return 100;
      if (previous === 0 && current === 0) return 0;
      if (previous === 0 && current < 0) return -100;
      return ((current - previous) / previous) * 100;
    };

    const getColor = (percentage) => {
      if (percentage > 0) return "green";
      if (percentage < 0) return "red";
      return "gray";
    };

    this.state.kpiData = [
      {
        name: "Pendapatan",
        value: this.formatLargeNumber(revenueCurrent),
        percentage: percentageChange(revenueCurrent, revenuePrevious).toFixed(
          2
        ),
        color: getColor(percentageChange(revenueCurrent, revenuePrevious)),
        icon: "fa-money-bill",
        previousValue: this.formatLargeNumber(revenuePrevious),
      },
      {
        name: "Order",
        value: totalOrdersCurrent,
        percentage: percentageChange(
          totalOrdersCurrent,
          totalOrdersPrevious
        ).toFixed(2),
        color: getColor(
          percentageChange(totalOrdersCurrent, totalOrdersPrevious)
        ),
        icon: "fa-shopping-cart",
        previousValue: totalOrdersPrevious,
      },
      {
        name: "Produk Terjual",
        value: totalProductsCurrent,
        percentage: percentageChange(
          totalProductsCurrent,
          totalProductsPrevious
        ).toFixed(2),
        color: getColor(
          percentageChange(totalProductsCurrent, totalProductsPrevious)
        ),
        icon: "fa-box",
        previousValue: totalProductsPrevious,
      },
      {
        name: "Sesi Aktif",
        value: activeSessions.length,
        percentage: 0,
        color: "green",
        icon: "fa-cash-register",
      },
    ];

    console.log("KPI Data:", this.state.kpiData);
    this.render();
  }

  attachEventListeners() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");

    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", () => this.filterData());
      endDateInput.addEventListener("change", () => this.filterData());
    } else {
      console.error("Date input elements not found");
    }

    if (periodSelection) {
      periodSelection.addEventListener(
        "change",
        this.filterDataByPeriod.bind(this)
      );
    } else {
      console.error("Period selection element not found");
    }

    if (periodSelection) {
      periodSelection.addEventListener("change", () => {
        console.log("Period selection changed");
        this.filterDataByPeriod();
      });
    } else {
      console.error("Period selection element not found");
    }

    kpiCards.forEach((card) => {
      card.addEventListener("click", (evt) => {
        this.handleKpiCardClick(evt);
      });
    });
  }

  attachEventListeners() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");
    const storeFilter = document.getElementById("storeFilter");

    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", () => this.filterData());
      endDateInput.addEventListener("change", () => this.filterData());
    } else {
      console.error("Date input elements not found");
    }

    if (periodSelection) {
      periodSelection.addEventListener(
        "change",
        this.filterDataByPeriod.bind(this)
      );
    } else {
      console.error("Period selection element not found");
    }

    if (storeFilter) {
      storeFilter.addEventListener("change", () => {
        this.state.storeFilter = storeFilter.value;
        this.filterData();
      });
    }

    // COUNTDOWN
    const timerButton = document.getElementById("timerButton");
    timerButton.addEventListener("click", this.toggleCountdown.bind(this));
  }

  filterData() {
    const startDate = document.getElementById("startDate")?.value;
    const endDate = document.getElementById("endDate")?.value;

    if (startDate && endDate) {
      this.state.startDate = startDate; // Store in state
      this.state.endDate = endDate; // Store in state
      this.updateKpiData(startDate, endDate);
    } else {
      this.state.startDate = null;
      this.state.endDate = null;
      this.updateKpiData();
    }
  }

  filterDataByPeriod() {
    const period = document.getElementById("periodSelection")?.value;
    const today = new Date();
    let startDate, endDate;

    if (period === "today") {
      // Today
      // Set startDate and endDate to today's date in UTC
      startDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate(),
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
          59
        )
      );
    } else if (period === "yesterday") {
      // Yesterday
      // Set startDate and endDate to yesterday's date in UTC
      startDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - 1,
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
          59
        )
      );
    } else if (period === "thisweek") {
      // Last 7 days
      // Set startDate to 7 days ago from today in UTC, and endDate to the end of today
      startDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - 7,
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
          59
        )
      );
    } else if (period === "lastweek") {
      // Last 15 days
      // Set startDate to 15 days ago from today in UTC, and endDate to the end of today
      startDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - (today.getDay() + 7),
          0,
          0,
          0
        )
      );
      endDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate() - (today.getDay() + 1),
          23,
          59,
          59
        )
      );
    } else if (period === "month") {
      // Current month to date
      // Set startDate to the first day of the current month in UTC, and endDate to the current day in UTC
      startDate = new Date(
        Date.UTC(today.getFullYear(), today.getMonth(), 1, 0, 0, 0)
      );
      endDate = new Date(
        Date.UTC(
          today.getFullYear(),
          today.getMonth(),
          today.getDate(),
          23,
          59,
          59
        )
      );
    } else if (period === "lastMonth") {
      // Last month
      // Set startDate to the first day of the previous month in UTC, and endDate to the last day of the previous month in UTC
      startDate = new Date(
        Date.UTC(today.getFullYear(), today.getMonth() - 1, 1, 0, 0, 0)
      );
      endDate = new Date(
        Date.UTC(today.getFullYear(), today.getMonth(), 0, 23, 59, 59)
      );
    } else if (period === "thisyear") {
      startDate = new Date(Date.UTC(today.getUTCFullYear(), 0, 1, 0, 0, 0));
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
    } else if (period === "lastyear") {
      startDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 0, 1, 0, 0, 0));
      endDate = new Date(
        Date.UTC(today.getUTCFullYear() - 1, 11, 31, 23, 59, 59, 999)
      );
    }

    if (startDate && endDate) {
      this.state.startDate = startDate.toISOString().split("T")[0];
      this.state.endDate = endDate.toISOString().split("T")[0];
      this.updateKpiData(this.state.startDate, this.state.endDate);
      console.log("update filterdatabyperiod success on kpi");
    } else {
      console.error("Invalid period selection in KPI.");
    }
  }

  render() {
    const kpiContainer = document.querySelector(".row");

    // Clear existing elements
    kpiContainer.innerHTML = "";

    // Render new KPI Cards
    this.state.kpiData.forEach((kpi) => {
      const cardHtml = `
              <div class="col-lg-3 px-1">
                  <div class="d-flex justify-content-between align-items-center kpi-card shadow-sm py-3 mx-1 px-4 w-100" 
                       data-name="${kpi.name}" 
                       style="background-color: #ffffff; border-radius: 5px; cursor: pointer;">
                      
                      <!-- Left Section: KPI Value and Name -->
                      <div class="text-start">
                          <!-- KPI Value -->
                          <div class="h2 fw-bold text-primary" style="font-size: 35px;">
                              ${kpi.value}
                          </div>
                                 
                          <!-- KPI Name -->
                          <div class="text-muted text-nowrap" style="font-size: 16px;">
                              ${kpi.name}
                          </div>
                      </div>
                      
                      <!-- Right Section: Icon -->
                      <div class="text-end" style="font-size: 2em; color: #0cba3e;">
                          <i class="fa ${kpi.icon}"></i>
                      </div>
                      
                  </div>
              </div>
          `;
      kpiContainer.insertAdjacentHTML("beforeend", cardHtml);
    });

    const kpiCards = document.querySelectorAll(".kpi-card");
    kpiCards.forEach((card) => {
      card.addEventListener("click", (evt) => this.handleKpiCardClick(evt));
    });
  }
  async handleKpiCardClick(evt) {
    const cardName = evt.currentTarget.dataset.name;
    let { startDate, endDate } = this.state;

    if (!startDate || !endDate) {
      const today = new Date();
      const firstDayOfMonth = new Date(
        today.getFullYear(),
        today.getMonth(),
        1
      );
      startDate = firstDayOfMonth.toISOString().split("T")[0];
      endDate = today.toISOString().split("T")[0];
    }

    const storeFilter = document.getElementById("storeFilter")?.value || "all";
    let domain = [
      ["date_order", ">=", startDate],
      ["date_order", "<=", endDate],
    ];

    if (storeFilter && storeFilter !== "all") {
      domain.push(["config_id", "=", parseInt(storeFilter)]);
    }

    let actionConfig = {
      type: "ir.actions.act_window",
      view_mode: "list",
      views: [[false, "list"]],
      target: "current",
    };

    let domainProduk = [
      ["create_date", ">=", startDate],
      ["create_date", "<=", endDate],
      ["price_unit", ">=", 0],
    ];

    // Sesuaikan konfigurasi aksi berdasarkan jenis kartu KPI
    switch (cardName) {
      case "Pendapatan":
        actionConfig = {
          ...actionConfig,
          name: "Detail Pendapatan",
          res_model: "pos.order",
          domain: domain,
        };
        break;

      case "Order":
        actionConfig = {
          ...actionConfig,
          name: "Detail Order",
          res_model: "pos.order",
          domain: domain,
        };
        break;

      case "Produk Terjual":
        actionConfig = {
          ...actionConfig,
          name: "Detail Produk Terjual",
          res_model: "pos.order.line",
          domain: domainProduk,
        };
        break;

      case "Sesi Aktif":
        actionConfig = {
          ...actionConfig,
          name: "Sesi POS Aktif",
          res_model: "pos.session",
          domain: [["state", "=", "opened"]],
        };
        break;

      default:
        console.warn(`Tidak ada aksi untuk jenis kartu: ${cardName}`);
        return; // Jangan lakukan apa pun jika tipe kartu tidak dikenali
    }

    try {
      await this.actionService.doAction(actionConfig);
    } catch (error) {
      console.error("Error handling card click:", error);
    }
  }
}

PosKpiCard.template = "owl.PosKpiCard";
