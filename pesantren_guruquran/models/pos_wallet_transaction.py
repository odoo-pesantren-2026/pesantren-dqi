from odoo import api, fields, models


class PoswalletTransaction(models.Model):
    _inherit = 'pos.wallet.transaction'

    siswa_id = fields.Many2one(comodel_name='cdn.siswa', string='Siswa',
                               compute='_compute_siswa', store=True, ondelete='cascade')

    @api.depends('partner_id')
    def _compute_siswa(self):
        for record in self:
            Siswa = self.env['cdn.siswa'].search(
                # siswa_id is partner_id
                [('partner_id', '=', record.partner_id.id)])
            if Siswa:
                record.siswa_id = Siswa[0].id
            else:
                record.siswa_id = False
