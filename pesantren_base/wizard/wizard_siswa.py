# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class WizardSearchSiswa(models.TransientModel):
    _name = 'wizard.search.siswa'
    _description = 'Wizard Search Siswa'

    siswa_id = fields.Many2one(
        'cdn.siswa', string='Siswa', required=False, store=True, ondelete='cascade')
    tmp_lahir = fields.Char(related='siswa_id.tmp_lahir',
                            string='Tmp Lahir', store=True)
    tgl_lahir = fields.Date(related='siswa_id.tgl_lahir',
                            string='Tgl Lahir', store=True)
    nis = fields.Char(related='siswa_id.nis', string='NIS',
                      required=False, store=True)
    barcode = fields.Char(string='Kartu Santri', readonly=False)

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Mengisi siswa_id berdasarkan barcode yang diinput"""
        if self.barcode:
            siswa = self.env['cdn.siswa'].search(
                [('barcode_santri', '=', self.barcode)], limit=1)

            if siswa:
                self.siswa_id = siswa.id
            else:
                self.siswa_id = False
                barcode_sementara = self.barcode
                self.barcode = False
                return {
                    'warning': {
                        'title': "Perhatian !",
                        'message': f"Data Santri dengan Kartu Santri {barcode_sementara} tidak ditemukan."
                    }
                }

    def button_search(self):
        if not self.siswa_id and self.barcode:
            siswa = self.env['cdn.siswa'].search(
                [('barcode_santri', '=', self.barcode)], limit=1)
            if siswa:
                self.siswa_id = siswa.id
            else:
                raise UserError(
                    f"Data Santri dengan Kartu Santri {self.barcode} tidak ditemukan")

        if not self.siswa_id:
            raise UserError('Silahkan isi data santri terlebih dahulu')

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cdn.siswa',
            'view_mode': 'form',
            'res_id': self.siswa_id.id,
            'target': 'current',
        }
