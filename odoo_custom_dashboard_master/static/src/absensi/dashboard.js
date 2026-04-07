import { registry } from "@web/core/registry";
import { AbsensiKpiCard } from "./kpi_card/kpi_card";
import { AbsensiChartRenderer } from "./chart_renderer/chart_renderer";
import { AbsensiList } from "./card_list/card_list";

// GAREK KPI CARD

const { Component, useState } = owl;

export class OwlAbsensiDashboard extends Component {
  setup() {
    this.state = useState({ showDatePicker: false });
  }
  toggleDatePicker() {
        this.state.showDatePicker = !this.state.showDatePicker;
    }
}

OwlAbsensiDashboard.template = "owl.OwlAbsensiDashboard";

OwlAbsensiDashboard.components = {
  AbsensiKpiCard,
  AbsensiChartRenderer,
  AbsensiList,
};

registry.category("actions").add("owl.absensi_dashboard", OwlAbsensiDashboard);
