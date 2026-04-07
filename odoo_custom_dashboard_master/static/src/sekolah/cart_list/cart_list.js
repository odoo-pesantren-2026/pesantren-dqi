/** @odoo-module **/

import { Component, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class TagihanLunasList extends Component {
  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    const today = new Date();
    this.state = {
      lunass: [],
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
          console.log(
            "dates state: ",
            this.state.startDate,
            "& ",
            this.state.endDate
          );
          const startDate = this.state.startDate;
          const endDate = this.state.endDate;
          console.log("dates: ", startDate, "& ", endDate);
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
    // Logika refresh chart
    console.log("Refreshing chart...");
    // Contoh penggunaan data fetching ulang
    this.fetchAllProducts();
  }

  async fetchAllProducts() {
    try {
      // Base domain untuk outgoing shipments
      //   let dateDomain = [["picking_type_code", "=", "outgoing"]];
      let domainLunas = [];
      if (this.state.startDate && this.state.endDate) {
        domainLunas.push(["invoice_date", ">=", this.state.startDate]);
        domainLunas.push(["invoice_date", "<=", this.state.endDate]);
      }

      //   console.log("Date Domain:", dateDomain);
      domainLunas.push(["payment_state", "=", "paid"]);
      domainLunas.push(["student", "!=", false]);

      const tagihanLunasData = await this.orm.call(
        "account.move",
        "search_read",
        [
          // dateDomain,
          domainLunas,
          [
            "id",
            "name",
            "siswa_id",
            "ruang_kelas_id",
            "amount_total_signed",
            "payment_state",
            "invoice_date",
            //   "create_date",
          ],
        ]
      );

      console.log("Fetched Lunas Data:", tagihanLunasData);
      this.state.lunass = this.getLunasData(tagihanLunasData);
      await this.render();
    } catch (error) {
      console.error("Error fetching product data:", error);
    }
  }

  //   getLunasData(tagihanLunasData) {
  //     // Urutkan data berdasarkan `create_date` secara descending (terbaru dulu)
  //     // const sortedData = tagihanLunasData.sort(
  //     //   (a, b) => new Date(b.create_date) - new Date(a.create_date)
  //     // );

  //     // Gunakan reduce untuk mendapatkan data unik berdasarkan ID produk atau nama (misalnya `name`)
  //     const uniqueLunas = tagihanLunasData.reduce((acc, lunas) => {
  //       // Gunakan `name` atau `id` sebagai kunci untuk mengeliminasi duplikasi
  //       if (!acc[lunas.name]) {
  //         acc[lunas.name] = {
  //           name: lunas.name,
  //           siswa: lunas.siswa_id,
  //           kelas: lunas.ruang_kelas_id,
  //           total: lunas.amount_total_signed,
  //           state: lunas.payment_state,
  //           //   create_date: product.create_date,
  //           id: lunas.id,
  //         };
  //       }
  //       return acc;
  //     }, {});

  //     // Kembalikan hanya produk terbaru berdasarkan tanggal (sortedData sudah diurutkan)
  //     return Object.values(uniqueLunas)
  //       .slice(0, 5)
  //       .map((lunas, index) => ({
  //         number: index + 1, // Nomor urutan
  //         id: lunas.id,
  //         name: lunas.name,
  //         siswa: lunas.siswa[1],
  //         kelas: lunas.kelas[1],
  //         total: lunas.total[1],
  //         state: lunas.state,
  //         // create_date: product.create_date,
  //       }));
  //   }

  getLunasData(tagihanLunasData) {
    const uniqueLunas = tagihanLunasData.reduce((acc, lunas) => {
      if (!acc[lunas.name]) {
        acc[lunas.name] = {
          name: lunas.name,
          siswa: lunas.siswa_id ? lunas.siswa_id[1] || "N/A" : "N/A",
          kelas: lunas.ruang_kelas_id
            ? lunas.ruang_kelas_id[1] || "N/A"
            : "N/A",
          total: lunas.amount_total_signed,
          state: lunas.payment_state,
          id: lunas.id,
        };
      }
      return acc;
    }, {});

    return Object.values(uniqueLunas)
      .slice(0, 10)
      .map((lunas, index) => ({
        number: index + 1,
        id: lunas.id,
        name: lunas.name || "N/A",
        siswa: lunas.siswa,
        kelas: lunas.kelas,
        total: lunas.total,
        state: lunas.state,
      }));
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

    console.log("Updated Dates:", this.state.startDate, this.state.endDate);

    // Fetch and filter products based on updated date range
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
          console.log("dates down: ", startDate, "& ", endDate);
          console.log(
            "dates down state: ",
            this.state.startDate,
            "& ",
            this.state.endDate
          );

          this.fetchAllProducts(startDate, endDate);
        }
      });
    }
  }

  redirectToLunasList(lunasId) {
    try {
      console.log("Redirecting to Tagihan Lunas Id:", lunasId);
      return this.action.doAction({
        type: "ir.actions.act_window",
        name: "Tagihan Lunas",
        res_model: "account.move",
        res_id: lunasId,
        views: [[false, "form"]],
        target: "current",
        domain: [["id", "=", lunasId]],
      });
    } catch (error) {
      console.error("Error in redirectToProductList:", error);
    }
  }

  onLunasClick(productId) {
    console.log("Product clicked:", productId);
    this.redirectToLunasList(productId);
  }
}

