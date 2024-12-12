# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = ['account.account']
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'code'
    # _rec_name = 'complete_name'

    parent_id = fields.Many2one('account.account', 'Parent Chart', index=True, ondelete='cascade')
    child_ids = fields.One2many('account.account', 'parent_id', 'Child Chart')
    parent_path = fields.Char(index=True, unaccent=False)

    @api.model
    def _search_new_account_code(self, company, digits, prefix):
        # 分隔符，金蝶为 "."，用友为""，注意odoo中一级科目，现金默认定义是4位头，银行是6位头
        delimiter = company.coa_delimiter or ''
        for num in range(1, 100):
            new_code = str(prefix.ljust(digits - 1, '0')) + delimiter + '%02d' % (num)
            rec = self.search([('code', '=', new_code), ('company_id', '=', company.id)], limit=1)
            if not rec:
                return new_code
        return super(AccountAccount, self)._search_new_account_code(company, digits, prefix)

    def refresh_account_parent(self, company=None):
        if not company:
            company = self.env.user.company_id
        self = self.filtered(lambda r: len(r.code) > 2).sorted(key=lambda r: r.code)
        done = 0
        # 分隔符 delimiter，用友为""，金蝶为 "."，注意odoo中一级科目，现金默认定义是4位头，银行是6位头
        # 我们使用 用友的多级科目方式，自动生成下级，此处直接覆盖原生
        delimiter = company.chart_template_id.delimiter or ''
        for rec in self:
            if len(rec.code) > 2:
                p_code = rec.code[:len(rec.code) - 2]
                if delimiter and delimiter != '':
                    p_code = rec.code[:len(rec.code) - 2 - len(delimiter)]
                p_acc = self.search([('company_id', '=', company.id), ('code', '=', p_code)])
                if p_acc and rec.parent_id != p_acc:
                    rec.write({'parent_id': p_acc.id})
                    done += 1

        return {
            'effect': {
                'fadeout': 'fast',
                'message': _('Update parent account chart done.<br/>【%s】 records updated.' % done),
                'img_url': '/web/image/%s/%s/image_1024' % (self.env.user._name,
                                                            self.env.user.id) if self.env.user.image_1024 else '/web/static/src/img/smile.svg',
                'type': 'rainbow_man',
            }
        }
