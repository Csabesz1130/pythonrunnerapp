from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit
from PyQt6.QtCore import pyqtSignal
from src.company_details_view_base import CompanyDetailsViewBase

class CompanyDetailsViewDemolition(CompanyDetailsViewBase):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, parent=None, company_data=None):
        super().__init__(firestore_service, "Company_Demolition", company_id, parent, company_data)
        self.setWindowTitle("Company Details - Demolition")

    def setup_specific_fields(self):
        self.name_edit = QLineEdit()
        self.form_layout.addRow("Company Name:", self.name_edit)

        self.program_combo = QComboBox()
        self.form_layout.addRow("Program:", self.program_combo)

        self.bontas_combo = QComboBox()
        self.bontas_combo.addItems(["BONTHATO", "MEG_NYITVA", "NEM_HOZZAFERHETO"])
        self.form_layout.addRow("Bontás (1):", self.bontas_combo)

        self.felszereles_combo = QComboBox()
        self.felszereles_combo.addItems(["CSOMAGOLVA", "SZALLITASRA_VAR", "ELSZALLITVA", "NINCS_STATUSZ"])
        self.form_layout.addRow("Felszerelés (2):", self.felszereles_combo)

        self.bazis_leszereles_check = QCheckBox()
        self.form_layout.addRow("Bázis Leszerelés (3):", self.bazis_leszereles_check)

    def update_specific_fields(self):
        self.name_edit.setText(self.company_data.get("CompanyName", ""))

        program_name = self.company_data.get("ProgramName", "")
        index = self.program_combo.findText(program_name)
        if index >= 0:
            self.program_combo.setCurrentIndex(index)
        elif program_name:
            self.program_combo.addItem(program_name)
            self.program_combo.setCurrentText(program_name)

        self.bontas_combo.setCurrentText(self.company_data.get("1", "BONTHATO"))
        self.felszereles_combo.setCurrentText(self.company_data.get("2", "NINCS_STATUSZ"))
        self.bazis_leszereles_check.setChecked(self.company_data.get("3", False))

    def set_specific_fields_edit_mode(self, editable):
        self.name_edit.setEnabled(editable)
        self.program_combo.setEnabled(editable)
        self.bontas_combo.setEnabled(editable)
        self.felszereles_combo.setEnabled(editable)
        self.bazis_leszereles_check.setEnabled(editable)

    def get_specific_fields_data(self):
        return {
            "CompanyName": self.name_edit.text(),
            "ProgramName": self.program_combo.currentText(),
            "1": self.bontas_combo.currentText(),
            "2": self.felszereles_combo.currentText(),
            "3": self.bazis_leszereles_check.isChecked()
        }

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            self.program_combo.clear()
            self.program_combo.addItems(festivals)
            logging.info(f"Populated {len(festivals)} festivals in the combo box")
        except Exception as e:
            logging.error(f"Error populating festivals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load festivals: {str(e)}")