/** @odoo-module */

import { registry } from "@web/core/registry";
import { StockKpiCard } from "./kpi_card/kpi_card";
import { StockChartRenderer } from "./chart_renderer/chart_renderer";
import { StockCardList } from "./card_list/card_list"; // Tambahkan import
import { StockCardList2 } from "./card_list/card_list"; // Tambahkan import
const { Component } = owl;

export class OwlStockDashboard extends Component {
  setup() {
    // Logic tambahan jika diperlukan
  }
}

// Daftarkan komponen dan template
OwlStockDashboard.template = "owl.OwlStockDashboard";
OwlStockDashboard.components = {
  StockKpiCard,
  StockChartRenderer,
  StockCardList,
  StockCardList2,
}; // Tambahkan ProductCardList

registry.category("actions").add("owl.stock_dashboard", OwlStockDashboard);
