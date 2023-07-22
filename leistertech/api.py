import frappe


@frappe.whitelist()
def update_pro_plan():
    pro_pan = frappe.get_all("Production Plan", filters={}, fields=["name"])
    for row in pro_pan:
        pro_doc = frappe.get_doc("Production Plan", row.name)
        if pro_doc.get_items_from == "Material Request":
            material_req_no = pro_doc.material_requests[0].material_request
            if material_req_no:
                frappe.db.sql(
                    """update `tabMaterial Request` set production_plan=%s where name=%s""",
                    (pro_doc.name, material_req_no),
                )
                frappe.db.sql(
                    """update `tabSales Order` set production_plan=%s where name in(select parent from `tabSales Order Item` where material_request=%s)""",
                    (pro_doc.name, material_req_no),
                )
        if pro_doc.get_items_from == "Sales Order":
            so_no = pro_doc.sales_orders[0].sales_order
            if so_no:
                frappe.db.sql(
                    """update `tabMaterial Request` set production_plan=%s where name in(select parent from `tabMaterial Request Item` where sales_order=%s)""",
                    (pro_doc.name, so_no),
                )
                frappe.db.sql(
                    """update `tabSales Order` set production_plan=%s where name=%s""",
                    (pro_doc.name, so_no),
                )
        print(f"{pro_doc.name} Updated")


@frappe.whitelist()
def update_pro_plan_ref():
    pro_pan = frappe.get_all("Production Plan", filters={}, fields=["name"])
    for row in pro_pan:
        pro_doc = frappe.get_doc("Production Plan", row.name)
        if pro_doc.get_items_from == "Material Request":
            material_req_no = pro_doc.material_requests[0].material_request
            if material_req_no:
                frappe.db.sql(
                    """update `tabProduction Plan` set material_request_ref=%s where name=%s""",
                    (material_req_no, pro_doc.name),
                )
                sales_order_no = frappe.db.sql(
                    """select sales_order from `tabMaterial Request Item` where parent=%s and docstatus<>2""",
                    material_req_no,
                )
                if len(sales_order_no) >= 1 and sales_order_no[0][0]:
                    frappe.db.sql(
                        """update `tabProduction Plan` set sales_order_ref=%s where name=%s""",
                        (sales_order_no[0][0], pro_doc.name),
                    )
        if pro_doc.get_items_from == "Sales Order":
            so_no = pro_doc.sales_orders[0].sales_order
            if so_no:
                frappe.db.sql(
                    """update `tabProduction Plan` set sales_order_ref=%s where name=%s""",
                    (so_no, pro_doc.name),
                )
                mr_no = frappe.db.sql(
                    """select parent from `tabMaterial Request Item` where sales_order=%s and docstatus<>2""",
                    so_no,
                )
                if len(mr_no) >= 1 and mr_no[0][0]:
                    frappe.db.sql(
                        """update `tabProduction Plan` set material_request_ref=%s where name=%s""",
                        (mr_no[0][0], pro_doc.name),
                    )
        print(f"{pro_doc.name} Updated")


def on_validate(pro_doc, method):
    if pro_doc.get_items_from:
        if pro_doc.get_items_from == "Material Request":
            material_req_no = pro_doc.material_requests[0].material_request
            if material_req_no:
                pro_doc.material_request_ref = material_req_no
                # frappe.db.sql(
                #     """update `tabProduction Plan` set material_request_ref=%s where name=%s""",
                #     (material_req_no, pro_doc.name),
                # )
                sales_order_no = frappe.db.sql(
                    """select sales_order from `tabMaterial Request Item` where parent=%s and docstatus<>2""",
                    material_req_no,
                )
                if len(sales_order_no) >= 1 and sales_order_no[0][0]:
                    pro_doc.sales_order_ref = sales_order_no[0][0]
                    # frappe.db.sql(
                    #     """update `tabProduction Plan` set sales_order_ref=%s where name=%s""",
                    #     (sales_order_no[0][0], pro_doc.name),
                    # )
        if pro_doc.get_items_from == "Sales Order":
            so_no = pro_doc.sales_orders[0].sales_order
            if so_no:
                pro_doc.sales_order_ref = so_no
                # frappe.db.sql(
                #     """update `tabProduction Plan` set sales_order_ref=%s where name=%s""",
                #     (so_no, pro_doc.name),
                # )
                mr_no = frappe.db.sql(
                    """select parent from `tabMaterial Request Item` where sales_order=%s and docstatus<>2""",
                    so_no,
                )
                if len(mr_no) >= 1 and mr_no[0][0]:
                    pro_doc.material_request_ref = mr_no[0][0]
                    # frappe.db.sql(
                    #     """update `tabProduction Plan` set material_request_ref=%s where name=%s""",
                    #     (mr_no[0][0], pro_doc.name),
                    # )


