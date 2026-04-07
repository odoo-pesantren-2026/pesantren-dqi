// /** @odoo-module **/
// import { AppsBar as BypasAppsBar } from "@muk_web_appsbar/webclient/appsbar/appsbar";
// import { useService } from "@web/core/utils/hooks";
// import { patch } from "@web/core/utils/patch";
// import { rpc } from "@web/core/network/rpc";
// import { useState } from "@odoo/owl";
// import { session } from "@web/session";

// patch(BypasAppsBar.prototype, {
//     setup() {
//         if (typeof super.setup === "function") {
//             super.setup(...arguments); // Pastikan tidak error jika `setup` superclass tidak ada
//         }
//         this.action = useService("action");

//         // Menginisialisasi state
//         this.state = useState({
//             wallet_balance: 0, // Nilai awal default
//         });

//         // Memuat data wallet dari backend
//         this.fetchDataWallet();
//     },

//     async fetchDataWallet() {
//         try {
//             const response = await rpc("/siswa/get_data", {
//                 domain: [['name', 'like', session.partner_display_name]], // Filter domain
//             });
//             console.log("Data Wallet Response:", response);

//             if (Array.isArray(response) && response[0] && typeof response[0].wallet_balance === "number") {
//                 this.state.wallet_balance = response[0].wallet_balance; // Update state
//             } else {
//                 console.warn("Respons wallet_balance tidak valid:", response);
//             }
//         } catch (error) {
//             console.error("Gagal mengambil data Wallet:", error);
//         }
//     },
// });
