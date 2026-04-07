
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
    this.notification = useService("notification");
    
    // Explicitly add partners to the reactive state
    this.state.partners = null;
  },

  // Fungsi untuk menangani pencarian saat input berubah
  async _onSearchInputChange() {
    if (!this.state) {
      return;
    }

    const query = this.state.query || "";
    console.log("Search input change detected. Query:", query);
    
    if (query && query.length >= 2) {
      console.log("Triggering performSearch for query:", query);
      await this.performSearch(query);
    } else if (query.length === 0) {
      this.state.partners = null;
    }
  },

  async performSearch(query, noLimit = false) {
    console.log(`Performing search: "${query}", noLimit: ${noLimit}`);
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

      console.log("Search response received. Partners found:", response?.partners?.length || 0);

      if (response && response.partners) {
        // Map data safely and ensure ID is numeric
        // Also ensure wallet_balance matches saldo_uang_saku for POS display
        this.state.partners = response.partners.map((data) => {
          const formattedData = { ...data };
          if (formattedData.id) {
              formattedData.id = Number(formattedData.id);
          }
          
          // Use saldo_uang_saku as the primary balance source
          const balance = formattedData.saldo_uang_saku || 0;
          formattedData.wallet_balance = balance;
          formattedData.wallet_balance_formatted = this.formatCurrency(balance);
          
          return formattedData;
        });
        
        console.log("Partners state updated. UI should refresh automatically.");

        const searchMoreButton = document.querySelector(".search-more-button");
        if (searchMoreButton) {
          searchMoreButton.style.display = noLimit ? "none" : "flex";
        }
      } else {
        console.warn("No partners found in response.");
        this.state.partners = [];
      }
    } catch (error) {
      console.error("Error searching for students:", error);
    }
  },

  async onEnter() {
    console.log("Search more triggered for:", this.state.query);
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
            // Find in local store or use raw data with numeric ID
            let partner = this.pos.models["res.partner"].find(p => p.id === response.partner_id);
            if (!partner) {
              partner = { ...response, id: Number(response.partner_id) };
              // Ensure balance alignment for scanned partner too
              partner.wallet_balance = partner.saldo_uang_saku || partner.wallet_balance || 0;
            }
            
            if (partner) {
              this.clickPartner(partner);
              this.props.close();

              const successSound = new Audio("/pos_wallet_odoo/static/src/mp3/s1.mp3");
              successSound.play();
              return;
            }
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
      if (!tableElement) return;
      
      const successSound = new Audio("/pos_wallet_odoo/static/src/mp3/s1.mp3");
      const failSound = new Audio("/pos_wallet_odoo/static/src/mp3/s2.mp3");
      this.originalTable = tableElement.cloneNode(true);

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

      const resultElement = document.createElement("div");
      resultElement.id = "barcode-result";
      resultElement.innerHTML = `Hasil: <span id="barcode-text">Belum ada hasil</span>`;
      resultElement.style.marginTop = "20px";
      resultElement.style.fontSize = "20px";
      resultElement.style.fontWeight = "bold";
      resultElement.style.color = "#28a745";
      resultElement.style.textAlign = "center";

      tableElement.replaceWith(videoContainer);
      videoContainer.after(resultElement);

      Quagga.init({
        inputStream: { name: "Live", type: "LiveStream", target: videoContainer, constraints: { facingMode: "environment" } },
        decoder: { readers: ["code_128_reader", "ean_reader", "ean_8_reader", "upc_reader", "upc_e_reader", "code_39_reader"] }
      },
        (err) => {
          if (err) {
            console.error("QuaggaJS gagal:", err);
            this.notification.add("Kamera tidak dapat diakses", { title: "Error", type: "danger" });
            return;
          }
          Quagga.start();
        }
      );

      Quagga.onDetected(async (result) => {
        const code = result.codeResult.code;
        const barcodeTextElement = document.getElementById("barcode-text");
        if (barcodeTextElement) barcodeTextElement.textContent = code;

        try {
          const response = await rpc("/siswa/get_data/bar", { barcode: code }, { headers: { accept: "application/json" } });
          if (response && response.partner_id) {
            let partner = this.pos.models["res.partner"].find(p => p.id === response.partner_id);
            if (!partner) {
                partner = { ...response, id: Number(response.partner_id) };
                partner.wallet_balance = partner.saldo_uang_saku || 0;
            }
            
            if (partner) {
                this.clickPartner(partner);
                successSound.play();
                if (typeof this.props.close === "function") this.props.close();
            }
          } else {
            failSound.play();
            this.notification.add("Barcode santri tidak ditemukan", { title: "Pencarian Gagal", type: "danger" });
          }
        } catch (error) {
          console.error("Error barcode scan:", error);
          failSound.play();
        }
        this.closeCamera(videoContainer, resultElement);
      });
      this.isCameraVisible = true;
    } else {
      this.closeCamera(document.getElementById("video-container"), document.getElementById("barcode-result"));
    }
  },

  closeCamera(videoContainer, resultElement) {
    if (typeof Quagga !== "undefined" && Quagga) Quagga.stop();
    if (videoContainer && this.originalTable) videoContainer.replaceWith(this.originalTable);
    if (resultElement) resultElement.remove();
    this.isCameraVisible = false;
  },

  getPartners() {
    return this.state.partners || super.getPartners();
  },
});

// Patch untuk komponen InheritData (PartnerLine)
patch(InheritData.prototype, {
  setup() {
    super.setup();
    if (this.props && this.props.partner && this.props.partner.barcode) {
      this.getWalletBalance(this.props.partner.barcode);
    }
  },

  async getWalletBalance(barcode) {
    if (!barcode) return;
    try {
      const response = await rpc("/siswa/get_data/bar", { barcode: barcode }, { headers: { accept: "application/json" } });
      if (!this.props || !this.props.partner) return;

      if (response && !response.error) {
        // Use saldo_uang_saku as truth for wallet_balance
        const walletBalance = response.saldo_uang_saku || response.wallet_balance || 0;
        this.props.partner.wallet_balance = walletBalance;
        this.props.partner.nis = response.nis || "";
        this.props.partner.wallet_balance_formatted = this.env.utils.formatCurrency(walletBalance);
      }
    } catch (error) {
      console.error("Error balance:", error);
    }
  },
});
