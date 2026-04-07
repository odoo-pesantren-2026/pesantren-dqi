/** @odoo-module **/
import { Component, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class OrangtuaCardList1 extends Component {
  static props = {
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      mutabaahData: [],
      isLoading: true,
      hasData: false,
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
    };

    onWillStart(async () => {
      await this.fetchMutabaahData();
    });

    onWillUpdateProps(async (nextProps) => {
      if (
        nextProps.startDate !== this.props.startDate ||
        nextProps.endDate !== this.props.endDate
      ) {
        this.state.currentStartDate = nextProps.startDate;
        this.state.currentEndDate = nextProps.endDate;
        await this.fetchMutabaahData();
      }
    });
  }

  async onMutabaahRowClick(mutabaah) {
    try {
      // Search for the mutabaah record that matches the student and date
      const mutabaahRecord = await this.orm.searchRead(
        "cdn.mutabaah_harian",
        [
          ["siswa_id.name", "=", mutabaah.student_name],
          ["tgl", "=", mutabaah.date],
          ["sesi_id.name", "=", mutabaah.session],
        ],
        ["id"]
      );

      if (mutabaahRecord.length > 0) {
        // Open the form view for the mutabaah record
        this.actionService.doAction({
          type: "ir.actions.act_window",
          res_model: "cdn.mutabaah_harian",
          res_id: mutabaahRecord[0].id,
          views: [[false, "form"]],
          target: "current",
        });
      }
    } catch (error) {
      console.error("Error navigating to mutabaah record:", error);
    }
  }

  async fetchMutabaahData() {
    try {
      this.state.isLoading = true;

      // const filterDomain = [];
      //     ["state", "=", "Done"],
      //     ["orangtua_id", "ilike", session.partner_display_name],
      //   ];

      // if (this.state.currentStartDate) {
      //   filterDomain.push(["tgl", ">=", this.state.currentStartDate]);
      // }
      // if (this.state.currentEndDate) {
      //   filterDomain.push(["tgl", "<=", this.state.currentEndDate]);
      // }
      // const siswaDomain = [
      //   ["orangtua_id", "ilike", session.partner_display_name],
      // ];

      // const siswaData = await this.orm.call("cdn.siswa", "search_read", [
      //   siswaDomain,
      //   ["name"],
      // ]);

      // console.log("Siswa Data :", siswaData);

      // let siswaIds = [];

      // console.log("Siswa Data List : ", siswaData);
      // siswaIds = siswaData.map((siswa) => siswa.name);
      // console.log("Siswa Data Nama :", siswaIds);

      // MENCARI SISWA BERDASARKAN ORANG TUA
      const siswaDomain = [
        ["orangtua_id", "ilike", session.partner_display_name],
      ];

      let siswaIds = [];

      const siswaData = await this.orm.call("cdn.siswa", "search_read", [
        siswaDomain,
        ["id"],
      ]);
      siswaIds = siswaData.map((siswa) => siswa.id);
      let combineMutabaahDomain = [
        ["siswa_id", "in", siswaIds],
        ["tgl", ">=", this.state.currentStartDate],
        ["tgl", "<=", this.state.currentEndDate],
        ["state", "=", "Done"],
      ];

      // const dateDomain = [];
      // if (this.state.currentStartDate) {
      //   dateDomain.push(["tgl", ">=", this.state.currentStartDate]);
      // }

      // if (this.state.currentEndDate) {
      //   dateDomain.push(["tgl", ">=", this.state.currentEndDate]);
      // }

      const mutabaahData = await this.orm.searchRead(
        "cdn.mutabaah_harian",
        combineMutabaahDomain,
        [
          "name",
          "tgl",
          "sesi_id",
          "siswa_id",
          "halaqoh_id",
          "total_skor",
          "total_skor_display",
          "state",
        ],
        { order: "tgl desc" }
      );

      if (!mutabaahData || mutabaahData.length === 0) {
        this.state.hasData = false;
        this.state.mutabaahData = [];
        return;
      }

      const processedData = mutabaahData.map((record) => ({
        student_name: record.siswa_id[1],
        date: record.tgl,
        session: record.sesi_id[1],
        halaqah: record.halaqoh_id[1],
        score: record.total_skor_display,
        reference: record.name,
      }));

      // Group by student and get their latest entry
      const studentLatestEntries = {};
      processedData.forEach((record) => {
        const studentName = record.student_name;
        if (
          !studentLatestEntries[studentName] ||
          new Date(record.date) >
            new Date(studentLatestEntries[studentName].date)
        ) {
          studentLatestEntries[studentName] = record;
        }
      });

      this.state.mutabaahData = Object.values(studentLatestEntries)
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .slice(0, 10)
        .map((item, index) => {
          const mutabaah = {
            number: index + 1,
            ...item,
          };

          mutabaah.onClick = () => this.onMutabaahRowClick(mutabaah);
          return mutabaah;
        });

      this.state.hasData = this.state.mutabaahData.length > 0;
    } catch (error) {
      console.error("Error fetching mutabaah data:", error);
      this.state.mutabaahData = [];
      this.state.hasData = false;
    } finally {
      this.state.isLoading = false;
    }
  }
}

