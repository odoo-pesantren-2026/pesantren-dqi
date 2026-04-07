# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class InvoiceDiagnosticWizard(models.TransientModel):
    _name = 'invoice.diagnostic.wizard'
    _description = 'Wizard untuk Diagnosa dan Perbaiki Invoice Bermasalah'

    # Fields for display
    inconsistent_invoice_count = fields.Integer(
        string='Jumlah Invoice Bermasalah',
        compute='_compute_inconsistent_invoices',
        readonly=True
    )
    inconsistent_invoice_ids = fields.Many2many(
        'account.move',
        string='Invoice Bermasalah',
        compute='_compute_inconsistent_invoices',
        readonly=True
    )
    result_message = fields.Text(string='Hasil', readonly=True)
    
    # Filter options
    partner_id = fields.Many2one('res.partner', string='Filter Partner (Santri)')
    
    @api.depends('partner_id')
    def _compute_inconsistent_invoices(self):
        """Find invoices with payment_state inconsistency"""
        for wizard in self:
            domain = [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                # Inconsistent: payment_state is 'paid' but still has residual
                '|',
                '&', ('payment_state', '=', 'paid'), ('amount_residual', '>', 0.01),
                # Or: payment_state is 'not_paid' but residual is 0
                '&', ('payment_state', '=', 'not_paid'), ('amount_residual', '<=', 0.01),
            ]
            
            if wizard.partner_id:
                domain.append(('partner_id', '=', wizard.partner_id.id))
            
            invoices = self.env['account.move'].search(domain, limit=100)
            wizard.inconsistent_invoice_ids = invoices
            wizard.inconsistent_invoice_count = len(invoices)

    def action_diagnose(self):
        """Diagnose all inconsistent invoices and show results"""
        self.ensure_one()
        
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ]
        
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        
        invoices = self.env['account.move'].search(domain)
        
        issues = []
        for inv in invoices:
            # Check for inconsistency
            is_paid_but_residual = inv.payment_state == 'paid' and inv.amount_residual > 0.01
            is_notpaid_but_zero = inv.payment_state == 'not_paid' and inv.amount_residual <= 0.01
            is_partial_wrong = inv.payment_state == 'partial' and (inv.amount_residual <= 0 or inv.amount_residual >= inv.amount_total)
            
            if is_paid_but_residual or is_notpaid_but_zero or is_partial_wrong:
                # Get payment info
                payments = inv._get_reconciled_payments()
                payment_info = ", ".join([f"{p.name} ({p.amount})" for p in payments]) if payments else "No payments"
                
                issues.append({
                    'invoice': inv.name,
                    'partner': inv.partner_id.name,
                    'total': inv.amount_total,
                    'residual': inv.amount_residual,
                    'payment_state': inv.payment_state,
                    'payments': payment_info,
                    'issue': 'PAID but has residual' if is_paid_but_residual else 
                             'NOT_PAID but zero residual' if is_notpaid_but_zero else
                             'PARTIAL state wrong'
                })
        
        # Format result
        if issues:
            result = f"Ditemukan {len(issues)} invoice bermasalah:\n\n"
            for i, issue in enumerate(issues, 1):
                result += f"{i}. {issue['invoice']} - {issue['partner']}\n"
                result += f"   Total: Rp {issue['total']:,.0f}\n"
                result += f"   Sisa: Rp {issue['residual']:,.0f}\n"
                result += f"   Status: {issue['payment_state']}\n"
                result += f"   Payments: {issue['payments']}\n"
                result += f"   Masalah: {issue['issue']}\n\n"
        else:
            result = "✅ Tidak ditemukan invoice dengan inkonsistensi payment_state."
        
        self.result_message = result
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.diagnostic.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_fix_payment_state(self):
        """Recompute payment_state for inconsistent invoices"""
        self.ensure_one()
        
        fixed_count = 0
        errors = []
        
        for inv in self.inconsistent_invoice_ids:
            try:
                # Force recompute payment state
                inv._compute_amount()
                inv.invalidate_recordset(['payment_state', 'amount_residual'])
                
                # Log the fix
                _logger.info(f"Recomputed payment_state for {inv.name}")
                fixed_count += 1
                
            except Exception as e:
                errors.append(f"{inv.name}: {str(e)}")
                _logger.error(f"Error fixing {inv.name}: {e}")
        
        if errors:
            self.result_message = f"✅ Diperbaiki: {fixed_count} invoice\n\n❌ Error:\n" + "\n".join(errors)
        else:
            self.result_message = f"✅ Berhasil memperbaiki {fixed_count} invoice.\n\nSilakan refresh halaman untuk melihat perubahan."
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.diagnostic.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_view_invoices(self):
        """Open list of inconsistent invoices"""
        self.ensure_one()
        
        return {
            'name': 'Invoice Bermasalah',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.inconsistent_invoice_ids.ids)],
            'target': 'current',
        }
