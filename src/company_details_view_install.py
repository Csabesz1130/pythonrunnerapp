from .company_details_view_base import CompanyDetailsViewBase
from PyQt6.QtWidgets import QLineEdit, QTextEdit, QComboBox, QCheckBox, QMessageBox
from PyQt6.QtCore import pyqtSignal
import logging

class CompanyDetailsViewInstall(CompanyDetailsViewBase):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, parent=None, company_data=None):
        super().__init__(firestore_service, company_id, "Company_Install", parent)
        if company_data:
            self.company_data = company_data
            self.populate_fields()

    def setup_specific_fields(self):
        self.quantity_edit = QLineEdit()
        self.form_layout.addRow("Quantity:", self.quantity_edit)

        self.sn_edit = QTextEdit()
        self.form_layout.addRow("SN List:", self.sn_edit)

        self.felderites_combo = QComboBox()
        self.felderites_combo.addItems(["", "TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"])
        self.form_layout.addRow("Felderítés:", self.felderites_combo)

        self.telepites_combo = QComboBox()
        self.telepites_combo.addItems(["", "KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"])
        self.form_layout.addRow("Telepítés:", self.telepites_combo)

        self.checkbox_fields = ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        self.checkboxes = {}
        for field in self.checkbox_fields:
            self.checkboxes[field] = QComboBox()
            self.checkboxes[field].addItems(["", "Van", "Nincs"])
            self.form_layout.addRow(f"{field}:", self.checkboxes[field])

    def populate_specific_fields(self):
        self.quantity_edit.setText(str(self.company_data.get("quantity", "")))
        self.sn_edit.setPlainText("\n".join(self.company_data.get("SN", [])))

        self.set_combo_value(self.felderites_combo, self.company_data.get("felderites", ""))
        self.set_combo_value(self.telepites_combo, self.company_data.get("telepites", ""))

        for field in self.checkbox_fields:
            value = self.company_data.get(field.lower(), "")
            self.set_combo_value(self.checkboxes[field], self.boolean_to_string(value))

    def set_combo_value(self, combo, value):
        index = combo.findText(str(value))
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentIndex(0)  # Set to empty if value not found

    def boolean_to_string(self, value):
        if isinstance(value, bool):
            return "Van" if value else "Nincs"
        elif isinstance(value, str):
            return value if value in ["Van", "Nincs"] else ""
        else:
            return ""

    def string_to_boolean(self, value):
        if value == "Van":
            return True
        elif value == "Nincs":
            return False
        else:
            return None

    def get_specific_fields_data(self):
        data = {
            "quantity": int(self.quantity_edit.text()) if self.quantity_edit.text() else None,
            "SN": self.sn_edit.toPlainText().split("\n"),
            "felderites": self.felderites_combo.currentText(),
            "telepites": self.telepites_combo.currentText(),
        }

        for field in self.checkbox_fields:
            value = self.string_to_boolean(self.checkboxes[field].currentText())
            if value is not None:
                data[field.lower()] = value

        return data

    def save_company(self):
        updated_data = {
            "CompanyName": self.name_edit.text(),
            "ProgramName": self.program_combo.currentText(),
            **self.get_specific_fields_data()
        }

        try:
            if self.company_id:
                self.firestore_service.update_company("Company_Install", self.company_id, updated_data)
            else:
                self.company_id = self.firestore_service.add_company("Company_Install", updated_data)

            self.companyUpdated.emit(self.company_id)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
            self.accept()
        except Exception as e:
            logging.error(f"Error saving company data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")