import { registry } from "@web/core/registry";
import { CrmChartRenderer } from "./chart_renderer/chart_renderer";
import { CrmList } from "./card_list/card_list";
import { CrmKpiCard } from "./kpi_card/kpi_card";

// GAREK KPI CARD

const { Component } = owl;

export class OwlCrmDashboard extends Component {
  setup() {}
}

OwlCrmDashboard.template = "owl.OwlCrmDashboard";

OwlCrmDashboard.components = {
  CrmKpiCard,
  CrmChartRenderer,
  CrmList,
};

registry
  .category("actions")
  .add("owl.crm_dashboard", OwlCrmDashboard);