export class TagihanBelumLunasList extends Component {
  setup() {
    this.orm = useService("orm");
    this.action = useService("action");
    const today = new Date();
    this.state = {
      lunass: [],
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
      const periodSelection = document.getElementById("periodSelection");
      if (periodSelection) {
        periodSelection.value = "thisMonth"; // Pilih default "Bulan Ini"
      }
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
          console.log(
            "dates state: ",
            this.state.startDate,
            "& ",
            this.state.endDate
          );
          const startDate = this.state.startDate;
          const endDate = this.state.endDate;
          console.log("dates: ", startDate, "& ", endDate);
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
    // Logika refresh chart
    console.log("Refreshing chart...");
    // Contoh penggunaan data fetching ulang
    this.fetchAllProducts();
  }

  async fetchAllProducts() {
    try {
      let domainLunas = [];
      if (this.state.startDate && this.state.endDate) {
        domainLunas.push(["invoice_date", ">=", this.state.startDate]);
        domainLunas.push(["invoice_date", "<=", this.state.endDate]);
      }

      domainLunas.push(["payment_state", "=", "not_paid"]);
      domainLunas.push(["student", "!=", false]);

      const tagihanLunasData = await this.orm.call(
        "account.move",
        "search_read",
        [
          domainLunas,
          [
            "id",
            "name",
            "siswa_id",
            "ruang_kelas_id",
            "amount_total_signed",
            "payment_state",
            "invoice_date",
          ],
        ]
      );

      console.log("Fetched Lunas Data:", tagihanLunasData);
      this.state.lunass = this.getLunasData(tagihanLunasData);
      await this.render();
    } catch (error) {
      console.error("Error fetching product data:", error);
    }
  }

  getLunasData(tagihanLunasData) {
    const uniqueLunas = tagihanLunasData.reduce((acc, lunas) => {
      if (!acc[lunas.name]) {
        acc[lunas.name] = {
          name: lunas.name,
          siswa: lunas.siswa_id ? lunas.siswa_id[1] || "N/A" : "N/A",
          kelas: lunas.ruang_kelas_id
            ? lunas.ruang_kelas_id[1] || "N/A"
            : "N/A",
          total: lunas.amount_total_signed,
          state: lunas.payment_state,
          id: lunas.id,
        };
      }
      return acc;
    }, {});

    return Object.values(uniqueLunas)
      .slice(0, 10)
      .map((lunas, index) => ({
        number: index + 1,
        id: lunas.id,
        name: lunas.name || "N/A",
        siswa: lunas.siswa,
        kelas: lunas.kelas,
        total: lunas.total,
        state: lunas.state,
      }));
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
    // Add change listener to period selection dropdown
  }

  updateDatesAndFilter(event) {
    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");

    this.state.startDate = startDateInput.value || null;
    this.state.endDate = endDateInput.value || null;

    console.log("Updated Dates:", this.state.startDate, this.state.endDate);

    // Fetch and filter products based on updated date range
    this.fetchAllProducts();
  }

  redirectToBelumLunas(belumId) {
    try {
      console.log("Redirecting to Tagihan Belum Lunas Id:", belumId);
      return this.action.doAction({
        type: "ir.actions.act_window",
        name: "Tagihan Belum Lunas",
        res_model: "account.move",
        res_id: belumId,
        views: [[false, "form"]],
        target: "current",
        domain: [["id", "=", belumId]],
      });
    } catch (error) {
      console.error("Error in redirectToProductList:", error);
    }
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
          this.fetchAllProducts();
        }
      });
    }
  }

  onBelumLunasClick(belumId) {
    console.log("Tagihan Belum Lunas Id:", belumId);
    this.redirectToBelumLunas(belumId);
  }
}

TagihanLunasList.template = "owl.TagihanLunasList";
TagihanBelumLunasList.template = "owl.TagihanBelumLunasList";
