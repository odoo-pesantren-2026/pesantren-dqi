import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import { useState } from "@odoo/owl";

export class PasswordToggleWidget extends CharField {
  static template = "custom_password_toggle.PasswordToggleWidget";

  setup() {
    super.setup();
    this.state = useState({
      isPasswordVisible: false,
    });
  }

  _togglePasswordVisibility() {
    this.state.isPasswordVisible = !this.state.isPasswordVisible;
  }

  _onInput(ev) {
    this.props.update(ev.target.value);
  }

  _onChange(ev) {
    this.props.update(ev.target.value);
  }

  _onKeydown(ev) {
    super.onKeydown(ev);
  }
}

registry.category("fields").add("password_toggle", PasswordToggleWidget);
