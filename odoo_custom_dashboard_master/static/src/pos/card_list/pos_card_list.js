/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PosCardList extends Component {
  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      products: [],
      startDate: null, // Store start date in state
      endDate: null, // Default to the current month's end date
      periodSelection: "month", // Default period is custom until user selects one
    };

    onMounted(() => {
      this.attachEventListeners();
      const periodSelection = document.getElementById("periodSelection");
      if (periodSelection) {
        periodSelection.value = "month";
      }
    });

    onWillStart(async () => {
      await this.fetchTopSellingProducts();
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
  // FUNC COUNTDOWN
  toggleCountdown() {
    if (this.isCountingDown) {
      // Jika sedang countdown, hentikan
      this.clearIntervals();
      // document.getElementById("timerCountdown").innerHTML = "<i class='fas fa-clock'></i>";
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
        this.refreshTabelList(); // Refresh with current filter dates
      }
      this.updateCountdownDisplay();
    }, 1000);
  }

  updateCountdownDisplay() {
    document.getElementById("timerCountdown").innerHTML = this.countdownTime;
  }

  refreshTabelList() {
    const period = document.getElementById("periodSelection")?.value;
    const today = new Date();
    let startDate, endDate;

    if (period === "today") {
      startDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate(),
        0,
        0,
        0
      );
      endDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate(),
        23,
        59,
        59
      );
    } else if (period === "yesterday") {
      startDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() - 1,
        0,
        0,
        0
      );
      endDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() - 1,
        23,
        59,
        59
      );
    } else if (period === "thisweek") {
      // Last 7 days
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
      // Last 15 days
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
    } else if (period === "month") {
      // Full current month
      startDate = new Date(today.getFullYear(), today.getMonth(), 1); // First day of the month
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0); // Last day of the month
    } else if (period === "lastMonth") {
      // Last month
      startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1); // First day of last month
      endDate = new Date(today.getFullYear(), today.getMonth(), 0); // Last day of last month
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
    } else if (period == "lastyear") {
      startDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 0, 1, 0, 0, 0));
      endDate = new Date(
        Date.UTC(today.getUTCFullYear() - 1, 11, 31, 23, 59, 59, 999)
      );
    } else if (period === "lastyear")
      if (startDate && endDate) {
        // Call fetchTopSellingProducts with the correct date range
        this.fetchTopSellingProducts(
          startDate.toISOString(),
          endDate.toISOString()
        );
        console.log(
          "(from Refresh) update filterdatabyperiod success on chart"
        );
      } else {
        console.error("(from Refresh) Invalid period selection in Chart.");
      }
  }
  clearIntervals() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);
    if (this.refreshInterval) clearInterval(this.refreshInterval);
  }

  // Fetch top-selling products with filtering by date range
  async fetchTopSellingProducts(startDate = null, endDate = null) {
    const today = new Date();
    if (!startDate || !endDate) {
      // Set startDate to the start of the current month
      startDate = new Date(today.getFullYear(), today.getMonth(), 1, 0, 0, 0);
      // Set endDate to the end of the current month
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
      // Get the selected store ID from the filter
      const storeFilter = document.getElementById("storeFilter");
      const selectedStoreId = storeFilter ? parseInt(storeFilter.value) : null;

      // Build the domain with base conditions
      let domainProduk = [
        ["order_id.state", "!=", "cancel"],
        ["order_id.date_order", ">=", startDate],
        ["order_id.date_order", "<=", endDate],
        ["price_subtotal_incl", ">=", 0],
      ];

      // Add store filter condition if a store is selected
      if (selectedStoreId) {
        domainProduk.push(["order_id.config_id", "=", selectedStoreId]);
      }

      // Fetch data from pos.order.line with the updated domain
      const productData = await this.orm.call(
        "pos.order.line",
        "search_read",
        [
          domainProduk,
          ["product_id", "price_subtotal_incl", "qty", "order_id"],
        ],
        { order: "product_id asc" }
      );

      // Group data by product name
      const groupedData = productData.reduce((acc, item) => {
        const productId = item.product_id[0]; // Product ID
        const productName = item.product_id[1]; // Product name

        if (!acc[productName]) {
          acc[productName] = {
            name: productName,
            totalSales: 0,
            soldStock: 0,
            productId: productId,
          };
        }
        acc[productName].totalSales += item.price_subtotal_incl;
        acc[productName].soldStock += item.qty;
        return acc;
      }, {});

      // Convert grouped data to an array, sort by soldStock (descending), and take top 5
      const products = Object.values(groupedData)
        .sort((a, b) => b.soldStock - a.soldStock) // Sort by soldStock descending
        .slice(0, 5) // Top 5 products
        .map((product, index) => ({
          number: index + 1,
          name:
            product.name.length > 20
              ? product.name.substring(0, 15) + "..."
              : product.name, // Truncate if longer than 15 characters
          fullname: product.name,
          totalSales: this.formatCurrency(product.totalSales),
          soldStock: product.soldStock,
          productId: product.productId,
        }));

      // Update the state with the new products list
      this.state.products = products;
      this.render();
      this.attachEventListeners();
    } catch (error) {
      console.error("Error fetching POS product data:", error);
    }
  }

  // Format currency with "Rp" and thousand separator
  formatCurrency(amount) {
    return "Rp " + amount.toLocaleString("id-ID");
  }

  // Attach event listeners for date inputs and filter
  attachEventListeners() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");

    const storeFilter = document.getElementById("storeFilter");
    if (storeFilter) {
      storeFilter.addEventListener("change", () => {
        this.fetchTopSellingProducts(
          this.state.startDate2,
          this.state.endDate2
        );
      });
    }

    // Handle date input change
    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", () => this.filterData());
      endDateInput.addEventListener("change", () => this.filterData());
    } else {
      console.error("Date input elements not found");
    }

    // Handle period selection change
    if (periodSelection) {
      periodSelection.addEventListener(
        "change",
        this.filterDataByPeriod.bind(this)
      );
    } else {
      console.error("Period selection element not found");
    }

    // Attach event listeners to table cards
    const tableList = document.querySelectorAll(".tabel-list");
    tableList.forEach((card) => {
      card.addEventListener("click", (evt) => {
        this.handleListClick(evt); // Ensure correct 'this' context
      });
    });

    // COUNTDOWN
    const timerButton = document.getElementById("timerButton");
    timerButton.addEventListener("click", this.toggleCountdown.bind(this));

    const datePickerButton = document.getElementById("datePickerButton");
    const datePickerContainer = document.getElementById("datePickerContainer");

    if (datePickerButton && datePickerContainer) {
      datePickerButton.addEventListener("click", (event) => {
        event.stopPropagation(); // Menghentikan event dari bubbling ke atas
        datePickerContainer.style.display = "flex";
      });
    } else {
      console.error("Date picker button or container element not found");
    }

    document.addEventListener("click", (event) => {
      const datePickerContainer = document.getElementById(
        "datePickerContainer"
      );
      const datePickerButton = document.getElementById("datePickerButton");
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
    const startDateInput = document.getElementById("startDate")?.value;
    const endDateInput = document.getElementById("endDate")?.value;

    if (startDateInput && endDateInput) {
      const startDate = new Date(startDateInput).toISOString().split("T")[0];
      const endDate = new Date(endDateInput).toISOString().split("T")[0];
      this.fetchTopSellingProducts(startDate, endDate);
      console.log("Data filtered between selected dates.");
    } else {
      console.error("Start date or end date input is missing.");
    }
  }

  // Function to calculate the start and end dates based on the selected period
  filterDataByPeriod() {
    const period = document.getElementById("periodSelection")?.value;
    const today = new Date();
    let startDate, endDate;

    if (period === "today") {
      // Set startDate to beginning of today (00:00:00)
      startDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate(),
        0,
        0,
        0
      );
      // Set endDate to end of today (23:59:59)
      endDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate(),
        23,
        59,
        59
      );
    } else if (period === "yesterday") {
      // Set startDate to beginning of yesterday
      startDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() - 1,
        0,
        0,
        0
      );
      // Set endDate to end of yesterday
      endDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() - 1,
        23,
        59,
        59
      );
    } else if (periodSelection === "7") {
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 7); // Set to 7 days ago
      startDate.setHours(0, 0, 0, 0); // Set start time to midnight

      endDate = new Date(today);
      endDate.setHours(23, 59, 59, 999); // Set end time to end of today
    } else if (period === "15") {
      // Last 15 days
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 15);
      endDate = today;
    } else if (period === "month") {
      // Current month to date
      startDate = new Date(
        Date.UTC(today.getFullYear(), today.getMonth(), 1, 0, 0, 0)
      );
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    } else if (period === "lastMonth") {
      // Last month
      startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      endDate = new Date(today.getFullYear(), today.getMonth(), 0);
    }

    if (startDate && endDate) {
      // Call fetchTopSellingProducts with the correct date range
      this.fetchTopSellingProducts(
        startDate.toISOString(),
        endDate.toISOString()
      );
      console.log("update filterdatabyperiod success on chart");
    } else {
      console.error("Invalid period selection in Chart.");
    }
  }

  async handleListClick(evt) {
    const productId = evt.currentTarget.dataset.productId;
    console.log("Product_id:", productId);

    // Get the current period selection
    const periodSelection = document.getElementById("periodSelection")?.value;
    const storeFilter = document.getElementById("storeFilter")?.value;
    const today = new Date();
    let startDate, endDate;

    // Calculate date range based on period selection
    if (periodSelection === "today") {
      startDate = new Date(today.setHours(0, 0, 0, 0)); // set time to midnight
      endDate = new Date(today.setHours(23, 59, 59, 999)); // set time to end of the day
    } else if (periodSelection === "yesterday") {
      today.setDate(today.getDate() - 1); // Set date to yesterday
      startDate = new Date(today.setHours(0, 0, 0, 0)); // Set to midnight of yesterday
      endDate = new Date(today.setHours(23, 59, 59, 999)); // End of yesterday
    } else if (periodSelection === "7") {
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 7); // Set to 7 days ago
      startDate.setHours(0, 0, 0, 0); // Set start time to midnight

      endDate = new Date(today);
      endDate.setHours(23, 59, 59, 999); // Set end time to end of today
    } else if (periodSelection === "15") {
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 15);
      endDate = today;
    } else if (periodSelection === "month") {
      startDate = new Date(today.getFullYear(), today.getMonth(), 1);
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0); // Last day of the month
    } else if (periodSelection === "lastMonth") {
      startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      endDate = new Date(today.getFullYear(), today.getMonth(), 0); // Last day of the previous month
    }

    // Build the domain filter
    let domain = [
      ["product_id", "=", parseInt(productId)],
      ["order_id.state", "!=", "cancel"],
    ];

    if (storeFilter && storeFilter !== "all") {
      domain.push(["order_id.config_id", "=", parseInt(storeFilter)]);
    }

    // Add date filters if dates are available
    if (startDate && endDate) {
      domain.push(
        ["order_id.date_order", ">=", startDate.toISOString()],
        ["order_id.date_order", "<=", endDate.toISOString()]
      );
    }

    console.log("Domain:", domain);

    // Stop countdown if it's running
    this.isCountingDown = false;
    this.clearIntervals();

    // Redirect to POS order line list view with filters
    await this.actionService.doAction({
      name: `Sales Details for Product ${productId}`,
      type: "ir.actions.act_window",
      res_model: "pos.order.line", // Changed from purchase.order.line to pos.order.line
      view_mode: "list",
      views: [[false, "list"]],
      target: "current",
      domain: domain,
      context: {
        create: false, // Disable creation of new records in the list view
      },
    });
  }
}
PosCardList.template = "owl.PosCardList";

