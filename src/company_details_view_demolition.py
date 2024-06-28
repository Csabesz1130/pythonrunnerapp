from PyQt6.QtWidgets import QCheckBox, QComboBox
from PyQt6.QtCore import pyqtSignal
from src.company_details_view_base import CompanyDetailsViewBase

class CompanyDetailsViewDemolition(CompanyDetailsViewBase):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, parent=None, company_data=None):
        super().__init__(firestore_service, "Company_Demolition", company_id, parent, company_data)
        self.setWindowTitle("Company Details - Demolition")

    def setup_specific_fields(self):
        self.bontas_combo = QComboBox()
        self.bontas_combo.addItems(["BONTHATO", "MEG_NYITVA", "NEM_HOZZAFERHETO"])
        self.form_layout.addRow("Bontás (1):", self.bontas_combo)

        self.felszereles_combo = QComboBox()
        self.felszereles_combo.addItems(["CSOMAGOLVA", "SZALLITASRA_VAR", "ELSZALLITVA", "NINCS_STATUSZ"])
        self.form_layout.addRow("Felszerelés (2):", self.felszereles_combo)

        self.bazis_leszereles_check = QCheckBox()
        self.form_layout.addRow("Bázis Leszerelés (3):", self.bazis_leszereles_check)

    def update_specific_fields(self):
        self.bontas_combo.setCurrentText(self.company_data.get("1", "BONTHATO"))
        self.felszereles_combo.setCurrentText(self.company_data.get("2", "NINCS_STATUSZ"))
        self.bazis_leszereles_check.setChecked(self.company_data.get("3", False))

    def set_specific_fields_edit_mode(self, editable):
        self.bontas_combo.setEnabled(editable)
        self.felszereles_combo.setEnabled(editable)
        self.bazis_leszereles_check.setEnabled(editable)

    def get_specific_fields_data(self):
        return {
            "1": self.bontas_combo.currentText(),
            "2": self.felszereles_combo.currentText(),
            "3": self.bazis_leszereles_check.isChecked()
        }