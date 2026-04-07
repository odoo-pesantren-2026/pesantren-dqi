/** @odoo-module **/
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PelanggaranCardList extends Component {
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true }
    };

    setup() {
        this.orm = useService('orm');
        this.actionService = useService('action');
        this.state = {
            pelanggarans: [],
            isLoading: true,
            hasData: false,
            currentStartDate: this.props.startDate,
            currentEndDate: this.props.endDate
        };

        onWillStart(async () => {
            await this.fetchPelanggaranSantri();
        });

        onWillUpdateProps(async (nextProps) => {
            if (nextProps.startDate !== this.props.startDate || 
                nextProps.endDate !== this.props.endDate) {
                this.state.currentStartDate = nextProps.startDate;
                this.state.currentEndDate = nextProps.endDate;
                await this.fetchPelanggaranSantri();
            }
        });
    }

    async onPelanggaranRowClick(pelanggaran) {
        try {
            const pelanggaranRecord = await this.orm.searchRead(
                'cdn.pelanggaran', 
                [
                    ['siswa_id.name', '=', pelanggaran.student_name],
                    ['tgl_pelanggaran', '=', this.formatDateForSearch(pelanggaran.tanggal)],
                    ['pelanggaran_id.name', '=', pelanggaran.pelanggaran_name],
                    ['poin', '=', pelanggaran.points]
                ], 
                ['id', 'name']
            );
    
            if (pelanggaranRecord.length > 0) {

                this.actionService.doAction({
                    type: 'ir.actions.act_window',
                    res_model: 'cdn.pelanggaran',
                    res_id: pelanggaranRecord[0].id,
                    views: [[false, 'form']],
                    target: 'current'
                });
            } else {
                console.warn("No matching pelanggaran record found");
            }
        } catch (error) {
            console.error("Error navigating to pelanggaran record:", error);
        }
    }
    formatDateForSearch(dateStr) {
        if (!dateStr) return null;
        const [day, month, year] = dateStr.split('/');
        return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
    }
    
    async fetchPelanggaranSantri() {
        try {
            this.state.isLoading = true;

            const filterDomain = [
                ['state', '=', 'approved'],
                ['poin', '>', 0]
            ];

            if (this.state.currentStartDate) {
                filterDomain.push(['tgl_pelanggaran', '>=', this.state.currentStartDate]);
            }
            if (this.state.currentEndDate) {
                filterDomain.push(['tgl_pelanggaran', '<=', this.state.currentEndDate]);
            }

            const pelanggaranRecords = await this.orm.searchRead(
                'cdn.pelanggaran',
                filterDomain,
                [
                    'siswa_id',
                    'pelanggaran_id',
                    'kategori',
                    'poin',
                    'tgl_pelanggaran',
                    'kelas_id',
                    'deskripsi'
                ],
                { 
                    order: 'create_date DESC, poin DESC'
                }
            );

            if (!pelanggaranRecords || pelanggaranRecords.length === 0) {
                this.state.hasData = false;
                this.state.pelanggarans = [];
                return;
            }

            const studentIds = [...new Set(pelanggaranRecords.map(p => p.siswa_id[0]))];
            const students = await this.orm.searchRead(
                'cdn.siswa',
                [['id', 'in', studentIds]],
                ['id', 'name', 'ruang_kelas_id']
            );
           
            const studentMap = new Map(students.map(s => [s.id, s]));

            this.state.pelanggarans = pelanggaranRecords
                .map((p,index) => {
                    const pelanggaran = {
                        number: index + 1,
                        student_name: studentMap.get(p.siswa_id[0])?.name || "N/A",
                        pelanggaran_name: p.pelanggaran_id[1] || "N/A",
                        kategori: p.kategori || "N/A",
                        points: p.poin || 0,
                        tanggal: this.formatDate(p.tgl_pelanggaran),
                        kelas: p.kelas_id ? p.kelas_id[1] : "N/A",
                        deskripsi: p.deskripsi || ""
                    };
                    
                    pelanggaran.onClick = () => this.onPelanggaranRowClick(pelanggaran);
                    return pelanggaran;
                })
                .sort((a, b) => new Date(b.tanggal) - new Date(a.tanggal))
                .slice(0, 10);

            this.state.hasData = this.state.pelanggarans.length > 0;

        } catch (error) {
            console.error("Error fetching pelanggaran data:", error);
            this.state.pelanggarans = [];
            this.state.hasData = false;
        } finally {
            this.state.isLoading = false;
        }
    }

    formatDate(dateStr) {
        if (!dateStr) return "N/A";
        const date = new Date(dateStr);
        return date.toLocaleDateString('id-ID', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }
}

