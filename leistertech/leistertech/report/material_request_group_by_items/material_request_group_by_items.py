# Copyright (c) 2023, rakesh and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import msgprint, _


def execute(filters=None):
    columns = [
        {
            "fieldname": "item_code",
            "label": _("Item Code"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 200,
        },
        {
            "fieldname": "qty",
            "label": _("Request Quantity"),
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "fieldname": "actual_qty",
            "label": _("Actual Quantity"),
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "fieldname": "projected_qty",
            "label": _("Projected Quantity"),
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "fieldname": "count",
            "label": _("Material Request Pending"),
            "fieldtype": "Float",
            "width": 200,
        },
    ]
    data = frappe.db.sql(
        """SELECT
			mri.item_code,
			(mri.qty) AS qty,
			(mri.actual_qty) AS actual_qty,
			(mri.projected_qty) AS projected_qty,
			COUNT(DISTINCT mq.name) AS count
			FROM
				`tabMaterial Request` mq
			JOIN
				`tabMaterial Request Item` mri ON mq.name = mri.parent
			WHERE
				mq.status = 'Pending'
			GROUP BY
				mri.item_code
		"""
    )
    return columns, data
