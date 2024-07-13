from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
import logging

class CompanyDetailsViewBase(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, collection, company_id, parent=None, company_data=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.collection = collection
        self.company_id = company_id
        self.company_data = company_data or {}
        self.setup_ui()
        self.populate_festivals()
        if company_id and not company_data:
            self.load_company_data()
        self.update_ui_with_data()
        self.set_edit_mode(True if not company_id else False)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.id_label = QLabel()
        self.form_layout.addRow("ID:", self.id_label)

        self.name_edit = QLineEdit()
        self.form_layout.addRow("Company Name:", self.name_edit)

        self.program_combo = QComboBox()
        self.form_layout.addRow("Program:", self.program_combo)

        self.quantity_edit = QLineEdit()
        self.form_layout.addRow("Quantity:", self.quantity_edit)

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
        if self.collection == "Company_Install":
            self.setup_install_fields()
        else:
            self.setup_demolition_fields()

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            self.program_combo.clear()
            self.program_combo.addItems(festivals)
        except Exception as e:
            logging.error(f"Error populating festivals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load festivals: {str(e)}")

    def load_company_data(self):
        try:
            self.company_data = self.firestore_service.get_company(self.collection, self.company_id)
            self.update_ui_with_data()
        except Exception as e:
            logging.error(f"Error loading company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")

    def update_ui_with_data(self):
        self.id_label.setText(str(self.company_data.get("Id", "")))
        self.name_edit.setText(self.company_data.get("CompanyName", ""))
        self.quantity_edit.setText(str(self.company_data.get("quantity", "")))

        program_name = self.company_data.get("ProgramName", "")
        index = self.program_combo.findText(program_name)
        if index >= 0:
            self.program_combo.setCurrentIndex(index)
        elif program_name:
            self.program_combo.addItem(program_name)
            self.program_combo.setCurrentText(program_name)

        last_modified = self.company_data.get("LastModified")
        if last_modified:
            self.last_modified_label.setText(last_modified.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.last_modified_label.setText("")
        self.update_specific_fields()

    def set_edit_mode(self, editable):
        self.name_edit.setEnabled(editable)
        self.program_combo.setEnabled(editable)
        self.quantity_edit.setEnabled(editable)
        self.set_specific_fields_edit_mode(editable)
        self.save_button.setEnabled(editable)
        self.cancel_button.setEnabled(editable)
        self.edit_button.setEnabled(not editable)
        self.delete_button.setEnabled(not editable)

    def save_company(self):
        try:
            data = {
                "Id": self.company_id,
                "CompanyName": self.name_edit.text(),
                "ProgramName": self.program_combo.currentText(),
                "quantity": int(self.quantity_edit.text()) if self.quantity_edit.text() else None,
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
        except ValueError:
            QMessageBox.critical(self, "Error", "Quantity must be a valid integer or empty.")
        except Exception as e:
            logging.error(f"Error saving company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")

    def get_specific_fields_data(self):
        if self.collection == "Company_Install":
            return {
                "1": self.felderites_combo.currentText(),
                "2": self.telepites_combo.currentText(),
                "3": self.eloszto_check.isChecked(),
                "4": self.aram_check.isChecked(),
                "5": self.halozat_check.isChecked(),
                "6": self.ptg_check.isChecked(),
                "7": self.szoftver_check.isChecked(),
                "8": self.param_check.isChecked(),
                "9": self.helyszin_check.isChecked()
            }
        else:
            return {
                "1": self.bontas_combo.currentText(),
                "2": self.felszereles_combo.currentText(),
                "3": self.bazis_leszereles_check.isChecked()
            }

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
                logging.error(f"Error deleting company: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete company: {str(e)}")