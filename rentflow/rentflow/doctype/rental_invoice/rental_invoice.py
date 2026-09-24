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