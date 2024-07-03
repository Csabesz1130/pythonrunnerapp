from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt

class EditFieldDialog(QDialog):
    def __init__(self, collection, parent=None):
        super().__init__(parent)
        self.collection = collection
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.field_combo = QComboBox()
        self.populate_field_combo()
        form.addRow("Field:", self.field_combo)

        self.value_stack = QStackedWidget()
        self.text_input = QLineEdit()
        self.boolean_combo = QComboBox()
        self.boolean_combo.addItems(["Van", "Nincs"])
        self.option_combo = QComboBox()

        self.value_stack.addWidget(self.text_input)
        self.value_stack.addWidget(self.boolean_combo)
        self.value_stack.addWidget(self.option_combo)
        form.addRow("New value:", self.value_stack)

        layout.addLayout(form)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.accept)
        layout.addWidget(self.apply_button)

        self.field_combo.currentTextChanged.connect(self.update_value_widget)
        self.update_value_widget(self.field_combo.currentText())

    def populate_field_combo(self):
        fields = self.get_field_mapping().keys()
        self.field_combo.addItems(fields)

    def update_value_widget(self, field):
        boolean_fields = ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín", "Bázis Leszerelés"]
        option_fields = {
            "Felderítés": ["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"],
            "Telepítés": ["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"],
            "Bontás": ["BONTHATO", "MEG_NYITVA", "NEM_HOZZAFERHETO"],
            "Felszerelés": ["CSOMAGOLVA", "SZALLITASRA_VAR", "ELSZALLITVA", "NINCS_STATUSZ"]
        }

        if field in boolean_fields:
            self.value_stack.setCurrentWidget(self.boolean_combo)
        elif field in option_fields:
            self.option_combo.clear()
            self.option_combo.addItems(option_fields[field])
            self.value_stack.setCurrentWidget(self.option_combo)
        else:
            self.value_stack.setCurrentWidget(self.text_input)

    def get_field_and_value(self):
        field = self.field_combo.currentText()
        field_mapping = self.get_field_mapping()
        db_field = field_mapping[field]

        if self.value_stack.currentWidget() == self.boolean_combo:
            value = self.boolean_combo.currentText() == "Van"
        elif self.value_stack.currentWidget() == self.option_combo:
            value = self.option_combo.currentText()
        else:
            value = self.text_input.text()

        return field, value  # Return the display field name, not the db_field

    def get_field_mapping(self):
        if self.collection == "Company_Install":
            return {
                "CompanyName": "CompanyName",
                "ProgramName": "ProgramName",
                "Felderítés": "1",
                "Telepítés": "2",
                "Elosztó": "3",
                "Áram": "4",
                "Hálózat": "5",
                "PTG": "6",
                "Szoftver": "7",
                "Param": "8",
                "Helyszín": "9"
            }
        else:  # Company_Demolition
            return {
                "CompanyName": "CompanyName",
                "ProgramName": "ProgramName",
                "Bontás": "1",
                "Felszerelés": "2",
                "Bázis Leszerelés": "3"
            }