def update_material_request(self, method):
    orgin = "Custom"
    sales_order = None
    production_plan = None
    if len(self.items) >= 1:
        if self.items[0].sales_order:
            orgin = "Sales Order"
            sales_order = self.items[0].sales_order
        if self.items[0].production_plan:
            orgin = "Production Plan"
            production_plan = self.items[0].production_plan
    if production_plan:
        sales_order = (
            frappe.db.get_value("Production Plan", production_plan, "sales_order_ref")
            or ""
        )
    if sales_order:
        production_plan = (
            frappe.db.get_value(
                "Production Plan", {"sales_order_ref": sales_order}, "name"
            )
            or ""
        )
    frappe.db.sql(
        """update `tabMaterial Request` set material_request_origin=%s,custom_sales_order=%s,custom_production_plan=%s where name=%s""",
        (orgin, sales_order, production_plan, self.name),
    )
    if production_plan:
        production_plan_doc = frappe.get_doc("Production Plan", production_plan)
        if not production_plan_doc.docstatus == 2:
            material_requests = frappe.get_all(
                "Material Request",
                filters={"custom_production_plan": production_plan},
                fields=["name"],
            )
            production_plan_doc.material_request_child = []
            for row in material_requests:
                production_plan_doc.append(
                    "material_request_child", dict(material_request_all=row.get("name"))
                )
            production_plan_doc.save()
    if sales_order:
        sales_order_doc = frappe.get_doc("Sales Order", sales_order)
        if not sales_order_doc.docstatus == 2:
            material_requests = frappe.get_all(
                "Material Request",
                filters={"custom_sales_order": sales_order},
                fields=["name"],
            )
            sales_order_doc.material_request_child = []
            for row in material_requests:
                sales_order_doc.append(
                    "material_request_child", dict(material_request_all=row.get("name"))
                )
            sales_order_doc.flags.ignore_mandatory = True
            sales_order_doc.save()


def update_existing_material_request():
    material_requests = frappe.get_all(
        "Material Request", filters={}, fields=["name"], order_by="name asc"
    )
    for material_request in material_requests:
        self = frappe.get_doc("Material Request", material_request.get("name"))
        orgin = "Custom"
        sales_order = None
        production_plan = None
        if len(self.items) >= 1:
            if self.items[0].sales_order:
                orgin = "Sales Order"
                sales_order = self.items[0].sales_order
            if self.items[0].production_plan:
                orgin = "Production Plan"
                production_plan = self.items[0].production_plan
        if production_plan:
            sales_order = (
                frappe.db.get_value(
                    "Production Plan", production_plan, "sales_order_ref"
                )
                or ""
            )
        if sales_order:
            production_plan = (
                frappe.db.get_value(
                    "Production Plan", {"sales_order_ref": sales_order}, "name"
                )
                or ""
            )
        frappe.db.sql(
            """update `tabMaterial Request` set material_request_origin=%s,custom_sales_order=%s,custom_production_plan=%s where name=%s""",
            (orgin, sales_order, production_plan, self.name),
        )
        if production_plan:
            production_plan_doc = frappe.get_doc("Production Plan", production_plan)
            if not production_plan_doc.docstatus == 2:
                material_requests = frappe.get_all(
                    "Material Request",
                    filters={"custom_production_plan": production_plan},
                    fields=["name"],
                )
                production_plan_doc.material_request_child = []
                for row in material_requests:
                    production_plan_doc.append(
                        "material_request_child",
                        dict(material_request_all=row.get("name")),
                    )
                production_plan_doc.save()
        if sales_order:
            sales_order_doc = frappe.get_doc("Sales Order", sales_order)
            if not sales_order_doc.docstatus == 2:
                material_requests = frappe.get_all(
                    "Material Request",
                    filters={"custom_sales_order": sales_order},
                    fields=["name"],
                )
                sales_order_doc.material_request_child = []
                for row in material_requests:
                    sales_order_doc.append(
                        "material_request_child",
                        dict(material_request_all=row.get("name")),
                    )
                sales_order_doc.flags.ignore_mandatory = True
                sales_order_doc.save()
        print(f"{material_request.get('name')} Updated")
