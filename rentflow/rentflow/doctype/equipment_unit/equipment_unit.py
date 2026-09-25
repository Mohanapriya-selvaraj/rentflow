# Copyright (c) 2026, Mohanapriya S and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EquipmentUnit(Document):
  def autoname(self):
    self.name=frappe.model.naming.make_autoname(f"{self.category[:3].upper()}-.#####")  
