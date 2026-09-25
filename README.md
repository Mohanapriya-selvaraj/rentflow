### Rentflow

A custom frappe app for a construction & event equipment rental

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch HEAD
bench install-app rentflow
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/rentflow
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
## B3 Dangerous Patterns — Document Lifecycle Bugs

### Bug 1: self.save() inside validate()

validate() is already called during the document save process.
Calling self.save() inside validate() causes recursive save and
validation calls.

### Bug 2: unit.save() inside validate()

Calling unit.save() inside validate() saves another document during the validation lifecycle. The Equipment Unit status should instead be
updated in an appropriate lifecycle event such as on_submit().

### Corrected Version
def validate(self):
    self.rental_total = sum(r.line_amount for r in self.items)


def on_submit(self):
    for item in self.items:
        frappe.db.set_value(
            "Equipment Unit",
            item.equipment_unit,
            "current_status",
            "Reserved"
        )
# B4 — Optimistic Locking

If two staff members open the same Rental Booking at the same time,
both initially have the same version of the document.

If Staff A saves the booking first, Frappe updates the document's
modification timestamp.

When Staff B tries to save the old version, Frappe detects that the
document was modified after Staff B opened it.

Frappe raises:

"Document has been modified after you have opened it"

This prevents Staff B's old data from silently overwriting Staff A's
changes.
# C3-Booking Item & Rental Invoice:
A test Yard Staff record was renamed using frappe rename_doc().
Yes, the handled_by field in linked Rental Booking records updates automatically.
This happens because handled_by is a Link field that references the Yard Staff DocType. When frappe.rename_doc() is used, Frappe updates the linked references to the new document name.
For example:
Before rename:
Yard Staff: STAFF-0001
Rental Booking handled_by: STAFF-0001
After rename:
Yard Staff: STAFF-0099
Rental Booking handled_by: STAFF-0099
Therefore, linked Rental Bookings continue to reference the renamed Yard Staff record.
# E1-Complete Lifecycle-On_update:
        def on_update(self):
            self.final_amount = self.rental_total + self.damage_total
            self.save()
    ->rentflow (app) Calling self.save() inside on_update() causes recursion because save() triggers on_update() again.save() triggers on_update() again.

Incorrect:

    def on_update(self):
        self.final_amount = self.rental_total + self.damage_total
        self.save()

The calculation should instead be performed during validate()
  def validate(self):
       self.final_amount = self.rental_total + self.damage_total

# E2-Autoname & Renaming

# Autoname
Equipment Unit overrides autoname() to generate the document name using the first three characters of the category followed by a five-digit naming series.

Example:

Generator -> GEN-00001
# Renaming
Yard Staff can be renamed using:
frappe.rename_doc(
    "Yard Staff",
    "STAFF-0001",
    "STAFF-0005",
    merge=False
)
merge=False performs a normal rename.

merge=True is used to merge the source document into an existing target document. It can affect the target document's existing data,so it should only be used when a merge is intentional.

# E3-One Performance Judgment Call

In on_update, I would use frappe.db.get_value() because only the low_availability_threshold value is required.
threshold = frappe.db.get_value(
    "RentFlow Settings",
    None,
    "low_availability_threshold"
)
# H2 - Rental Booking form script
frappe.call is asynchronous, so the validation may continue before the result comes back. Therefore, do the availability check in onload or refresh instead.
 # I-## SQL Parameterization

#### F-string version
today = frappe.utils.today()
query = f"""
SELECT name, customer_name, end_date, status, handled_by
FROM `tabRental Booking`
WHERE status = 'Checked Out'
AND end_date < '{today}'
"""
#### Parameterized version
today = frappe.utils.today()
query = """
SELECT name, customer_name, end_date, status, handled_by
FROM `tabRental Booking`
WHERE status = 'Checked Out'
AND end_date < %(today)s
"""
frappe.db.sql(query, {
    "today": today
})
The parameterized version is preferred because the SQL statement and the input values are kept separate. Values are passed as parameters instead of being directly inserted into the SQL string. This provides safer and more consistent handling of query values and avoids constructing SQL with f-strings.
# J -Print Format:
# Jinja Data Access

We can use frappe.get_all() directly inside the Jinja template to get data from the database. But this puts database logic inside the template.
Another way is to get the data in before_print() and store it in doc.precomputed_field. Then the Jinja template only displays the data.
This keeps the database logic in Python and the display logic in the Jinja template.
# K2 — Spot the N+1

The original code has an N+1 query problem. It first fetches all Rental Bookings, then runs a separate frappe.get_doc() query for each booking to fetch the Yard Staff.

For example, if there are 100 bookings, this can result in 101 database queries.

I fixed this by fetching the booking and staff details together using a SQL JOIN:

result = frappe.db.sql("""
    SELECT
        rb.name AS booking_name,
        ys.staff_name,
        ys.phone
    FROM `tabRental Booking` rb
    LEFT JOIN `tabYard Staff` ys
        ON ys.name = rb.handled_by
""", as_dict=True)

for row in result:
    print(row.staff_name, row.phone)
# N1-Security,Folded In:

There are 5 uses of ignore_permissions=True
1. In after_install(), it is used for Equipment Category.insert(ignore_permissions=True) to create the required default Equipment Categories during app installation.
2. In after_install(), it is used for RentFlow Settings.insert(ignore_permissions=True) to create the required RentFlow Settings during app installation.
3. In Rental Booking.on_submit(), it is used for Rental Invoice.insert(ignore_permissions=True) to automatically create the Rental Invoice when a booking is submitted.
4. flag_overdue_returns() uses ignore_permissions=True to create the daily audit record even when the scheduler user does not have permission to create Audit Log records.
These bypasses are used only for required installation,auto logging and booking operations.
5.log_change(doc,method)  
#### JavaScript Field Hiding
if (
    !frappe.user.has_role("RF Manager") &&
    !frappe.user.has_role("Administrator")
) {
    frm.set_df_property("customer_phone", "hidden", 1);
}
The customer_phone field is hidden for non-managers using JavaScript.
A direct API call can still retrieve the customer_phone field.
This shows that JavaScript only hides the field in the UI. It does not provide security. Actual security must be handled using server-side permissions.