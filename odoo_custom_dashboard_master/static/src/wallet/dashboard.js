/** @odoo-module */

import { registry } from "@web/core/registry";
import { WalletKpiCard } from "./kpi_card/kpi_card";
import { WalletChartRenderer } from "./chart_renderer/chart_renderer";
import { WalletCardList } from "./card_list/card_list";
import { WalletCardList2 } from "./card_list/card_list";
const { Component } = owl;

export class OwlWalletDashboard extends Component {
  setup() {}
}

OwlWalletDashboard.template = "owl.WalletDashboard";
OwlWalletDashboard.components = {
  WalletKpiCard,
  WalletChartRenderer,
  WalletCardList,
  WalletCardList2,
};

registry.category("actions").add("owl.wallet_dashboard", OwlWalletDashboard);
