# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _ ,api
from odoo.exceptions import UserError


class AccountRegisterPayments(models.TransientModel):
    """Inherits the account.payment.register model to add the new
     fields and functions"""
    _inherit = "account.payment.register"

    bank_reference = fields.Char(string="Referensi bank", copy=False)
    cheque_reference = fields.Char(string="Cheque Reference", copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)

    def _prepare_payment_vals(self, invoices):
        """Its prepare the payment values for the invoice and update
         the MultiPayment"""
        res = super(AccountRegisterPayments, self)._prepare_payment_vals(
            invoices)
        # Check payment method is Check or PDC
        check_pdc_ids = self.env['account.payment.method'].search(
            [('code', 'in', ['pdc', 'check_printing'])])
        if self.payment_method_id.id in check_pdc_ids.ids:
            currency_id = self.env['res.currency'].browse(res['currency_id'])
            journal_id = self.env['account.journal'].browse(res['journal_id'])
            # Updating values in case of Multi payments
            res.update({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference,
                'check_manual_sequencing': journal_id.check_manual_sequencing,
                'effective_date': self.effective_date,
                'check_amount_in_words': currency_id.amount_to_text(
                    res['amount']),
            })
        return res

    def _create_payment_vals_from_wizard(self, batch_result):
        """It super the wizard action of the create payment values and update
         the bank and cheque values"""
        res = super(AccountRegisterPayments,
                    self)._create_payment_vals_from_wizard(
            batch_result)
        if self.effective_date:
            res.update({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference,
                'effective_date': self.effective_date,
            })
        return res

    def _create_payment_vals_from_batch(self, batch_result):
        """It super the batch action of the create payment values and update
         the bank and cheque values"""
        res = super(AccountRegisterPayments,
                    self)._create_payment_vals_from_batch(
            batch_result)
        if self.effective_date:
            res.update({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference,
                'effective_date': self.effective_date,
            })
        return res

    def _create_payments(self):
        """USed to create a list of payments and update the bank and
         cheque reference"""
        payments = super(AccountRegisterPayments, self)._create_payments()

        for payment in payments:
            payment.write({
                'bank_reference': self.bank_reference,
                'cheque_reference': self.cheque_reference
            })
        return payments

    def action_create_payments_and_preview(self):

        if self.payment_method_line_id.name == 'Dompet Santri':
            invoice = False
            if self.line_ids and self.line_ids[0].move_id:
                invoice = self.line_ids[0].move_id
            
            if not invoice:
                raise UserError("Tidak dapat menemukan faktur terkait")

            amount = self.amount
            santri = self.env['cdn.siswa'].search([('partner_id', '=', self.partner_id.id)], limit=1)
            
            if santri and santri.status_akun in ['nonaktif', 'blokir']:
                status = santri.status_akun.capitalize()
                raise UserError(f"Transaksi tidak dapat diproses karena akun santri bernama {santri.name} saat ini berstatus {status}. Mohon hubungi pengurus pesantren untuk informasi lebih lanjut.")

            return {
                'type': 'ir.actions.act_window',
                'name': 'Konfirmasi PIN Dompet Santri',
                'res_model': 'dompet.santri.pin.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_payment_id': self.id,
                    'default_santri_id': santri.id,
                    'default_nomor_tagihan': self.communication,
                    'default_invoice_id': invoice.id,
                    'default_amount': amount,
                },
                'views': [(False, 'form')],
            }
        else:

            # Buat pembayaran menggunakan metode asli
            payments = self.sudo()._create_payments()
            
            # Dapatkan invoice terkait
            invoice = False
            if self.line_ids and self.line_ids[0].move_id:
                invoice = self.line_ids[0].move_id
            
            # Jika invoice ditemukan, buka dialog konfirmasi unduh
            if invoice:
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Unduh Transaksi',
                    'res_model': 'invoice.download.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_invoice_id': invoice.id,
                        'default_invoice_name': invoice.name or invoice.ref or '',
                    },
                    'views': [(False, 'form')],
                }
            
            # Jika tidak ada invoice, kembalikan action default
            action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_payments')
            return action

    # def action_create_payments_and_preview(self):
    #     """Membuat pembayaran dengan sudo dan memperbaiki currency_id"""
    #     # Simpan currency_id dan company_id sebelum menggunakan sudo
    #     currency_id = self.currency_id.id
    #     company_id = self.company_id.id
        
    #     # Buat pembayaran menggunakan sudo
    #     payments = self.sudo()._create_payments()
        
    #     # Perbaiki currency_id yang hilang akibat penggunaan sudo
    #     if payments:
    #         self.env.cr.execute("""
    #             UPDATE account_move 
    #             SET currency_id = %s, company_id = %s
    #             WHERE id IN (
    #                 SELECT move_id FROM account_payment WHERE id IN %s
    #             ) AND (currency_id IS NULL OR company_id IS NULL)
    #         """, (currency_id, company_id, tuple(payments.ids)))
            
    #         # Perbaiki juga currency_id pada account_move_line
    #         self.env.cr.execute("""
    #             UPDATE account_move_line 
    #             SET currency_id = %s, company_id = %s
    #             WHERE move_id IN (
    #                 SELECT move_id FROM account_payment WHERE id IN %s
    #             ) AND (currency_id IS NULL OR company_id IS NULL)
    #         """, (currency_id, company_id, tuple(payments.ids)))
        
    #     # Dapatkan invoice terkait
    #     invoice = False
    #     if self.line_ids and self.line_ids[0].move_id:
    #         invoice = self.line_ids[0].move_id
        
    #     # Jika invoice ditemukan, buka dialog konfirmasi unduh
    #     if invoice:
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'name': 'Cetak Transaksi',
    #             'res_model': 'invoice.download.wizard',
    #             'view_mode': 'form',
    #             'target': 'new',
    #             'context': {
    #                 'default_invoice_id': invoice.id,
    #                 'default_invoice_name': invoice.name or invoice.ref or '',
    #             },
    #             'views': [(False, 'form')],
    #         }
        
    #     # Jika tidak ada invoice, kembalikan action default
    #     action = self.env['ir.actions.act_window']._for_xml_id('account.action_account_payments')
    #     return action

