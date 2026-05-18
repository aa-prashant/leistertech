import frappe


TERMINAL_STATUSES = {
    "Material Request": {
        "Cancelled",
        "Closed",
        "Completed",
        "Manufactured",
        "Ordered",
        "Received",
        "Stopped",
    },
    "Production Plan": {"Cancelled", "Closed", "Completed"},
    "Sales Order": {"Cancelled", "Closed", "Completed"},
}


@frappe.whitelist()
def update_pro_plan():
    pro_pan = frappe.get_all("Production Plan", filters={}, fields=["name"])
    for row in pro_pan:
        pro_doc = frappe.get_doc("Production Plan", row.name)
        if _is_terminal_doc(pro_doc):
            continue

        if pro_doc.get_items_from == "Material Request":
            material_req_no = pro_doc.material_requests[0].material_request
            if material_req_no:
                frappe.db.sql(
                    """update `tabMaterial Request`
                    set production_plan=%s
                    where name=%s
                        and docstatus<>2
                        and coalesce(status, '') not in %s""",
                    (pro_doc.name, material_req_no, tuple(TERMINAL_STATUSES["Material Request"])),
                )
                frappe.db.sql(
                    """update `tabSales Order`
                    set production_plan=%s
                    where name in(select parent from `tabSales Order Item` where material_request=%s)
                        and docstatus<>2
                        and coalesce(status, '') not in %s""",
                    (pro_doc.name, material_req_no, tuple(TERMINAL_STATUSES["Sales Order"])),
                )
        if pro_doc.get_items_from == "Sales Order":
            so_no = pro_doc.sales_orders[0].sales_order
            if so_no:
                frappe.db.sql(
                    """update `tabMaterial Request`
                    set production_plan=%s
                    where name in(select parent from `tabMaterial Request Item` where sales_order=%s)
                        and docstatus<>2
                        and coalesce(status, '') not in %s""",
                    (pro_doc.name, so_no, tuple(TERMINAL_STATUSES["Material Request"])),
                )
                frappe.db.sql(
                    """update `tabSales Order`
                    set production_plan=%s
                    where name=%s
                        and docstatus<>2
                        and coalesce(status, '') not in %s""",
                    (pro_doc.name, so_no, tuple(TERMINAL_STATUSES["Sales Order"])),
                )
        print(f"{pro_doc.name} Updated")


@frappe.whitelist()
def update_pro_plan_ref():
    pro_pan = frappe.get_all("Production Plan", filters={}, fields=["name"])
    for row in pro_pan:
        pro_doc = frappe.get_doc("Production Plan", row.name)
        if _is_terminal_doc(pro_doc):
            continue

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
    if _is_terminal_doc(pro_doc):
        return

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


def _get_material_request_references(material_request):
    orgin = "Custom"
    sales_order = ""
    production_plan = ""

    if len(material_request.items) >= 1:
        if material_request.items[0].sales_order:
            orgin = "Sales Order"
            sales_order = material_request.items[0].sales_order
        if material_request.items[0].production_plan:
            orgin = "Production Plan"
            production_plan = material_request.items[0].production_plan

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

    return orgin, sales_order, production_plan


def _is_terminal_state(doctype, docstatus=None, status=None):
    return frappe.utils.cint(docstatus) == 2 or (status or "") in TERMINAL_STATUSES.get(
        doctype, set()
    )


def _is_terminal_doc(doc):
    return _is_terminal_state(doc.doctype, doc.get("docstatus"), doc.get("status"))


def _set_material_request_references(material_request, orgin, sales_order, production_plan):
    material_request.material_request_origin = orgin
    material_request.custom_sales_order = sales_order
    material_request.custom_production_plan = production_plan


def _update_material_request_references(name, orgin, sales_order, production_plan):
    current = frappe.db.get_value(
        "Material Request",
        name,
        [
            "docstatus",
            "status",
            "material_request_origin",
            "custom_sales_order",
            "custom_production_plan",
        ],
        as_dict=True,
    )

    if not current or _is_terminal_state(
        "Material Request", current.docstatus, current.status
    ):
        return False

    values = {
        "material_request_origin": orgin,
        "custom_sales_order": sales_order,
        "custom_production_plan": production_plan,
    }

    if all((current.get(field) or "") == (value or "") for field, value in values.items()):
        return False

    frappe.db.set_value("Material Request", name, values, update_modified=False)
    return True


