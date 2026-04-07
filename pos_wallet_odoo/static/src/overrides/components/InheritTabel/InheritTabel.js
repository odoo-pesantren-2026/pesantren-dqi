
import { PartnerLine as InheritData } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { PartnerList as InheritTabel } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

// Patch untuk komponen InheritTabel (PartnerList)
patch(InheritTabel.prototype, {
  setup() {
    super.setup();
    this.isCameraVisible = false;
    this.originalTable = null;
    this.notification = useService("notification"); // Gunakan notification service
  },

  // Fungsi untuk menangani pencarian saat input berubah
  async _onSearchInputChange() {
    if (!this.state || !this.state.query) {
      this.partners = null;
      this.render();
      return;
    }

    const query = this.state.query;
    if (query && query.length >= 2) {
      await this.performSearch(query);
    }
  },

  async performSearch(query, noLimit = false) {
    try {
      const response = await rpc(
        "/siswa/search",
        { query: query, no_limit: noLimit },
        {
          headers: {
            accept: "application/json",
          },
        }
      );

      if (response && response.partners) {
        this.partners = response.partners.map((partner) => {
          if (partner.saldo_uang_saku !== undefined) {
            partner.wallet_balance_formatted = this.formatCurrency(
              partner.saldo_uang_saku
            );
          }
          return partner;
        });

        this.render();

        const searchMoreButton = document.querySelector(".search-more-button");
        if (searchMoreButton && noLimit) {
          searchMoreButton.style.display = "none";
        }
      }
    } catch (error) {
      console.error("Error searching for students:", error);
    }
  },

  async onEnter() {
    if (this.state && this.state.query) {
      await this.performSearch(this.state.query, true);
    }
  },

  // Helper function to format currency in IDR
  formatCurrency(amount) {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0);
  },

  // Perbaikan untuk pencarian barcode
  async handleEnterKey(ev) {
    if (ev.key === "Enter") {
      if (!this.state || !this.state.query) {
        return;
      }

      const query = this.state.query;
      const isBarcode = /^\d+$/.test(query);

      if (isBarcode) {
        try {
          const response = await rpc(
            "/siswa/get_data/bar",
            { barcode: query },
            {
              headers: {
                accept: "application/json",
              },
            }
          );

          if (response && response.partner_id) {
            this.clickPartner(response.partner_id);
            this.props.close();

            const successSound = new Audio(
              "/pos_wallet_odoo/static/src/mp3/s1.mp3"
            );
            successSound.play();
            return; // Exit if found
          }
        } catch (error) {
          console.error("Barcode search error:", error);
        }
      }

      // If not numeric or not found as direct barcode, trigger general search
      await this.onEnter();
    }
  },

  async BarCodeSantri() {
    const tableElement = document.getElementById("barcode");

    if (!this.isCameraVisible) {
      if (!tableElement) {
        console.error("Tabel tidak ditemukan.");
        return;
      }

      // Siapkan suara berhasil dan gagal
      const successSound = new Audio("/pos_wallet_odoo/static/src/mp3/s1.mp3");
      const failSound = new Audio("/pos_wallet_odoo/static/src/mp3/s2.mp3");

      // Simpan tabel asli
      this.originalTable = tableElement.cloneNode(true);

      // Buat kontainer video untuk scanner
      const videoContainer = document.createElement("div");
      videoContainer.id = "video-container";
      videoContainer.style.width = "100%";
      videoContainer.style.height = "250px";
      videoContainer.style.maxWidth = "400px";
      videoContainer.style.margin = "auto";
      videoContainer.style.border = "2px solid #ddd";
      videoContainer.style.borderRadius = "10px";
      videoContainer.style.boxShadow = "0 4px 8px rgba(0, 0, 0, 0.2)";
      videoContainer.style.overflow = "hidden";
      videoContainer.style.position = "relative";

      // Buat elemen untuk hasil barcode
      const resultElement = document.createElement("div");
      resultElement.id = "barcode-result";
      resultElement.innerHTML = `Hasil: <span id="barcode-text">Belum ada hasil</span>`;
      resultElement.style.marginTop = "20px";
      resultElement.style.fontSize = "20px";
      resultElement.style.fontWeight = "bold";
      resultElement.style.color = "#28a745";
      resultElement.style.textAlign = "center";

      // Ganti tabel dengan videoContainer dan resultElement
      tableElement.replaceWith(videoContainer);
      videoContainer.after(resultElement);

      // Inisialisasi QuaggaJS
      Quagga.init(
        {
          inputStream: {
            name: "Live",
            type: "LiveStream",
            target: videoContainer,
            constraints: {
              facingMode: "environment",
            },
          },
          decoder: {
            readers: [
              "code_128_reader",
              "ean_reader",
              "ean_8_reader",
              "upc_reader",
              "upc_e_reader",
              "code_39_reader",
            ],
          },
        },
        (err) => {
          if (err) {
            console.error("QuaggaJS gagal diinisialisasi:", err);
            this.notification.add("Kamera tidak dapat diakses", {
              title: "Error",
              type: "danger",
            });
            return;
          }
          Quagga.start();
        }
      );

      // Menampilkan hasil barcode
      Quagga.onDetected(async (result) => {
        const code = result.codeResult.code;
        const barcodeTextElement = document.getElementById("barcode-text");
        if (barcodeTextElement) {
          barcodeTextElement.textContent = code;
        }

        try {
          // Panggil API untuk mendapatkan data partner berdasarkan kode hasil scan
          const response = await rpc(
            "/siswa/get_data/bar",
            { barcode: code },
            {
              headers: {
                accept: "application/json",
              },
            }
          );

          if (response && response.partner_id) {
            // Panggil fungsi clickPartner jika partner ditemukan
            this.clickPartner(response.partner_id);
            successSound.play();

            // Tutup dialog setelah partner dipilih
            if (typeof this.props.close === "function") {
              this.props.close();
            }
          } else {
            console.warn("Partner tidak ditemukan atau data tidak lengkap.");
            failSound.play();

            // Tampilkan notifikasi error
            this.notification.add("Barcode santri tidak ditemukan", {
              title: "Pencarian Gagal",
              type: "danger",
            });
          }
        } catch (error) {
          console.error("Error saat mengambil data partner:", error);
          failSound.play();

          // Tampilkan notifikasi error
          this.notification.add("Terjadi kesalahan saat mencari data", {
            title: "Error",
            type: "danger",
          });
        }

        // Tutup kamera dan kembalikan tampilan
        this.closeCamera(videoContainer, resultElement);
      });

      // Tandai kamera sebagai aktif
      this.isCameraVisible = true;
    } else {
      // Jika kamera sudah aktif, tutup kamera dan kembalikan tampilan
      const videoContainer = document.getElementById("video-container");
      const resultElement = document.getElementById("barcode-result");
      if (videoContainer && resultElement) {
        this.closeCamera(videoContainer, resultElement);
      }
    }
  },

  closeCamera(videoContainer, resultElement) {
    // Pastikan Quagga ada sebelum mencoba menghentikannya
    if (typeof Quagga !== "undefined" && Quagga) {
      // Hentikan QuaggaJS jika sudah diinisialisasi
      Quagga.stop();
    }

    // Kembalikan tabel asli
    if (videoContainer && this.originalTable) {
      videoContainer.replaceWith(this.originalTable);
    }
    if (resultElement) {
      resultElement.remove();
    }

    // Tandai kamera sebagai tidak aktif
    this.isCameraVisible = false;
  },

  // Perbarui method getPartners untuk mengakomodasi pencarian real-time
  getPartners() {
    return this.partners || super.getPartners();
  },
});

