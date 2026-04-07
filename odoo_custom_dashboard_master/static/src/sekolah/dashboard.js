/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";
import { SekolahKpiCard } from "./kpi_card/kpi_card";
import { SekolahChartRenderer } from "./chart_renderer/chart_renderer";
import { TagihanBelumLunasList } from "./cart_list/cart_list";
import { TagihanLunasList } from "./cart_list/cart_list";

export class OwlSekolahDashboard extends Component {
   setup() {
    this.state = useState({ showDatePicker: false });
  }
  toggleDatePicker() {
        this.state.showDatePicker = !this.state.showDatePicker;
    }
}

OwlSekolahDashboard.template = "owl.OwlSekolahDashboard";

registry.category("actions").add("owl.sekolah_dashboard", OwlSekolahDashboard);
OwlSekolahDashboard.components = {
  SekolahChartRenderer,
  SekolahKpiCard,
  TagihanLunasList,
  TagihanBelumLunasList,
};
