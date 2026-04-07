/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { useState } from "@odoo/owl";

export class PasswordToggleField extends CharField {
    static template = "web_password_toggle.PasswordToggleField";

    setup() {
        super.setup();
        this.passwordState = useState({
            showPassword: false,
        });
    }

    togglePasswordVisibility() {
        this.passwordState.showPassword = !this.passwordState.showPassword;
    }

    get fieldType() {
        return this.passwordState.showPassword ? "text" : "password";
    }
}

export const passwordToggleField = {
    ...charField,
    component: PasswordToggleField,
};

registry.category("fields").add("password_toggle", passwordToggleField);