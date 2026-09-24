import frappe

def get_shop_name():
    return frappe.db.get_single_value("RentFlow Settings", "company_name")