def _get_material_request_names(fieldname, value):
    if not value:
        return []

    return [
        row.name
        for row in frappe.get_all(
            "Material Request",
            filters={fieldname: value},
            fields=["name"],
            order_by="name asc",
        )
    ]


def _sync_material_request_child(parent_doctype, parent_name, material_request_names):
    if not parent_name:
        return False

    parent = frappe.db.get_value(
        parent_doctype, parent_name, ["name", "docstatus", "status"], as_dict=True
    )
    if not parent or _is_terminal_state(parent_doctype, parent.docstatus, parent.status):
        return False

    material_request_names = [name for name in material_request_names if name]
    filters = {
        "parenttype": parent_doctype,
        "parent": parent_name,
        "parentfield": "material_request_child",
    }
    existing = frappe.get_all(
        "Material Request Child",
        filters=filters,
        fields=["name", "material_request_all"],
        order_by="idx asc",
    )

    if [row.material_request_all for row in existing] == material_request_names:
        return False

    frappe.db.delete("Material Request Child", filters)
    for idx, material_request in enumerate(material_request_names, start=1):
        frappe.get_doc(
            {
                "doctype": "Material Request Child",
                "parenttype": parent_doctype,
                "parent": parent_name,
                "parentfield": "material_request_child",
                "docstatus": parent.docstatus,
                "idx": idx,
                "material_request_all": material_request,
            }
        ).insert(ignore_permissions=True)

    frappe.db.set_value(
        parent_doctype,
        parent_name,
        {"modified": frappe.utils.now(), "modified_by": frappe.session.user},
        update_modified=False,
    )
    return True


def _sync_parent_material_request_children(sales_orders=None, production_plans=None):
    updated = {"Sales Order": 0, "Production Plan": 0}

    for production_plan in sorted(production_plans or []):
        if _sync_material_request_child(
            "Production Plan",
            production_plan,
            _get_material_request_names("custom_production_plan", production_plan),
        ):
            updated["Production Plan"] += 1

    for sales_order in sorted(sales_orders or []):
        if _sync_material_request_child(
            "Sales Order",
            sales_order,
            _get_material_request_names("custom_sales_order", sales_order),
        ):
            updated["Sales Order"] += 1

    return updated


def update_material_request(self, method):
    if _is_terminal_doc(self):
        return

    orgin, sales_order, production_plan = _get_material_request_references(self)
    _set_material_request_references(self, orgin, sales_order, production_plan)


def sync_material_request_parent_links(self, method=None):
    if _is_terminal_doc(self):
        return

    sales_orders = set()
    production_plans = set()

    for material_request in (self, self.get_doc_before_save()):
        if not material_request:
            continue
        if material_request.get("custom_sales_order"):
            sales_orders.add(material_request.custom_sales_order)
        if material_request.get("custom_production_plan"):
            production_plans.add(material_request.custom_production_plan)

    _sync_parent_material_request_children(sales_orders, production_plans)


def update_existing_material_request():
    material_requests = frappe.get_all(
        "Material Request", filters={}, fields=["name"], order_by="name asc"
    )
    sales_orders = set()
    production_plans = set()
    material_requests_updated = 0

    for material_request in material_requests:
        self = frappe.get_doc("Material Request", material_request.get("name"))
        if _is_terminal_doc(self):
            continue

        orgin, sales_order, production_plan = _get_material_request_references(self)

        if _update_material_request_references(self.name, orgin, sales_order, production_plan):
            material_requests_updated += 1

        if production_plan:
            production_plans.add(production_plan)
        if sales_order:
            sales_orders.add(sales_order)

    parents_updated = _sync_parent_material_request_children(sales_orders, production_plans)
    print(
        "Updated {0} Material Requests, {1} Sales Orders, {2} Production Plans".format(
            material_requests_updated,
            parents_updated["Sales Order"],
            parents_updated["Production Plan"],
        )
    )
