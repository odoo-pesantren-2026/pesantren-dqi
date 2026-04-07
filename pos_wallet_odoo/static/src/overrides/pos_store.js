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
            // Search for partner with this VA or VA Saku
            // Since we loaded these fields in pos_session, we can search in local partners
            const partner = this.models["res.partner"].find(
                (p) => p.virtual_account === code || p.va_saku === code || p.barcode === code
            );

            if (partner) {
                this.get_order().set_partner(partner);
                console.log("Partner selected via VA scan:", partner.name);
                return true;
            }

            // If not found in local, try to fetch from server as fallback
            const response = await rpc('/siswa/get_data/bar', { barcode: code });
            if (response && response.partner_id) {
                const fetchedPartner = this.models["res.partner"].get(response.partner_id);
                if (fetchedPartner) {
                    this.get_order().set_partner(fetchedPartner);
                    return true;
                }
            }
        } catch (error) {
            console.error("Error processing VA barcode:", error);
        }

        return false;
    }
});
