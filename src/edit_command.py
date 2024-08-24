class EditCommand:
    def __init__(self, companies, field, old_values, new_value):
        self.companies = companies
        self.field = field
        self.old_values = old_values
        self.new_value = new_value

    def execute(self):
        for company in self.companies:
            company[self.field] = self.new_value

    def undo(self):
        for company, old_value in zip(self.companies, self.old_values):
            company[self.field] = old_value