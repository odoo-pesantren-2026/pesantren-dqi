/** @odoo-module */

import { PaymentScreen as BaypasPayment } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { loadJS, loadCSS } from "@web/core/assets";

let pinAttempt = 0;
let simpleKeyboardLoaded = false;

class CustomModal {
  constructor() {
    this.modalContainer = document.getElementById("custom-modal-container");
    if (!this.modalContainer) {
      this.modalContainer = document.createElement("div");
      this.modalContainer.id = "custom-modal-container";
      document.body.appendChild(this.modalContainer);

      this.addStyles();
    }
  }

  addStyles() {
    const styleElement = document.createElement("style");
    styleElement.textContent = `
      .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      
      .modal-overlay.show {
        opacity: 1;
      }
      
      .modal-box {
        background: #fff;
        padding: 2rem;
        border-radius: 0.75rem;
        max-width: 400px;
        width: 90%;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        text-align: center;
        position: relative;
        transform: translateY(-20px);
        opacity: 0;
        transition: all 0.3s ease;
      }
      
      .modal-overlay.show .modal-box {
        transform: translateY(0);
        opacity: 1;
      }
      
      .modal-close {
        position: absolute;
        top: 1rem;
        right: 1rem;
        font-size: 1.2rem;
        cursor: pointer;
        color: #a0aec0;
      }
      
      .modal-close:hover {
        color: #718096;
      }
      
      h2.modal-title {
        color: #e53e3e;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
      }
      
      h2.modal-title.warning {
        color: #dd6b20;
      }
      
      h2.modal-title.info {
        color: #3182ce;
      }
      
      p.modal-body {
        color: #4a5568;
        font-size: 1rem;
        margin-bottom: 1.5rem;
      }
      
      .modal-btn {
        display: inline-block;
        padding: 0.5rem 1.5rem;
        background-color: rgb(15 ,159, 98);
        color: white;
        border-radius: 0.5rem;
        text-decoration: none;
        font-weight: 600;
        transition: background 0.3s ease;
        cursor: pointer;
        border: none;
      }
      
      .modal-btn:hover {
        background-color: rgb(0, 120, 0);
      }
      
      .modal-fade-out {
        opacity: 0 !important;
        transform: translateY(20px) !important;
      }
    `;
    document.head.appendChild(styleElement);
  }

  showModal(options = {}) {
    const {
      title = "Terjadi Kesalahan",
      body = "Maaf, sistem mengalami gangguan.",
      buttonText = "Tutup",
      type = "error",
    } = options;

    const modalHTML = `
      <div class="modal-overlay">
        <div class="modal-box">
          <span class="modal-close">&times;</span>
          <h2 class="modal-title ${type}">${title}</h2>
          <p class="modal-body">${body}</p>
          <button class="modal-btn">${buttonText}</button>
        </div>
      </div>
    `;

    this.modalContainer.innerHTML = modalHTML;

    const overlay = this.modalContainer.querySelector(".modal-overlay");
    const closeBtn = this.modalContainer.querySelector(".modal-close");
    const actionBtn = this.modalContainer.querySelector(".modal-btn");
    const modalBox = this.modalContainer.querySelector(".modal-box");

    setTimeout(() => {
      overlay.classList.add("show");
    }, 10);

    const closeModal = () => {
      modalBox.classList.add("modal-fade-out");
      overlay.classList.remove("show");
      setTimeout(() => {
        this.modalContainer.innerHTML = "";
      }, 300);
    };

    closeBtn.addEventListener("click", closeModal);
    actionBtn.addEventListener("click", closeModal);

    return new Promise((resolve) => {
      actionBtn.addEventListener("click", () => {
        resolve();
      });
    });
  }
}

async function loadSimpleKeyboard() {
  if (!simpleKeyboardLoaded) {
    try {
      await loadJS(
        "https://cdn.jsdelivr.net/npm/simple-keyboard@latest/build/index.min.js"
      );
      await loadCSS(
        "https://cdn.jsdelivr.net/npm/simple-keyboard@latest/build/css/index.min.css"
      );
      simpleKeyboardLoaded = true;
    } catch (error) {
      console.error("Keyboard Gak kenek:", error);
      return false;
    }
  }
  return true;
}

