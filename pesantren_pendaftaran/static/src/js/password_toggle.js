/** @odoo-module **/

import { CharField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";

export class TogglePassword extends CharField {
  setup() {
    super.setup();
    this.showPassword = false;
  }

  toggleVisibility() {
    const input = this.el.querySelector("input");
    this.showPassword = !this.showPassword;
    input.type = this.showPassword ? "text" : "password";
  }

  render() {
    super.render();
    const input = this.el.querySelector("input");
    input.type = "password";

    const eye = document.createElement("span");
    eye.innerHTML = "👁️";
    eye.style.cursor = "pointer";
    eye.style.marginLeft = "8px";
    eye.addEventListener("click", this.toggleVisibility.bind(this));

    this.el.appendChild(eye);
  }
}

registry.category("fields").add("toggle_password", TogglePassword);
