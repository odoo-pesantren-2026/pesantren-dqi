import { registry } from "@web/core/registry";
import { PendaftaranKpiCard } from "./kpi_card/kpi_card";
import { PendaftaranChartRenderer } from "./chart_renderer/chart_renderer";
import { PendaftaranList } from "./card_list/card_list";

const { Component, useState } = owl;

export class OwlPendaftaranDashboard extends Component {
   setup() {
    this.state = useState({ showDatePicker: false });
  }
  toggleDatePicker() {
        this.state.showDatePicker = !this.state.showDatePicker;
    }
}

OwlPendaftaranDashboard.template = "owl.OwlPendaftaranDashboard";

OwlPendaftaranDashboard.components = {
  PendaftaranKpiCard,
  PendaftaranChartRenderer,
  PendaftaranList,
};

registry
  .category("actions")
  .add("owl.pendaftaran_dashboard", OwlPendaftaranDashboard);
