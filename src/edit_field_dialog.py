from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QComboBox, QLineEdit, QPushButton, QStackedWidget

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

        self.value_stack.addWidget(self.text_input)
        self.value_stack.addWidget(self.boolean_combo)
        form.addRow("New value:", self.value_stack)

        layout.addLayout(form)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.accept)
        layout.addWidget(self.apply_button)

        self.field_combo.currentTextChanged.connect(self.update_value_widget)
        self.update_value_widget(self.field_combo.currentText())

    def populate_field_combo(self):
        if self.collection == "Company_Install":
            fields = ["Felderítés", "Telepítés", "Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        else:  # Company_Demolition
            fields = ["Bontás", "Felszerelés", "Bázis Leszerelés"]
        self.field_combo.addItems(fields)

    def update_value_widget(self, field):
        is_boolean = field in ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín", "Bázis Leszerelés"]
        self.value_stack.setCurrentIndex(1 if is_boolean else 0)

    def get_field_and_value(self):
        field = self.field_combo.currentText()
        if self.value_stack.currentIndex() == 1:  # Boolean value
            value = self.boolean_combo.currentText() == "Van"
        else:
            value = self.text_input.text()

        # Map the field names to their corresponding Firestore field names
        field_mapping = self.get_field_mapping()
        return field_mapping.get(field, field), value

    def get_field_mapping(self):
        if self.collection == "Company_Install":
            return {
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
                "Bontás": "1",
                "Felszerelés": "2",
                "Bázis Leszerelés": "3"
            }