// /** @odoo-module **/
// import { registry } from "@web/core/registry";

// function autoFocusKartuSantri(fieldName, nextField) {
//   return {
//     mounted() {
//       console.log(`Widget auto_focus_kartu mounted untuk field: ${fieldName}`);

//       this.el.addEventListener("change", (event) => {
//         console.log(`Event change terdeteksi pada field: ${event.target.name}`);

//         if (event.target.name === fieldName) {
//           console.log(`Nilai dari ${fieldName}:`, event.target.value); 

//           setTimeout(() => {
//             console.log(`Mencari field dengan name="${nextField}"`);
//             const kartuField = document.querySelector(
//               `input[name="${nextField}"]`
//             );

//             if (kartuField) {
//               console.log("Field kartu ditemukan, memindahkan fokus...");
//               kartuField.focus();
//             } else {
//               console.error("Field kartu tidak ditemukan!");
//             }
//           }, 200);
//         }
//       });
//     },
//   };
// }

// registry
//   .category("fields")
//   .add("auto_focus_kartu", autoFocusKartuSantri("santri_id", "kartu"));
