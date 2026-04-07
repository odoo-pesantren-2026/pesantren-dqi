/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted, onWillUnmount, useState } = owl;

export class KeamananKpiCard extends Component {
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

  async updateKpiData() {
    this.showLoading();
    try {
      const domain = [["state", "=", "Permission"]];
      const domain2 = [["state", "=", "Return"]];
      const domain3 = [
        "|",
        ["state", "=", "Permission"],
        ["state", "=", "Return"],
      ];
      const domain4 = [
        "|",
        ["state", "=", "Permission"],
        ["state", "=", "Return"],
      ];

      if (this.state.startDate) {
        domain.push(["tgl_ijin", ">=", this.state.startDate]);
        domain2.push(["tgl_ijin", ">=", this.state.startDate]);
        domain3.push(["tgl_ijin", ">=", this.state.startDate]);
        domain4.push(["tgl_ijin", ">=", this.state.startDate]);
      }
      if (this.state.endDate) {
        domain.push(["tgl_ijin", "<=", this.state.endDate]);
        domain2.push(["tgl_ijin", "<=", this.state.endDate]);
        domain3.push(["tgl_ijin", "<=", this.state.endDate]);
        domain4.push(["tgl_ijin", "<=", this.state.endDate]);
      }

      const santriKeluar = await this.orm.call("cdn.perijinan", "search_read", [
        domain,
        ["id", "tgl_ijin", "state"],
      ]);

      const santriMasuk = await this.orm.call("cdn.perijinan", "search_read", [
        domain2,
        ["id", "tgl_ijin", "state"],
      ]);

      let Selisih = Math.abs(santriKeluar.length - santriMasuk.length);

      const total = await this.orm.call("cdn.perijinan", "search_read", [
        domain4,
        ["id", "tgl_ijin", "state"],
      ]);

      this.state.kpiData = [
        {
          name: "Keluar",
          value: santriKeluar.length,
          icon: "fa-door-open",
          color: "#00e396",
          res_model: "cdn.perijinan",
          domain: domain,
        },
        {
          name: "Masuk",
          value: santriMasuk.length,
          icon: "fa-door-closed",
          color: "#00e396",
          res_model: "cdn.perijinan",
          domain: domain2,
        },
        {
          name: "Selisih",
          value: Selisih,
          icon: "fa-sliders-h",
          color: "#00e396",
          res_model: "cdn.perijinan",
          domain: domain3,
        },
        {
          name: "Total",
          value: total.length,
          icon: "fa-list-ol",
          color: "#00e396",
          res_model: "cdn.perijinan",
          domain: domain4,
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

KeamananKpiCard.template = "owl.KeamananKpiCard";