export class PosCardList1 extends Component {
  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      partners: [],
      startDate: null, // Store start date in state
      endDate: null, // Default to the current month's end date
      periodSelection: "month", // Default period is custom until user selects one
    };

    onMounted(() => {
      this.attachEventListeners();
      const periodSelection = document.getElementById("periodSelection");
      if (periodSelection) {
        periodSelection.value = "month";
      }
    });

    onWillStart(async () => {
      await this.fetchTopSellingPartners();
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
  // FUNC COUNTDOWN
  toggleCountdown() {
    if (this.isCountingDown) {
      // Jika sedang countdown, hentikan
      this.clearIntervals();
      // document.getElementById("timerCountdown").innerHTML = "<i class='fas fa-clock'></i>";
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
        this.refreshTabelList(); // Refresh with current filter dates
      }
      this.updateCountdownDisplay();
    }, 1000);
  }

  updateCountdownDisplay() {
    document.getElementById("timerCountdown").innerHTML = this.countdownTime;
  }

  refreshTabelList() {
    const period = document.getElementById("periodSelection")?.value;
    const today = new Date();
    let startDate, endDate;

    if (period === "today") {
      // Set startDate to beginning of today (00:00:00)
      startDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate(),
        0,
        0,
        0
      );
      // Set endDate to end of today (23:59:59)
      endDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate(),
        23,
        59,
        59
      );
    } else if (period === "yesterday") {
      startDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() - 1,
        0,
        0,
        0
      );
      endDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() - 1,
        23,
        59,
        59
      );
    } else if (period === "7") {
      // Last 7 days
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 7);
      endDate = today;
    } else if (period === "15") {
      // Last 15 days
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 15);
      endDate = today;
    } else if (period === "month") {
      // Full current month
      startDate = new Date(today.getFullYear(), today.getMonth(), 1); // First day of the month
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0); // Last day of the month
    } else if (period === "lastMonth") {
      // Last month
      startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1); // First day of last month
      endDate = new Date(today.getFullYear(), today.getMonth(), 0); // Last day of last month
    }

    if (startDate && endDate) {
      // Call fetchTopSellingPartners with the correct date range
      this.fetchTopSellingPartners(
        startDate.toISOString(),
        endDate.toISOString()
      );
      console.log("(from Refresh) update filterdatabyperiod success on chart");
    } else {
      console.error("(from Refresh) Invalid period selection in Chart.");
    }
  }
  clearIntervals() {
    if (this.countdownInterval) clearInterval(this.countdownInterval);
    if (this.refreshInterval) clearInterval(this.refreshInterval);
  }

  // Fetch top-selling products with filtering by date range
  async fetchTopSellingPartners(startDate = null, endDate = null) {
    const today = new Date();
    if (!startDate || !endDate) {
      // Set startDate to the first day of the current month
      startDate = new Date(today.getFullYear(), today.getMonth(), 1, 0, 0, 0);
      // Set endDate to the last day of the current month
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
      // Fetch data from pos.order, focusing on partner_id
      const partnerData = await this.orm.call(
        "pos.order",
        "search_read",
        [
          [
            ["state", "!=", "cancel"],
            ["date_order", ">=", startDate],
            ["date_order", "<=", endDate],
            ["partner_id", "!=", false],
          ],
          ["partner_id", "amount_total"],
        ],
        { order: "partner_id asc" }
      );

      // Group data by partner name
      const groupedData = partnerData.reduce((acc, item) => {
        const partnerId = item.partner_id[0]; // ID of the partner
        const partnerName = item.partner_id[1] || "Unknown Partner"; // Name of the partner (fallback to 'Unknown Partner')

        if (!acc[partnerName]) {
          acc[partnerName] = {
            name: partnerName,
            totalSales: 0,
            totalOrders: 0,
            partnerId: partnerId, // Store partner ID
          };
        }
        acc[partnerName].totalSales += item.amount_total; // Add to total sales
        acc[partnerName].totalOrders += 1; // Increment order count
        return acc;
      }, {});

      // Convert grouped data to an array, sort by totalSales (descending), and take top 5
      const partners = Object.values(groupedData)
        .sort((a, b) => b.totalSales - a.totalSales) // Sort by totalSales descending
        .slice(0, 5) // Take the top 5 partners
        .map((partner, index) => ({
          number: index + 1,
          name: partner.name,
          totalSales: this.formatCurrency(partner.totalSales),
          totalOrders: partner.totalOrders,
          partnerId: partner.partnerId, // Ensure partnerId is included
        }));

      // Update the state with the new partners list
      this.state.partners = partners;
      this.render();
      this.attachEventListeners(); // Reattach event listeners after re-rendering
    } catch (error) {
      console.error("Error fetching POS partner data:", error);
    }
  }

  // Format currency with "Rp" and thousand separator
  formatCurrency(amount) {
    return "Rp " + amount.toLocaleString("id-ID");
  }

  // Attach event listeners for date inputs and filter
  attachEventListeners() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");
    const storeFilter = document.getElementById("storeFilter");

    // Handle date input change
    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", () => this.filterData());
      endDateInput.addEventListener("change", () => this.filterData());
    } else {
      console.error("Date input elements not found");
    }

    // Handle period selection change
    if (periodSelection) {
      periodSelection.addEventListener(
        "change",
        this.filterDataByPeriod.bind(this)
      );
    } else {
      console.error("Period selection element not found");
    }

    // Attach event listeners to table cards
    const tableList = document.querySelectorAll(".tabel-list-cust");
    tableList.forEach((card) => {
      card.addEventListener("click", (evt) => {
        this.handleListClick(evt); // Ensure correct 'this' context
      });
    });

    // COUNTDOWN
    const timerButton = document.getElementById("timerButton");
    timerButton.addEventListener("click", this.toggleCountdown.bind(this));

    const datePickerButton = document.getElementById("datePickerButton");
    const datePickerContainer = document.getElementById("datePickerContainer");

    if (datePickerButton && datePickerContainer) {
      datePickerButton.addEventListener("click", (event) => {
        event.stopPropagation(); // Menghentikan event dari bubbling ke atas
        datePickerContainer.style.display = "flex";
      });
    } else {
      console.error("Date picker button or container element not found");
    }

    document.addEventListener("click", (event) => {
      const datePickerContainer = document.getElementById(
        "datePickerContainer"
      );
      const datePickerButton = document.getElementById("datePickerButton");
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
    const startDateInput = document.getElementById("startDate")?.value;
    const endDateInput = document.getElementById("endDate")?.value;

    if (startDateInput && endDateInput) {
      const startDate = new Date(startDateInput).toISOString().split("T")[0];
      const endDate = new Date(endDateInput).toISOString().split("T")[0];
      this.fetchTopSellingPartners(startDate, endDate);
      console.log("Data filtered between selected dates.");
    } else {
      console.error("Start date or end date input is missing.");
    }
  }

  // Function to calculate the start and end dates based on the selected period
  filterDataByPeriod() {
    const period = document.getElementById("periodSelection")?.value;
    const today = new Date();
    let startDate, endDate;

    if (period === "today") {
      // Set startDate to beginning of today (00:00:00)
      startDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate(),
        0,
        0,
        0
      );
      // Set endDate to end of today (23:59:59)
      endDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate(),
        23,
        59,
        59
      );
    } else if (period === "yesterday") {
      // Set startDate to beginning of yesterday
      startDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() - 1,
        0,
        0,
        0
      );
      // Set endDate to end of yesterday
      endDate = new Date(
        today.getFullYear(),
        today.getMonth(),
        today.getDate() - 1,
        23,
        59,
        59
      );
    } else if (periodSelection === "7") {
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 7); // Set to 7 days ago
      startDate.setHours(0, 0, 0, 0); // Set start time to midnight

      endDate = new Date(today);
      endDate.setHours(23, 59, 59, 999); // Set end time to end of today
    } else if (period === "15") {
      // Last 15 days
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 15);
      endDate = today;
    } else if (period === "month") {
      // Current month to date
      startDate = new Date(
        Date.UTC(today.getFullYear(), today.getMonth(), 1, 0, 0, 0)
      );
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    } else if (period === "lastMonth") {
      // Last month
      startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      endDate = new Date(today.getFullYear(), today.getMonth(), 0);
    }

    if (startDate && endDate) {
      // Call fetchTopSellingPartners with the correct date range
      this.fetchTopSellingPartners(
        startDate.toISOString(),
        endDate.toISOString()
      );
      console.log("update filterdatabyperiod success on chart");
    } else {
      console.error("Invalid period selection in Chart.");
    }
  }

  async handleListClick(evt) {
    const custID = evt.currentTarget.dataset.partnerId;
    console.log("Customer:", custID);

    // Get the current period selection
    const periodSelection = document.getElementById("periodSelection")?.value;
    const storeFilter = document.getElementById("storeFilter")?.value;
    const today = new Date();
    let startDate, endDate;

    // Calculate date range based on period selection
    if (periodSelection === "today") {
      startDate = new Date(today.setHours(0, 0, 0, 0)); // set time to midnight
      endDate = new Date(today.setHours(23, 59, 59, 999)); // set time to end of the day
    } else if (periodSelection === "yesterday") {
      today.setDate(today.getDate() - 1); // Set date to yesterday
      startDate = new Date(today.setHours(0, 0, 0, 0)); // Set to midnight of yesterday
      endDate = new Date(today.setHours(23, 59, 59, 999)); // End of yesterday
    } else if (periodSelection === "7") {
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 7); // Set to 7 days ago
      startDate.setHours(0, 0, 0, 0); // Set start time to midnight

      endDate = new Date(today);
      endDate.setHours(23, 59, 59, 999); // Set end time to end of today
    } else if (periodSelection === "15") {
      startDate = new Date(today);
      startDate.setDate(today.getDate() - 15);
      endDate = today;
    } else if (periodSelection === "month") {
      startDate = new Date(today.getFullYear(), today.getMonth(), 1);
      endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0); // Last day of the month
    } else if (periodSelection === "lastMonth") {
      startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      endDate = new Date(today.getFullYear(), today.getMonth(), 0); // Last day of the previous month
    }

    // Build the domain filter
    let domain = [["partner_id", "=", parseInt(custID)]];

    if (storeFilter && storeFilter !== "all") {
      domain.push(["config_id", "=", parseInt(storeFilter)]); // Changed from order_id.config_id
    }

    // Add date filters if dates are available
    if (startDate && endDate) {
      domain.push(
        ["date_order", ">=", startDate.toISOString()],
        ["date_order", "<=", endDate.toISOString()]
      );
    }

    console.log("Domain:", domain);

    // Stop countdown if it's running
    this.isCountingDown = false;
    this.clearIntervals();

    // Redirect to POS order line list view with filters
    await this.actionService.doAction({
      name: `Sales Details for customer ${custID}`,
      type: "ir.actions.act_window",
      res_model: "pos.order", // Changed from purchase.order.line to pos.order.line
      view_mode: "list",
      views: [[false, "list"]],
      target: "current",
      domain: domain,
      context: {
        create: false, // Disable creation of new records in the list view
      },
    });
  }
}
PosCardList1.template = "owl.PosCardList1";