class AccountPayment(models.Model):
    """It inherits the account.payment model for adding new fields
     and functions"""
    _inherit = "account.payment"

    bank_reference = fields.Char(string="Bank Reference", copy=False)
    cheque_reference = fields.Char(string="Cheque Reference",copy=False)
    effective_date = fields.Date('Effective Date',
                                 help='Effective date of PDC', copy=False,
                                 default=False)

    def open_payment_matching_screen(self):
        """Open reconciliation view for customers/suppliers"""
        move_line_id = False
        for move_line in self.line_ids:
            if move_line.account_id.reconcile:
                move_line_id = move_line.id
                break
        if not self.partner_id:
            raise UserError(_("Payments without a customer can't be matched"))
        action_context = {'company_ids': [self.company_id.id], 'partner_ids': [
            self.partner_id.commercial_partner_id.id]}
        if self.partner_type == 'customer':
            action_context.update({'mode': 'customers'})
        elif self.partner_type == 'supplier':
            action_context.update({'mode': 'suppliers'})
        if move_line_id:
            action_context.update({'move_line_id': move_line_id})
        return {
            'type': 'ir.actions.client',
            'tag': 'manual_reconciliation_view',
            'context': action_context,
        }

    def print_checks(self):
        """ Check that the recordset is valid, set the payments state to
        sent and call print_checks() """
        # Since this method can be called via a client_action_multi, we
        # need to make sure the received records are what we expect
        selfs = self.filtered(lambda r:
                              r.payment_method_id.code
                              in ['check_printing', 'pdc']
                              and r.state != 'reconciled')
        if len(selfs) == 0:
            raise UserError(_(
                "Payments to print as a checks must have 'Check' "
                "or 'PDC' selected as payment method and "
                "not have already been reconciled"))
        if any(payment.journal_id != selfs[0].journal_id for payment in selfs):
            raise UserError(_(
                "In order to print multiple checks at once, they "
                "must belong to the same bank journal."))

        if not selfs[0].journal_id.check_manual_sequencing:
            # The wizard asks for the number printed on the first
            # pre-printed check so payments are attributed the
            # number of the check the'll be printed on.
            last_printed_check = selfs.search([
                ('journal_id', '=', selfs[0].journal_id.id),
                ('check_number', '!=', "0")], order="check_number desc",
                limit=1)
            next_check_number = last_printed_check and int(
                last_printed_check.check_number) + 1 or 1
            return {
                'name': _('Print Pre-numbered Checks'),
                'type': 'ir.actions.act_window',
                'res_model': 'print.prenumbered.checks',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'payment_ids': self.ids,
                    'default_next_check_number': next_check_number,
                }
            }
        else:
            self.filtered(lambda r: r.state == 'draft').post()
            self.write({'state': 'sent'})
            return self.do_print_checks()

    def _prepare_payment_moves(self):
        """ supered function to set effective date """
        res = super(AccountPayment, self)._prepare_payment_moves()
        inbound_pdc_id = self.env.ref(
            'base_accounting_kit.account_payment_method_pdc_in').id
        outbound_pdc_id = self.env.ref(
            'base_accounting_kit.account_payment_method_pdc_out').id
        if self.payment_method_id.id == inbound_pdc_id or \
                self.payment_method_id.id == outbound_pdc_id \
                and self.effective_date:
            res[0]['date'] = self.effective_date
            for line in res[0]['line_ids']:
                line[2]['date_maturity'] = self.effective_date
        return res

    def mark_as_sent(self):
        """Updates the is_move_sent value of the payment model"""
        self.write({'is_sent': True})

    def unmark_as_sent(self):
        """Updates the is_move_sent value of the payment model"""
        self.write({'is_sent': False})