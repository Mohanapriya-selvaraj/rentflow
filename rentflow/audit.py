import frappe

def log_change(doc,method):
    newdoc=frappe.get_doc({
    "doctype":"Wildcard audit Log",
     "doctype_name":doc.doctype,
     "document_name":doc.name,
     "action":method,
     "user":frappe.session.user,
     "timestamp":frappe.utils.now()
    }
    )
    newdoc.insert()
            