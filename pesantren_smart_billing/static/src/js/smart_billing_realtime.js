/** @odoo-module **/

import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";

/**
 * Smart Billing Realtime Update Service
 * 
 * Listens for bus notifications from the server when payment status changes
 * and triggers form reload to show updated data without manual refresh.
 */
export const smartBillingRealtimeService = {
    dependencies: ["bus_service", "action"],

    start(env, { bus_service, action }) {
        // Subscribe to smart_billing_update channel
        bus_service.subscribe("smart_billing_update", (payload) => {
            console.log("[SmartBilling] Received update notification:", payload);

            // Check if we need to reload the current view
            const actionService = action;
            const currentController = actionService.currentController;

            if (currentController && currentController.action) {
                const currentAction = currentController.action;
                const currentModel = currentAction.res_model;
                const currentResId = currentAction.res_id;

                console.log("[SmartBilling] Current view:", { model: currentModel, resId: currentResId });
                console.log("[SmartBilling] Payload type:", payload.type, "invoice_id:", payload.invoice_id);

                // Reload if viewing related invoice or partner
                const shouldReload =
                    // Viewing invoice that was just paid (fully or partially)
                    ((payload.type === 'invoice_paid' || payload.type === 'invoice_partial') &&
                        currentModel === 'account.move' &&
                        currentResId === payload.invoice_id) ||
                    // Viewing partner related to the payment
                    (currentModel === 'res.partner' &&
                        currentResId === payload.partner_id) ||
                    // Viewing siswa related to the topup
                    (payload.type === 'topup_completed' &&
                        currentModel === 'cdn.siswa' &&
                        payload.siswa_id &&
                        currentResId === payload.siswa_id) ||
                    // Overpayment credited to wallet
                    (payload.type === 'overpayment_credited' &&
                        currentModel === 'cdn.siswa' &&
                        payload.siswa_id &&
                        currentResId === payload.siswa_id) ||
                    // Viewing the transaction itself
                    (currentModel === 'smart.billing.transaction' &&
                        currentResId === payload.res_id);

                console.log("[SmartBilling] shouldReload:", shouldReload);

                if (shouldReload) {
                    console.log("[SmartBilling] Reloading current view...");
                    // Reload the current action/view
                    browser.setTimeout(() => {
                        const controller = actionService.currentController;
                        if (controller && controller.action) {
                            // Trigger reload by re-executing the action
                            actionService.doAction(controller.action, {
                                clearBreadcrumbs: false,
                                additionalContext: { smart_billing_reload: true }
                            });
                        }
                    }, 500); // Small delay to ensure data is committed
                }
            }
        });

        console.log("[SmartBilling] Realtime update service started");
    },
};

// Register the service
registry.category("services").add("smart_billing_realtime", smartBillingRealtimeService);
