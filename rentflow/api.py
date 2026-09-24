import frappe
import frappe.share
from frappe.query_builder import DocType
from frappe.utils import today

@frappe.whitelist()
def share_booking(booking_name, user_email):
    frappe.share.add(
        "Rental Booking",
        booking_name,
        user_email,
        read=1,
        write=0
    )

    return {"message": "Booking shared successfully"}

@frappe.whitelist()
def unsafe_get_booking(booking_name):
    booking = frappe.get_doc("Rental Booking", booking_name)
    return booking.as_dict()

@frappe.whitelist()
def safe_get_booking(booking_name):
    bookings = frappe.get_list(
        "Rental Booking",
        filters={"name": booking_name},
        fields=[
            "name",
            "customer_name",
            "customer_phone",
            "customer_email",
            "start_date",
            "end_date",
            "status"
        ]
    )
    if not bookings:
        return None
    booking = bookings[0]
    if "RF Manager" not in frappe.get_roles():
        booking.pop("customer_phone", None)
        booking.pop("customer_email", None)

    return booking

def send_email(bookingid):
    booking=frappe.get_doc("Rental Booking",bookingid)
    if not booking.customer_email:
        return 
    frappe.sendmail(
        recipients=[booking.customer_email],
        subject=f"Booking Confirmation -{booking.name}",
        message=f"""
        <p>Your rental booking <b>{booking.name}</b> has been confirmed.</p>
        <p>Rental Total: {booking.rental_total}</p>
        <p>Deposit Amount: {booking.deposit_collected}</p>
        <p>Status: {booking.status}</p>
        """
    )
@frappe.whitelist()
def rename_yard_staff(old_name, new_name):
        return frappe.rename_doc(
            "Yard Staff",
            old_name,
            new_name,
            merge=False
        )
   
@frappe.whitelist()
def get_overdue_returns():
    RB = DocType("Rental Booking")

    result = (
        frappe.qb
        .from_(RB)
        .select(
            RB.name,
            RB.customer_name,
            RB.end_date
        )
        .where(
            (RB.status == "Checked Out")
            & (RB.end_date < today())
        )
        .orderby(RB.end_date)
        .run(as_dict=True)
    )

    return result
@frappe.whitelist()
def reassign_bookings(from_staff, to_staff):
    try:
        frappe.db.sql("""
            UPDATE `tabRental Booking`
            SET handled_by = %s
            WHERE handled_by = %s
            AND status NOT IN ('Returned', 'Cancelled', 'Closed')
        """, (to_staff, from_staff))

        frappe.db.commit()

    except Exception:
        frappe.db.rollback()
        frappe.log_error(
            frappe.get_traceback(),
            "Reassignment Failed"
        )
        raise