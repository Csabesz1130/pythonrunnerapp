# File: src/ui/add_company_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QComboBox, QMessageBox)
from PyQt6.QtCore import pyqtSignal

class AddCompanyDialog(QDialog):
    companyAdded = pyqtSignal(dict)

    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.setWindowTitle("Add New Company")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Company Name
        self.name_edit = QLineEdit(self)
        form_layout.addRow("Company Name:", self.name_edit)

        # Program Name (as a dropdown)
        self.program_combo = QComboBox(self)
        self.load_programs()
        form_layout.addRow("Program:", self.program_combo)

        # Quantity
        self.quantity_edit = QLineEdit(self)
        self.quantity_edit.setPlaceholderText("Enter a number")
        form_layout.addRow("Quantity:", self.quantity_edit)

        # Status fields
        self.felderites_combo = QComboBox(self)
        self.felderites_combo.addItems(["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"])
        form_layout.addRow("Felderítés:", self.felderites_combo)

        self.telepites_combo = QComboBox(self)
        self.telepites_combo.addItems(["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"])
        form_layout.addRow("Telepítés:", self.telepites_combo)

        # Boolean fields
        for field in ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]:
            combo = QComboBox(self)
            combo.addItems(["Igen", "Nem"])
            form_layout.addRow(f"{field}:", combo)
            setattr(self, f"{field.lower()}_combo", combo)

        layout.addLayout(form_layout)

        # Submit button
        self.submit_button = QPushButton("Add Company", self)
        self.submit_button.clicked.connect(self.add_company)
        layout.addWidget(self.submit_button)

    def load_programs(self):
        try:
            programs = self.firestore_service.get_programs()
            self.program_combo.addItems(programs)
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to load programs: {str(e)}")

    def add_company(self):
        try:
            new_company = {
                "CompanyName": self.name_edit.text(),
                "ProgramName": self.program_combo.currentText(),
                "quantity": int(self.quantity_edit.text()) if self.quantity_edit.text() else None,
                "1": self.felderites_combo.currentText(),
                "2": self.telepites_combo.currentText(),
                "3": self.eloszto_combo.currentText() == "Igen",
                "4": self.aram_combo.currentText() == "Igen",
                "5": self.halozat_combo.currentText() == "Igen",
                "6": self.ptg_combo.currentText() == "Igen",
                "7": self.szoftver_combo.currentText() == "Igen",
                "8": self.param_combo.currentText() == "Igen",
                "9": self.helyszin_combo.currentText() == "Igen",
            }

            # Validate data
            if not new_company["CompanyName"]:
                raise ValueError("Company Name is required")

            # Add to Firestore
            doc_ref = self.firestore_service.add_company("Company_Install", new_company)
            new_company["Id"] = doc_ref  # Assuming add_company returns the new document ID

            self.companyAdded.emit(new_company)
            QMessageBox.information(self, "Success", "Company added successfully!")
            self.accept()
        except ValueError as ve:
            QMessageBox.warning(self, "Input Error", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add company: {str(e)}")