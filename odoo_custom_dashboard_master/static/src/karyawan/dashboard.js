import { registry } from "@web/core/registry";
import { KaryawanKpiCard } from "./kpi_card/kpi_card";
import { KaryawanChartRenderer } from "./chart_renderer/chart_renderer";
import { KaryawanList } from "./card_list/card_list";

const { Component } = owl;

export class OwlKaryawanDashboard extends Component {
  setup() {}
}

OwlKaryawanDashboard.template = "owl.OwlKaryawanDashboard";

OwlKaryawanDashboard.components = {
  KaryawanKpiCard,
  KaryawanChartRenderer,
  KaryawanList,
};

registry
  .category("actions")
  .add("owl.karyawan_dashboard", OwlKaryawanDashboard);
