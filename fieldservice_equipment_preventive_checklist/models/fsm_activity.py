# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

CHECK_RESULTS = ("pass", "fail", "na")
QUESTION_RESULTS = ("yes", "no")


class FSMActivity(models.Model):
    _inherit = "fsm.activity"

    equipment_line_id = fields.Many2one(
        "fsm.order.equipment.line", index=True, ondelete="cascade"
    )
    answer_type = fields.Selection(
        [("check", "Check"), ("question", "Yes/No Question")],
        default="check",
        required=True,
    )
    result = fields.Selection(
        [
            ("pass", "Approved"),
            ("fail", "Reproved"),
            ("na", "Not Applicable"),
            ("yes", "Yes"),
            ("no", "No"),
        ],
        readonly=True,
    )

    def _set_result(self, result):
        self.write({"result": result})
        self.action_done()

    def action_result_pass(self):
        self._set_result("pass")

    def action_result_fail(self):
        self._set_result("fail")

    def action_result_na(self):
        self._set_result("na")

    def action_result_yes(self):
        self._set_result("yes")

    def action_result_no(self):
        self._set_result("no")
