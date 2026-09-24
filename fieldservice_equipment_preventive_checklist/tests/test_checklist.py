# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestPreventiveChecklist(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env.ref("fieldservice.test_location")
        cls.visit_type = cls.env.ref(
            "fieldservice_equipment_preventive.preventive_type_maintenance"
        )
        cls.responsible = cls.env["res.users"].create(
            {"name": "Workshop", "login": "workshop"}
        )
        cls.corrective_type = cls.env["fsm.order.type"].create({"name": "Corrective"})
        cls.template = cls.env["fsm.template"].create(
            {
                "name": "Sheet",
                "temp_activity_ids": [
                    (
                        0,
                        0,
                        {"name": "In use?", "answer_type": "question", "sequence": 1},
                    ),
                    (0, 0, {"name": "Check alarms", "sequence": 2}),
                    (0, 0, {"name": "Check seals", "sequence": 3}),
                ],
            }
        )
        cls.equipment = cls.env["fsm.equipment"].create(
            {
                "name": "Autoclave",
                "current_location_id": cls.location.id,
                "preventive_ids": [
                    (
                        0,
                        0,
                        {
                            "type_id": cls.visit_type.id,
                            "interval": 1,
                            "template_id": cls.template.id,
                        },
                    )
                ],
            }
        )

    def _create_line(self):
        order = self.env["fsm.order"].create(
            {
                "location_id": self.location.id,
                "equipment_line_ids": [
                    (
                        0,
                        0,
                        {
                            "equipment_id": self.equipment.id,
                            "preventive_id": self.equipment.preventive_ids.id,
                            "template_id": self.template.id,
                        },
                    )
                ],
            }
        )
        return order.equipment_line_ids

    def test_sheet_approved(self):
        line = self._create_line()
        question, alarms, seals = line.checklist_activity_ids.sorted("sequence")
        self.assertEqual(question.answer_type, "question")
        self.assertEqual(line.action_open_checklist()["res_id"], line.id)
        question.action_result_no()
        alarms.action_result_pass()
        self.assertFalse(line.conclusion)
        with self.assertRaises(UserError):
            line.action_done()
        seals.action_result_na()
        self.assertEqual(line.conclusion, "pass")
        line.action_done()
        self.assertEqual(line.validated_by_id, self.env.user)
        self.assertFalse(line.corrective_order_id)
        line.action_pending()
        self.assertFalse(line.validated_by_id)

    def test_sheet_reproved_opens_corrective(self):
        self.visit_type.write(
            {
                "corrective_on_fail": True,
                "corrective_order_type_id": self.corrective_type.id,
                "corrective_user_id": self.responsible.id,
            }
        )
        line = self._create_line()
        question, alarms, seals = line.checklist_activity_ids.sorted("sequence")
        question.action_result_yes()
        alarms.action_result_fail()
        seals.action_result_pass()
        self.assertEqual(line.conclusion, "fail")
        line.action_done()
        corrective = line.corrective_order_id
        self.assertEqual(corrective.type, self.corrective_type)
        self.assertEqual(corrective.equipment_ids, self.equipment)
        self.assertIn("Check alarms", corrective.description)
        self.assertNotIn("Check seals", corrective.description)
        self.assertEqual(corrective.activity_ids.user_id, self.responsible)
        # validating again does not open a second corrective order
        line.action_pending()
        line.action_done()
        self.assertEqual(line.corrective_order_id, corrective)

    def test_reproved_without_corrective_setup(self):
        line = self._create_line()
        for activity in line.checklist_activity_ids:
            activity._set_result("fail")
        line.action_done()
        self.assertFalse(line.corrective_order_id)
        self.visit_type.corrective_on_fail = True
        other = self._create_line()
        for activity in other.checklist_activity_ids:
            activity._set_result("fail")
        other.action_done()
        self.assertTrue(other.corrective_order_id)
        self.assertFalse(other.corrective_order_id.activity_ids)

    def test_template_change_rebuilds_sheet(self):
        line = self._create_line()
        line.template_id = False
        self.assertFalse(line.checklist_activity_ids)
        line.note = "No sheet"
        line.action_done()
        self.assertFalse(line.conclusion)
