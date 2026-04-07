# -*- coding: utf-8 -*-

from odoo import models, fields


class ActivationResultWizard(models.TransientModel):
    _name = 'activation.result.wizard'
    _description = 'Activation Result Wizard'

    message = fields.Text(string='Message', readonly=True)
