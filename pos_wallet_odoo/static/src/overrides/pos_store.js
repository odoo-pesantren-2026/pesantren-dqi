/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";

patch(PosStore.prototype, {
    async _processBarcode(code) {
        const result = await super._processBarcode(...arguments);
        if (result) {
            return result;
        }

        // If not handled by standard barcode reader, check if it's a VA
        console.log("Processing custom barcode for VA:", code);

        try {
            // 1. Check in local partners first
            let partner = this.models["res.partner"].find(
                (p) => p.virtual_account === code || p.va_saku === code || p.barcode === code
            );

            if (partner) {
                this.get_order().set_partner(partner);
                return true;
            }

            // 2. Fallback: Search from server
            const response = await rpc('/siswa/get_data/bar', { barcode: code });
            if (response && response.partner_id) {
                // If not in local store, try to use the response data directly.
                // Odoo 17's set_partner can often handle these the same way as records.
                this.get_order().set_partner(response);
                return true;
            }
        } catch (error) {
            console.error("Error processing VA barcode:", error);
        }

        return false;
    }
});
