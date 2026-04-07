/** @odoo-module **/
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class MusyrifPerijinanCardList extends Component {
  static props = {
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.orm = useService("orm");
    this.state = {
      perijinans: [],
      isLoading: true,
      hasData: false,
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
      sevenDayData: [],
    };

    onWillStart(async () => {
      await this.fetchPerijinanSantri();
    });

    onWillUpdateProps(async (nextProps) => {
      if (
        nextProps.startDate !== this.props.startDate ||
        nextProps.endDate !== this.props.endDate
      ) {
        this.state.currentStartDate = nextProps.startDate;
        this.state.currentEndDate = nextProps.endDate;
        await this.fetchPerijinanSantri();
      }
    });
  }

  async fetchPerijinanSantri() {
    try {
      this.state.isLoading = true;

      // Ambil data 7 hari terakhir
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const sevenDaysAgoDB = sevenDaysAgo.toISOString().split("T")[0];

      // 🔹 Domain: Hapus filter musyrif_id → semua data ditampilkan
      const sevenDayDomain = [
        ["state", "in", ["Draft", "Check"]],
        ["tgl_ijin", ">=", sevenDaysAgoDB],
        // Tidak ada filter musyrif_id
      ];

      // Ambil data 7 hari terakhir (semua musyrif)
      const sevenDayPerijinan = await this.orm.searchRead(
        "cdn.perijinan",
        sevenDayDomain,
        [
          "name",
          "siswa_id",
          "tgl_ijin",
          "tgl_kembali",
          "penjemput",
          "keperluan",
          "state",
          "kelas_id",
          "kamar_id",
          "halaqoh_id",
          "musyrif_id",
          "catatan",
          "lama_ijin",
        ],
        {
          order: "create_date DESC",
        }
      );

      // Simpan data 7 hari
      this.state.sevenDayData = sevenDayPerijinan;

      // Data gabungan: 7 hari + filter rentang tanggal (jika ada)
      let filteredData = [...this.state.sevenDayData];

      // Jika ada filter tanggal, ambil data tambahan
      if (this.state.currentStartDate || this.state.currentEndDate) {
        const filterDomain = [["state", "in", ["Draft", "Check", "Rejected", ]]];

        if (this.state.currentStartDate) {
          filterDomain.push(["tgl_ijin", ">=", this.state.currentStartDate]);
        }
        if (this.state.currentEndDate) {
          filterDomain.push(["tgl_ijin", "<=", this.state.currentEndDate]);
        }

        // 🔹 Hapus filter musyrif_id di sini juga
        // Tidak menambahkan ["musyrif_id", ...]

        const filteredPerijinan = await this.orm.searchRead(
          "cdn.perijinan",
          filterDomain,
          [
            "name",
            "siswa_id",
            "tgl_ijin",
            "tgl_kembali",
            "penjemput",
            "keperluan",
            "state",
            "kelas_id",
            "kamar_id",
            "halaqoh_id",
            "musyrif_id",
            "catatan",
            "lama_ijin",
          ],
          {
            order: "create_date DESC",
          }
        );

        // Gabungkan data tanpa duplikasi
        const allIds = new Set();
        filteredData = [...filteredData, ...filteredPerijinan].filter((item) => {
          if (!allIds.has(item.id)) {
            allIds.add(item.id);
            return true;
          }
          return false;
        });
      }

      // Format data untuk UI
      this.state.perijinans = filteredData.map((p) => ({
        id: p.id,
        name: p.name,
        student_name: p.siswa_id[1],
        tgl_ijin: this.formatDate(p.tgl_ijin),
        tgl_kembali: this.formatDate(p.tgl_kembali),
        penjemput: p.penjemput,
        keperluan:
          typeof p.keperluan === "string" && p.keperluan.includes(",")
            ? p.keperluan.split(",")[1].trim()
            : Array.isArray(p.keperluan) && p.keperluan[1]
              ? p.keperluan[1]
              : p.keperluan || "N/A",
        state: p.state,
        kelas: p.kelas_id ? p.kelas_id[1] : "N/A",
        kamar: p.kamar_id ? p.kamar_id[1] : "N/A",
        halaqoh: p.halaqoh_id ? p.halaqoh_id[1] : "N/A",
        musyrif: p.musyrif_id ? p.musyrif_id[1] : "Semua Musyrif",
        catatan: p.catatan || "-",
        lama_ijin: p.lama_ijin || 0,
      }));

      this.state.hasData = this.state.perijinans.length > 0;
    } catch (error) {
      console.error("Error fetching perijinan data:", error);
      this.state.perijinans = [];
      this.state.hasData = false;
    } finally {
      this.state.isLoading = false;
    }
  }

  // Fungsi approve dengan SweetAlert
  async handleApprove(perijinanId, student_name) {
    try {
      const result = await Swal.fire({
        title: "Konfirmasi Persetujuan",
        text: `Apakah Anda yakin ingin menyetujui perijinan atas nama ${student_name} ini?`,
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Ya, Setujui",
        cancelButtonText: "Batal",
      });

      if (result.isConfirmed) {
        await this.orm.call("cdn.perijinan", "action_approved", [perijinanId]);
        await this.fetchPerijinanSantri();
        Swal.fire("Berhasil!", "Perijinan telah disetujui.", "success").then(() => {
          location.reload(); // Reload untuk memastikan UI segar
        });
      }
    } catch (error) {
      console.error("Error approving perijinan:", error);
      Swal.fire("Error!", "Terjadi kesalahan saat menyetujui perijinan.", "error");
    }
  }

  // Fungsi reject dengan SweetAlert
  async handleReject(perijinanId, student_name) {
    try {
      const result = await Swal.fire({
        title: "Konfirmasi Penolakan",
        text: `Apakah Anda yakin ingin menolak perijinan atas nama ${student_name} ini?`,
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Ya, Tolak",
        cancelButtonText: "Batal",
      });

      if (result.isConfirmed) {
        await this.orm.call("cdn.perijinan", "action_rejected", [perijinanId]);
        await this.fetchPerijinanSantri();
        Swal.fire("Berhasil!", "Perijinan telah ditolak.", "success").then(() => {
          location.reload();
        });
      }
    } catch (error) {
      console.error("Error rejecting perijinan:", error);
      Swal.fire("Error!", "Terjadi kesalahan saat menolak perijinan.", "error");
    }
  }

  formatDate(dateStr) {
    if (!dateStr) return "N/A";
    const date = new Date(dateStr);
    return date.toLocaleDateString("id-ID", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }
}

MusyrifPerijinanCardList.template = "owl.MusyrifPerijinanCardList";