OrangtuaCardList1.template = "owl.OrangtuaCardList1";

export class OrangtuaCardList2 extends Component {
  static props = {
    startDate: { type: String, optional: true },
    endDate: { type: String, optional: true },
  };

  setup() {
    this.orm = useService("orm");
    this.actionService = useService("action");
    this.state = {
      topTahfidz: [],
      isLoading: true,
      hasData: false,
      currentStartDate: this.props.startDate,
      currentEndDate: this.props.endDate,
    };

    onWillStart(async () => {
      await this.fetchTahfidzTertinggi();
    });

    onWillUpdateProps(async (nextProps) => {
      if (
        nextProps.startDate !== this.props.startDate ||
        nextProps.endDate !== this.props.endDate
      ) {
        this.state.currentStartDate = nextProps.startDate;
        this.state.currentEndDate = nextProps.endDate;
        await this.fetchTahfidzTertinggi();
      }
    });
  }

  async onTahfidzRowClick(tahfidz) {
    try {
      const tahfidzRecords = await this.orm.searchRead(
        "cdn.tahfidz_quran",
        [
          ["siswa_id.name", "=", tahfidz.name],
          // ["jml_baris", "=", tahfidz.total_baris],
          ["state", "=", "done"],
        ],
        ["id"],
        { limit: 1, order: "tanggal desc" }
      );

      if (tahfidzRecords.length > 0) {
        await this.actionService.doAction({
          type: "ir.actions.act_window",
          res_model: "cdn.tahfidz_quran",
          res_id: tahfidzRecords[0].id,
          views: [[false, "form"]],
          target: "current",
        });
      }
    } catch (error) {
      console.error("Error navigating to tahfidz record:", error);
    }
  }

  async fetchTahfidzTertinggi() {
    let siswaIds = [];
    try {
      this.state.isLoading = true;

      const siswaDomain = [
        ["orangtua_id", "ilike", session.partner_display_name],
      ];

      const siswaData = await this.orm.call("cdn.siswa", "search_read", [
        siswaDomain,
        ["id"],
      ]); 

      siswaIds = siswaData.map((siswa) => siswa.id);

      const siswaFilterDomain = [["siswa_id", "in", siswaIds]];

      const filterDomain = [];
      //     ["state", "=", "done"],
      //     ["siswa_id", "!=", false],
      //     ["orangtua_id", "ilike", session.partner_display_name],
      //   ];

      //   if (this.state.currentStartDate) {
      //     filterDomain.push(["tanggal", ">=", this.state.currentStartDate]);
      //   }
      //   if (this.state.currentEndDate) {
      //     filterDomain.push(["tanggal", "<=", this.state.currentEndDate]);
      //   }

      let combineTahfidzDomain = [
        ["siswa_id", "in", siswaIds],
        ["tanggal", ">=", this.state.currentStartDate],
        ["tanggal", "<=", this.state.currentEndDate],
        ["state", "=", "done"], 
      ];

      // if (this.state.currentStartDate && this.state.currentEndDate) {
      //   // dateDomain.push(["tanggal", ">=", this.state.currentStartDate]);
      //   combineTahfidzDomain = [];
      // }

      // if (this.state.currentEndDate) {
      //   dateDomain.push(["tanggal", ">=", this.state.currentEndDate]);
      // }

      const tahfidzRecords = await this.orm.searchRead(
        "cdn.tahfidz_quran",
        // dateDomain,
        combineTahfidzDomain,
        [
          "siswa_id",
          "tanggal",
          "surah_id",
          "ayat_awal",
          "ayat_akhir",
          "nilai_id",
          "halaqoh_id",
        ],
        {
          order: "tanggal desc",
          limit: 100,
        }
      );

      if (!tahfidzRecords || tahfidzRecords.length === 0) {
        this.state.hasData = false;
        this.state.topTahfidz = [];
        return;
      }

      const uniqueTahfidzMap = new Map();

      tahfidzRecords.forEach((record) => {
        const studentName = record.siswa_id ? record.siswa_id[1] : "N/A";
        const key = `${studentName}_${record.tanggal}_${record.surah_id?.[0]}_${record.ayat_awal_name}`;
        const date = new Date(record.tanggal);

        if (!uniqueTahfidzMap.has(key)) {
          const tahfidz = {
            name: studentName,
            tanggal: record.tanggal,
            date: date,
            surah: record.surah_id ? record.surah_id[1] : "N/A",
            // surah: record.surah_id,
            ayatAwal: parseInt(record.ayat_awal) || 0,
            ayatAkhir: parseInt(record.ayat_akhir?.[1]) || 0,
            nilai: record.nilai_id ? record.nilai_id[1] : "N/A",
            halaqoh: record.halaqoh_id ? record.halaqoh_id[1] : "N/A",
          };

          tahfidz.onClick = () => this.onTahfidzRowClick(tahfidz);
          uniqueTahfidzMap.set(key, tahfidz);
        }
      });

      this.state.topTahfidz = Array.from(uniqueTahfidzMap.values())
        .sort((a, b) => b.date - a.date)
        .map((item, index) => ({
          ...item,
          number: index + 1,
        }));

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

OrangtuaCardList2.template = "owl.OrangtuaCardList2";
