/** @odoo-module */
import { registry } from "@web/core/registry";
import { PosKpiCard } from "./kpi_card/pos_kpi_card";
import { PosChartRenderer } from "./chart_renderer/pos_chart_renderer";
import { PosCardList, PosCardList1 } from "./card_list/pos_card_list";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class OwlPosDashboard extends Component {
    setup() {
        this.orm = useService("orm");

        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        const formatDate = d => d.toISOString().split("T")[0];

        // Helper formatter
        const formatCustomLabel = (date) => {
            const months = [
                "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                "Jul", "Agt", "Sept", "Okt", "Nov", "Des"
            ];
            const day = date.getDate();
            const month = months[date.getMonth()];
            const year = date.getFullYear();
            return `${day} ${month} ${year}`;
        };

        this.state = useState({
            stores: [],
            selectedStore: null,
            startDate: formatDate(firstDay),
            endDate: formatDate(lastDay),
            buttonLabel: formatCustomLabel(firstDay) + " - " + formatCustomLabel(lastDay),
            showDatePicker: false,
        });

        onWillStart(async () => {
            await this.fetchStores();
        });
    }

    async fetchStores() {
        try {
            const stores = await this.orm.call(
                "pos.config",
                "search_read",
                [[], ["id", "name"]],
                { order: "name asc" }
            );
            this.state.stores = stores;
        } catch (error) {
            console.error("Error fetching stores:", error);
        }
    }

    handleStoreChange(event) {
        const selectedStoreId = parseInt(event.target.value);
        this.state.selectedStore = selectedStoreId || null;
    }

    toggleDatePicker() {
        this.state.showDatePicker = !this.state.showDatePicker;
    }

    onDateChange(ev, field) {
        this.state[field] = ev.target.value;
        this.updateDateLabel();

        const periodSelect = document.getElementById("periodSelection");
        if (periodSelect) {
            periodSelect.value = "";
        }
    }

    updateDateLabel() {
        const { startDate, endDate } = this.state;

        const isValidDate = (d) => d && !isNaN(new Date(d).getTime());

        if (!isValidDate(startDate)) {
            this.state.buttonLabel = "Pilih Tanggal";
            return;
        }

        const start = new Date(startDate);
        const end = endDate && isValidDate(endDate) ? new Date(endDate) : null;

        const formatCustom = (d) => {
            const months = [
                "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
                "Jul", "Agt", "Sep", "Okt", "Nov", "Des"
            ];
            const day = d.getDate();
            const month = months[d.getMonth()];
            const year = d.getFullYear();
            return `${day} ${month} ${year}`;
        };

        if (!end || start.getTime() === end.getTime()) {
            this.state.buttonLabel = formatCustom(start);
        } else {
            this.state.buttonLabel = `${formatCustom(start)} - ${formatCustom(end)}`;
        }
    }

    onPeriodChange(ev) {
        const period = ev.target.value;
        const now = new Date();

        let startDate, endDate;

        switch (period) {
            case "today":
                startDate = endDate = this.formatDate(now);
                break;

            case "yesterday":
                const yesterday = new Date(now);
                yesterday.setDate(now.getDate() - 1);
                startDate = endDate = this.formatDate(yesterday);
                break;

            case "thisweek":
                const dayOfWeek = now.getDay();
                const diffToMonday = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
                const mondayThisWeek = new Date(now);
                mondayThisWeek.setDate(now.getDate() + diffToMonday);
                startDate = this.formatDate(mondayThisWeek);
                endDate = this.formatDate(now);
                break;

            case "lastweek":
                const lastMonday = new Date(now);
                lastMonday.setDate(now.getDate() - 7);
                const dayOfLastMonday = lastMonday.getDay();
                const diffToLastMonday = dayOfLastMonday === 0 ? -6 : 1 - dayOfLastMonday;
                const mondayLastWeek = new Date(lastMonday);
                mondayLastWeek.setDate(lastMonday.getDate() + diffToLastMonday);
                const sundayLastWeek = new Date(mondayLastWeek);
                sundayLastWeek.setDate(mondayLastWeek.getDate() + 6);
                startDate = this.formatDate(mondayLastWeek);
                endDate = this.formatDate(sundayLastWeek);
                break;

            case "month":
                startDate = this.formatDate(new Date(now.getFullYear(), now.getMonth(), 1));
                endDate = this.formatDate(new Date(now.getFullYear(), now.getMonth() + 1, 0));
                break;

            case "lastMonth":
                const lastMonth = now.getMonth() - 1;
                const lastMonthYear = lastMonth < 0 ? now.getFullYear() - 1 : now.getFullYear();
                const adjustedMonth = lastMonth < 0 ? 11 : lastMonth;
                startDate = this.formatDate(new Date(lastMonthYear, adjustedMonth, 1));
                endDate = this.formatDate(new Date(lastMonthYear, adjustedMonth + 1, 0));
                break;

            case "thisyear":
                const currentYear = now.getFullYear();
                startDate = this.formatDate(new Date(currentYear, 0, 2)); // ✅ Diperbaiki jadi 1 Jan
                endDate = this.formatDate(new Date(currentYear, 11, 31));
                break;

            case "lastyear":
                const lastYear = now.getFullYear() - 1; // ✅ Diperbaiki
                startDate = this.formatDate(new Date(lastYear, 0, 2)); // ✅ Diperbaiki jadi 1 Jan
                endDate = this.formatDate(new Date(lastYear, 11, 31));
                break;

            default:
                return;
        }

        console.log(`[PERIODE] ${period} → Start: ${startDate}, End: ${endDate}`);

        this.state.startDate = startDate;
        this.state.endDate = endDate;
        this.updateDateLabel();
        this.state.showDatePicker = false;
    }

    formatDate(date) {
        return date.toISOString().split("T")[0];
    }
}

OwlPosDashboard.template = "owl.OwlPosDashboard";
OwlPosDashboard.components = {
    PosKpiCard,
    PosChartRenderer,
    PosCardList,
    PosCardList1,
};

registry.category("actions").add("owl.pos_dashboard", OwlPosDashboard);