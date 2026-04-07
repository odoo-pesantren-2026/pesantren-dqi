/** @odoo-module **/
const { Component, onWillStart, onMounted, onWillUpdateProps, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";

export class SekolahKpiCard extends Component {
  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");

    this.state = {
      kpiData: [],
      animations: {},
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
      isFiltered: false
    };
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;

    const today = new Date();
    const firstDayOfYear = new Date(today.getFullYear(), 0, 1);

    this.defaultStartDate = firstDayOfYear.toISOString().split('T')[0];
    this.defaultEndDate = today.toISOString().split('T')[0];

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

    onMounted(() => {
      const timerButton = document.getElementById("timerButton");
      if (timerButton) {
        timerButton.addEventListener("click", () => this.handleTimerClick());
      }
      this.startKpiAnimations();
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

    onWillUnmount(() => {
      this.cleanup();
      const timerButton = document.getElementById("timerButton");
      if (timerButton) {
        timerButton.removeEventListener("click", () => this.handleTimerClick());
      }
    });
  }

  async checkModelAccess() {
    try {
      const models = ['cdn.siswa', 'cdn.orangtua', 'hr.employee', 'cdn.master_kelas'];
      for (const model of models) {
        const access = await this.orm.call(
          'ir.model.access',
          'check',
          [model, 'read'],
          { context: this.env.context }
        );
      }
    } catch (error) {
      console.error('Error checking model access:', error);
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
    Object.values(this.state.animations).forEach(animationId => {
      cancelAnimationFrame(animationId);
    });
    this.state.animations = {};
  }

  // Method untuk animasi KPI
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

    // Clear existing animation
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

  async fetchData(startDate, endDate) {
    try {
      // Remove date domain filter, use empty domain instead
      const domain = [];

      let siswaData = [], ortuData = [], guruData = [], kelasData = [];

      try {
        siswaData = await this.orm.call(
          'cdn.siswa',
          'search_read',
          [domain, ['id', 'complete_name', 'jns_kelamin', 'tahfidz_terakhir_id', 'pelanggaran_count', 'penilaian_quran_count']],
          { context: this.env.context }
        );
      } catch (error) {
        console.warn('Error fetching siswa data:', error);
      }

      try {
        ortuData = await this.orm.call(
          'cdn.orangtua',
          'search_read',
          [domain, ['id', 'complete_name']],
          { context: this.env.context }
        );
      } catch (error) {
        console.warn('Error fetching orangtua data:', error);
      }

      try {
        guruData = await this.orm.call(
          'hr.employee',
          'search_read',
          [[["jns_pegawai_ids.code", "=", "guru"]], ['id', 'jns_pegawai_ids']],
          { context: this.env.context }
        );
      } catch (error) {
        console.warn('Error fetching guru data:', error);
      }

      try {
        kelasData = await this.orm.call(
          'cdn.master_kelas',
          'search_read',
          [domain, ['id', 'name']],
          { context: this.env.context }
        );
      } catch (error) {
        console.warn('Error fetching kelas data:', error);
      }

      console.log('Raw Data Sekolah:', {
        siswaData,
        ortuData,
        guruData,
        kelasData
      });

      // Calculate totals (with null checks)
      const totalSiswa = siswaData?.length || 0;
      const totalOrtu = ortuData?.length || 0;
      const totalGuru = guruData?.length || 0;
      const totalKelas = kelasData?.length || 0;

      // Update state with new data
      this.state.kpiData = [
        {
          name: 'Siswa',
          value: totalSiswa,
          icon: 'fa-user-graduate',
          color: '#16a34a',
          res_model: 'cdn.siswa',
          domain: domain,
        },
        {
          name: 'Wali',
          value: totalOrtu,
          icon: 'fa-users',
          color: '#16a34a',
          res_model: 'cdn.orangtua',
          domain: domain,
        },
        {
          name: 'Guru',
          value: totalGuru,
          icon: 'fa-chalkboard-user',
          color: '#16a34a',
          res_model: 'hr.employee',
          domain: [...domain, ['jns_pegawai_ids.code', '=', 'guru']],
        },
        {
          name: 'Kelas',
          value: totalKelas,
          icon: 'fa-ruler',
          color: '#16a34a',
          res_model: 'cdn.master_kelas',
          domain: domain,
        },
      ];

      // Start animations for new values
      this.startKpiAnimations();

    } catch (error) {
      console.error('Error in fetchData sekolah:', error);
    }
  }

  async refreshData() {
    const startDate = this.state.isFiltered ? this.state.currentStartDate : this.defaultStartDate;
    const endDate = this.state.isFiltered ? this.state.currentEndDate : this.defaultEndDate;
    await this.fetchData(startDate, endDate);
  }

  handleKpiCardClick(evt) {
    const cardName = evt.currentTarget.dataset.name;
    const cardData = this.state.kpiData.find(kpi => kpi.name === cardName);

    if (cardData) {
      const { res_model, domain } = cardData;

      // Handle khusus untuk model Kelas
      if (cardName === "Kelas") {
        const actionId = "pesantren_base.action_cdn_master_kelas";
        this.actionService
          .loadAction(actionId)
          .then((action) => {
            const newAction = {
              ...action,
              domain: domain,
              view_mode: "kanban",
              views: [[false, "kanban"]],
            };
            return this.actionService.doAction(newAction);
          })
          .then(() => {
            console.log(`Berpindah ke actionId: ${actionId} Dengan Domain:`, domain);
          })
          .catch((error) => {
            console.error(`Terjadi Error di ${actionId}:`, error);
          });
        return;
      }

      // Untuk model lainnya
      this.actionService.doAction({
        name: `${cardName}`,
        type: 'ir.actions.act_window',
        res_model: res_model,
        view_mode: 'list,form',
        views: [[false, 'list'], [false, 'form']],
        target: 'current',
        domain: domain,
      });
    }
  }
}

SekolahKpiCard.template = "owl.SekolahKpiCard";

SekolahKpiCard.props = {
  startDate: { type: String, optional: true },
  endDate: { type: String, optional: true },
};