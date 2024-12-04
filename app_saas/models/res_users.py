# -*- coding: utf-8 -*-

try:
    import urlparse
except:
    from urllib.parse import urlparse
try:
    import urllib2
except:
    from urllib import request as urllib2



from odoo import api, fields, models, _
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.http import request, Response
from odoo.tools.misc import ustr

from ast import literal_eval
import json
import requests
from datetime import timedelta
import random

import logging
_logger = logging.getLogger(__name__)

class OauthBindError(Exception):
    # 增加一种错误类型
    pass

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    @api.model
    def auth_oauth(self, provider, params):
        # 这里原生是已取 token，实际用 code 时要另取token
        access_token = params.get('access_token')
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        if oauth_provider.code_endpoint and oauth_provider.scope.find('odoo') >= 0:
            # odoo 特殊处理，用code取token
            if not access_token and params.get('code'):
                params.update({
                    'scope': oauth_provider.scope or '',
                    'client_id': oauth_provider.client_id or '',
                })
                if hasattr(oauth_provider, 'client_secret') and oauth_provider.client_secret:
                    params.update({
                        'client_secret': oauth_provider.client_secret or '',
                    })
                response = requests.get(oauth_provider.code_endpoint, params=params, timeout=20)
                if response.ok:
                    ret = response.json()
                res = {**ret, **params}
                res.pop('code')
        self = self.with_context(auth_extra=params)
        res = super(ResUsers, self).auth_oauth(provider, res)
        return res
        
    def _create_user_from_template(self, values):
        # 处理odooapp.cn 为 server 时 默认为内部用户
        oauth_provider_id = values.get('oauth_provider_id')
        if oauth_provider_id:
            provider = request.env['auth.oauth.provider'].sudo().browse(int(oauth_provider_id))
            if provider and provider.scope.find('odoo') >= 0:
                template_user = request.env.ref('base.default_user')
                if provider and hasattr(provider, 'user_template_id'):
                    template_user = provider.user_template_id

                if not values.get('login'):
                    raise ValueError(_('Signup: no login given for new user'))
                if not values.get('partner_id') and not values.get('name'):
                    raise ValueError(_('Signup: no name or partner given for new user'))

                # create a copy of the template user (attached to a specific partner_id if given)
                values['active'] = True
                try:
                    with self.env.cr.savepoint():
                        return template_user.sudo().with_context(no_reset_password=True).copy(values)
                except Exception as e:
                    # copy may failed if asked login is not available.
                    raise SignupError(ustr(e))
        res = super(ResUsers, self)._create_user_from_template(values)
        self._cr.commit()
        return res

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        # 此处生成 创建 odoo user 的初始值，增加字段如头像
        res = super(ResUsers, self)._generate_signup_values(provider, validation, params)
        # 后置增加字段，包括 headimgurl
        if validation.get('mobile'):
            res['mobile'] = validation.get('mobile')
        if validation.get('headimgurl'):
            res['image_1920'] = self.sudo()._get_image_from_url(validation.get('headimgurl'))
        return res
