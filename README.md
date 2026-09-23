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