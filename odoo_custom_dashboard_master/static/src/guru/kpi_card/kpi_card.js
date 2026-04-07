/** @odoo-module */
import { Component, onWillStart, onMounted, onWillUpdateProps, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class GuruKpiCard extends Component {
  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");

    this.state = {
      kpiData: [],
      animations: {},
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
      isFiltered: false,
    };

    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;

    // 👇 TAMBAHKAN: Cache & debounce
    this._fetchPromise = null;
    this._lastFetchKey = null;

    const today = new Date();
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDayOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    this.defaultStartDate = this.getLocalDateString(firstDayOfMonth);
    this.defaultEndDate = this.getLocalDateString(lastDayOfMonth);

    if (this.props.startDate && this.props.endDate) {
      this.state.isFiltered = true;
    }

    onWillUpdateProps(async (nextProps) => {
      if (nextProps.startDate !== this.props.startDate ||
        nextProps.endDate !== this.props.endDate) {
        this.state.currentStartDate = nextProps.startDate;
        this.state.currentEndDate = nextProps.endDate;
        this.state.isFiltered = !!(nextProps.startDate && nextProps.endDate);
        await this.fetchData(this.state.currentStartDate, this.state.currentEndDate);
      }
    });

    onWillStart(async () => {
      try {
        await this.checkModelAccess();
        await this.fetchData(
          this.state.currentStartDate || this.defaultStartDate,
          this.state.currentEndDate || this.defaultEndDate
        );
      } catch (error) {
        console.error("Failed to fetch KPI data:", error);
      }
    });

    onMounted(() => {
      const timerButton = document.getElementById("timerButton");
      if (timerButton) {
        timerButton.addEventListener("click", () => this.handleTimerClick());
      }

      // 👇 HANYA animate jika data sudah ada (tidak fetch lagi)
      if (this.state.kpiData.length > 0) {
        // Delay kecil agar DOM ready
        setTimeout(() => this.startKpiAnimations(), 50);
      }
    });

    onWillUnmount(() => {
      this.cleanup();
      const timerButton = document.getElementById("timerButton");
      if (timerButton) {
        timerButton.removeEventListener("click", () => this.handleTimerClick());
      }
    });
  }

  getLocalDateString(date) {
    if (!date || isNaN(date.getTime())) {
      console.error("Invalid date in getLocalDateString:", date);
      return "";
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  async checkModelAccess() {
    try {
      const models = [
        "cdn.absensi_siswa_lines",
        "cdn.absen_halaqoh_line",
        "cdn.absen_ekskul_line",
      ];
      for (const model of models) {
        await this.orm.call("ir.model.access", "check", [model, "read"], {
          context: this.env.context,
        });
      }
    } catch (error) {
      console.error("Error checking model access:", error);
    }
  }

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

  cleanup() {
    this.stopCountdown();
    Object.values(this.state.animations).forEach((animationId) => {
      cancelAnimationFrame(animationId);
    });
    this.state.animations = {};
  }

  startKpiAnimations() {
    this.state.kpiData.forEach((kpi, index) => {
      const countElement = document.getElementById(`counter-${index}`);
      if (countElement) {
        this.animateNumber(countElement, 0, kpi.value);
      }
    });
  }

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

  // 👇 OPTIMIZED fetchData dengan cache
  async fetchData(startDate, endDate) {
    const effectiveStartDate = startDate || this.defaultStartDate;
    const effectiveEndDate = endDate || this.defaultEndDate;

    // 👇 CREATE unique key untuk cache
    const fetchKey = `${effectiveStartDate}_${effectiveEndDate}`;

    // 👇 RETURN cached promise jika sedang fetch dengan key yang sama
    if (this._fetchPromise && this._lastFetchKey === fetchKey) {
      console.log("⚡ GuruKpiCard: Using cached fetch promise");
      return this._fetchPromise;
    }

    this._lastFetchKey = fetchKey;

    // 👇 CREATE new promise dan cache
    this._fetchPromise = this._performFetch(effectiveStartDate, effectiveEndDate);

    try {
      await this._fetchPromise;
    } finally {
      // 👇 Clear cache setelah 100ms
      setTimeout(() => {
        this._fetchPromise = null;
        this._lastFetchKey = null;
      }, 100);
    }
  }

  async _performFetch(effectiveStartDate, effectiveEndDate) {
    try {
      console.log("📊 GuruKpiCard: Fetching data", { effectiveStartDate, effectiveEndDate });

      const start = new Date(effectiveStartDate);
      const end = new Date(effectiveEndDate);

      if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        console.error("Invalid dates provided:", { effectiveStartDate, effectiveEndDate });
        return;
      }
      if (start > end) {
        console.error("Start date is after end date:", { effectiveStartDate, effectiveEndDate });
        return;
      }

      const domainAbsenSiswa = [["kehadiran", "!=", false]];
      const domainAbsenHalaqoh = [["kehadiran", "!=", false]];
      const domainAbsenEkskul = [["kehadiran", "!=", false]];

      if (effectiveStartDate) {
        domainAbsenSiswa.push(["tanggal", ">=", effectiveStartDate + " 00:00:00"]);
        domainAbsenHalaqoh.push(["tanggal", ">=", effectiveStartDate + " 00:00:00"]);
        domainAbsenEkskul.push(["tanggal", ">=", effectiveStartDate + " 00:00:00"]);
      }
      if (effectiveEndDate) {
        domainAbsenSiswa.push(["tanggal", "<=", effectiveEndDate + " 23:59:59"]);
        domainAbsenHalaqoh.push(["tanggal", "<=", effectiveEndDate + " 23:59:59"]);
        domainAbsenEkskul.push(["tanggal", "<=", effectiveEndDate + " 23:59:59"]);
      }

      // 👇 PARALLEL fetch untuk speed
      const [absensiSiswa, absensiHalaqoh, absensiEkskul] = await Promise.all([
        this.orm.call(
          "cdn.absensi_siswa_lines",
          "search_read",
          [domainAbsenSiswa, ["id", "siswa_id", "kehadiran", "create_date"]],
          { context: this.env.context }
        ).catch(err => {
          console.warn("Error fetching absensi_siswa_lines:", err);
          return [];
        }),
        this.orm.call(
          "cdn.absen_halaqoh_line",
          "search_read",
          [domainAbsenHalaqoh, ["id", "siswa_id", "kehadiran", "create_date"]],
          { context: this.env.context }
        ).catch(err => {
          console.warn("Error fetching absen_halaqoh_line:", err);
          return [];
        }),
        this.orm.call(
          "cdn.absen_ekskul_line",
          "search_read",
          [domainAbsenEkskul, ["id", "siswa_id", "kehadiran", "create_date"]],
          { context: this.env.context }
        ).catch(err => {
          console.warn("Error fetching absen_ekskul_line:", err);
          return [];
        })
      ]);

      const totalAbsenSiswa = absensiSiswa?.length || 0;
      const totalAbsenHalaqoh = absensiHalaqoh?.length || 0;
      const totalAbsenEkskul = absensiEkskul?.length || 0;

      this.state.kpiData = [
        {
          name: "Absen Siswa",
          value: totalAbsenSiswa,
          icon: "fa-user-check",
          color: "#00e396",
          res_model: "cdn.absensi_siswa_lines",
          domain: domainAbsenSiswa,
        },
        {
          name: "Absen Halaqoh",
          value: totalAbsenHalaqoh,
          icon: "fa-quran",
          color: "#00e396",
          res_model: "cdn.absen_halaqoh_line",
          domain: domainAbsenHalaqoh,
        },
        {
          name: "Absen Ekskul",
          value: totalAbsenEkskul,
          icon: "fa-chalkboard-teacher",
          color: "#00e396",
          res_model: "cdn.absen_ekskul_line",
          domain: domainAbsenEkskul,
        },
      ];

      console.log("✅ GuruKpiCard: Data updated");

      // 👇 Trigger animation setelah DOM update
      setTimeout(() => this.startKpiAnimations(), 50);

    } catch (error) {
      console.error("Error in fetchData:", error);
    }
  }

  async refreshData() {
    const startDate = this.state.isFiltered ? this.state.currentStartDate : this.defaultStartDate;
    const endDate = this.state.isFiltered ? this.state.currentEndDate : this.defaultEndDate;

    console.log("🔄 GuruKpiCard: Refreshing data and triggering event");

    // 👇 Force clear cache untuk refresh
    this._fetchPromise = null;
    this._lastFetchKey = null;

    await this.fetchData(startDate, endDate);

    // Dispatch event untuk component lain
    window.dispatchEvent(new CustomEvent('guru-dashboard-refresh', {
      detail: { startDate, endDate, timestamp: Date.now() }
    }));
  }

  attachEventListeners() {
    const kpiCards = document.querySelectorAll(".kpi-card");
    kpiCards.forEach((card) => {
      card.addEventListener("click", (evt) => {
        this.handleKpiCardClick(evt);
      });
    });
  }

  handleKpiCardClick(evt) {
    const cardName = evt.currentTarget.dataset.name;
    const cardData = this.state.kpiData.find((kpi) => kpi.name === cardName);

    if (cardData) {
      const { res_model, domain } = cardData;

      this.actionService.doAction({
        name: `${cardName}`,
        type: "ir.actions.act_window",
        res_model: res_model,
        view_mode: "list,form",
        views: [[false, "list"], [false, "form"]],
        target: "current",
        domain: domain,
      });
    }
  }
}

GuruKpiCard.template = "owl.GuruKpiCard";

GuruKpiCard.props = {
  startDate: { type: String, optional: true },
  endDate: { type: String, optional: true },
};