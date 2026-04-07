/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
const { Component, useRef, onWillStart, onMounted, onWillUnmount, useState } =
  owl;
import { session } from "@web/session";

export class PenagihanKpiCard extends Component {
  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.refreshInterval = null;
    this.loadingOverlayRef = useRef("loadingOverlay");
    this.default_period = "thisMonth";
    this.state = useState({
      kpiData: [],
      startDate: null,
      endDate: null,
    });

    this.refreshInterval = null;
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;

    // Setup for component lifecycle events
    onWillStart(async () => {
      try {
        await this.updateKpiData();
      } catch (error) {
        console.error("Failed to update KPI data:", error);
      }
    });

    // Attach event listeners after mounting
    onMounted(() => {
      this.attachEventListeners();
      const periodSelection = document.getElementById("periodSelection");
      if (periodSelection) {
        periodSelection.value = "thisMonth"; // Pilih default "Bulan Ini"
      }
    });

    // Cleanup interval on component unmount
    onWillUnmount(() => {
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
      }
    });
  }

  // Loading Overlay
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

  // FUNC COUNTDOWN
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

  refreshChart() {
    // Logika refresh chart
    console.log("Refreshing Card...");
    // Contoh penggunaan data fetching ulang
    this.updateKpiData();
  }

  // FUNC COUNTDOWN END

  // async updateKpiData() {
  //   // this.showLoading();
  //   try {
  //     // Build domain filter based on date range from state
  //     // const domain = [["picking_type_code", "=", "internal"]];
  //     // const domain2 = [["picking_type_code", "=", "incoming"]];
  //     // const domain3 = [["picking_type_code", "=", "outgoing"]];

  //     const domain1 = [];
  //     const domain2 = [];
  //     const domain3 = [];
  //     const domain = [];
  //     if (this.state.startDate) {
  //       domain1.push(["invoice_date", ">=", this.state.startDate]);
  //     }
  //     if (this.state.endDate) {
  //       domain1.push(["invoice_date", "<=", this.state.endDate]);
  //     }

  //     domain1.push(["status_in_payment", "=", "paid"]);

  //     let lunasData = await this.orm.call("account.move", "search_read", [
  //       domain1,
  //       ["id", "price_subtotal", "amount_untaxed_in_currency_signed"],
  //     ]);

  //     let absensiData = await this.orm.call(
  //       "cdn.absensi_siswa",
  //       "search_read",
  //       [domain2, ["id", "kelas_id", "tanggal"]]
  //     );

  //     let jumlahRpp = await this.orm.call("cdn.master_rpp", "search_read", [
  //       // [["jns_pegawai", "=", "guru"]],
  //       domain3,
  //       ["id", "name"],
  //     ]);
  //     // console.log("Stock3 Data:", stock3);

  //     const kelasData = await this.orm.call("cdn.master_kelas", "search_read", [
  //       domain,
  //       ["id", "name"],
  //     ]);

  //     // Instead of lunasData.length, sum up the price_subtotal or amount_untaxed_in_currency_signed
  //     let lunas = lunasData.reduce((total, record) => {
  //       // You can use either price_subtotal or amount_untaxed_in_currency_signed depending on which field you need
  //       return total + record.amount_untaxed_in_currency_signed;
  //     }, 0);
  //     let absensi = absensiData.length;
  //     let jumlahrpp = jumlahRpp.length;
  //     let kelas = kelasData.length;

  //     this.state.kpiData = [
  //       {
  //         name: "Tagihan Lunas",
  //         value: lunas,
  //         icon: "fa-check-circle",
  //         res_model: "cdn.penugasan",
  //         domain: domain1,
  //       }, // Ikon transfer untuk menggambarkan pergerakan barang internal
  //       {
  //         name: "Tagihan Belum Lunas",
  //         value: absensi,
  //         icon: "fa-times-circle",
  //         res_model: "cdn.absensi_siswa",
  //         domain: domain2,
  //       }, // Ikon truk untuk penerimaan barang
  //       {
  //         //<i class="fa-solid "></i>
  //         name: "Total Tagihan Overdue",
  //         value: jumlahrpp,
  //         icon: "fa-exclamation-triangle",
  //         res_model: "cdn.master_rpp",
  //         domain: domain3,
  //       }, // Ikon pengiriman cepat untuk DO
  //       {
  //         name: "Pendapatan dari penagihan",
  //         value: kelas,
  //         icon: "fa-wallet",
  //         res_model: "cdn.master_kelas",
  //         domain: domain,
  //       }, // Ikon gudang untuk menggambarkan mutasi barang
  //     ];

  //     // Apply the animation to each KPI element
  //     this.state.kpiData.forEach((kpi, index) => {
  //       const kpiElement = document.querySelector(`.kpi-value-${index}`);
  //       if (kpiElement) {
  //         animateValue(kpiElement, 0, kpi.value, 1000); // Animate from 0 to target value over 1 second
  //       }
  //     });
  //   } catch (error) {
  //     console.error("Error fetching KPI data:", error);
  //   } finally {
  //     this.hideLoading();
  //   }
  // }

  formatLargeNumber(number) {
    if (number >= 1000000) {
      return (number / 1000000).toFixed(1).replace(/\.0$/, "") + " jt";
    } else if (number >= 1000) {
      return (number / 1000).toFixed(0) + "rb";
    }
    return number.toFixed(0);
  }

  async updateKpiData() {
    this.showLoading();
    try {
      const domain1 = [];
      const domain2 = [];
      const domain3 = [];
      const domain = [];

      if (this.state.startDate) {
        domain1.push(["invoice_date", ">=", this.state.startDate]);
        domain2.push(["invoice_date", ">=", this.state.startDate]);
        domain3.push(["invoice_date", ">=", this.state.startDate]);
        domain.push(["invoice_date", ">=", this.state.startDate]);
      }
      if (this.state.endDate) {
        domain1.push(["invoice_date", "<=", this.state.endDate]);
        domain2.push(["invoice_date", "<=", this.state.endDate]);
        domain3.push(["invoice_date", "<=", this.state.endDate]);
        domain.push(["invoice_date", "<=", this.state.endDate]);
      }

      domain.push(["state", "=", "cancel"]);
      domain1.push(["payment_state", "=", "paid"]);
      domain1.push(["move_type", "=", "out_invoice"]);
      domain2.push(["move_type", "=", "out_invoice"]);
      domain2.push(["payment_state", "=", "not_paid"]);
      domain2.push(["state", "!=", "draft"]);
      domain2.push(["state", "!=", "cancel"]);
      domain3.push(["payment_state", "=", "partial"]);
      domain3.push(["state", "!=", "draft"]);

      let lunasData = await this.orm.call("account.move", "search_read", [
        domain1,
        ["id", "amount_untaxed_in_currency_signed"],
      ]);

      let belumLunasData = await this.orm.call("account.move", "search_read", [
        domain2,
        ["id", "amount_untaxed_in_currency_signed"],
      ]);

      let terbayarSebagian = await this.orm.call(
        "account.move",
        "search_read",
        [domain3, ["id", "amount_untaxed_in_currency_signed"]]
      );

      let pembayaranDibatalkan = await this.orm.call(
        "account.move",
        "search_read",
        [domain, ["id", "amount_untaxed_in_currency_signed"]]
      );

      // Safer sum calculation with null check
      let lunas = lunasData.reduce((total, record) => {
        const amount = record.amount_untaxed_in_currency_signed || 0;
        return total + amount;
      }, 0);

      let belumLunas = belumLunasData.reduce((total, record) => {
        const amount = record.amount_untaxed_in_currency_signed || 0;
        return total + amount;
      }, 0);

      let sebagian = terbayarSebagian.reduce((total, record) => {
        const amount = record.amount_untaxed_in_currency_signed || 0;
        return total + amount;
      }, 0);

      let dibatalkan = pembayaranDibatalkan.reduce((total, record) => {
        const amount = record.amount_untaxed_in_currency_signed || 0;
        return total + amount;
      }, 0);

      const resModel = "account.move";

      this.state.kpiData = [
        {
          name: "Faktur Lunas",
          value: this.formatLargeNumber(lunas),
          icon: "fa-circle-check",
          res_model: resModel,
          domain: domain1,
        },
        {
          name: "Faktur Terhutang",
          value: this.formatLargeNumber(belumLunas),
          icon: "fa-exclamation-circle",
          res_model: resModel,
          domain: domain2,
        },
        {
          name: "Faktur Terbayar Sebagian",
          value: this.formatLargeNumber(sebagian),
          icon: "fa-hand-holding-usd",
          res_model: resModel,
          domain: domain3,
        },
        {
          name: "Dibatalkan",
          value: this.formatLargeNumber(dibatalkan),
          icon: "fa-times-circle",
          res_model: resModel,
          domain: domain,
        },
      ];

      // Only try to animate if the function exists
      if (typeof animateValue === "function") {
        this.state.kpiData.forEach((kpi, index) => {
          const kpiElement = document.querySelector(`.kpi-value-${index}`);
          if (kpiElement) {
            animateValue(kpiElement, 0, kpi.value, 1000);
          }
        });
      }
    } catch (error) {
      console.error("Error fetching KPI data:", error);
      throw error; // Re-throw the error so it can be handled by the caller
    } finally {
      this.hideLoading();
    }
  }

  attachEventListeners() {
    // Add click listener to each KPI card
    const kpiCards = document.querySelectorAll(".kpi-card");
    var timerButton = document.getElementById("timerButton");
    if (timerButton) {
      timerButton.addEventListener("click", this.toggleCountdown.bind(this));
    } else {
      console.error("Timer button element not found");
    }
    kpiCards.forEach((card) => {
      card.addEventListener("click", (evt) => {
        this.handleKpiCardClick(evt);
      });
    });

    // Add change listeners to date inputs
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");

    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", (event) => {
        this.state.startDate = event.target.value || null;
        this.updateKpiData();
      });
      endDateInput.addEventListener("change", (event) => {
        this.state.endDate = event.target.value || null;
        this.updateKpiData();
      });
    }
    const today = new Date();
    let startDate;
    let endDate;
    // Add change listener to period selection dropdown
    if (periodSelection) {
      this.showLoading();
      try {
        const handlePeriodChange = () => {
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
            this.state.startDate = startDate.toISOString().split("T")[0];
            this.state.endDate = endDate.toISOString().split("T")[0];
            startDateInput.value = this.state.startDate;
            endDateInput.value = this.state.endDate;
            console.log("dates down kpi: ", startDate, "& ", endDate);
            console.log(
              "dates down state kpi: ",
              this.state.startDate,
              "& ",
              this.state.endDate
            );
            this.updateKpiData();
          }
        };

        // Attach the listener for future changes
        periodSelection.addEventListener("change", handlePeriodChange);

        // Trigger the function immediately to apply the default filter on load
        handlePeriodChange();
      } catch {
        console.log("Terjadi Error");
      } finally {
        this.hideLoading();
      }
      // Set a default value for periodSelection (e.g., 'month')

      // Define the change event listener
    }
  }

  async handleKpiCardClick(evt) {
    this.clearIntervals();
    document.getElementById("timerIcon").className = "fas fa-clock";
    document.getElementById("timerCountdown").textContent = "";
    this.clearIntervals();
    this.updateCountdownDisplay();
    const cardName = evt.currentTarget.dataset.name;
    const cardData = this.state.kpiData.find((kpi) => kpi.name === cardName);
    console.log("Kpicard yang di klik", cardData);

    if (cardData) {
      const { res_model, domain } = cardData;
      await this.actionService.doAction({
        name: `${cardName} Details`,
        type: "ir.actions.act_window",
        res_model: res_model,
        view_mode: "list",
        views: [[false, "list"]],
        target: "current",
        domain: domain,
      });
    } else {
      console.error(`No data found for KPI card: ${cardName}`);
    }
  }
}

PenagihanKpiCard.template = "owl.PenagihanKpiCard";
