import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
                             QCheckBox, QComboBox, QTextEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from src.company_details_view_base import CompanyDetailsViewBase

class CompanyDetailsView(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Company Details - Demolition")
        self.setGeometry(200, 200, 600, 800)
        self.firestore_service = firestore_service
        self.company_id = company_id
        self.company_data = {}
        self.setup_ui()
        if company_id:
            self.load_company_data()
        self.set_edit_mode(False)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.id_label = QLabel()
        form_layout.addRow("ID:", self.id_label)

        self.name_edit = QLineEdit()
        form_layout.addRow("Company Name:", self.name_edit)

        self.program_edit = QLineEdit()
        form_layout.addRow("Program:", self.program_edit)

        self.bontas_combo = QComboBox()
        self.bontas_combo.addItems(["Bontható", "Még Nyitva", "Nem Hozzáférhető"])
        form_layout.addRow("Field 1 (Bontás):", self.bontas_combo)

        self.felszereles_combo = QComboBox()
        self.felszereles_combo.addItems(["CSOMAGOLVA", "SZÁLLÍTÁSRA_VÁR", "ELSZÁLLÍTVA", "NINCS_STATUSZ"])
        form_layout.addRow("Felszerelés:", self.felszereles_combo)

        self.bazis_leszereles_check = QCheckBox()
        form_layout.addRow("Bázis Leszerelés:", self.bazis_leszereles_check)

        self.last_modified_label = QLabel()
        form_layout.addRow("Last Modified:", self.last_modified_label)

        main_layout.addLayout(form_layout)

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

    def load_company_data(self):
        try:
            self.company_data = self.firestore_service.get_company("Company_Demolition", self.company_id)
            self.update_ui_with_data()
        except Exception as e:
            logging.error(f"Error loading company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")

    def update_ui_with_data(self):
        self.id_label.setText(str(self.company_data.get("Id", "")))
        self.name_edit.setText(self.company_data.get("CompanyName", ""))
        self.program_edit.setText(self.company_data.get("ProgramName", ""))
        self.bontas_combo.setCurrentText(self.company_data.get("1", "Bontható"))
        self.felszereles_combo.setCurrentText(self.company_data.get("Felszerelés", "NINCS_STATUSZ"))
        self.bazis_leszereles_check.setChecked(self.company_data.get("Bázis Leszerelés", False))
        last_modified = self.company_data.get("LastModified")
        if last_modified:
            self.last_modified_label.setText(last_modified.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.last_modified_label.setText("")

    def set_edit_mode(self, editable):
        self.name_edit.setEnabled(editable)
        self.program_edit.setEnabled(editable)
        self.bontas_combo.setEnabled(editable)
        self.felszereles_combo.setEnabled(editable)
        self.bazis_leszereles_check.setEnabled(editable)
        self.save_button.setEnabled(editable)
        self.cancel_button.setEnabled(editable)
        self.edit_button.setEnabled(not editable)
        self.delete_button.setEnabled(not editable)

    def save_company(self):
        try:
            data = {
                "CompanyName": self.name_edit.text(),
                "ProgramName": self.program_edit.text(),
                "Field 1": self.bontas_combo.currentText(),
                "Felszerelés": self.felszereles_combo.currentText(),
                "Bázis Leszerelés": self.bazis_leszereles_check.isChecked(),
                "LastModified": datetime.now()
            }

            if self.company_id:
                self.firestore_service.update_company("Company_Demolition", self.company_id, data)
            else:
                self.company_id = self.firestore_service.add_company("Company_Demolition", data)

            self.set_edit_mode(False)
            self.load_company_data()  # Refresh data after save
            self.companyUpdated.emit(self.company_id)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
        except Exception as e:
            logging.error(f"Error saving company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")

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
                self.firestore_service.delete_company("Company_Demolition", self.company_id)
                QMessageBox.information(self, "Success", "Company deleted successfully!")
                self.companyUpdated.emit(self.company_id)
                self.accept()  # Close the dialog
            except Exception as e:
                logging.error(f"Error deleting company: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete company: {str(e)}")