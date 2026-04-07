// import { FormRenderer } from "@web/views/form/form_renderer";
// import { patch } from "@web/core/utils/patch";

// patch(FormRenderer.prototype, "cdn.perijinan.autofocus", {
//     setup() {
//         this._super(...arguments);
        
//         // Tambahkan efek samping untuk fokus
//         if (this.props.record.data.siswa_id) {
//             this.autofocusKeperluan();
//         }
//     },

//     autofocusKeperluan() {
//         // Gunakan nextTick untuk memastikan rendering selesai
//         this.env.config.onRendered(() => {
//             const keperluanInput = this.rootRef.el?.querySelector('input[name="keperluan"]');
//             if (keperluanInput) {
//                 keperluanInput.focus();
//             }
//         });
//     }
// });



/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";

patch(FormRenderer.prototype, 'pesantren_kesantrian.perijinan_checkout', {
    setup() {
        this._super(...arguments);
        this.onFieldKeyDown = this.onFieldKeyDown.bind(this);
    },

    onFieldKeyDown(ev, fieldName) {
        // Jika Enter ditekan di field barcode atau siswa_id
        if ((fieldName === 'barcode' || fieldName === 'siswa_id') && ev.key === 'Enter') {
            ev.preventDefault();
            // Fokus ke keperluan
            const keperluanInput = this.el.querySelector('input[name="keperluan"]');
            if (keperluanInput) keperluanInput.focus();
        }
        // Jika Enter ditekan di field keperluan
        else if (fieldName === 'keperluan' && ev.key === 'Enter') {
            ev.preventDefault();
            // Fokus ke penjemput
            const penjemputInput = this.el.querySelector('input[name="penjemput"]');
            if (penjemputInput) penjemputInput.focus();
        }
    },

    renderNode(node) {
        const result = this._super(...arguments);
        
        if (node.tag === 'field' && 
            (node.attrs.name === 'barcode' || 
             node.attrs.name === 'siswa_id' || 
             node.attrs.name === 'keperluan')) {
            
            const input = this.el.querySelector(`[name="${node.attrs.name}"] input`);
            if (input) {
                input.addEventListener('keydown', (ev) => this.onFieldKeyDown(ev, node.attrs.name));
            }
        }
        
        return result;
    }
});
