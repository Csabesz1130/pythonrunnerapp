from .company_details_view_base import CompanyDetailsViewBase
from PyQt6.QtWidgets import QComboBox, QCheckBox

class CompanyDetailsViewDemolition(CompanyDetailsViewBase):
    def __init__(self, firestore_service, company_id, parent=None):
        super().__init__(firestore_service, company_id, "Company_Demolition", parent)

    def setup_specific_fields(self):
        self.bontas_combo = QComboBox()
        self.bontas_combo.addItems(["BONTHATO", "MEG_NYITVA", "NEM_HOZZAFERHETO"])
        self.form_layout.addRow("Bontás:", self.bontas_combo)

        self.felszereles_combo = QComboBox()
        self.felszereles_combo.addItems(["CSOMAGOLVA", "SZALLITASRA_VAR", "ELSZALLITVA", "NINCS_STATUSZ"])
        self.form_layout.addRow("Felszerelés:", self.felszereles_combo)

        self.bazis_leszereles_check = QCheckBox()
        self.form_layout.addRow("Bázis Leszerelés:", self.bazis_leszereles_check)

    def populate_specific_fields(self):
        self.bontas_combo.setCurrentText(self.company_data.get("1", "BONTHATO"))
        self.felszereles_combo.setCurrentText(self.company_data.get("2", "NINCS_STATUSZ"))
        self.bazis_leszereles_check.setChecked(self.company_data.get("3", False))

    def get_specific_fields_data(self):
        return {
            "1": self.bontas_combo.currentText(),
            "2": self.felszereles_combo.currentText(),
            "3": self.bazis_leszereles_check.isChecked()
        }