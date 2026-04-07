/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { CutiKpiCard } from "./kpi_card/kpi_card";
import { CutiChartRenderer } from "./chart_renderer/chart_renderer";
import { CutiList } from "./cart_list/cart_list";
import { Cuti2List } from "./cart_list/cart_list";

export class OwlCutiDashboard extends Component {}

OwlCutiDashboard.template = "owl.OwlCutiDashboard";

registry.category("actions").add("owl.cuti_dashboard", OwlCutiDashboard);
OwlCutiDashboard.components = {
  CutiKpiCard,
  CutiChartRenderer,
  CutiList,
  Cuti2List,
};
