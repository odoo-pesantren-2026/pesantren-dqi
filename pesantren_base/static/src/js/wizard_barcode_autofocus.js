/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { registry } from "@web/core/registry";

export class BarcodeAutoFocusFormController extends FormController {
  async onFieldChanged(event) {
    await super.onFieldChanged(event);

    const fieldChanged = Object.keys(event.data.changes || {})[0];
    if (fieldChanged === "barcode") {
      setTimeout(() => {
        const barcodeInput = this.el.querySelector('input[name="barcode"]');
        if (barcodeInput) {
          barcodeInput.focus();
          barcodeInput.select();
        }
      }, 300);
    }
  }
}

registry.category("views").add("barcode_autofocus_form", {
  ...registry.category("views").get("form"),
  Controller: BarcodeAutoFocusFormController,
});
