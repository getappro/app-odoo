# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    ai_passport_root_user = fields.Many2one('res.users', string='Ai Passport Admin', help="Ai通行证用户绑定的本Odoo超管")