// Patch untuk komponen InheritData (PartnerLine)
patch(InheritData.prototype, {
  setup() {
    super.setup();
    // Pastikan barcode ada sebelum memanggil getWalletBalance
    if (this.props && this.props.partner && this.props.partner.barcode) {
      this.getWalletBalance(this.props.partner.barcode);
    }
  },

  async getWalletBalance(barcode) {
    if (!barcode) {
      return; // Keluar jika barcode tidak ada
    }

    try {
      const response = await rpc(
        "/siswa/get_data/bar",
        { barcode: barcode },
        {
          headers: {
            accept: "application/json",
          },
        }
      );

      // Pastikan this.props.partner tersedia
      if (!this.props || !this.props.partner) {
        return;
      }

      // Set wallet_balance dan lainnya ke props.partner
      if (response && !response.error) {
        // Ambil wallet_balance dan nis dari response
        const walletBalance = response.wallet_balance || 0;
        this.props.partner.wallet_balance = walletBalance;
        this.props.partner.nis = response.nis || "";

        // Format wallet_balance ke format rupiah tanpa desimal
        const formattedBalance = new Intl.NumberFormat("id-ID", {
          style: "currency",
          currency: "IDR",
          minimumFractionDigits: 0, // Tidak ada desimal
          maximumFractionDigits: 0, // Tidak ada desimal
        }).format(walletBalance);

        // Simpan hasil format ke wallet_balance yang ditampilkan
        this.props.partner.wallet_balance_formatted = formattedBalance;

        // Trigger render update
        this.render();
      } else {
        console.error("Error fetching data:", response?.error);
        this.props.partner.wallet_balance = 0; // Atur ke 0 jika ada error
        this.props.partner.wallet_balance_formatted = "Rp 0"; // Format default
      }
    } catch (error) {
      console.error("Error fetching wallet balance:", error);
      if (this.props && this.props.partner) {
        this.props.partner.wallet_balance = 0; // Atur ke 0 jika ada error
        this.props.partner.wallet_balance_formatted = "Rp 0"; // Format default
      }
    }
  },
});
