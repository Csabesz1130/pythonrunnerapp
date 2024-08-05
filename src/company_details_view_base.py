from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
                             QCheckBox, QPushButton, QTextEdit, QMessageBox)
from PyQt6.QtCore import pyqtSignal
import logging

class CompanyDetailsViewBase(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, collection, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.company_id = company_id
        self.collection = collection
        self.company_data = {}
        self.setup_ui()
        self.load_company_data()

    def setup_ui(self):
        self.setWindowTitle("Company Details")
        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.form_layout.addRow("Company Name:", self.name_edit)

        self.program_combo = QComboBox()
        self.populate_programs()
        self.form_layout.addRow("Program:", self.program_combo)

        self.setup_specific_fields()

        layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_company)
        layout.addWidget(self.save_button)

    def populate_programs(self):
        try:
            programs = self.firestore_service.get_programs()
            self.program_combo.addItems(programs)
        except Exception as e:
            logging.error(f"Error populating programs: {e}")
            QMessageBox.warning(self, "Warning", "Failed to load programs. Some data may be missing.")

    def setup_specific_fields(self):
        # This method should be overridden in subclasses
        pass

    def load_company_data(self):
        if self.company_id:
            try:
                self.company_data = self.firestore_service.get_company(self.collection, self.company_id)
                if self.company_data:
                    self.populate_fields()
                else:
                    QMessageBox.warning(self, "Not Found", f"Company with ID {self.company_id} not found.")
            except Exception as e:
                logging.error(f"Error loading company data: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")

    def populate_fields(self):
        self.name_edit.setText(self.company_data.get("CompanyName", ""))
        self.program_combo.setCurrentText(self.company_data.get("ProgramName", ""))
        self.populate_specific_fields()

    def populate_specific_fields(self):
        # This method should be overridden in subclasses
        pass

    def save_company(self):
        updated_data = {
            "CompanyName": self.name_edit.text(),
            "ProgramName": self.program_combo.currentText(),
        }
        updated_data.update(self.get_specific_fields_data())

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

    def get_specific_fields_data(self):
        # This method should be overridden in subclasses
        return {}