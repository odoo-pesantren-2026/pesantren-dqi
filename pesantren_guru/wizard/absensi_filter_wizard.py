# -*- coding: utf-8 -*-

from odoo import models, fields


class AbsensiFilterWizard(models.TransientModel):
    _name = 'cdn.absensi.filter.wizard'
    _description = 'Filter Manual Tanggal Absensi'

    date_start = fields.Date(string='Dari Tanggal', required=True)
    date_end = fields.Date(string='Sampai Tanggal', required=True)

    def action_filter(self):
        domain = []
        if self.date_start:
            domain.append(('tanggal', '>=', self.date_start))
        if self.date_end:
            domain.append(('tanggal', '<=', self.date_end))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hasil Filter Absensi',
            'res_model': 'cdn.absensi_siswa',
            'view_mode': 'tree,form',
            'domain': domain,
            'target': 'current',
            'context': dict(self.env.context),
        }
