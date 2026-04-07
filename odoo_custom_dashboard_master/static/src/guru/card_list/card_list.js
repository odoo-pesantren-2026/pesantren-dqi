/** @odoo-module **/
import { Component, onWillStart, onWillUpdateProps, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class GuruList extends Component {
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true }
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = {
            items: [],
            isLoading: true,
            hasData: false,
            currentStartDate: this.props.startDate,
            currentEndDate: this.props.endDate
        };

        // 👇 FLAG untuk prevent double fetch
        this.isFetching = false;
        this.hasInitialFetch = false;
        this._handleRefreshEvent = this.handleRefreshEvent.bind(this);

        onWillStart(async () => {
            if (this.hasInitialFetch) return;
            await this.fetchData();
            this.hasInitialFetch = true;
        });

        onWillUpdateProps(async (nextProps) => {
            if (nextProps.startDate !== this.props.startDate ||
                nextProps.endDate !== this.props.endDate) {
                this.state.currentStartDate = nextProps.startDate;
                this.state.currentEndDate = nextProps.endDate;
                await this.fetchData();
            }
        });

        onMounted(() => {
            window.addEventListener('guru-dashboard-refresh', this._handleRefreshEvent);
        });

        onWillUnmount(() => {
            window.removeEventListener('guru-dashboard-refresh', this._handleRefreshEvent);
        });
    }

    async handleRefreshEvent(event) {
        console.log("🔔 GuruList: Received refresh event");
        const { startDate, endDate } = event.detail;
        this.state.currentStartDate = startDate;
        this.state.currentEndDate = endDate;
        await this.fetchData();
    }

    async fetchData() {
        // 👇 PREVENT duplicate fetch
        if (this.isFetching) {
            console.log("⏭️ GuruList: Skipping fetch - already fetching");
            return;
        }

        this.isFetching = true;

        try {
            this.state.isLoading = true;

            const domain = [['penilaian_id.state', '=', 'done']];

            if (this.state.currentStartDate) {
                domain.push(['penilaian_id.tanggal', '>=', this.state.currentStartDate]);
            }
            if (this.state.currentEndDate) {
                domain.push(['penilaian_id.tanggal', '<=', this.state.currentEndDate]);
            }

            let lineRecords = [];
            let penilaianRecords = [];

            try {
                lineRecords = await this.orm.searchRead(
                    "cdn.penilaian_quran_line",
                    domain,
                    ["id", "penilaian_id", "jml_baris"],
                    {
                        context: {
                            ...this.env.context,
                            from_guru_quran: true,
                        },
                    }
                );
            } catch (e) {
                console.error("Error fetching penilaian_quran_lines:", e);
            }

            if (!lineRecords.length) {
                this.state.items = [];
                this.state.hasData = false;
                return;
            }

            const penilaianIds = [...new Set(lineRecords.map(l => l.penilaian_id?.[0]).filter(Boolean))];

            try {
                penilaianRecords = await this.orm.searchRead(
                    "cdn.penilaian_quran",
                    [["id", "in", penilaianIds]],
                    ["id", "siswa_id", "halaqoh_id"],
                    {
                        context: {
                            ...this.env.context,
                            from_guru_quran: true,
                        },
                    }
                );
            } catch (e) {
                console.error("Error fetching penilaian_quran:", e);
            }

            const penilaianMap = new Map(penilaianRecords.map(p => [
                p.id,
                {
                    siswa: p.siswa_id ? p.siswa_id[1] : 'N/A',
                    halaqoh: p.halaqoh_id ? p.halaqoh_id[1] : 'N/A',
                }
            ]));

            const totalPerSiswa = {};
            for (const line of lineRecords) {
                const penilaianId = line.penilaian_id?.[0];
                const info = penilaianMap.get(penilaianId);
                if (!info) continue;

                if (!totalPerSiswa[info.siswa]) {
                    totalPerSiswa[info.siswa] = {
                        nama: info.siswa,
                        halaqoh: info.halaqoh,
                        total_baris: 0,
                        penilaian_id: penilaianId,
                    };
                }
                totalPerSiswa[info.siswa].total_baris += line.jml_baris || 0;
            }

            const sorted = Object.values(totalPerSiswa)
                .sort((a, b) => b.total_baris - a.total_baris)
                .slice(0, 10);

            this.state.items = sorted.map((item, index) => ({
                id: item.penilaian_id,
                number: index + 1,
                nama: item.nama,
                halaqoh: item.halaqoh,
                baris: item.total_baris,
            }));

            this.state.hasData = this.state.items.length > 0;

        } catch (error) {
            console.error("Error fetching Top Hafalan data:", error);
            this.state.items = [];
            this.state.hasData = false;
        } finally {
            this.state.isLoading = false;
            this.isFetching = false; // 👈 Reset flag
        }
    }

    openRecord(penilaianId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Detail Penilaian",
            res_model: "cdn.penilaian_quran",
            res_id: penilaianId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

GuruList.template = "owl.GuruList";

export class EkskulList extends Component {
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true }
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = {
            items: [],
            isLoading: true,
            hasData: false,
            currentStartDate: this.props.startDate,
            currentEndDate: this.props.endDate
        };

        // 👇 FLAG untuk prevent double fetch
        this.isFetching = false;
        this.hasInitialFetch = false;
        this._handleRefreshEvent = this.handleRefreshEvent.bind(this);

        onWillStart(async () => {
            if (this.hasInitialFetch) return;
            await this.fetchData();
            this.hasInitialFetch = true;
        });

        onWillUpdateProps(async (nextProps) => {
            if (nextProps.startDate !== this.props.startDate ||
                nextProps.endDate !== this.props.endDate) {
                this.state.currentStartDate = nextProps.startDate;
                this.state.currentEndDate = nextProps.endDate;
                await this.fetchData();
            }
        });

        onMounted(() => {
            window.addEventListener('guru-dashboard-refresh', this._handleRefreshEvent);
        });

        onWillUnmount(() => {
            window.removeEventListener('guru-dashboard-refresh', this._handleRefreshEvent);
        });
    }

    async handleRefreshEvent(event) {
        console.log("🔔 EkskulList: Received refresh event");
        const { startDate, endDate } = event.detail;
        this.state.currentStartDate = startDate;
        this.state.currentEndDate = endDate;
        await this.fetchData();
    }

    async fetchData() {
        // 👇 PREVENT duplicate fetch
        if (this.isFetching) {
            console.log("⏭️ EkskulList: Skipping fetch - already fetching");
            return;
        }

        this.isFetching = true;

        try {
            this.state.isLoading = true;

            const domain = [];

            if (this.state.currentStartDate) {
                domain.push(["tanggal", ">=", this.state.currentStartDate]);
            }
            if (this.state.currentEndDate) {
                domain.push(["tanggal", "<=", this.state.currentEndDate]);
            }

            const records = await this.orm.searchRead(
                "cdn.absen_ekskul_line",
                domain,
                ["id", "siswa_id", "guru", "ekskul", "kehadiran", "tanggal"],
                {
                    order: 'tanggal DESC',
                    limit: 10
                }
            );

            if (!records || records.length === 0) {
                this.state.items = [];
                this.state.hasData = false;
                return;
            }

            this.state.items = records.map((rec, i) => ({
                number: i + 1,
                id: rec.id,
                nama: Array.isArray(rec.siswa_id) ? rec.siswa_id[1] : "N/A",
                ekskul: Array.isArray(rec.ekskul) ? rec.ekskul[1] : "N/A",
                pembimbing: Array.isArray(rec.guru) ? rec.guru[1] : "N/A",
                kehadiran: rec.kehadiran || "N/A",
            }));

            this.state.hasData = this.state.items.length > 0;

        } catch (error) {
            console.error("Error fetching Ekskul data:", error);
            this.state.items = [];
            this.state.hasData = false;
        } finally {
            this.state.isLoading = false;
            this.isFetching = false; // 👈 Reset flag
        }
    }

    openRecord(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Kehadiran Ekskul",
            res_model: "cdn.absen_ekskul_line",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

EkskulList.template = "owl.EkskulList";