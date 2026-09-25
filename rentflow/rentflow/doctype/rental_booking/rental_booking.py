# Copyright (c) 2026, Mohanapriya S and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class RentalBooking(Document):
    def validate(self):
        
        if getdate(self.start_date) > getdate(self.end_date):
            frappe.throw("End date must be after Start date")

        for item in self.items:
            conflict = frappe.db.sql("""
                select rb.name
                from `tabRental Booking` rb
                inner join `tabBooking Item` bi
                    on bi.parent = rb.name
                where rb.docstatus = 1
                  and rb.status not in ('Cancelled', 'Returned')
                  and bi.equipment_unit = %s
                  and rb.start_date <= %s
                  and rb.end_date >= %s
                  and rb.name != %s
                  limit 1
            """, (
                item.equipment_unit,
                self.end_date,
                self.start_date,
                self.name or ""
            ), as_dict=True)

            if conflict:
                frappe.throw(
                    f"Equipment Unit {item.equipment_unit} is already booked in {conflict[0].name}"
                )


        rtotal = 0
        dtotal = 0

        rank = {
            "New": 1,
            "Good": 2,
            "Fair": 3,
            "Poor": 4,
            "Damaged": 5
        }

        settings = frappe.get_single("Rentflow Settings")
        damage_rate = settings.damage_fee_per_grade_drop

        for item in self.items:
            item.line_days = (
                getdate(self.end_date) - getdate(self.start_date)
            ).days + 1

            item.line_amount = item.daily_rate * item.line_days * item.quantity
            rtotal += item.line_amount

            if (
                item.checkin_condition_grade
                and item.checkout_condition_grade
                and rank[item.checkin_condition_grade]
                > rank[item.checkout_condition_grade]
            ):
                diff = (
                    rank[item.checkin_condition_grade]
                    - rank[item.checkout_condition_grade]
                )

                item.damage_fee = damage_rate * diff
                dtotal += item.damage_fee
            else:
                item.damage_fee = 0

        self.rental_total = rtotal
        self.damage_total = dtotal
        self.final_amount = rtotal + dtotal

    def before_submit(self):
        if (self.status != "Confirmed"):
            frappe.throw("The Status must be Confirmed before Submission")

        if not self.deposit_collected or self.deposit_collected<=0:
            frappe.throw("You  must enter the Deposite collected amount before Submission")

        for item in self.items:
                    conflict = frappe.db.sql("""
                        select rb.name
                        from `tabRental Booking` rb
                        inner join `tabBooking Item` bi
                            on bi.parent = rb.name
                        where rb.docstatus = 1
                          and rb.status not in ('Cancelled', 'Returned')
                          and bi.equipment_unit = %s
                          and rb.start_date <= %s
                          and rb.end_date >= %s
                          and rb.name != %s
                          limit 1
                    """, (
                        item.equipment_unit,
                        self.end_date,
                        self.start_date,
                        self.name or ""
                    ), as_dict=True)
        
                    if conflict:
                        frappe.throw(
                            f"Equipment Unit {item.equipment_unit} is already booked in {conflict[0].name}"
                        )


    def on_submit(self):
        for item in self.items:
            frappe.db.set_value("Equipment Unit",item.equipment_unit,"current_status","Reserved")

        invoice = frappe.get_doc({
            "doctype": "Rental Invoice",
            "rental_booking": self.name,
            "rental_amount": self.rental_total,
            "damage_amount": self.damage_total,
            "total_amount": self.final_amount
        })
        invoice.insert(ignore_permissions=True)
        frappe.enqueue(
            "rentflow.api.send_email",bookingid=self.name
        )
        
    def before_print(self):
        self.print_summary = (
            f"{self.customer_name} - "
            f"{self.start_date} to {self.end_date}"
        )
    def on_cancel(self):
        self.status = "Cancelled"
        for item in self.items:
            frappe.db.set_value(
                "Equipment Unit",
                item.equipment_unit,
                "current_status",
                "Available"
            )
        invoice_name = frappe.db.get_value(
            "Rental Invoice",
            {"rental_booking": self.name},
            "name"
        )
        if invoice_name:
            invoice = frappe.get_doc("Rental Invoice", invoice_name)
            if invoice.payment_status == "Unpaid" and invoice.docstatus == 1:
                invoice.cancel()
  
    def on_trash(self):
        if self.status not in ("Cancelled","Draft"):
           frappe.throw("Only Cancelled or Draft bookings can be deleted")
    def on_update(self):
        self.final_amount = self.rental_total + self.damage_total
    def on_update_after_submit(self):
        rank = {
            "New": 1,
            "Good": 2,
            "Fair": 3,
            "Poor": 4,
            "Damaged": 5
        }

        settings = frappe.get_single("Rentflow Settings")
        damage_rate = settings.damage_fee_per_grade_drop

        dtotal = 0

        for item in self.items:
            if (
                item.checkin_condition_grade
                and item.checkout_condition_grade
                and rank[item.checkin_condition_grade]
                > rank[item.checkout_condition_grade]
            ):
                diff = (
                    rank[item.checkin_condition_grade]
                    - rank[item.checkout_condition_grade]
                )

                item.damage_fee = damage_rate * diff
            else:
                item.damage_fee = 0

            dtotal += item.damage_fee

        self.damage_total = dtotal
        self.final_amount = self.rental_total + dtotal

        self.db_update()
        
        invoice_name = frappe.db.get_value(
            "Rental Invoice",
            {"rental_booking": self.name},
            "name"
        )

        if invoice_name:
            frappe.db.set_value(
                "Rental Invoice",
                invoice_name,
                {
                    "damage_amount": dtotal,
                    "total_amount": self.final_amount
                }
            )
        invoice = frappe.get_doc("Rental Invoice", invoice_name)

        if self.status == "Invoiced" and invoice.docstatus == 0:
            invoice.submit()
            
def get_permission_query_conditions(user):
        if "RF Inspector" in frappe.get_roles(user):
            return f"""
                `tabRental Booking`.handled_by IN (
                    SELECT name
                    FROM `tabYard Staff`
                    WHERE user = {frappe.db.escape(user)}
                )
            """

        return "" 