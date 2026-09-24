import frappe


def after_install():
    categories = [
        {
            "category_name": "Power Drill",
            "description": "Electric power drill",
            "daily_rate": 500,
            "deposit_amount": 1000
        },
        {
            "category_name": "Generator",
            "description": "Portable generator",
            "daily_rate": 1500,
            "deposit_amount": 3000
        },
        {
            "category_name": "Scaffold Tower Set",
            "description": "Scaffold tower equipment",
            "daily_rate": 1000,
            "deposit_amount": 2000
        }
    ]

    for data in categories:
        if not frappe.db.exists(
            "Equipment Category",
            {"category_name": data["category_name"]}
        ):
            frappe.get_doc({
                "doctype": "Equipment Category",
                **data
            }).insert(ignore_permissions=True)

    if not frappe.db.exists("RentFlow Settings", "RentFlow Settings"):
        frappe.get_doc({
            "doctype": "RentFlow Settings",
            "shop_name": "Anchor Point Equipment Rental",
            "manager_email": "manager@example.com",
            "default_deposit_percent": 20,
            "damage_fee_per_grade_drop": 500,
            "late_fee_per_day": 100,
            "low_availability_alert_enabled": 1
        }).insert(ignore_permissions=True)

    frappe.db.commit()

    frappe.msgprint("RentFlow installed successfully.")