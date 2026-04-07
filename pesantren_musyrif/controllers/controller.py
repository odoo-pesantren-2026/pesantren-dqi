from odoo import http,fields
from odoo.http import request
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class MusyrifController(http.Controller):

    @http.route('/santri/get/data', type='json', auth='user')
    def get_data_santri():
        pass