# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FSMOrderEquipmentLine(models.Model):
    _inherit = "fsm.order.equipment.line"

    checklist_activity_ids = fields.One2many(
        "fsm.activity", "equipment_line_id", string="Checklist"
    )
    conclusion = fields.Selection(
        [("pass", "Approved"), ("fail", "Reproved")],
        compute="_compute_conclusion",
        store=True,
    )
    validated_by_id = fields.Many2one("res.users", readonly=True)
    signature = fields.Image(copy=False, max_width=1024, max_height=1024)
    corrective_order_id = fields.Many2one(
        "fsm.order", string="Corrective Order", readonly=True, copy=False
    )

    @api.depends("checklist_activity_ids.result")
    def _compute_conclusion(self):
        for line in self:
            results = line.checklist_activity_ids.mapped("result")
            if "fail" in results:
                line.conclusion = "fail"
            elif results and all(results):
                line.conclusion = "pass"
            else:
                line.conclusion = False

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._copy_template_activities()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if "template_id" in vals:
            self._copy_template_activities()
        return res

    def _copy_template_activities(self):
        """The sheet of the line: a copy of the activities of its template."""
        for line in self:
            line.checklist_activity_ids.unlink()
            self.env["fsm.activity"].create(
                [
                    {
                        "equipment_line_id": line.id,
                        "name": activity.name,
                        "sequence": activity.sequence,
                        "required": activity.required,
                        "ref": activity.ref,
                        "answer_type": activity.answer_type,
                    }
                    for activity in line.template_id.temp_activity_ids
                ]
            )

    def action_open_checklist(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.display_name,
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_done(self):
        for line in self:
            pending = line.checklist_activity_ids.filtered(lambda a: not a.result)
            if pending:
                raise UserError(
                    _(
                        "Answer every activity of the sheet of %(equipment)s "
                        "before validating it: %(activities)s",
                        equipment=line.equipment_id.display_name,
                        activities=", ".join(pending.mapped("name")),
                    )
                )
        res = super().action_done()
        self.write({"validated_by_id": self.env.user.id})
        self.filtered(lambda line: line.conclusion == "fail")._open_corrective_orders()
        return res

    def action_pending(self):
        self.write({"validated_by_id": False})
        return super().action_pending()

    def _prepare_corrective_order_values(self):
        self.ensure_one()
        visit_type = self.preventive_type_id
        failed = self.checklist_activity_ids.filtered(lambda a: a.result == "fail")
        return {
            "location_id": self.order_id.location_id.id,
            "company_id": self.order_id.company_id.id,
            "type": visit_type.corrective_order_type_id.id,
            "equipment_ids": [(6, 0, self.equipment_id.ids)],
            "description": _(
                "Reproved on %(order)s (%(type)s):\n%(activities)s",
                order=self.order_id.name,
                type=visit_type.name,
                activities="\n".join(f"- {name}" for name in failed.mapped("name")),
            ),
        }

    def _open_corrective_orders(self):
        """One corrective order per reproved equipment, for what was reproved."""
        for line in self.filtered(
            lambda line: line.preventive_type_id.corrective_on_fail
            and not line.corrective_order_id
        ):
            order = self.env["fsm.order"].create(
                line._prepare_corrective_order_values()
            )
            line.corrective_order_id = order
            responsible = line.preventive_type_id.corrective_user_id
            if responsible:
                order.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=responsible.id,
                    summary=_("Corrective order from a reproved preventive visit"),
                    note=order.description,
                )
