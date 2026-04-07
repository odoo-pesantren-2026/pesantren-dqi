/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class KeamananCardList extends Component {
  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    const today = new Date();
    this.state = {
      keluarIjin: [],
      startDate: new Date(
        Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
      )
        .toISOString()
        .split("T")[0],
      endDate: new Date(
        Date.UTC(
          today.getUTCFullYear(),
          today.getUTCMonth(),
          today.getUTCDate(),
          23,
          59,
          59,
          999
        )
      )
        .toISOString()
        .split("T")[0],
    };
    this.refreshInterval = null;
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;
    onWillStart(async () => {
      await this.fetchAllProducts();
    });

    onMounted(() => {
      this.attachEventListeners();
      this.filterDataByPeriod();
    });

    onWillUnmount(() => {
      // COUNTDOWN
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
      }
    });
  }

  toggleCountdown() {
    if (this.isCountingDown) {
      this.clearIntervals();
      document.getElementById("timerCountdown").textContent = "";
      const clockElement = document.getElementById("timerIcon");
      if (clockElement) {
        clockElement.classList.add("fas", "fa-clock");
      }
    } else {
      this.isCountingDown = true;
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
    this.countdownTime = 10;
    this.isCountingDown = false;
  }

  startCountdown() {
    this.countdownTime = 10;
    this.clearIntervals();
    this.updateCountdownDisplay();

    this.countdownInterval = setInterval(() => {
      this.countdownTime--;

      if (this.countdownTime < 0) {
        this.countdownTime = 10;
        if (this.state.startDate && this.state.endDate) {
          // console.log(
          //   "dates state: ",
          //   this.state.startDate,
          //   "& ",
          //   this.state.endDate
          // );
          const startDate = this.state.startDate;
          const endDate = this.state.endDate;
          // console.log("dates: ", startDate, "& ", endDate);
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

  refreshChart(startDate, endDate) {
    this.fetchAllProducts();
  }

  // async fetchAllProducts() {
  //   try {
  //     // Base domain untuk outgoing shipments

  //     let keluarDomain = [];
  //     keluarDomain.push(["state", "=", "Permission"]);
  //     // Tambahkan filter date jika ada
  //     if (this.state.startDate && this.state.endDate) {
  //       keluarDomain.push(["tgl_ijin", ">=", this.state.startDate]);
  //       keluarDomain.push(["tgl_ijin", "<=", this.state.endDate]);
  //     }

  //     const keluarData = await this.orm.call("cdn_perijinan", "search_read", [
  //       keluarDomain,
  //       [
  //         "id",
  //         "name",
  //         "siswa_id",
  //         "tgl_ijin",
  //         "keperluan",
  //         "lama_ijin",
  //         "state",
  //       ],
  //     ]);

  //     console.log("Santri Keluar", keluarData);
  //     this.state.keluarIjin = this.getKeluarData(keluarData);
  //     await this.render();
  //   } catch (error) {
  //     console.error("Error fetching Santri Keluar:", error);
  //   }
  // }

  // getKeluarData(keluarData) {
  //   // Urutkan data berdasarkan `create_date` secara descending (terbaru dulu)

  //   // Gunakan reduce untuk mendapatkan data unik berdasarkan ID produk atau nama (misalnya `name`)
  //   const uniqueKeluar = keluarData.reduce((acc, data) => {
  //     // Gunakan `name` atau `id` sebagai kunci untuk mengeliminasi duplikasi
  //     if (!acc[data.name]) {
  //       acc[data.name] = {
  //         name: data.name,
  //         siswa: data.siswa_id ? data.siswa_id[1] || "N/A" : "N/A", // Tambahkan lokasi jika diperlukan
  //         tgl_ijin: data.tgl_ijin, // Tambahkan tujuan jika diperlukan
  //         keperluan: data.keperluan, // Tambahkan mitra jika diperlukan
  //         lamaijin: data.lama_ijin, // Status produk
  //         state: data.state, // Tanggal pembuatan
  //         id: data.id,
  //       };
  //     }
  //     return acc;
  //   }, {});

  //   // Kembalikan hanya produk terbaru berdasarkan tanggal (sortedData sudah diurutkan)
  //   return Object.values(uniqueKeluar)
  //     .slice(0, 5)
  //     .map((data, index) => ({
  //       number: index + 1, // Nomor urutan
  //       id: data.id,
  //       name: data.name,
  //       siswa: data.siswa,
  //       tgl_ijin: data.tgl_ijin,
  //       keperluan: data.keperluan,
  //       lamaijin: data.lama_ijin,
  //       state: data.state,
  //     }));
  // }

  async fetchAllProducts() {
    try {
      let keluarDomain = [];
      keluarDomain.push(["state", "=", "Permission"]);

      if (this.state.startDate && this.state.endDate) {
        keluarDomain.push(["tgl_ijin", ">=", this.state.startDate]);
        keluarDomain.push(["tgl_ijin", "<=", this.state.endDate]);
      }

      let keluarData = await this.orm.call("cdn.perijinan", "search_read", [
        // dateDomain,
        keluarDomain,
        [
          "id",
          "name",
          "siswa_id",
          "tgl_ijin",
          "lama_ijin",
          "keperluan",
          "state",
        ],
      ]);

      // console.log("Testing Fetch", tagihanLunasData);

      this.state.keluarIjin = this.getKeluarData(keluarData);
      await this.render();
    } catch (error) {
      console.error("Error fetching Santri Keluar:", error);
    }
  }

  getKeluarData(keluarData) {
    const uniqueKeluar = keluarData.reduce((acc, data) => {
      if (!acc[data.name]) {
        acc[data.name] = {
          name: data.name,
          siswa: data.siswa_id ? data.siswa_id[1] || "N/A" : "N/A",
          tgl_ijin: data.tgl_ijin,
          keperluan: String(data.keperluan).replace(/^\d+,\s*/, ""),
          lamaijin: data.lama_ijin,
          state: data.state,
          id: data.id,
        };
      }
      return acc;
    }, {});

    return Object.values(uniqueKeluar)
      .slice(0, 10)
      .sort((a, b) => new Date(b.tgl_ijin) - new Date(a.tgl_ijin))
      .map((data, index) => ({
        number: index + 1,
        id: data.id,
        name: data.name,
        siswa: data.siswa,
        tgl_ijin: this.formatDate(data.tgl_ijin),
        keperluan: data.keperluan,
        lamaijin: data.lamaijin,
        state: data.state,
      }));
  }

  formatDate(dateString) {
    const date = new Date(dateString);
    const day = date.getDate();
    const month = date.toLocaleString("id-ID", { month: "long" }); // Use 'long' for full month name
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");

    return `${day} ${month} ${year}, ${hours}:${minutes}`;
  }

  attachEventListeners() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const timerButton = document.getElementById("timerButton");

    if (timerButton) {
      timerButton.addEventListener("click", this.toggleCountdown.bind(this));
    } else {
      console.error("Timer button element not found");
    }

    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", async (event) => {
        this.state.startDate = event.target.value;
        await this.fetchAllProducts();
      });

      endDateInput.addEventListener("change", async (event) => {
        this.state.endDate = event.target.value;
        await this.fetchAllProducts();
      });
    } else {
      console.error("Date input elements not found");
    }

    const today = new Date();
    let startDate = new Date(
      Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
    );
    let endDate = new Date(
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
    // Add change listener to period selection dropdown
    if (periodSelection) {
      periodSelection.addEventListener("change", () => {
        switch (periodSelection.value) {
          case "7":
            startDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate() - 7
              )
            );
            endDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate()
              )
            );
            break;
          case "15":
            startDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate() - 15
              )
            );
            endDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate()
              )
            );
            break;
          case "month":
            // Set startDate to the 1st of the current month at 00:00:01 UTC
            startDate = new Date(
              Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
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
          case "today":
            // Set startDate and endDate to today
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
            // Set startDate and endDate to yesterday
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
          case "lastMonth":
            startDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth() - 1,
                1,
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
          default:
            startDate = null;
            endDate = null;
        }

        // Update the input fields and the state
        if (startDate && endDate) {
          this.state.startDate = startDate.toISOString().split("T")[0];
          this.state.endDate = endDate.toISOString().split("T")[0];
          startDateInput.value = this.state.startDate;
          endDateInput.value = this.state.endDate;
          this.fetchAllProducts();
        }
      });
    }
  }

  updateDatesAndFilter(event) {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");

    this.state.startDate = startDateInput.value || null;
    this.state.endDate = endDateInput.value || null;

    this.fetchAllProducts();
  }

  filterData() {
    var startDate = document.getElementById("startDate")?.value;
    var endDate = document.getElementById("endDate")?.value;

    if (startDate && endDate) {
      this.fetchAllProducts(startDate, endDate);
      this.state.startDate = startDate;
      this.state.endDate = endDate;
    } else {
      this.fetchAllProducts();
    }
  }

  filterDataByPeriod() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");

    // Langsung eksekusi logic tanpa mendaftarkan event listener baru
    const today = new Date();
    let startDate = new Date(
      Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
    );
    let endDate = new Date(
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

    if (periodSelection) {
      periodSelection.addEventListener("change", () => {
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
          // console.log("dates down: ", startDate, "& ", endDate);
          // console.log(
          //   "dates down state: ",
          //   this.state.startDate,
          //   "& ",
          //   this.state.endDate
          // );

          this.fetchAllProducts(startDate, endDate);
        }
      });
    }
  }

  redirectToProductList(productId) {
    try {
      return this.action.doAction({
        type: "ir.actions.act_window",
        name: "Product",
        res_model: "cdn.perijinan",
        res_id: productId,
        views: [[false, "form"]],
        target: "current",
        domain: [["id", "=", productId]],
      });
    } catch (error) {
      console.error("Error in redirectToProductList:", error);
    }
  }

  onProductClick(productId) {
    this.redirectToProductList(productId);
  }
}

