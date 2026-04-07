from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    limit_weekly_reset_day = fields.Selection(
        related='company_id.limit_weekly_reset_day', readonly=False)
    limit_monthly_reset_day = fields.Integer(
        related='company_id.limit_monthly_reset_day', readonly=False)
    limit_reset_hour = fields.Integer(
        related='company_id.limit_reset_hour', readonly=False)
    max_wallet = fields.Float(
        related='company_id.max_wallet', readonly=False)
    standard_limit_amount = fields.Float(
        related='company_id.standard_limit_amount', readonly=False)
