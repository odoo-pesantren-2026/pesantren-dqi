/** @odoo-module **/
const { Component, onWillStart, onMounted, onWillUpdateProps, onWillUnmount } = owl;
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class MusyrifKpiCard extends Component {

    setup() {
        this.orm = useService('orm');
        this.actionService = useService('action');

        this.state = {
            kpiData: [],
            animations: {},
            currentStartDate: this.props.startDate,
            currentEndDate: this.props.endDate,
            isFiltered: false
        };

        // Countdown related properties
        this.countdownInterval = null;
        this.countdownTime = 10;
        this.isCountingDown = false;

        // Set default dates if not provided
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
            // Attach event listener to the timer button
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
            // Remove event listener when component unmounts
            const timerButton = document.getElementById("timerButton");
            if (timerButton) {
                timerButton.removeEventListener("click", () => this.handleTimerClick());
            }
        });
    }

    async checkModelAccess() {
        try {
            const models = ['cdn.siswa', 'cdn.perijinan', 'cdn.pelanggaran', 'cdn.kesehatan'];
            for (const model of models) {
                const access = await this.orm.call(
                    'ir.model.access',
                    'check',
                    [model, 'read'],
                    { context: this.env.context }
                );
                // Jika tidak punya akses, error akan dilempar
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

    async fetchData(startDate, endDate) {
        try {
            // Gunakan default jika tidak ada tanggal
            startDate = startDate || this.defaultStartDate;
            endDate = endDate || this.defaultEndDate;

            // Hanya filter berdasarkan tanggal, tanpa filter musyrif_id
            const dateDomain = [
                ['create_date', '>=', startDate],
                ['create_date', '<=', endDate]
            ];

            let siswaData = [], perijinanData = [], pelanggaranData = [], kesehatanData = [];

            // Ambil semua siswa tanpa filter
            try {
                siswaData = await this.orm.call(
                    'cdn.siswa',
                    'search_read',
                    [[], ['id', 'complete_name', 'jns_kelamin', 'penilaian_quran_count', 'create_date']],
                    {
                        context: {
                        ...this.env.context,
                        from_musyrif: true,
                        },
                    }
                );
            } catch (error) {
                console.warn('Error fetching siswa data:', error);
            }

            // Perijinan: hanya Draft dalam rentang tanggal
            try {
                perijinanData = await this.orm.call(
                    'cdn.perijinan',
                    'search_read',
                    [[...dateDomain, ['state', '=', 'Draft']],
                    ['create_date', 'tgl_ijin', 'siswa_id']],
                    {
                        context: {
                        ...this.env.context,
                        from_musyrif: true,
                        },
                    }
                );
            } catch (error) {
                console.warn('Error fetching perijinan data:', error);
            }

            // Pelanggaran: semua pelanggaran dalam rentang tanggal
            try {
                pelanggaranData = await this.orm.call(
                    'cdn.pelanggaran',
                    'search_read',
                    [dateDomain, ['tgl_pelanggaran', 'siswa_id', 'pelanggaran_id']],
                    {
                        context: {
                        ...this.env.context,
                        from_musyrif: true,
                        },
                    }
                );
            } catch (error) {
                console.warn('Error fetching pelanggaran data:', error);
            }

            // Kesehatan: status tertentu dalam rentang tanggal
            try {
                kesehatanData = await this.orm.call(
                    'cdn.kesehatan',
                    'search_read',
                    [[
                        ...dateDomain,
                        ['state', 'in', ['periksa', 'pengobatan', 'rawat']]
                    ], ['tgl_diperiksa', 'siswa_id', 'keluhan', 'state']],
                    {
                        context: {
                        ...this.env.context,
                        from_musyrif: true,
                        },
                    }
                );
            } catch (error) {
                console.warn('Error fetching kesehatan data:', error);
            }

            const totalSiswa = siswaData?.length || 0;
            const totalPerijinan = perijinanData?.length || 0;
            const totalPelanggaran = pelanggaranData?.length || 0;
            const totalKesehatan = kesehatanData?.length || 0;

            // Update KPI data tanpa filter musyrif_id
            this.state.kpiData = [
                {
                    name: 'Santri',
                    value: totalSiswa,
                    icon: 'fa-user-graduate',
                    color: '#00e396',
                    res_model: 'cdn.siswa',
                    domain: [], // Semua siswa
                },
                {
                    name: 'Pengajuan Izin Santri',
                    value: totalPerijinan,
                    icon: 'fa-file-signature',
                    color: '#00e396',
                    res_model: 'cdn.perijinan',
                    domain: [...dateDomain, ['state', '=', 'Draft']],
                },
                {
                    name: 'Pelanggaran',
                    value: totalPelanggaran,
                    icon: 'fa-circle-exclamation',
                    color: '#00e396',
                    res_model: 'cdn.pelanggaran',
                    domain: dateDomain,
                },
                {
                    name: 'Santri yang Sakit',
                    value: totalKesehatan,
                    icon: 'fa-heartbeat',
                    color: '#00e396',
                    res_model: 'cdn.kesehatan',
                    domain: [
                        ...dateDomain,
                        ['state', 'in', ['periksa', 'pengobatan', 'rawat']]
                    ],
                },
            ];

            // Jalankan animasi jika ada data
            if (this.state.kpiData.some(kpi => kpi.value > 0)) {
                this.startKpiAnimations();
            }

        } catch (error) {
            console.error('Error in fetchData:', error);
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

            this.actionService.doAction({
                name: `${cardName}`,
                type: 'ir.actions.act_window',
                res_model: res_model,
                view_mode: 'list,form',
                views: [[false, 'list'], [false, 'form']],
                target: 'current',
                domain: domain,
                context: {
                    ...this.env.context,
                    from_musyrif: true,
                },
            });
        }
    }
}

MusyrifKpiCard.template = "owl.MusyrifKpiCard";

MusyrifKpiCard.props = {
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
};