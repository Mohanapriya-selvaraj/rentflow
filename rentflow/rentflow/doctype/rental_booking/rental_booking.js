// Copyright (c) 2026, Mohanapriya S and contributors
// For license information, please see license.txt




frappe.ui.form.on("Rental Booking", {
setup(frm) {
    frm.set_query("equipment_unit", "items", function(doc, cdt, cdn) {

        if (frm.is_new()) {
            return {
                filters: {
                    current_status: "Available"
                }
            };
        }
        const selected_units = (doc.items || [])
            .filter(row => row.name !== cdn)
            .map(row => row.equipment_unit)
            .filter(Boolean);

        if (!selected_units.length) {
            return {
                filters: {
                    current_status: "Available"
                }
            };
        }
        return {
            or_filters: [
                ["current_status", "=", "Available"],
                ["name", "in", selected_units]
            ]
        };
    });
},
 	refresh(frm) {
        if (!frappe.user.has_role("RF Manager")) {
       frm.set_df_property("customer_phone", "hidden", 1);
     }
        const colors = {
            "Draft": "gray",
            "Confirmed": "blue",
            "Checked Out": "orange",
            "Returned": "green",
            "Invoiced": "purple",
            "Closed": "green",
            "Cancelled": "red"
        };

        if (frm.doc.status) {
            frm.dashboard.add_indicator(
                __(frm.doc.status),
                colors[frm.doc.status] || "gray"
            );
        }

        if (frm.doc.status === "Checked Out") {
         frm.add_custom_button(__("Log Return"), function() {
            show_return_dialog(frm);
        });
    }
         frm.add_custom_button(__("Transfer Handler"), function() {
            frappe.prompt(
            [
                {
                    fieldname: "handler",
                    fieldtype: "Link",
                    label:"New Handler",
                    options: "Yard Staff",
                    reqd: 1
                }
            ],
            function(values) {
                frappe.confirm(
                    __("Are you sure you want to transfer this booking to {0}?", [values.handler]),
                    function() {
                        frappe.call({
                            method: "rentflow.api.transfer_handler",
                            args: {
                                booking: frm.doc.name,
                                new_handler: values.handler
                            },
                            callback: function(r) {
                                console.log(r.message);
                                frm.reload_doc();
                            }
                        });
    }
                );
            },
            __("Transfer Handler"),
            __("Continue")
        );
    });

    if (frm.doc.docstatus === 1) {
        frm.add_custom_button("View Rental Invoice", function () {
            frappe.db.get_value(
                "Rental Invoice",
                { rental_booking: frm.doc.name },
                "name"
            ).then(r => {
                if (r.message && r.message.name) {
                    frappe.set_route(
                        "Form",
                        "Rental Invoice",
                        r.message.name
                    );
                } else {
                    frappe.msgprint("Rental Invoice not found.");
                }
            });
        });
    }
 	},
    start_date(frm) {
    check_rental_period(frm);
            },

    end_date(frm) {
        check_rental_period(frm);
    },
    
    
 });

 function check_rental_period(frm) {
    if (!frm.doc.start_date || !frm.doc.end_date) {
        return;
    }

    const days = frappe.datetime.get_diff(
        frm.doc.end_date,
        frm.doc.start_date
    );

    if (days > 30) {
        frappe.show_alert({
            message: __("Rental period is more than 30 days."),
            indicator: "orange"
        });
    }
}

function show_return_dialog(frm) {
    const fields = [];

    (frm.doc.items || []).forEach((row) => {
        fields.push({
            fieldname:row.name,
            fieldtype: "Select",
            label: row.equipment_unit,
            options: ["New", "Good", "Fair", "Poor", "Damaged"].join("\n"),
            reqd: 1
        });
    });

    fields.push({
        fieldname: "notes",
        fieldtype: "Small Text",
        label: __("Notes")
    });

    const dialog = new frappe.ui.Dialog({
        title: "Log Return",
        fields: fields,
        primary_action_label:"Submit",
        primary_action(values) {
                    const grades = {
                        "New":1,
                        "Good":2, 
                        "Fair":3,
                         "Poor":4, 
                         "Damaged":5};

                    let grade_dropped = false;

                    (frm.doc.items || []).forEach((row) => {
                        const checkout_grade = row.checkout_condition_grade;
                        const checkin_grade = values[row.name];

                        if (grades[checkin_grade] > grades[checkout_grade]) {
                            grade_dropped = true;
                        }
                    });
                    if (grade_dropped && !values.notes) {
                        frappe.msgprint(("Notes are mandatory when the condition grade is dropped."));
                        return;
                    }

                    (frm.doc.items || []).forEach((row) => {
                    frappe.model.set_value(
                        row.doctype,
                        row.name,
                        "checkin_condition_grade",
                        values[row.name]
                    );
                    const checkout_grade = row.checkout_condition_grade;
                    const checkin_grade = values[row.name];
                    const checkout= grades[checkout_grade];
                    const checkin = grades[checkin_grade];

                    const grade_drop = checkin - checkout;

                    if (grade_drop > 0) {
                        frappe.model.set_value(
                            row.doctype,
                            row.name,
                            "damage_fee",
                            grade_drop * 500
                        );
                    } else {
                        frappe.model.set_value(
                            row.doctype,
                            row.name,
                            "damage_fee",
                            0
                        );
                    }
                    });
                    frm.trigger("start_date");
                    dialog.hide();
                    
                }
    });
    dialog.show();
}

frappe.ui.form.on("Booking Item", {
    quantity(frm, cdt, cdn) {
        calculate_line_amount(frm, cdt, cdn);
    },

    start_date(frm, cdt, cdn) {
        calculate_line_amount(frm, cdt, cdn);
    },

    end_date(frm, cdt, cdn) {
        calculate_line_amount(frm, cdt, cdn);
    }
});

function calculate_line_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];

    if (!row.quantity || !row.daily_rate || !row.start_date || !row.end_date) {
        frappe.throw("Enter the details correctely...")
    }

    let days = frappe.datetime.get_diff(
        row.end_date,
        row.start_date
    )+1;

    let amount =row.daily_rate * days * row.quantity;

    frappe.model.set_value(
        cdt,
        cdn,
        "line_amount",
        amount
    );
}
