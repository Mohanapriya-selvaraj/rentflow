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
            "Rented"
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