patch(BaypasPayment.prototype, {
  async checkPaymentMethod() {
    super.setup();

    const order = this.pos.get_order();
    console.log(order);

    const data = order.payment_ids
      .map((paymentline) => {
        const paymentMethodName =
          paymentline.payment_method_id.name.toLowerCase();
        if (["Dompet Santri", "dompet santri"].includes(paymentMethodName)) {
          return {
            payment_method_id: paymentline.payment_method_id,
            amount: paymentline.amount,
          };
        }
      })
      .filter(Boolean);

    console.log(data);
    return data;
  },

  // getOrderDetails() {
  //   const order = this.pos.get_order();
  //   const orderLines = order.get_orderlines();

  //   const details = {
  //     order_name: order.name || order.uid,
  //     order_date: new Date().toISOString(),
  //     total_amount: order.get_total_with_tax(),
  //     items: orderLines.map((line) => {
  //       console.log("Debug line:", line); // Debug log
  //       console.log("Debug product:", line.product); // Debug log

  //       // Coba beberapa cara untuk mendapatkan product info
  //       let productName = "Unknown Product";
  //       let productId = null;

  //       try {
  //         if (line.get_product) {
  //           const product = line.get_product();
  //           productName = product.display_name || product.name || productName;
  //           productId = product.id;
  //         } else if (line.product) {
  //           productName =
  //             line.product.display_name || line.product.name || productName;
  //           productId = line.product.id;
  //         } else if (line.product_id && Array.isArray(line.product_id)) {
  //           // Kadang product_id adalah array [id, name]
  //           productId = line.product_id[0];
  //           productName = line.product_id[1] || productName;
  //         }
  //       } catch (error) {
  //         console.log("Error getting product info:", error);
  //       }

  //       return {
  //         product_name: productName,
  //         quantity: line.quantity,
  //         price_unit: line.price,
  //         price_subtotal: line.get_price_with_tax(),
  //         product_id: productId,
  //       };
  //     }),
  //     taxes: order.get_tax_details().map((tax) => ({
  //       name: tax.name,
  //       amount: tax.amount,
  //     })),
  //   };

  //   console.log("Debug details:", details); // Debug log
  //   return details;
  // },

  getOrderDetails() {
    const order = this.pos.get_order();
    const orderLines = order.get_orderlines();

    const details = {
      order_name: order.name || order.uid,
      order_date: new Date().toISOString(),
      total_amount: order.get_total_with_tax(),
      items: orderLines.map((line) => {
        console.log("Debug line:", line);

        let productName = "Unknown Product";
        let productId = null;
        let quantity = 0;
        let priceUnit = 0;
        let priceSubtotal = 0;

        try {
          if (line.get_product && typeof line.get_product === "function") {
            const product = line.get_product();
            productName = product.display_name || product.name || productName;
            productId = product.id;
          } else if (line.product) {
            productName =
              line.product.display_name || line.product.name || productName;
            productId = line.product.id;
          } else if (line.product_id) {
            if (Array.isArray(line.product_id)) {
              productId = line.product_id[0];
              productName = line.product_id[1] || productName;
            } else {
              productId = line.product_id;
            }
          }

          if (line.get_quantity && typeof line.get_quantity === "function") {
            quantity = line.get_quantity();
          } else if (line.qty !== undefined) {
            quantity = line.qty;
          } else if (line.quantity !== undefined) {
            quantity = line.quantity;
          }

          if (
            line.get_unit_price &&
            typeof line.get_unit_price === "function"
          ) {
            priceUnit = line.get_unit_price();
          } else if (line.price_unit !== undefined) {
            priceUnit = line.price_unit;
          } else if (line.price !== undefined) {
            priceUnit = line.price;
          }

          if (
            line.get_price_with_tax &&
            typeof line.get_price_with_tax === "function"
          ) {
            priceSubtotal = line.get_price_with_tax();
          } else if (
            line.get_price_without_tax &&
            typeof line.get_price_without_tax === "function"
          ) {
            priceSubtotal = line.get_price_without_tax();
          } else if (line.price_subtotal_incl !== undefined) {
            priceSubtotal = line.price_subtotal_incl;
          } else if (line.price_subtotal !== undefined) {
            priceSubtotal = line.price_subtotal;
          } else {
            priceSubtotal = quantity * priceUnit;
          }

          console.log(
            `Product: ${productName}, Qty: ${quantity}, Price: ${priceUnit}, Subtotal: ${priceSubtotal}`
          );
        } catch (error) {
          console.log("Error getting product info:", error);
        }

        return {
          product_name: productName,
          quantity: quantity,
          price_unit: priceUnit,
          price_subtotal: priceSubtotal,
          product_id: productId,
        };
      }),
      taxes: order.get_tax_details().map((tax) => ({
        name: tax.name,
        amount: tax.amount,
      })),
    };

    console.log("Order Details:", details);
    return details;
  },

  async clickSetSubTotal() {
    const customModal = new CustomModal();

    const paymentMethodCount = await this.checkPaymentMethod();
    if (paymentMethodCount.length > 0) {
      const currentOrder = this.pos.get_order();
      const client = currentOrder.get_partner();
      if (!client) {
        customModal.showModal({
          title: "  Pelanggan Tidak Dipilih",
          body: " Silakan pilih pelanggan dari daftar sebelum memasukkan PIN.",
          type: "error",
        });
        return;
      }

      const clientData = await this.getData(client.name);
      if (clientData) {
        const clientPin = clientData.pin || "654321";
        const walletBalance = clientData.saldo_uang_saku || 0;
        await this.showPinInputPopup(clientPin, walletBalance, client.id);
      }
    } else {
      this.validateOrder();
    }
  },

  async getData(name) {
    const apiUrl = "/siswa/get_data";
    try {
      const domainFilter = [["name", "like", name]];

      const data = await rpc(
        apiUrl,
        { domain: domainFilter },
        {
          headers: {
            accept: "application/json",
          },
        }
      );
      return data[0] || null;
    } catch (error) {
      console.error("Kesalahan saat mengambil data:", error);
      return null;
    }
  },

  async showPinInputPopup(clientPin, walletBalance, clientId) {
    const keyboardLoaded = await loadSimpleKeyboard();
    if (!keyboardLoaded) {
      this._showFallbackPinInput(clientPin, walletBalance, clientId);
      return;
    }

    const popup = document.createElement("div");

    const keyboardStyle = document.createElement("style");
    keyboardStyle.textContent = `
            .simple-keyboard {
                margin-top: 20px;
            }
            .simple-keyboard .hg-button {
                height: 45px;
                font-size: 20px;
                border-radius: 5px;
                background: #f5f5f5;
                border: 1px solid #ddd;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }
            .simple-keyboard .hg-button:hover {
                background: #e0e0e0;
            }
            .simple-keyboard .hg-button.hg-functionBtn {
                background: #ddd;
            }
            .numeric-pin-input {
                letter-spacing: 5px;
                font-size: 24px;
                text-align: center;
                padding: 10px;
            }
        `;
    document.head.appendChild(keyboardStyle);

    popup.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;">
                <div style="
                    background: white;
                    padding: 20px 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                    text-align: center;
                    width: 340px;">
                    <h3 style="margin: 0; color: #333;">Masukkan PIN Pelanggan</h3>
                    <p style="font-size: 14px; color: #666; margin: 10px 0;">Pastikan PIN sesuai untuk melanjutkan transaksi.</p>
                    <input
                        type="password"
                        id="pinInput"
                        placeholder="______"
                        class="numeric-pin-input"
                        maxlength="6"
                        style="width: 100%; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px;"
                        >

                    <!-- Container untuk simple-keyboard -->
                    <div id="keyboard" class="simple-keyboard"></div>

                    <div style="margin-top: 20px; display: flex; justify-content: space-between;">
                        <button id="submitPinButton"
                            style="padding: 12px 0; width: 48%; font-size: 16px; color: white; background: #007BFF; border: none; border-radius: 5px; cursor: pointer;">
                            Simpan
                        </button>
                        <button id="cancelButton"
                            style="padding: 12px 0; width: 48%; font-size: 16px; color: #333; background: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; cursor: pointer;">
                            Batal
                        </button>
                    </div>
                </div>
            </div>
        `;

    document.body.appendChild(popup);

    const pinInput = document.getElementById("pinInput");
    pinInput.focus();

    pinInput.addEventListener("input", function (e) {
      // Hapus karakter non-numerik
      this.value = this.value.replace(/[^0-9]/g, "");

      // Batasi panjang maksimum input
      if (this.value.length > 6) {
        this.value = this.value.slice(0, 6);
      }

      // Update keyboard juga
      keyboard.setInput(this.value);
    });

    // Cegah paste konten non-numerik
    pinInput.addEventListener("paste", function (e) {
      e.preventDefault();
      const pastedText = (e.clipboardData || window.clipboardData).getData(
        "text"
      );
      const numericText = pastedText.replace(/[^0-9]/g, "").slice(0, 6);

      if (numericText) {
        this.value = numericText;
        keyboard.setInput(numericText);
      }
    });

    pinInput.addEventListener("keydown", function (e) {
      if (
        [46, 8, 9, 27, 13].indexOf(e.keyCode) !== -1 ||
        // Allow: Ctrl+A, Command+A
        (e.keyCode === 65 && (e.ctrlKey === true || e.metaKey === true)) ||
        // Allow: home, end, left, right, down, up
        (e.keyCode >= 35 && e.keyCode <= 40)
      ) {
        return;
      }

      if (
        (e.shiftKey || e.keyCode < 48 || e.keyCode > 57) &&
        (e.keyCode < 96 || e.keyCode > 105)
      ) {
        e.preventDefault();
      }
    });

    const submitButton = document.getElementById("submitPinButton");
    const cancelButton = document.getElementById("cancelButton");

    const keyboard = new window.SimpleKeyboard.default({
      onChange: (input) => {
        pinInput.value = input;
      },
      layout: {
        default: ["1 2 3", "4 5 6", "7 8 9", "{clear} 0 {bksp}"],
      },
      display: {
        "{clear}": "Hapus",
        "{bksp}": "⌫",
      },
      theme: "hg-theme-default hg-layout-numeric",
      maxLength: 6,
      inputPattern: /^[0-9]*$/,
      onKeyPress: (button) => {
        if (button === "{clear}") {
          keyboard.setInput("");
          pinInput.value = "";
        }
      },
    });

    submitButton.onclick = async () => {
      const enteredPin = pinInput.value.trim();
      if (!enteredPin) {
        const warningModal = document.createElement("div");
        warningModal.innerHTML = `
            <div style="
              position: fixed;
              top: 0;
              left: 0;
              width: 100%;
              height: 100%;
              background: rgba(0,0,0,0.5);
              display: flex;
              justify-content: center;
              align-items: center;
              z-index: 10000;">
              <div style="
                background: white;
                padding: 20px 25px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                text-align: center;
                width: 300px;
                animation: fadeIn 0.2s ease;">
                <div style="
                  width: 50px;
                  height: 50px;
                  margin: 0 auto 15px auto;
                  border-radius: 50%;
                  background: #ffefef;
                  display: flex;
                  align-items: center;
                  justify-content: center;">
                  <span style="
                    color: #e74c3c;
                    font-size: 30px;
                    font-weight: bold;">!</span>
                </div>
                <h3 style="margin: 0 0 10px 0; color: #333;">Peringatan</h3>
                <p style="font-size: 15px; color: #555; margin: 0 0 20px 0;">PIN tidak boleh kosong!</p>
                <button id="closeWarningBtn" 
                  style="
                    padding: 10px 25px;
                    font-size: 15px;
                    color: white;
                    background: #3498db;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background 0.2s;">OK</button>
              </div>
            </div>
          `;

        document.body.appendChild(warningModal);

        document
          .getElementById("closeWarningBtn")
          .addEventListener("click", () => {
            document.body.removeChild(warningModal);
          });

        warningModal.addEventListener("click", (e) => {
          if (e.target === warningModal) {
            document.body.removeChild(warningModal);
          }
        });

        return;
      }

      document.body.removeChild(popup);
      document.head.removeChild(keyboardStyle);
      await this.apply_pin(enteredPin, clientPin, walletBalance, clientId);
    };

    cancelButton.onclick = () => {
      document.body.removeChild(popup);
      document.head.removeChild(keyboardStyle);
    };

    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        document.body.removeChild(popup);
        document.head.removeChild(keyboardStyle);
      }
    });
  },

  _showFallbackPinInput(clientPin, walletBalance, clientId) {
    const popup = document.createElement("div");
    popup.innerHTML = `
            <div style="
                position: fixed; 
                top: 0; 
                left: 0; 
                width: 100%; 
                height: 100%; 
                background: rgba(0,0,0,0.5); 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                z-index: 9999;">
                <div style="
                    background: white; 
                    padding: 20px 30px; 
                    border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2); 
                    text-align: center; 
                    width: 320px;
                    animation: fadeIn 0.3s ease;">
                    <h3 style="margin: 0; color: #333;">Masukkan PIN Pelanggan</h3>
                    <p style="font-size: 14px; color: #666; margin: 10px 0;">Pastikan PIN sesuai untuk melanjutkan transaksi.</p>
                    <input 
                        type="password" 
                        id="pinInput" 
                        placeholder="Masukkan PIN Anda" 
                        style="padding: 10px; width: 100%; font-size: 16px; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; text-align: center; letter-spacing: 4px;"
                        maxlength="6">
                    
                    <div style="margin-top: 15px; display: flex; justify-content: space-between;">
                        <button id="submitPinButton" 
                            style="padding: 12px 0; width: 48%; font-size: 16px; color: white; background: #007BFF; border: none; border-radius: 5px; cursor: pointer;">
                            Submit
                        </button>
                        <button id="cancelButton" 
                            style="padding: 12px 0; width: 48%; font-size: 16px; color: #333; background: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; cursor: pointer;">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        `;

    document.body.appendChild(popup);

    const pinInput = document.getElementById("pinInput");
    pinInput.focus(); // Tambahkan baris ini

    const submitButton = document.getElementById("submitPinButton");
    const cancelButton = document.getElementById("cancelButton");

    submitButton.onclick = async () => {
      const enteredPin = pinInput.value.trim();
      if (!enteredPin) {
        alert("PIN tidak boleh kosong!");
        return;
      }
      document.body.removeChild(popup);
      await this.apply_pin(enteredPin, clientPin, walletBalance, clientId);
    };

    cancelButton.onclick = () => {
      document.body.removeChild(popup);
    };

    popup.addEventListener("click", (e) => {
      if (e.target === popup) {
        document.body.removeChild(popup);
      }
    });
  },

  // _showErrorPopup(title, message) {
  //   const errorPopup = document.createElement("div");
  //   errorPopup.innerHTML = `  <div
  //     style="
  //       position: fixed;
  //       inset: 0;
  //       background: rgba(0, 0, 0, 0.5);
  //       display: flex;
  //       align-items: center;
  //       justify-content: center;
  //       z-index: 999;
  //     "
  //   >
  //     <div
  //       style="
  //         background: #fff;
  //         padding: 2rem;
  //         border-radius: 0.75rem;
  //         max-width: 400px;
  //         width: 90%;
  //         box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  //         text-align: center;
  //         position: relative;
  //       "
  //     >
  //       <span
  //         id="exitButton"
  //         style="
  //           position: absolute;
  //           top: 1rem;
  //           right: 1rem;
  //           font-size: 1.2rem;
  //           cursor: default;
  //           color: #a0aec0;
  //           cursor: pointer;
  //         "
  //         >&times;</span
  //       >
  //       <h2 style="color: #e53e3e; font-size: 1.5rem; margin-bottom: 0.5rem">
  //         ${title}
  //       </h2>
  //       <p style="color: #4a5568; font-size: 1rem; margin-bottom: 1.5rem">
  //         ${message}
  //       </p>
  //       <span
  //         id="exitButton"
  //         style="
  //           display: inline-block;
  //           padding: 0.5rem 1rem;
  //           background-color: rgb(0, 187, 0);
  //           color: white;
  //           border-radius: 0.5rem;
  //           text-decoration: none;
  //           font-weight: 600;
  //           cursor: pointer;
  //         "
  //         >Tutup</span
  //       >
  //     </div>
  //   </div>`;
  // },

  async apply_pin(enteredPin, clientPin, walletBalance, clientId) {
    const customModal = new CustomModal();

    if (pinAttempt >= 3) {
      customModal.showModal({
        title: "PIN Diblokir",
        body: "Anda telah memasukkan PIN yang salah 3 kali. Silakan tunggu 1 jam untuk mencoba lagi.",
        type: "error",
      });
      // this.dialog.add(AlertDialog, {
      //   title: _t("PIN Diblokir"),
      //   body: _t(
      //     "Anda telah memasukkan PIN yang salah 3 kali. Silakan tunggu 1 jam untuk mencoba lagi."
      //   ),
      // });
      return;
    } else if (walletBalance <= 0) {
      customModal.showModal({
        title: "Saldo Anda Kurang",
        body: "Anda tidak bisa melanjutkan transaksi karena saldo anda kurang.",
        type: "warning",
      });
      return;
    }

    if (enteredPin === clientPin) {
      pinAttempt = 0; // Reset counter PIN
      const paymentMethodCount = await this.checkPaymentMethod();
      const totalAmount = paymentMethodCount[0].amount;
      const orderDetails = this.getOrderDetails();

      console.log("Data:", totalAmount);
      if (totalAmount > walletBalance) {
        customModal.showModal({
          title: "Saldo Tidak Mencukupi",
          body: "Saldo pelanggan tidak cukup untuk membayar transaksi ini.",
          type: "warning",
        });
        return;
      }

      try {
        // Panggil controller untuk mengurangi saldo
        const result = await rpc("/siswa/deduct_wallet", {
          partner_id: clientId,
          amount: totalAmount,
          order_details: orderDetails,
        });
        if (result.success) {
          this.validateOrder(); // Panggil fungsi validasi order jika diperlukan
        } else if (result.warning) {
          customModal.showModal({
            title: "Batas Penggunaan Saldo",
            body:
              result.message || "Santri telah mencapai batas penggunaan saldo",
            type: "warning",
          });
        } else if (result.error) {
          customModal.showModal({
            title: "Akses Ditolak",
            body: result.error || "Terjadi Kesalahan saat mengurangi saldo",
          });
        } else {
          customModal.showModal({
            title: "Kesalahan",
            body: "Terjadi kesalahan saat mengurangi saldo: " + result.error,
            type: "error",
          });
        }
      } catch (error) {
        customModal.showModal({
          title: "Kesalahan",
          body: "Terjadi kesalahan saat mengurangi saldo: " + result.error,
          type: "error",
        });
      }
    } else {
      pinAttempt += 1;
      const remainingAttempts = 3 - pinAttempt;
      const isBlocked = pinAttempt >= 3;

      customModal.showModal({
        title: isBlocked ? "PIN Diblokir" : "PIN Salah",
        body: isBlocked
          ? "Anda telah memasukkan PIN yang salah 3 kali. Silakan tunggu 1 jam untuk mencoba lagi."
          : `PIN Salah, Anda memiliki ${remainingAttempts} kesempatan lagi.`,
        type: "error",
      });

      if (isBlocked) {
        setTimeout(() => {
          pinAttempt = 0;
        }, 3600000); // Reset setelah 1 jam
      }
    }
  },
});
