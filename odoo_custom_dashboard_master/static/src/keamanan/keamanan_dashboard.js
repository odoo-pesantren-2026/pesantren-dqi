/** @odoo-module */

import { registry } from "@web/core/registry";
import { KeamananKpiCard } from "./kpi_card/kpi_card";
import { KeamananChartRenderer } from "./chart_renderer/chart_renderer";
import { KeamananCardList } from "./card_list/card_list"; // Tambahkan import
import { KeamananCardList2 } from "./card_list/card_list"; // Tambahkan import
const { Component } = owl;

export class OwlKeamananDashboard extends Component {
  setup() {
    // Logic tambahan jika diperlukan
  }
}

// Daftarkan komponen dan template
OwlKeamananDashboard.template = "owl.OwlKeamananDashboard";
OwlKeamananDashboard.components = {
  KeamananKpiCard,
  KeamananChartRenderer,
  KeamananCardList,
  KeamananCardList2,
}; // Tambahkan ProductCardList

registry.category("actions").add("owl.keamanan_dashboard", OwlKeamananDashboard);