PelanggaranCardList.template = 'owl.PelanggaranCardList';

export class TahfidzCardList extends Component {
    static props = {
        startDate: { type: String, optional: true },
        endDate: { type: String, optional: true }
    };

    setup() {
        this.orm = useService('orm');
        this.actionService = useService('action');
        this.state = {
            topTahfidz: [],
            isLoading: true,
            hasData: false,
            currentStartDate: this.props.startDate,
            currentEndDate: this.props.endDate
        };

        onWillStart(async () => {
            await this.fetchTahfidzTertinggi();
        });

        onWillUpdateProps(async (nextProps) => {
            if (nextProps.startDate !== this.props.startDate || 
                nextProps.endDate !== this.props.endDate) {
                this.state.currentStartDate = nextProps.startDate;
                this.state.currentEndDate = nextProps.endDate;
                await this.fetchTahfidzTertinggi();
            }
        });
    }

   async onTahfidzRowClick(tahfidz) {
    try {
        const record = await this.orm.searchRead(
            'cdn.penilaian_quran',
            [
                ['siswa_id.name', '=', tahfidz.name],
                ['state', '=', 'done']
            ],
            ['id'],
            { order: 'tanggal desc', limit: 1 }
        );

        if (record.length > 0) {
            this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'cdn.penilaian_quran',
                res_id: record[0].id,
                views: [[false, 'form']],
                target: 'current'
            });
        }
    } catch (error) {
        console.error("Error navigating to tahfidz record:", error);
    }
}


    async fetchTahfidzTertinggi() {
    try {
        this.state.isLoading = true;

        // 🔍 Filter hanya penilaian yang selesai
        const domain = [['state', '=', 'done']];

        if (this.state.currentStartDate) {
            domain.push(['tanggal', '>=', this.state.currentStartDate]);
        }
        if (this.state.currentEndDate) {
            domain.push(['tanggal', '<=', this.state.currentEndDate]);
        }

        // Ambil semua penilaian done
        const penilaianRecords = await this.orm.searchRead(
            'cdn.penilaian_quran',
            domain,
            ['id', 'siswa_id', 'tanggal']
        );

        if (!penilaianRecords.length) {
            this.state.topTahfidz = [];
            this.state.hasData = false;
            return;
        }

        const penilaianIds = penilaianRecords.map(p => p.id);

        // 🔹 Ambil detail tahfidz line
        const tahfidzLines = await this.orm.searchRead(
            'cdn.penilaian_quran_line',
            [['penilaian_id', 'in', penilaianIds]],
            ['penilaian_id', 'jml_baris']
        );

        if (!tahfidzLines.length) {
            this.state.topTahfidz = [];
            this.state.hasData = false;
            return;
        }

        // 🔢 Hitung total jml_baris per santri
        const totalPerSantri = {};
        for (const line of tahfidzLines) {
            const penilaian = penilaianRecords.find(p => p.id === line.penilaian_id[0]);
            if (!penilaian || !penilaian.siswa_id) continue;

            const siswaName = penilaian.siswa_id[1];
            if (!totalPerSantri[siswaName]) {
                totalPerSantri[siswaName] = {
                    name: siswaName,
                    total_baris: 0
                };
            }
            totalPerSantri[siswaName].total_baris += line.jml_baris || 0;
        }

        // 🔽 Urutkan dan ambil top 10
        const sortedData = Object.values(totalPerSantri)
            .sort((a, b) => b.total_baris - a.total_baris)
            .slice(0, 10);

        // Tambahkan nomor urut + klik action
        this.state.topTahfidz = sortedData.map((item, index) => {
            const tahfidz = {
                number: index + 1,
                ...item
            };

            tahfidz.onClick = () => this.onTahfidzRowClick(tahfidz);
            return tahfidz;
        });

        this.state.hasData = this.state.topTahfidz.length > 0;
    } catch (error) {
        console.error("Error fetching tahfidz data:", error);
        this.state.topTahfidz = [];
        this.state.hasData = false;
    } finally {
        this.state.isLoading = false;
    }
}

}

TahfidzCardList.template = 'owl.TahfidzCardList';

