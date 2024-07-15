from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QComboBox, QCheckBox, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QDateTime
import logging

class CompanyDetailsViewInstall(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, parent=None, company_data=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.company_id = company_id
        self.company_data = company_data or {}
        self.is_new_company = not company_id
        logging.debug(f"Initializing CompanyDetailsViewInstall with company_id: {company_id}, company_data: {self.company_data}")
        self.setup_ui()
        self.populate_festivals()
        if not self.is_new_company:
            self.update_ui_with_data()
        self.set_edit_mode(True)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.id_label = QLineEdit()
        self.id_label.setReadOnly(True)
        form.addRow("ID:", self.id_label)

        self.name_edit = QLineEdit()
        form.addRow("Company Name:", self.name_edit)

        self.program_combo = QComboBox()
        form.addRow("Program:", self.program_combo)

        self.quantity_edit = QLineEdit()
        self.quantity_edit.setValidator(QIntValidator(0, 999999))
        form.addRow("Quantity:", self.quantity_edit)

        self.felderites_combo = QComboBox()
        self.felderites_combo.addItems(["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"])
        form.addRow("Felderítés:", self.felderites_combo)

        self.telepites_combo = QComboBox()
        self.telepites_combo.addItems(["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"])
        form.addRow("Telepítés:", self.telepites_combo)

        self.eloszto_check = QCheckBox()
        form.addRow("Elosztó:", self.eloszto_check)

        self.aram_check = QCheckBox()
        form.addRow("Áram:", self.aram_check)

        self.halozat_check = QCheckBox()
        form.addRow("Hálózat:", self.halozat_check)

        self.ptg_check = QCheckBox()
        form.addRow("PTG:", self.ptg_check)

        self.szoftver_check = QCheckBox()
        form.addRow("Szoftver:", self.szoftver_check)

        self.param_check = QCheckBox()
        form.addRow("Param:", self.param_check)

        self.helyszin_check = QCheckBox()
        form.addRow("Helyszín:", self.helyszin_check)

        self.last_modified_label = QLineEdit()
        self.last_modified_label.setReadOnly(True)
        form.addRow("Last Modified:", self.last_modified_label)

        layout.addLayout(form)

        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.enable_editing)
        button_layout.addWidget(self.edit_button)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_company)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_edit)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            self.program_combo.clear()
            self.program_combo.addItems(festivals)
            logging.info(f"Populated {len(festivals)} festivals in the combo box")
        except Exception as e:
            logging.error(f"Error populating festivals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load festivals: {str(e)}")

    def initialize_new_company(self):
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.company_data = {
            "Id": self.company_id,
            "CompanyName": "",
            "ProgramName": "",
            "1": "TELEPÍTHETŐ",
            "2": "KIADVA",
            "3": False,
            "4": False,
            "5": False,
            "6": False,
            "7": False,
            "8": False,
            "9": False,
            "LastModified": current_time,
            "CreatedAt": current_time
        }
        self.update_ui_with_data()

    def check_id_exists(self):
        new_id = self.id_edit.text()
        if new_id and self.is_new_company:
            exists = self.firestore_service.check_id_exists("Company_Install", new_id)
            if exists:
                self.id_edit.setStyleSheet("background-color: #FFCCCB;")
                QMessageBox.warning(self, "ID Exists", "This ID already exists. Please choose a different one.")
            else:
                self.id_edit.setStyleSheet("background-color: #90EE90;")

    def update_ui_with_data(self):
        self.id_label.setText(str(self.company_data.get("Id", "")))
        self.name_edit.setText(self.company_data.get("CompanyName", ""))
        self.name_edit.setReadOnly(False)  # Ensure Company Name is editable

        program_name = self.company_data.get("ProgramName", "")
        index = self.program_combo.findText(program_name)
        if index >= 0:
            self.program_combo.setCurrentIndex(index)
        elif program_name:
            self.program_combo.addItem(program_name)
            self.program_combo.setCurrentText(program_name)

        self.felderites_combo.setCurrentText(self.company_data.get("1", "TELEPÍTHETŐ"))
        self.telepites_combo.setCurrentText(self.company_data.get("2", "KIADVA"))
        self.eloszto_check.setChecked(self.company_data.get("3", False))
        self.aram_check.setChecked(self.company_data.get("4", False))
        self.halozat_check.setChecked(self.company_data.get("5", False))
        self.ptg_check.setChecked(self.company_data.get("6", False))
        self.szoftver_check.setChecked(self.company_data.get("7", False))
        self.param_check.setChecked(self.company_data.get("8", False))
        self.helyszin_check.setChecked(self.company_data.get("9", False))

        last_modified = self.company_data.get("LastModified", "")
        if isinstance(last_modified, QDateTime):
            last_modified = last_modified.toString("yyyy-MM-dd HH:mm:ss")
        self.last_modified_label.setText(str(last_modified))

        logging.debug(f"Updated UI with company data: {self.company_data}")

    def set_edit_mode(self, editable):
        self.name_edit.setEnabled(editable)
        self.program_combo.setEnabled(editable)
        self.felderites_combo.setEnabled(editable)
        self.telepites_combo.setEnabled(editable)
        self.eloszto_check.setEnabled(editable)
        self.aram_check.setEnabled(editable)
        self.halozat_check.setEnabled(editable)
        self.ptg_check.setEnabled(editable)
        self.szoftver_check.setEnabled(editable)
        self.param_check.setEnabled(editable)
        self.helyszin_check.setEnabled(editable)
        self.save_button.setEnabled(editable)
        self.cancel_button.setEnabled(editable)
        self.edit_button.setEnabled(not editable)

        logging.info(f"Edit mode set to: {editable}")

    def enable_editing(self):
        self.set_edit_mode(True)
        logging.info("Edit mode enabled")

    def cancel_edit(self):
        if self.company_id:
            self.load_company_data()
        else:
            self.close()
        self.set_edit_mode(False)
        logging.info("Edit cancelled, view mode restored")

    def load_company_data(self):
        try:
            self.company_data = self.firestore_service.get_company("Company_Install", self.company_id)
            if self.company_data is None:
                raise ValueError(f"No data found for company ID: {self.company_id}")
            self.update_ui_with_data()
        except Exception as e:
            logging.error(f"Error loading company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")
            self.close()

    def save_company(self):
        try:
            current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
            data = {
                "Id": self.company_id,
                "CompanyName": self.name_edit.text(),
                "ProgramName": self.program_combo.currentText(),
                "1": self.felderites_combo.currentText(),
                "2": self.telepites_combo.currentText(),
                "3": self.eloszto_check.isChecked(),
                "4": self.aram_check.isChecked(),
                "5": self.halozat_check.isChecked(),
                "6": self.ptg_check.isChecked(),
                "7": self.szoftver_check.isChecked(),
                "8": self.param_check.isChecked(),
                "9": self.helyszin_check.isChecked(),
                "LastModified": current_time
            }

            if "CreatedAt" not in self.company_data:
                data["CreatedAt"] = current_time

            self.firestore_service.update_company("Company_Install", self.company_id, data)
            logging.info(f"{'Updated' if 'CreatedAt' in self.company_data else 'Added new'} company with ID: {self.company_id}")

            self.company_data.update(data)  # Update local data
            self.set_edit_mode(False)
            self.update_ui_with_data()  # Refresh UI with updated data
            self.companyUpdated.emit(self.company_id)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
        except Exception as e:
            logging.error(f"Error saving company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")