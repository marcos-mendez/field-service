# Copyright 2026 Pop Solutions
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Field Service - Equipment Preventive Checklist",
    "summary": "Checklist sheet per equipment on preventive visits",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "development_status": "Beta",
    "website": "https://github.com/OCA/field-service",
    "category": "Field Service",
    "author": "Pop Solutions, Odoo Community Association (OCA)",
    "maintainers": ["marcos-mendez"],
    "depends": ["fieldservice_equipment_preventive", "fieldservice_activity"],
    "data": [
        "views/fsm_preventive_type_views.xml",
        "views/fsm_template_views.xml",
        "views/fsm_order_equipment_line_views.xml",
    ],
}
