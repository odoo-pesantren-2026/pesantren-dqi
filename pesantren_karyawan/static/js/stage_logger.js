// odoo.define('pesantren_karyawan.stage_logger', function (require) {
//     "use strict";

//     const { Component } = require('web.Component');
//     const { onMounted } = require('web.custom_hooks');

//     class StageLogger extends Component {
//         constructor() {
//             super(...arguments);
//             onMounted(() => {
//                 const stageSelect = document.getElementById('stage_id');
//                 if (stageSelect) {
//                     stageSelect.addEventListener('change', (event) => {
//                         const selectedStage = event.target.value;
//                         console.log("Stage ID changed to:", selectedStage);
//                     });
//                 }
//             });
//         }
//     }

//     return StageLogger;
// });
