from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QComboBox, QCheckBox, QMessageBox, QTextEdit, QMenu)
from PyQt6.QtCore import pyqtSignal, QDateTime, Qt
import logging
from datetime import datetime

from google.cloud.firestore_v1 import SERVER_TIMESTAMP


class CompanyDetailsViewInstall(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, parent=None, company_data=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.company_id = company_id
        self.company_data = company_data or {}
        self.is_new_company = company_id is None
        self.setup_ui()
        self.populate_festivals()
        if self.is_new_company:
            self.initialize_new_company()
        else:
            self.load_company_data()
        self.update_ui_with_data()
        self.set_edit_mode(True if self.is_new_company else False)

        # Enable context menu for right-click
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def load_company_data(self):
        if self.company_id:
            self.company_data = self.firestore_service.get_company("Company_Install", self.company_id)
            if self.company_data is None:
                logging.error(f"Failed to load company data for ID: {self.company_id}")
                QMessageBox.critical(self, "Error", f"Failed to load company data for ID: {self.company_id}")
                self.close()


    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        form.addRow("ID:", self.id_edit)

        self.name_edit = QLineEdit()
        form.addRow("Company Name:", self.name_edit)

        self.program_combo = QComboBox()
        form.addRow("Program:", self.program_combo)

        self.quantity_edit = QLineEdit()
        self.quantity_edit.setValidator(QIntValidator(0, 999999))
        form.addRow("Igény:", self.quantity_edit)

        self.kiadott_label = QLineEdit()
        self.kiadott_label.setReadOnly(True)
        form.addRow("Kiadott:", self.kiadott_label)

        self.sn_edit = QTextEdit()
        form.addRow("SN:", self.sn_edit)

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

        self.setLayout(layout)

    def update_ui_with_data(self):
        logging.info(f"Updating UI with data for company ID: {self.company_id}")

        if not self.company_data:
            logging.warning("No company data available to update UI")
            return

        # Update basic company information
        self.id_edit.setText(str(self.company_data.get("Id", "")))
        self.name_edit.setText(self.company_data.get("CompanyName", ""))

        # Update program selection
        program_name = self.company_data.get("ProgramName", "")
        index = self.program_combo.findText(program_name)
        if index >= 0:
            self.program_combo.setCurrentIndex(index)
        elif program_name:
            self.program_combo.addItem(program_name)
            self.program_combo.setCurrentText(program_name)

        # Update quantity
        quantity = self.company_data.get("quantity")
        self.quantity_edit.setText(str(quantity) if quantity is not None else "")

        # Handle SN list
        sn_list = self.firestore_service.get_sn_list(self.company_data)
        if sn_list:
            self.sn_edit.setPlainText("\n".join(sn_list))
            self.kiadott_label.setText(str(len(sn_list)))
        else:
            self.sn_edit.setPlainText("No SN entries available")
            self.kiadott_label.setText(str(self.company_data.get("sn_count", 0)))

        # Update other fields
        self.felderites_combo.setCurrentText(self.company_data.get("1", "TELEPÍTHETŐ"))
        self.telepites_combo.setCurrentText(self.company_data.get("2", "KIADVA"))
        self.eloszto_check.setChecked(self.company_data.get("3", False))
        self.aram_check.setChecked(self.company_data.get("4", False))
        self.halozat_check.setChecked(self.company_data.get("5", False))
        self.ptg_check.setChecked(self.company_data.get("6", False))
        self.szoftver_check.setChecked(self.company_data.get("7", False))
        self.param_check.setChecked(self.company_data.get("8", False))
        self.helyszin_check.setChecked(self.company_data.get("9", False))

        # Update Last Modified field
        last_modified = self.company_data.get("LastModified", "")
        if last_modified:
            if isinstance(last_modified, datetime):
                last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(last_modified, str):
                try:
                    last_modified_dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                    last_modified_str = last_modified_dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    last_modified_str = last_modified  # Keep it as is if parsing fails
            elif last_modified == SERVER_TIMESTAMP:
                last_modified_str = "Pending server update"
            else:
                last_modified_str = str(last_modified)
        else:
            last_modified_str = ""

        self.last_modified_label.setText(last_modified_str)

        logging.debug(f"Updated UI with company data: {self.company_data}")
        logging.info("Finished updating UI")

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
        self.company_data = {
            "Id": "",  # This will be set when saving
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
            "LastModified": None,  # Set to None for new companies
            "CreatedAt": None  # Set to None, will be updated when saving
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

    def fetch_sn_list(self):
        if not self.company_id:
            QMessageBox.warning(self, "Warning", "Please save the company first.")
            return

        try:
            sn_list = self.firestore_service.get_sn_list(self.company_id)
            self.sn_edit.setPlainText("\n".join(sn_list))
            self.kiadott_label.setText(str(len(sn_list)))
            QMessageBox.information(self, "Success", f"Fetched {len(sn_list)} SN entries.")
        except Exception as e:
            logging.error(f"Error fetching SN list: {e}")
            QMessageBox.critical(self, "Error", f"Failed to fetch SN list: {str(e)}")

    def show_context_menu(self, position):
        context_menu = QMenu(self)
        fetch_sn_action = context_menu.addAction("Fetch SN List")
        action = context_menu.exec(self.mapToGlobal(position))
        if action == fetch_sn_action:
            self.fetch_sn_list()

    def update_ui_with_data(self):
        logging.info(f"Updating UI with data for company ID: {self.company_id}")

        if not isinstance(self.company_data, dict):
            logging.error(f"Invalid company data type: {type(self.company_data)}")
            QMessageBox.critical(self, "Error", "Invalid company data format")
            return

        if not self.company_data:
            logging.warning("No company data available to update UI")
            return

        try:
            # Update basic company information
            self.id_edit.setText(str(self.company_data.get("Id", "")))
            self.name_edit.setText(self.company_data.get("CompanyName", ""))

            # Update program selection
            program_name = self.company_data.get("ProgramName", "")
            index = self.program_combo.findText(program_name)
            if index >= 0:
                self.program_combo.setCurrentIndex(index)
            elif program_name:
                self.program_combo.addItem(program_name)
                self.program_combo.setCurrentText(program_name)

            # Update quantity
            quantity = self.company_data.get("quantity")
            self.quantity_edit.setText(str(quantity) if quantity is not None else "")

            # Handle SN list
            sn_list = self.firestore_service.get_sn_list(self.company_data.get('firestore_id'))
            if sn_list:
                self.sn_edit.setPlainText("\n".join(sn_list))
                self.kiadott_label.setText(str(len(sn_list)))
            else:
                self.sn_edit.setPlainText("No SN entries available")
                self.kiadott_label.setText("0")

            # Update other fields
            self.felderites_combo.setCurrentText(self.company_data.get("1", "TELEPÍTHETŐ"))
            self.telepites_combo.setCurrentText(self.company_data.get("2", "KIADVA"))
            self.eloszto_check.setChecked(self.company_data.get("3", False))
            self.aram_check.setChecked(self.company_data.get("4", False))
            self.halozat_check.setChecked(self.company_data.get("5", False))
            self.ptg_check.setChecked(self.company_data.get("6", False))
            self.szoftver_check.setChecked(self.company_data.get("7", False))
            self.param_check.setChecked(self.company_data.get("8", False))
            self.helyszin_check.setChecked(self.company_data.get("9", False))

            # Update Last Modified field
            last_modified = self.company_data.get("LastModified", "")
            if last_modified:
                if isinstance(last_modified, datetime):
                    last_modified_str = last_modified.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(last_modified, str):
                    try:
                        last_modified_dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                        last_modified_str = last_modified_dt.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        last_modified_str = last_modified  # Keep it as is if parsing fails
                elif last_modified == SERVER_TIMESTAMP:
                    last_modified_str = "Pending server update"
                else:
                    last_modified_str = str(last_modified)
            else:
                last_modified_str = ""

            self.last_modified_label.setText(last_modified_str)

            logging.debug(f"Updated UI with company data: {self.company_data}")
            logging.info("Finished updating UI")
        except Exception as e:
            logging.error(f"Error updating UI with company data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to update UI with company data: {str(e)}")

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
        if self.company_id:
            try:
                self.company_data = self.firestore_service.get_company("Company_Install", self.company_id)
                if self.company_data is None:
                    raise ValueError(f"No data found for company ID: {self.company_id}")
                if not isinstance(self.company_data, dict):
                    raise TypeError(f"Expected dict, got {type(self.company_data)} for company ID: {self.company_id}")
            except Exception as e:
                logging.error(f"Error loading company data: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")
                self.close()

    def save_company(self):
        try:
            # Prepare main company data
            data = {
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
                "LastModified": self.firestore_service.server_timestamp()
            }

            # Handle quantity field
            quantity_text = self.quantity_edit.text()
            if quantity_text:
                try:
                    data["quantity"] = int(quantity_text)
                except ValueError:
                    logging.warning(f"Invalid quantity value: {quantity_text}. Setting to None.")
                    data["quantity"] = None
            else:
                data["quantity"] = None

            # Handle SN list
            sn_text = self.sn_edit.toPlainText()
            sn_list = [sn.strip() for sn in sn_text.split('\n') if sn.strip()]

            # Save or update company data
            if self.is_new_company:
                new_id = self.firestore_service.generate_id()
                data["Id"] = new_id
                data["CreatedAt"] = self.firestore_service.server_timestamp()
                self.company_id = self.firestore_service.add_company("Company_Install", data)
                self.is_new_company = False
            else:
                data["Id"] = self.company_id
                self.firestore_service.update_company("Company_Install", self.company_id, data)

            # Update SN list
            self.firestore_service.update_sn_list(self.company_id, sn_list)

            # Update local data
            self.company_data.update(data)
            self.company_data['SN'] = sn_list

            # Update UI
            self.set_edit_mode(False)
            self.update_ui_with_data()
            self.companyUpdated.emit(self.company_id)

            QMessageBox.information(self, "Success", "Company data saved successfully!")
        except Exception as e:
            logging.error(f"Error saving company data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")