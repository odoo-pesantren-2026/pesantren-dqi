import { registry } from "@web/core/registry";
import { PenagihanKpiCard } from "./kpi_card/kpi_card";
import { PenagihanChartRenderer } from "./chart_renderer/chart_renderer";
import { TagihanLunasList } from "./card_list/cart_list";
import { TagihanBelumLunasList } from "./card_list/cart_list";

const { Component,useState } = owl;

export class OwlPenagihanDashboard extends Component {
  setup() {
    this.state = useState({ showDatePicker: false });
  }
  toggleDatePicker() {
        this.state.showDatePicker = !this.state.showDatePicker;
    }
}

OwlPenagihanDashboard.template = "owl.OwlPenagihanDashboard";

OwlPenagihanDashboard.components = {
  PenagihanKpiCard,
  PenagihanChartRenderer,
  TagihanLunasList,
  TagihanBelumLunasList,
};

registry
  .category("actions")
  .add("owl.penagihan_dashboard", OwlPenagihanDashboard);
