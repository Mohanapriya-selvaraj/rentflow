# Copyright (c) 2026, Mohanapriya S and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RentalInvoice(Document):
	def autoname(self):
		self.invoice_number = frappe.model.naming.make_autoname(
			"INV-.YYYY.-.#####"
		)
		self.name = self.invoice_number
	def on_update_after_submit(self):
		if self.payment_status == "Paid":
			frappe.db.set_value(
				"Rental Booking",
				self.rental_booking,
				"payment_status",
				"Paid"
			)

			frappe.db.set_value(
				"Rental Booking",
				self.rental_booking,
				"status",
				"Closed"
			)