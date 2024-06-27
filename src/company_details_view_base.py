from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime

class CompanyDetailsViewBase(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, collection, company_id=None, parent=None):
        super().__init__(parent)
        self.setGeometry(200, 200, 600, 800)
        self.firestore_service = firestore_service
        self.collection = collection
        self.company_id = company_id
        self.company_data = {}
        self.setup_ui()
        if company_id:
            self.load_company_data()
        else:
            self.id_label.setText(company_id)  # Set the new ID in the UI
            self.set_edit_mode(True if not company_id else False)  # Set to edit mode for new companies

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.id_label = QLabel()
        self.form_layout.addRow("ID:", self.id_label)

        self.name_edit = QLineEdit()
        self.form_layout.addRow("Company Name:", self.name_edit)

        self.program_edit = QLineEdit()
        self.form_layout.addRow("Program:", self.program_edit)

        self.setup_specific_fields()

        self.last_modified_label = QLabel()
        self.form_layout.addRow("Last Modified:", self.last_modified_label)

        main_layout.addLayout(self.form_layout)

        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(lambda: self.set_edit_mode(True))
        button_layout.addWidget(self.edit_button)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_company)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_edit)
        button_layout.addWidget(self.cancel_button)

        self.delete_button = QPushButton("Delete Company")
        self.delete_button.clicked.connect(self.delete_company)
        button_layout.addWidget(self.delete_button)

        main_layout.addLayout(button_layout)

    def setup_specific_fields(self):
        pass

    def load_company_data(self):
        try:
            self.company_data = self.firestore_service.get_company(self.collection, self.company_id)
            self.update_ui_with_data()
        except Exception as e:
            print(f"Error loading company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")

    def update_ui_with_data(self):
        self.id_label.setText(str(self.company_data.get("Id", "")))
        self.name_edit.setText(self.company_data.get("CompanyName", ""))
        self.program_edit.setText(self.company_data.get("ProgramName", ""))
        last_modified = self.company_data.get("LastModified")
        if last_modified:
            self.last_modified_label.setText(last_modified.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.last_modified_label.setText("")
        self.update_specific_fields()

    def update_specific_fields(self):
        pass

    def set_edit_mode(self, editable):
        self.name_edit.setEnabled(editable)
        self.program_edit.setEnabled(editable)
        self.set_specific_fields_edit_mode(editable)
        self.save_button.setEnabled(editable)
        self.cancel_button.setEnabled(editable)
        self.edit_button.setEnabled(not editable)
        self.delete_button.setEnabled(not editable)

    def set_specific_fields_edit_mode(self, editable):
        pass

    def save_company(self):
        try:
            data = {
                "Id": self.company_id,
                "CompanyName": self.name_edit.text(),
                "ProgramName": self.program_edit.text(),
                "LastModified": datetime.now()
            }
            data.update(self.get_specific_fields_data())

            if self.company_id:
                self.firestore_service.update_company(self.collection, self.company_id, data)
            else:
                self.company_id = self.firestore_service.add_company(self.collection, data)

            self.set_edit_mode(False)
            self.load_company_data()
            self.companyUpdated.emit(self.company_id)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
        except Exception as e:
            print(f"Error saving company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")

    def get_specific_fields_data(self):
        return {}

    def cancel_edit(self):
        if self.company_id:
            self.load_company_data()
        else:
            self.close()
        self.set_edit_mode(False)

    def delete_company(self):
        if not self.company_id:
            return

        reply = QMessageBox.question(self, "Delete Company", "Are you sure you want to delete this company?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.firestore_service.delete_company(self.collection, self.company_id)
                QMessageBox.information(self, "Success", "Company deleted successfully!")
                self.companyUpdated.emit(self.company_id)
                self.accept()
            except Exception as e:
                print(f"Error deleting company: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete company: {str(e)}")