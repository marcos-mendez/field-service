# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class FSMPreventiveType(models.Model):
    _inherit = "fsm.preventive.type"

    corrective_on_fail = fields.Boolean(
        string="Corrective Order When Reproved",
        help="Open a corrective order for the equipment whose sheet is reproved.",
    )
    corrective_order_type_id = fields.Many2one(
        "fsm.order.type", string="Corrective Order Type"
    )
    corrective_user_id = fields.Many2one(
        "res.users",
        string="Corrective Responsible",
        help="Gets an activity on each corrective order opened.",
    )