export class KeamananCardList2 extends Component {
  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    const today = new Date();
    this.state = {
      keluarIjin: [],
      startDate: new Date(
        Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
      )
        .toISOString()
        .split("T")[0],
      endDate: new Date(
        Date.UTC(
          today.getUTCFullYear(),
          today.getUTCMonth(),
          today.getUTCDate(),
          23,
          59,
          59,
          999
        )
      )
        .toISOString()
        .split("T")[0],
    };
    this.refreshInterval = null;
    this.countdownInterval = null;
    this.countdownTime = 10;
    this.isCountingDown = false;
    onWillStart(async () => {
      await this.fetchAllProducts();
    });

    onMounted(() => {
      this.attachEventListeners();
      this.filterDataByPeriod();
    });

    onWillUnmount(() => {
      // COUNTDOWN
      if (this.countdownInterval) {
        clearInterval(this.countdownInterval);
      }
    });
  }

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
        if (this.state.startDate && this.state.endDate) {
          // console.log(
          //   "dates state: ",
          //   this.state.startDate,
          //   "& ",
          //   this.state.endDate
          // );
          const startDate = this.state.startDate;
          const endDate = this.state.endDate;
          // s
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

  refreshChart(startDate, endDate) {
    this.fetchAllProducts();
  }

  // async fetchAllProducts() {
  //   try {
  //     // Base domain untuk outgoing shipments

  //     let keluarDomain = [];
  //     keluarDomain.push(["state", "=", "Permission"]);
  //     // Tambahkan filter date jika ada
  //     if (this.state.startDate && this.state.endDate) {
  //       keluarDomain.push(["tgl_ijin", ">=", this.state.startDate]);
  //       keluarDomain.push(["tgl_ijin", "<=", this.state.endDate]);
  //     }

  //     const keluarData = await this.orm.call("cdn_perijinan", "search_read", [
  //       keluarDomain,
  //       [
  //         "id",
  //         "name",
  //         "siswa_id",
  //         "tgl_ijin",
  //         "keperluan",
  //         "lama_ijin",
  //         "state",
  //       ],
  //     ]);

  //     console.log("Santri Keluar", keluarData);
  //     this.state.keluarIjin = this.getKeluarData(keluarData);
  //     await this.render();
  //   } catch (error) {
  //     console.error("Error fetching Santri Keluar:", error);
  //   }
  // }

  // getKeluarData(keluarData) {
  //   // Urutkan data berdasarkan `create_date` secara descending (terbaru dulu)

  //   // Gunakan reduce untuk mendapatkan data unik berdasarkan ID produk atau nama (misalnya `name`)
  //   const uniqueKeluar = keluarData.reduce((acc, data) => {
  //     // Gunakan `name` atau `id` sebagai kunci untuk mengeliminasi duplikasi
  //     if (!acc[data.name]) {
  //       acc[data.name] = {
  //         name: data.name,
  //         siswa: data.siswa_id ? data.siswa_id[1] || "N/A" : "N/A", // Tambahkan lokasi jika diperlukan
  //         tgl_ijin: data.tgl_ijin, // Tambahkan tujuan jika diperlukan
  //         keperluan: data.keperluan, // Tambahkan mitra jika diperlukan
  //         lamaijin: data.lama_ijin, // Status produk
  //         state: data.state, // Tanggal pembuatan
  //         id: data.id,
  //       };
  //     }
  //     return acc;
  //   }, {});

  //   // Kembalikan hanya produk terbaru berdasarkan tanggal (sortedData sudah diurutkan)
  //   return Object.values(uniqueKeluar)
  //     .slice(0, 5)
  //     .map((data, index) => ({
  //       number: index + 1, // Nomor urutan
  //       id: data.id,
  //       name: data.name,
  //       siswa: data.siswa,
  //       tgl_ijin: data.tgl_ijin,
  //       keperluan: data.keperluan,
  //       lamaijin: data.lama_ijin,
  //       state: data.state,
  //     }));
  // }

  async fetchAllProducts() {
    try {
      let keluarDomain = [];
      keluarDomain.push(["state", "=", "Return"]);

      if (this.state.startDate && this.state.endDate) {
        keluarDomain.push(["tgl_ijin", ">=", this.state.startDate]);
        keluarDomain.push(["tgl_ijin", "<=", this.state.endDate]);
      }

      let keluarData = await this.orm.call("cdn.perijinan", "search_read", [
        // dateDomain,
        keluarDomain,
        [
          "id",
          "name",
          "siswa_id",
          "tgl_ijin",
          "lama_ijin",
          "keperluan",
          "state",
        ],
      ]);

      this.state.keluarIjin = this.getKeluarData(keluarData);
      await this.render();
    } catch (error) {
      console.error("Error fetching Santri Keluar:", error);
    }
  }

  getKeluarData(keluarData) {
    const uniqueKeluar = keluarData.reduce((acc, data) => {
      if (!acc[data.name]) {
        acc[data.name] = {
          name: data.name,
          siswa: data.siswa_id ? data.siswa_id[1] || "N/A" : "N/A",
          tgl_ijin: data.tgl_ijin,
          keperluan: String(data.keperluan).replace(/^\d+,\s*/, ""),
          lamaijin: data.lama_ijin,
          state: data.state,
          id: data.id,
        };
      }
      return acc;
    }, {});

    return Object.values(uniqueKeluar)
      .slice(0, 10)
      .sort((a, b) => new Date(b.tgl_ijin) - new Date(a.tgl_ijin))
      .map((data, index) => ({
        number: index + 1,
        id: data.id,
        name: data.name,
        siswa: data.siswa,
        tgl_ijin: this.formatDate(data.tgl_ijin),
        keperluan: data.keperluan,
        lamaijin: data.lamaijin,
        state: data.state,
      }));
  }

  formatDate(dateString) {
    const date = new Date(dateString);
    const day = date.getDate();
    const month = date.toLocaleString("id-ID", { month: "long" }); // Use 'long' for full month name
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");

    return `${day} ${month} ${year}, ${hours}:${minutes}`;
  }

  attachEventListeners() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const timerButton = document.getElementById("timerButton");

    if (timerButton) {
      timerButton.addEventListener("click", this.toggleCountdown.bind(this));
    } else {
      console.error("Timer button element not found");
    }

    if (startDateInput && endDateInput) {
      startDateInput.addEventListener("change", async (event) => {
        this.state.startDate = event.target.value;
        await this.fetchAllProducts();
      });

      endDateInput.addEventListener("change", async (event) => {
        this.state.endDate = event.target.value;
        await this.fetchAllProducts();
      });
    } else {
      console.error("Date input elements not found");
    }

    const today = new Date();
    let startDate = new Date(
      Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
    );
    let endDate = new Date(
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
    // Add change listener to period selection dropdown
    if (periodSelection) {
      periodSelection.addEventListener("change", () => {
        switch (periodSelection.value) {
          case "7":
            startDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate() - 7
              )
            );
            endDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate()
              )
            );
            break;
          case "15":
            startDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate() - 15
              )
            );
            endDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth(),
                today.getUTCDate()
              )
            );
            break;
          case "month":
            // Set startDate to the 1st of the current month at 00:00:01 UTC
            startDate = new Date(
              Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
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
          case "today":
            // Set startDate and endDate to today
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
            // Set startDate and endDate to yesterday
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
          case "lastMonth":
            startDate = new Date(
              Date.UTC(
                today.getUTCFullYear(),
                today.getUTCMonth() - 1,
                1,
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
          default:
            startDate = null;
            endDate = null;
        }

        // Update the input fields and the state
        if (startDate && endDate) {
          this.state.startDate = startDate.toISOString().split("T")[0];
          this.state.endDate = endDate.toISOString().split("T")[0];
          startDateInput.value = this.state.startDate;
          endDateInput.value = this.state.endDate;
          this.fetchAllProducts();
        }
      });
    }
  }

  updateDatesAndFilter(event) {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");

    this.state.startDate = startDateInput.value || null;
    this.state.endDate = endDateInput.value || null;

    this.fetchAllProducts();
  }

  filterData() {
    var startDate = document.getElementById("startDate")?.value;
    var endDate = document.getElementById("endDate")?.value;

    if (startDate && endDate) {
      this.fetchAllProducts(startDate, endDate);
      this.state.startDate = startDate;
      this.state.endDate = endDate;
    } else {
      this.fetchAllProducts();
    }
  }

  filterDataByPeriod() {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const periodSelection = document.getElementById("periodSelection");

    // Langsung eksekusi logic tanpa mendaftarkan event listener baru
    const today = new Date();
    let startDate = new Date(
      Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), 1, 0, 0, 1)
    );
    let endDate = new Date(
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

    if (periodSelection) {
      periodSelection.addEventListener("change", () => {
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

        if (startDate && endDate) {
          this.state.startDate = startDate.toISOString().split("T")[0];
          this.state.endDate = endDate.toISOString().split("T")[0];
          startDateInput.value = this.state.startDate;
          endDateInput.value = this.state.endDate;
          // console.log("dates down: ", startDate, "& ", endDate);
          // console.log(
          //   "dates down state: ",
          //   this.state.startDate,
          //   "& ",
          //   this.state.endDate
          // );

          this.fetchAllProducts(startDate, endDate);
        }
      });
    }
  }

  redirectToProductList(productId) {
    try {
      return this.action.doAction({
        type: "ir.actions.act_window",
        name: "Product",
        res_model: "cdn.perijinan",
        res_id: productId,
        views: [[false, "form"]],
        target: "current",
        domain: [["id", "=", productId]],
      });
    } catch (error) {
      console.error("Error in redirectToProductList:", error);
    }
  }

  onProductClick(productId) {
    this.redirectToProductList(productId);
  }
}

KeamananCardList.template = "owl.KeamananCardList";
KeamananCardList2.template = "owl.KeamananCardList2";
