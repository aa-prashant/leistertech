// Copyright (c) 2023, rakesh and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Territory-wise Sales Leistertech"] = {
	"filters": [
		{
			fieldname:"transaction_date",
			label: __("Transaction Date"),
			fieldtype: "DateRange",
			default: [frappe.datetime.add_months(frappe.datetime.get_today(),-1), frappe.datetime.get_today()],
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		}
	]
};
