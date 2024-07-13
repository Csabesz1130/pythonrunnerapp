from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QMessageBox, QVBoxLayout, QFormLayout, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal
from src.company_details_view_base import CompanyDetailsViewBase
import logging

class CompanyDetailsViewDemolition(CompanyDetailsViewBase):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, parent=None, company_data=None):
        super().__init__(firestore_service, "Company_Demolition", company_id, parent, company_data)
        self.setWindowTitle("Company Details - Demolition")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.id_label = QLineEdit()
        self.id_label.setReadOnly(True)
        self.form_layout.addRow("ID:", self.id_label)

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

        self.last_modified_label = QLineEdit()
        self.last_modified_label.setReadOnly(True)
        self.form_layout.addRow("Last Modified:", self.last_modified_label)

        layout.addLayout(self.form_layout)

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

        self.delete_button = QPushButton("Delete Company")
        self.delete_button.clicked.connect(self.delete_company)
        button_layout.addWidget(self.delete_button)

        layout.addLayout(button_layout)

        self.populate_festivals()
        self.update_ui_with_data()
        self.set_edit_mode(False)

    def set_edit_mode(self, editable):
        logging.info(f"Setting edit mode to: {editable}")
        self.name_edit.setReadOnly(not editable)
        self.program_combo.setEnabled(editable)
        self.bontas_combo.setEnabled(editable)
        self.felszereles_combo.setEnabled(editable)
        self.bazis_leszereles_check.setEnabled(editable)

        self.save_button.setEnabled(editable)
        self.cancel_button.setEnabled(editable)
        self.edit_button.setEnabled(not editable)
        self.delete_button.setEnabled(not editable)

        logging.info(f"Name edit read-only: {self.name_edit.isReadOnly()}")
        logging.info(f"Program combo enabled: {self.program_combo.isEnabled()}")
        logging.info(f"Bontas combo enabled: {self.bontas_combo.isEnabled()}")
        logging.info(f"Felszereles combo enabled: {self.felszereles_combo.isEnabled()}")
        logging.info(f"Bazis leszereles check enabled: {self.bazis_leszereles_check.isEnabled()}")

    def enable_editing(self):
        logging.info("Enable editing button clicked")
        self.set_edit_mode(True)

    def update_ui_with_data(self):
        self.id_label.setText(str(self.company_data.get("Id", "")))
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
        self.bazis_leszereles_check.setChecked(self.company_data.get("3", "Nincs") == "Van")

        last_modified = self.company_data.get("LastModified", "")
        self.last_modified_label.setText(str(last_modified) if last_modified else "")

    def set_edit_mode(self, editable):
        self.name_edit.setReadOnly(not editable)
        self.program_combo.setEnabled(editable)
        self.bontas_combo.setEnabled(editable)
        self.felszereles_combo.setEnabled(editable)
        self.bazis_leszereles_check.setEnabled(editable)

        self.save_button.setEnabled(editable)
        self.cancel_button.setEnabled(editable)
        self.edit_button.setEnabled(not editable)
        self.delete_button.setEnabled(not editable)

    def get_company_data(self):
        return {
            "Id": self.id_label.text(),
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