/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS, loadCSS } from "@web/core/assets";

// Global tracking variables
let pinAttempt = 0;
let simpleKeyboardLoaded = false;

// Load the simple-keyboard library
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
      console.error("Keyboard tidak dapat dimuat:", error);
      return false;
    }
  }
  return true;
}

// Register client action for the PIN popup
registry.category("actions").add("custom_pin_popup", async (env, action) => {
  const { params } = action;

  // Extract partner_id from context or params
  const partnerId = params.partner_id || action.context?.active_id;

  if (!partnerId) {
    env.services.notification.add("Partner ID tidak ditemukan", {
      type: "danger",
    });
    return Promise.resolve();
  }

  const orm = env.services.orm;
  const notification = env.services.notification;
  const dialog = env.services.dialog;
  const model = params.model || "res.partner.change.pin";

  let recordId;
  try {
    recordId = await orm.create(model, [{}]);
    if (Array.isArray(recordId)) {
      recordId = recordId[0];
    }
  } catch (error) {
    notification.add("Gagal membuat record sementara: " + error.message, {
      type: "danger",
    });
    return Promise.resolve();
  }

  const showPinInputPopup = async () => {
    const keyboardLoaded = await loadSimpleKeyboard();
    if (!keyboardLoaded) {
      showFallbackPinInput();
      return;
    }

    const popup = document.createElement("div");
    popup.id = "pin-change-popup";

    const keyboardStyle = document.createElement("style");
    keyboardStyle.id = "simple-keyboard-style";
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
                    <h3 style="margin: 0; color: #333;">Ubah PIN</h3>
                    <p style="font-size: 14px; color: #666; margin: 10px 0;">Masukkan PIN baru Anda.</p>
                    <input
                        type="password"
                        id="pinInput"
                        placeholder="______"
                        maxlength="6"
                        class="numeric-pin-input"
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
    const submitButton = document.getElementById("submitPinButton");
    const cancelButton = document.getElementById("cancelButton");

    pinInput.focus();

    // Active input element (for keyboard focus)
    let activeInput = pinInput;

    // Add input validation for PIN field
    pinInput.addEventListener("input", function (e) {
      // Remove non-numeric characters
      this.value = this.value.replace(/[^0-9]/g, "");

      // Limit maximum input length
      if (this.value.length > 6) {
        this.value = this.value.slice(0, 6);
      }

      // Update keyboard
      keyboard.setInput(this.value);
    });

    // Prevent pasting non-numeric content
    const preventNonNumericPaste = function (e) {
      e.preventDefault();
      const pastedText = (e.clipboardData || window.clipboardData).getData(
        "text"
      );
      const numericText = pastedText.replace(/[^0-9]/g, "").slice(0, 6);

      if (numericText) {
        this.value = numericText;
        if (activeInput === this) {
          keyboard.setInput(numericText);
        }
      }
    };

    pinInput.addEventListener("paste", preventNonNumericPaste);

    // Prevent non-numeric key press
    const preventNonNumericKeydown = function (e) {
      // Allow: backspace, delete, tab, escape, enter
      if (
        [46, 8, 9, 27, 13].indexOf(e.keyCode) !== -1 ||
        // Allow: Ctrl+A, Command+A
        (e.keyCode === 65 && (e.ctrlKey === true || e.metaKey === true)) ||
        // Allow: home, end, left, right, down, up
        (e.keyCode >= 35 && e.keyCode <= 40)
      ) {
        return;
      }
      // Ensure that it's a number and stop the keypress if not
      if (
        (e.shiftKey || e.keyCode < 48 || e.keyCode > 57) &&
        (e.keyCode < 96 || e.keyCode > 105)
      ) {
        e.preventDefault();
      }
    };

    pinInput.addEventListener("keydown", preventNonNumericKeydown);

    // Initialize virtual keyboard
    const keyboard = new window.SimpleKeyboard.default({
      onChange: (input) => {
        activeInput.value = input;
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
          activeInput.value = "";
        }
      },
    });

    // Show warning popup
    // const showWarning = (message) => {
    //   const warningModal = document.createElement("div");
    //   warningModal.id = "pin-warning-modal";
    //   warningModal.innerHTML = `
    //             <div style="
    //               position: fixed;
    //               top: 0;
    //               left: 0;
    //               width: 100%;
    //               height: 100%;
    //               background: rgba(0,0,0,0.5);
    //               display: flex;
    //               justify-content: center;
    //               align-items: center;
    //               z-index: 10000;">
    //               <div style="
    //                 background: white;
    //                 padding: 20px 25px;
    //                 border-radius: 10px;
    //                 box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    //                 text-align: center;
    //                 width: 300px;
    //                 animation: fadeIn 0.2s ease;">
    //                 <div style="
    //                   width: 50px;
    //                   height: 50px;
    //                   margin: 0 auto 15px auto;
    //                   border-radius: 50%;
    //                   background: #ffefef;
    //                   display: flex;
    //                   align-items: center;
    //                   justify-content: center;">
    //                   <span style="
    //                     color: #e74c3c;
    //                     font-size: 30px;
    //                     font-weight: bold;">!</span>
    //                 </div>
    //                 <h3 style="margin: 0 0 10px 0; color: #333;">Peringatan</h3>
    //                 <p style="font-size: 15px; color: #555; margin: 0 0 20px 0;">${message}</p>
    //                 <button id="closeWarningBtn"
    //                   style="
    //                     padding: 10px 25px;
    //                     font-size: 15px;
    //                     color: white;
    //                     background: #3498db;
    //                     border: none;
    //                     border-radius: 5px;
    //                     cursor: pointer;
    //                     transition: background 0.2s;">OK</button>
    //               </div>
    //             </div>
    //         `;

    //   document.body.appendChild(warningModal);

    //   document
    //     .getElementById("closeWarningBtn")
    //     .addEventListener("click", () => {
    //       document.body.removeChild(warningModal);
    //     });

    //   warningModal.addEventListener("click", (e) => {
    //     if (e.target === warningModal) {
    //       document.body.removeChild(warningModal);
    //     }
    //   });
    // };

    // const showWarning = (message) => {
    //   const style = document.createElement("style");
    //   style.innerHTML = `
    //     @keyframes fadeIn {
    //       from {
    //         opacity: 0;
    //         transform: translateY(-20px);
    //       }
    //       to {
    //         opacity: 1;
    //         transform: translateY(0);
    //       }
    //     }
    //   `;
    //   document.head.appendChild(style);

    //   const warningModal = document.createElement("div");
    //   warningModal.id = "pin-warning-modal";
    //   warningModal.innerHTML = `
    //     <div style="
    //       position: fixed;
    //       top: 0;
    //       left: 0;
    //       width: 100%;
    //       height: 100%;
    //       background: rgba(0,0,0,0.5);
    //       display: flex;
    //       justify-content: center;
    //       align-items: center;
    //       z-index: 10000;">
    //       <div style="
    //         background: white;
    //         padding: 20px 25px;
    //         border-radius: 10px;
    //         box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    //         text-align: center;
    //         width: 300px;
    //         animation: fadeIn 0.3s ease;">
    //         <div style="
    //           width: 50px;
    //           height: 50px;
    //           margin: 0 auto 15px auto;
    //           border-radius: 50%;
    //           background: #ffefef;
    //           display: flex;
    //           align-items: center;
    //           justify-content: center;">
    //           <span style="
    //             color: #e74c3c;
    //             font-size: 30px;
    //             font-weight: bold;">!</span>
    //         </div>
    //         <h3 style="margin: 0 0 10px 0; color: #333;">Peringatan</h3>
    //         <p style="font-size: 15px; color: #555; margin: 0 0 20px 0;">${message}</p>
    //         <button id="closeWarningBtn"
    //           style="
    //             padding: 10px 25px;
    //             font-size: 15px;
    //             color: white;
    //             background: #3498db;
    //             border: none;
    //             border-radius: 5px;
    //             cursor: pointer;
    //             transition: background 0.2s;">OK</button>
    //       </div>
    //     </div>
    //   `;

    //   document.body.appendChild(warningModal);

    //   document
    //     .getElementById("closeWarningBtn")
    //     .addEventListener("click", () => {
    //       document.body.removeChild(warningModal);
    //     });

    //   warningModal.addEventListener("click", (e) => {
    //     if (e.target === warningModal) {
    //       document.body.removeChild(warningModal);
    //     }
    //   });
    // };

    const showWarning = (message) => {
      const style = document.createElement("style");
      style.innerHTML = `
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
    
        @keyframes fadeOut {
          from {
            opacity: 1;
            transform: translateY(0);
          }
          to {
            opacity: 0;
            transform: translateY(-20px);
          }
        }
    
        .warning-backdrop {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0,0,0,0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 10000;
        }
    
        .warning-box {
          background: white;
          padding: 20px 25px;
          border-radius: 10px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.2);
          text-align: center;
          width: 300px;
          animation: fadeIn 0.3s ease;
        }
    
        .fade-out {
          animation: fadeOut 0.3s ease forwards !important;
        }
      `;
      document.head.appendChild(style);

      const warningModal = document.createElement("div");
      warningModal.className = "warning-backdrop";
      warningModal.innerHTML = `
        <div id="warning-box" class="warning-box">
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
          <p style="font-size: 15px; color: #555; margin: 0 0 20px 0;">${message}</p>
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
      `;

      document.body.appendChild(warningModal);

      const warningBox = warningModal.querySelector("#warning-box");

      const closeModal = () => {
        warningBox.classList.add("fade-out");
        setTimeout(() => {
          document.body.removeChild(warningModal);
        }, 300);
      };

      document
        .getElementById("closeWarningBtn")
        .addEventListener("click", closeModal);

      warningModal.addEventListener("click", (e) => {
        if (e.target === warningModal) {
          closeModal();
        }
      });
    };

    const cleanup = () => {
      const popup = document.getElementById("pin-change-popup");
      const style = document.getElementById("simple-keyboard-style");

      if (popup) document.body.removeChild(popup);
      if (style) document.head.removeChild(style);
    };

    submitButton.onclick = async () => {
      const enteredPin = pinInput.value.trim();

      if (!enteredPin) {
        showWarning("PIN tidak boleh kosong!");
        return;
      }

      if (enteredPin.length !== 6) {
        showWarning("PIN harus terdiri dari 6 digit!");
        return;
      }

      if (!enteredPin.match(/^\d+$/)) {
        showWarning("PIN harus berupa angka!");
        return;
      }

      // Clean up DOM
      cleanup();

      try {
        // First, update the wallet_pin field on the record
        await orm.write(model, [recordId], {
          wallet_pin: enteredPin,
        });

        // Then call the change_pin method to update res.partner
        // Pass the context with active_id to ensure correct partner is updated
        await orm.call(model, "change_pin", [recordId], {
          context: {
            active_id: partnerId,
            active_model: "res.partner",
          },
        });

        notification.add("PIN berhasil diperbarui!", { type: "success" });

        // Reload the UI to show updated data
        // env.services.action.doAction({
        //   type: "ir.actions.client",
        //   tag: "reload",
        // });
      } catch (error) {
        notification.add(`Gagal memperbarui PIN: ${error.message || error}`, {
          type: "danger",
        });
      }
    };

    // Handle cancel button click
    cancelButton.onclick = () => {
      cleanup();
    };

    // Close on click outside
    popup.addEventListener("click", (e) => {
      if (e.target === popup.firstElementChild) {
        cleanup();
      }
    });

    // Handle ESC key to close popup
    const handleEscKey = (e) => {
      if (e.key === "Escape") {
        cleanup();
        document.removeEventListener("keydown", handleEscKey);
      }
    };

    document.addEventListener("keydown", handleEscKey);
  };

  // Fallback for when SimpleKeyboard can't be loaded
  const showFallbackPinInput = () => {
    pinAttempt++; // Increment the attempt counter

    const popup = document.createElement("div");
    popup.id = "fallback-pin-popup";
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
                    <h3 style="margin: 0; color: #333;">Ubah PIN</h3>
                    <p style="font-size: 14px; color: #666; margin: 10px 0;">Masukkan PIN baru Anda.</p>
                    <input
                        type="password"
                        id="fallbackPinInput"
                        placeholder="Masukkan PIN baru"
                        maxlength="6"
                        style="width: 100%; border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; padding: 10px;"
                        >
                    <div style="margin-top: 20px; display: flex; justify-content: space-between;">
                        <button id="fallbackSubmitButton"
                            style="padding: 12px 0; width: 48%; font-size: 16px; color: white; background: #007BFF; border: none; border-radius: 5px; cursor: pointer;">
                            Simpan
                        </button>
                        <button id="fallbackCancelButton"
                            style="padding: 12px 0; width: 48%; font-size: 16px; color: #333; background: #f0f0f0; border: 1px solid #ccc; border-radius: 5px; cursor: pointer;">
                            Batal
                        </button>
                    </div>
                </div>
            </div>
        `;

    document.body.appendChild(popup);

    const pinInput = document.getElementById("fallbackPinInput");
    const submitButton = document.getElementById("fallbackSubmitButton");
    const cancelButton = document.getElementById("fallbackCancelButton");

    pinInput.focus();

    // Add numeric validation
    const validateNumericInput = (e) => {
      e.target.value = e.target.value.replace(/[^0-9]/g, "");
    };

    pinInput.addEventListener("input", validateNumericInput);

    // Clean up function
    const cleanup = () => {
      const popup = document.getElementById("fallback-pin-popup");
      if (popup) document.body.removeChild(popup);
    };

    // Handle submit
    submitButton.onclick = async () => {
      const pin = pinInput.value.trim();

      if (!pin) {
        notification.add("PIN tidak boleh kosong!", { type: "danger" });
        return;
      }

      if (pin.length !== 6) {
        notification.add("PIN harus terdiri dari 6 digit!", { type: "danger" });
        return;
      }

      cleanup();

      try {
        // First, update the wallet_pin field on the record
        await orm.write(model, [recordId], { wallet_pin: pin });

        // Then call the change_pin method to update res.partner
        await orm.call(model, "change_pin", [recordId], {
          context: {
            active_id: partnerId,
            active_model: "res.partner",
          },
        });

        notification.add("PIN berhasil diperbarui!", { type: "success" });

        // Reload the UI to show updated data
        env.services.action.doAction({
          type: "ir.actions.client",
          tag: "reload",
        });
      } catch (error) {
        notification.add(`Gagal memperbarui PIN: ${error.message || error}`, {
          type: "danger",
        });
      }
    };

    // Handle cancel
    cancelButton.onclick = () => {
      cleanup();
    };

    // Close on outside click
    popup.addEventListener("click", (e) => {
      if (e.target === popup.firstElementChild) {
        cleanup();
      }
    });

    // Handle ESC key
    const handleEscKey = (e) => {
      if (e.key === "Escape") {
        cleanup();
        document.removeEventListener("keydown", handleEscKey);
      }
    };

    document.addEventListener("keydown", handleEscKey);
  };

  // Show the PIN input popup
  await showPinInputPopup();

  return Promise.resolve();
});
