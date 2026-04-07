# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import logging


_logger = logging.getLogger(__name__)


class WizardSearchSiswa(models.TransientModel):
    _name = 'wizard.register.kartu'
    _description = 'Wizard untuk registrasi kartu dan pin wallet'

    kartu_santri = fields.Char(string="Kartu Santri Baru", required=True)
    pin = fields.Char(string="PIN", required=True)

    @api.onchange('kartu_santri')
    def _onchange_kartu_santri(self):
        if self.kartu_santri:
            existing_kartu = self.env['cdn.siswa'].search(
                [('barcode', '=', self.kartu_santri)], limit=1)

            if existing_kartu:
                self.kartu_santri = False
                return {
                    'warning': {
                        'title': 'Registrasi gagal!',
                        'message': 'Kartu yang Anda masukkan sudah terdaftar dalam sistem.'
                    }
                }

    def _get_partner_id(self):
        context = self._context
        active_id = context.get('active_id')
        model = context.get('active_model')

        partner_id = active_id
        if model == 'cdn.siswa':
            Siswa = self.env['cdn.siswa'].browse(active_id)
            partner_id = Siswa.partner_id.id
        return partner_id

    def action_register(self):
        context = self._context
        active_id = context.get('active_id')

        Partner = self.env["res.partner"].browse(self._get_partner_id())
        Partner.write({
            'wallet_pin': self.pin
        })

        Kartu = self.env['cdn.siswa'].browse(active_id)
        Kartu.write({
            'barcode': self.kartu_santri,
            'barcode_santri': self.kartu_santri,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sukses!',
                'message': 'Registrasi berhasil! Kartu santri telah terdaftar.',
                'type': 'success',
                'sticky': False,
            }
        }
