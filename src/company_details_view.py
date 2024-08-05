from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
                             QCheckBox, QPushButton, QTextEdit, QMessageBox)
from PyQt6.QtCore import pyqtSignal
import logging

class CompanyDetailsView(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, collection, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.company_id = company_id
        self.collection = collection
        self.company_data = {}
        self.fields = {}
        self.field_mapping = self.get_field_mapping(collection)
        self.setup_ui()
        self.load_company_data()

    def get_field_mapping(self, collection):
        # This should be the same as in DynamicFirestoreModel
        common_fields = {
            "Id": "ID",
            "CompanyName": "Name",
            "ProgramName": "Program",
            "LastAdded": "LastAdded",
            "LastModified": "Last Modified"
        }

        if collection == "Company_Install":
            specific_fields = {
                "quantity": "Igény",
                "SN": "Kiadott",
                "1": "Felderítés",
                "2": "Telepítés",
                "3": "Elosztó",
                "4": "Áram",
                "5": "Hálózat",
                "6": "PTG",
                "7": "Szoftver",
                "8": "Param",
                "9": "Helyszín",
            }
        elif collection == "Company_Demolition":
            specific_fields = {
                "1": "Bontás",
                "2": "Felszerelés",
                "3": "Bázis Leszerelés",
            }
        else:
            logging.warning(f"Unknown collection: {collection}")
            specific_fields = {}

        return {**common_fields, **specific_fields}

    def setup_ui(self):
        self.setWindowTitle("Company Details")
        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_company)
        layout.addWidget(self.save_button)

    def create_dynamic_fields(self):
        for key, value in self.company_data.items():
            field_name = self.field_mapping.get(key, key)

            if key in ['Id', 'CreatedAt', 'LastModified', 'LastAdded']:
                field = QLineEdit()
                field.setReadOnly(True)
            elif isinstance(value, bool):
                field = QCheckBox()
            elif isinstance(value, (int, float)):
                field = QLineEdit()
                field.setValidator(QDoubleValidator() if isinstance(value, float) else QIntValidator())
            elif key in ['1', '2']:  # Assuming these are combo box fields
                field = QComboBox()
                field.addItems(["", "TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"])
            else:
                field = QLineEdit()

            self.fields[key] = field
            self.form_layout.addRow(field_name, field)

    def populate_fields(self):
        for key, field in self.fields.items():
            value = self.company_data.get(key, '')
            if isinstance(field, QLineEdit):
                field.setText(str(value))
            elif isinstance(field, QCheckBox):
                field.setChecked(bool(value))
            elif isinstance(field, QComboBox):
                index = field.findText(str(value))
                if index >= 0:
                    field.setCurrentIndex(index)

    def load_company_data(self):
        if self.company_id:
            try:
                self.company_data = self.firestore_service.get_company(self.collection, self.company_id)
                if self.company_data:
                    self.create_dynamic_fields()
                    self.populate_fields()
                else:
                    QMessageBox.warning(self, "Not Found", f"Company with ID {self.company_id} not found.")
            except Exception as e:
                logging.error(f"Error loading company data: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")

    def save_company(self):
        updated_data = {}
        for key, field in self.fields.items():
            if isinstance(field, QLineEdit):
                updated_data[key] = field.text()
            elif isinstance(field, QCheckBox):
                updated_data[key] = field.isChecked()
            elif isinstance(field, QComboBox):
                updated_data[key] = field.currentText()

        try:
            if self.company_id:
                self.firestore_service.update_company(self.collection, self.company_id, updated_data)
            else:
                self.company_id = self.firestore_service.add_company(self.collection, updated_data)

            self.companyUpdated.emit(self.company_id)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
            self.accept()
        except Exception as e:
            logging.error(f"Error saving company data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")