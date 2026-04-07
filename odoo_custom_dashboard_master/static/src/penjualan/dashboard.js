import { registry } from "@web/core/registry";
import { PenjualanKpiCard } from "./kpi_card/kpi_card";
import { PenjualanChartRenderer } from "./chart_renderer/chart_renderer";
import { PenjualanList } from "./card_list/card_list";
import { CardListPenjualan } from "./card_list/card_list";

const { Component } = owl;

export class OwlPenjualanDashboard extends Component {
  setup() {}
}

OwlPenjualanDashboard.template = "owl.OwlPenjualanDashboard";

OwlPenjualanDashboard.components = {
  PenjualanKpiCard,
  PenjualanChartRenderer,
  PenjualanList,
  CardListPenjualan,
};

registry
  .category("actions")
  .add("owl.penjualan_dashboard", OwlPenjualanDashboard);
