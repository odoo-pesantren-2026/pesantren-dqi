// /** @odoo-module **/

// import { registry } from "@web/core/registry";
// import { useListener } from "@web/core/utils/hooks";
// import { Component, onMounted, useState } from "@odoo/owl";

// // 1. Definisikan template terlebih dahulu
// const passwordToggleTemplate = `
// <button class="btn btn-secondary fa fa-eye" title="Tampilkan Kata Sandi" type="button"/>
// `;

// export class TogglePasswordButton extends Component {
//     setup() {
//         this.state = useState({
//             isVisible: false
//         });
        
//         useListener("click", () => this.togglePasswordVisibility());
        
//         onMounted(() => {
//             // Pastikan elemen password yang terkait ada
//             this.passwordField = this.el.closest('.o_input_group').querySelector('input[type="password"], input[type="text"]');
//         });
//     }
    
//     /**
//      * Fungsi untuk mengubah visibilitas password saat icon mata diklik
//      */
//     togglePasswordVisibility() {
//         if (this.passwordField) {
//             if (this.state.isVisible) {
//                 this.passwordField.type = 'password';
//                 this.el.classList.remove('fa-eye-slash');
//                 this.el.classList.add('fa-eye');
//                 this.el.title = 'Tampilkan Kata Sandi';
//             } else {
//                 this.passwordField.type = 'text';
//                 this.el.classList.remove('fa-eye');
//                 this.el.classList.add('fa-eye-slash');
//                 this.el.title = 'Sembunyikan Kata Sandi';
//             }
//             this.state.isVisible = !this.state.isVisible;
//         }
//     }
// }

// // 2. Set template secara langsung tanpa referensi ke modul yang belum tentu ada
// TogglePasswordButton.template = passwordToggleTemplate;

// // 3. Daftarkan sebagai widget field bukan view component
// registry.category("fields").add("password_toggle", {
//     component: TogglePasswordButton,
//     supportedTypes: ["char"],
// });