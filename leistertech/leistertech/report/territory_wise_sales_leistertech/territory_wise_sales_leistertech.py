# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _

from erpnext import get_default_currency


def execute(filters=None):
    filters = frappe._dict(filters)
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    currency = get_default_currency()
    return [
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 150,
        },
        {
            "label": _("Opportunity Amount"),
            "fieldname": "opportunity_amount",
            "fieldtype": "Currency",
            "options": currency,
            "width": 150,
        },
        {
            "label": _("Quotation Amount"),
            "fieldname": "quotation_amount",
            "fieldtype": "Currency",
            "options": currency,
            "width": 150,
        },
        {
            "label": _("Order Amount"),
            "fieldname": "order_amount",
            "fieldtype": "Currency",
            "options": currency,
            "width": 150,
        },
        {
            "label": _("Billing Amount"),
            "fieldname": "billing_amount",
            "fieldtype": "Currency",
            "options": currency,
            "width": 150,
        },
    ]


def get_data(filters=None):
    data = []

    opportunities = get_opportunities(filters)
    quotations = get_quotations(filters)
    sales_orders = get_sales_orders(filters)
    sales_invoices = get_sales_invoice(filters)

    for territory in frappe.get_all("Territory"):
        territory_data = {
            "territory": territory.name,
            "opportunity_amount": sum(
                [
                    opportunity["opportunity_amount"]
                    for opportunity in opportunities
                    if opportunity["territory"] == territory.name
                ]
            ),
            "quotation_amount": sum(
                quotation["net_total"]
                for quotation in quotations
                if quotation["territory"] == territory.name
            ),
            "order_amount": sum(
                order["base_total"]
                for order in sales_orders
                if order["territory"] == territory.name
            ),
            "billing_amount": sum(
                invoice["base_total"]
                for invoice in sales_invoices
                if invoice["territory"] == territory.name
            ),
        }
        data.append(territory_data)

    return data


def get_opportunities(filters):
    conditions = ""

    if filters.get("transaction_date"):
        conditions = " WHERE transaction_date between {0} and {1}".format(
            frappe.db.escape(filters["transaction_date"][0]),
            frappe.db.escape(filters["transaction_date"][1]),
        )

    if filters.company:
        if conditions:
            conditions += " AND"
        else:
            conditions += " WHERE"
        conditions += " company = %(company)s"

    return frappe.db.sql(
        """
		SELECT name, territory, opportunity_amount
		FROM `tabOpportunity` {0}
	""".format(
            conditions
        ),
        filters,
        as_dict=1,
    )  # nosec


def get_quotations(filters):
    conditions = ""
    if filters.get("transaction_date"):
        conditions = " and transaction_date between {0} and {1}".format(
            frappe.db.escape(filters["transaction_date"][0]),
            frappe.db.escape(filters["transaction_date"][1]),
        )
    if filters.company:
        conditions += " and company = %(company)s"

    return frappe.db.sql(
        """
        SELECT `name`,`territory`,`net_total`
        FROM `tabQuotation`
        WHERE docstatus=1 {0}
        """.format(
            conditions
        ),
        filters,
        as_dict=1,
    )  # nosec


def get_sales_orders(filters):
    conditions = ""
    if filters.get("transaction_date"):
        conditions = " and transaction_date between {0} and {1}".format(
            frappe.db.escape(filters["transaction_date"][0]),
            frappe.db.escape(filters["transaction_date"][1]),
        )
    if filters.company:
        conditions += " and company = %(company)s"

    return frappe.db.sql(
        """
        SELECT `base_total`,`territory`
        FROM `tabSales Order`
        WHERE docstatus=1 {0}
        """.format(
            conditions
        ),
        filters,
        as_dict=1,
    )  # nosec


def get_sales_invoice(filters):
    if filters.get("transaction_date"):
        conditions = " and posting_date between {0} and {1}".format(
            frappe.db.escape(filters["transaction_date"][0]),
            frappe.db.escape(filters["transaction_date"][1]),
        )
    if filters.company:
        conditions += " and company = %(company)s"

    return frappe.db.sql(
        """
        SELECT `base_total`,`territory`
        FROM `tabSales Invoice`
        WHERE docstatus=1 {0}
        """.format(
            conditions
        ),
        filters,
        as_dict=1,
    )  # nosec
