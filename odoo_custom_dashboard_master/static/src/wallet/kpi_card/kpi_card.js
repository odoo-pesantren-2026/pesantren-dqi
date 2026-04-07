/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted, onWillUnmount, useState } = owl;

export class WalletKpiCard extends Component {
  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");

    this.state = useState({
      kpiData: [],
      startDate: null,
      endDate: null,
      isLoading: false,
      animations: {}
    });

    this.refreshInterval = null;
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;
    this.loadingOverlay = null;

    onWillStart(async () => {
      try {
        await this.updateKpiData();
      } catch (error) {
        console.error("Failed to update KPI data:", error);
      }
    });

    onMounted(() => {
      this.attachEventListeners();
      const periodSelection = document.getElementById("periodSelection");
      if (periodSelection) {
        periodSelection.value = "thisMonth";
      }
    });

    onWillUnmount(() => {
      this.cleanup();
    });
  }

  // Cleanup method
  cleanup() {
    this.stopCountdown();
    Object.values(this.state.animations).forEach(animationId => {
      cancelAnimationFrame(animationId);
    });
    this.state.animations = {};
  }

  // Loading Overlay
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

  // Animation method (consistent with kesantrian)
  animateNumber(element, start, end, duration = 500) {
    if (!element) return;

    // Check if end is a formatted string (contains 'jt', 'rb', etc)
    const isFormatted = typeof end === 'string' && (end.includes('jt') || end.includes('rb'));

    if (isFormatted) {
      // For formatted numbers, just display directly without animation
      element.textContent = end;
      return;
    }

    const range = end - start;
    const minFrame = 16;
    const steps = Math.max(Math.floor(duration / minFrame), 1);
    const increment = range / steps;
    let current = start;
    let step = 0;

    const animationKey = element.id;
    if (this.state.animations[animationKey]) {
      cancelAnimationFrame(this.state.animations[animationKey]);
    }

    const animate = () => {
      step++;
      current += increment;

      if (step <= steps) {
        element.textContent = Math.round(current).toLocaleString();
        this.state.animations[animationKey] = requestAnimationFrame(animate);
      } else {
        element.textContent = Math.round(end).toLocaleString();
        delete this.state.animations[animationKey];
      }
    };

    this.state.animations[animationKey] = requestAnimationFrame(animate);
  }

  // Start animations for all KPI cards
  startKpiAnimations() {
    this.state.kpiData.forEach((kpi, index) => {
      const countElement = document.getElementById(`counter-${index}`);
      if (countElement) {
        this.animateNumber(countElement, 0, kpi.value);
      }
    });
  }

  // Timer functions
  handleTimerClick() {
    if (this.isCountingDown) {
      this.stopCountdown();
    } else {
      this.startCountdown();
    }
    this.isCountingDown = !this.isCountingDown;
  }

  startCountdown() {
    this.countdownTime = 10;
    this.updateTimerUI();

    this.countdownInterval = setInterval(() => {
      this.countdownTime--;
      if (this.countdownTime < 0) {
        this.countdownTime = 10;
        this.refreshData();
      }
      this.updateTimerUI();
    }, 1000);
  }

  stopCountdown() {
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
    this.updateTimerUI(true);
  }

  updateTimerUI(stopped = false) {
    const timerIcon = document.getElementById("timerIcon");
    const timerCountdown = document.getElementById("timerCountdown");

    if (timerIcon) {
      timerIcon.className = stopped ? "fas fa-clock" : "fas fa-stop d-none";
    }
    if (timerCountdown) {
      timerCountdown.textContent = stopped ? "" : this.countdownTime;
    }
  }

  async refreshData() {
    console.log("Refreshing Card...");
    await this.updateKpiData();
  }

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
      const domain = [];
      const domain3 = [];
      const domain4 = [];

      if (this.state.startDate) {
        domain3.push(["create_date", ">=", this.state.startDate]);
      }
      if (this.state.endDate) {
        domain3.push(["create_date", "<=", this.state.endDate]);
      }

      const saldoDompet = await this.orm.call("cdn.siswa", "search_read", [
        domain,
        ["saldo_uang_saku"],
      ]);

      const totalSaldo = saldoDompet.reduce(
        (acc, item) => acc + (item.saldo_uang_saku || 0),
        0
      );

      const santriDenganSaldo = saldoDompet.filter(
        (item) => (item.saldo_uang_saku || 0) > 0
      );
      const saldoRataRata = santriDenganSaldo.reduce(
        (acc, item) => acc + (item.saldo_uang_saku || 0),
        0
      );
      const jumlahSantri = santriDenganSaldo.length;
      const rataRataSaldo = jumlahSantri > 0 ? saldoRataRata / jumlahSantri : 0;

      const getTransaksiData = await this.orm.call(
        "cdn.uang_saku",
        "search_read",
        [domain3, ["id"]]
      );

      const tertinggi = await this.orm.call("cdn.siswa", "search_read", [
        domain4,
        ["saldo_uang_saku", "name"],
      ]);

      const sorted = tertinggi.sort(
        (a, b) => (b.saldo_uang_saku || 0) - (a.saldo_uang_saku || 0)
      );

      const top10 = sorted.slice(0, 10);

      const totalSaldoTop10 = top10.reduce(
        (acc, item) => acc + (item.saldo_uang_saku || 0),
        0
      );

      const finalTotalSaldo = this.formatLargeNumber(totalSaldo);
      const finalRataRataSaldo = this.formatLargeNumber(rataRataSaldo);
      const totalTransaksi = getTransaksiData.length;
      const finalTertinggi = this.formatLargeNumber(totalSaldoTop10);

      const top10Ids = top10.map((santri) => santri.id);

      this.state.kpiData = [
        {
          name: "Total Saldo",
          value: finalTotalSaldo,
          icon: "fa-wallet",
          color: "#00e396",
          res_model: "cdn.siswa",
          domain: domain,
        },
        {
          name: "Rata Rata Saldo",
          value: finalRataRataSaldo,
          icon: "fa-chart-line",
          color: "#00e396",
          res_model: "cdn.siswa",
          domain: [],
        },
        {
          name: "Transaksi",
          value: totalTransaksi,
          icon: "fa-receipt",
          color: "#00e396",
          res_model: "cdn.uang_saku",
          domain: domain3,
        },
        {
          name: "Saldo Tertinggi",
          value: finalTertinggi,
          icon: "fa-medal",
          color: "#00e396",
          res_model: "cdn.siswa",
          domain: [["id", "in", top10Ids]],
        },
      ];

      // Start animations after data is loaded
      this.startKpiAnimations();

    } catch (error) {
      console.error("Error fetching KPI data:", error);
    } finally {
      this.hideLoading();
    }
  }

  attachEventListeners() {
    const kpiCards = document.querySelectorAll(".kpi-card");
    const timerButton = document.getElementById("timerButton");

    if (timerButton) {
      timerButton.addEventListener("click", () => this.handleTimerClick());
    } else {
      console.error("Timer button element not found");
    }

    kpiCards.forEach((card) => {
      card.addEventListener("click", (evt) => {
        this.handleKpiCardClick(evt);
      });
    });

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

    if (periodSelection) {
      const handlePeriodChange = () => {
        const today = new Date();
        let startDate, endDate;

        switch (periodSelection.value) {
          case "today":
            startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate(), 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate(), 23, 59, 59, 999));
            break;
          case "yesterday":
            startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - 1, 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - 1, 23, 59, 59, 999));
            break;
          case "thisWeek":
            const startOfWeek = today.getUTCDate() - today.getUTCDay();
            startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), startOfWeek, 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), startOfWeek + 6, 23, 59, 59, 999));
            break;
          case "lastWeek":
            const lastWeekStart = today.getUTCDate() - today.getUTCDay() - 7;
            startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), lastWeekStart, 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), lastWeekStart + 6, 23, 59, 59, 999));
            break;
          case "thisMonth":
            startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0, 23, 59, 59, 999));
            break;
          case "lastMonth":
            startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() - 1, 1, 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 0, 23, 59, 59, 999));
            break;
          case "thisYear":
            startDate = new Date(Date.UTC(today.getUTCFullYear(), 0, 1, 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear(), 11, 31, 23, 59, 59, 999));
            break;
          case "lastYear":
            startDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 0, 1, 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear() - 1, 11, 31, 23, 59, 59, 999));
            break;
          default:
            startDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 0, 1));
            endDate = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth() + 1, 0, 23, 59, 59, 999));
        }

        if (startDate && endDate) {
          this.state.startDate = startDate.toISOString().split("T")[0];
          this.state.endDate = endDate.toISOString().split("T")[0];
          startDateInput.value = this.state.startDate;
          endDateInput.value = this.state.endDate;
          this.updateKpiData();
        }
      };

      periodSelection.addEventListener("change", handlePeriodChange);
      handlePeriodChange();
    }
  }

  async handleKpiCardClick(evt) {
    this.stopCountdown();

    const cardName = evt.currentTarget.dataset.name;
    const cardData = this.state.kpiData.find((kpi) => kpi.name === cardName);

    if (cardData) {
      const { res_model, domain } = cardData;
      await this.actionService.doAction({
        name: `${cardName}`,
        type: "ir.actions.act_window",
        res_model: res_model,
        view_mode: "list,form",
        views: [[false, "list"], [false, "form"]],
        target: "current",
        domain: domain,
      });
    } else {
      console.error(`No data found for KPI card: ${cardName}`);
    }
  }
}

WalletKpiCard.template = "owl.WalletKpiCard";