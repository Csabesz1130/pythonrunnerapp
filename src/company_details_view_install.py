from PyQt6.QtWidgets import QCheckBox, QComboBox
from PyQt6.QtCore import pyqtSignal
from src.company_details_view_base import CompanyDetailsViewBase

class CompanyDetailsViewInstall(CompanyDetailsViewBase):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id=None, parent=None):
        super().__init__(firestore_service, "Company_Install", company_id, parent)
        self.setWindowTitle("Company Details - Install")

    def setup_specific_fields(self):
        self.eloszto_check = QCheckBox()
        self.form_layout.addRow("Eloszto:", self.eloszto_check)

        self.aram_check = QCheckBox()
        self.form_layout.addRow("Aram:", self.aram_check)

        self.halozat_check = QCheckBox()
        self.form_layout.addRow("Halozat:", self.halozat_check)

        self.telepites_combo = QComboBox()
        self.telepites_combo.addItems(["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"])
        self.form_layout.addRow("Telepítés:", self.telepites_combo)

        self.felderites_combo = QComboBox()
        self.felderites_combo.addItems(["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"])
        self.form_layout.addRow("Felderítés:", self.felderites_combo)

    def update_specific_fields(self):
        self.eloszto_check.setChecked(self.company_data.get("eloszto", False))
        self.aram_check.setChecked(self.company_data.get("aram", False))
        self.halozat_check.setChecked(self.company_data.get("halozat", False))
        self.telepites_combo.setCurrentText(self.company_data.get("telepites", "KIADVA"))
        self.felderites_combo.setCurrentText(self.company_data.get("felderites", "TELEPÍTHETŐ"))

    def set_specific_fields_edit_mode(self, editable):
        self.eloszto_check.setEnabled(editable)
        self.aram_check.setEnabled(editable)
        self.halozat_check.setEnabled(editable)
        self.telepites_combo.setEnabled(editable)
        self.felderites_combo.setEnabled(editable)

    def get_specific_fields_data(self):
        return {
            "eloszto": self.eloszto_check.isChecked(),
            "aram": self.aram_check.isChecked(),
            "halozat": self.halozat_check.isChecked(),
            "telepites": self.telepites_combo.currentText(),
            "felderites": self.felderites_combo.currentText()
        }