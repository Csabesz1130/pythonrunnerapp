from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QCheckBox, QPushButton, QTextEdit, QMessageBox
from PyQt6.QtCore import pyqtSignal

class CompanyDetailsViewInstall(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, parent=None, company_data=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.company_id = company_id
        self.company_data = company_data or {}
        self.setup_ui()
        self.populate_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Company Name:", self.name_edit)

        self.program_combo = QComboBox()
        form_layout.addRow("Program:", self.program_combo)

        self.quantity_edit = QLineEdit()
        form_layout.addRow("Quantity:", self.quantity_edit)

        self.sn_edit = QTextEdit()
        form_layout.addRow("SN List:", self.sn_edit)

        self.felderites_combo = QComboBox()
        self.felderites_combo.addItems(["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"])
        form_layout.addRow("Felderítés:", self.felderites_combo)

        self.telepites_combo = QComboBox()
        self.telepites_combo.addItems(["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"])
        form_layout.addRow("Telepítés:", self.telepites_combo)

        self.eloszto_check = QCheckBox()
        form_layout.addRow("Elosztó:", self.eloszto_check)

        self.aram_check = QCheckBox()
        form_layout.addRow("Áram:", self.aram_check)

        self.halozat_check = QCheckBox()
        form_layout.addRow("Hálózat:", self.halozat_check)

        self.ptg_check = QCheckBox()
        form_layout.addRow("PTG:", self.ptg_check)

        self.szoftver_check = QCheckBox()
        form_layout.addRow("Szoftver:", self.szoftver_check)

        self.param_check = QCheckBox()
        form_layout.addRow("Param:", self.param_check)

        self.helyszin_check = QCheckBox()
        form_layout.addRow("Helyszín:", self.helyszin_check)

        layout.addLayout(form_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_company)
        layout.addWidget(self.save_button)

    def populate_data(self):
        if self.company_data:
            self.name_edit.setText(self.company_data.get("CompanyName", ""))
            self.program_combo.setCurrentText(self.company_data.get("ProgramName", ""))
            self.quantity_edit.setText(str(self.company_data.get("quantity", "")))
            self.sn_edit.setPlainText("\n".join(self.company_data.get("SN", [])))
            self.felderites_combo.setCurrentText(self.company_data.get("1", "TELEPÍTHETŐ"))
            self.telepites_combo.setCurrentText(self.company_data.get("2", "KIADVA"))
            self.eloszto_check.setChecked(self.company_data.get("3", False))
            self.aram_check.setChecked(self.company_data.get("4", False))
            self.halozat_check.setChecked(self.company_data.get("5", False))
            self.ptg_check.setChecked(self.company_data.get("6", False))
            self.szoftver_check.setChecked(self.company_data.get("7", False))
            self.param_check.setChecked(self.company_data.get("8", False))
            self.helyszin_check.setChecked(self.company_data.get("9", False))

    def save_company(self):
        updated_data = {
            "CompanyName": self.name_edit.text(),
            "ProgramName": self.program_combo.currentText(),
            "quantity": int(self.quantity_edit.text()) if self.quantity_edit.text() else None,
            "SN": self.sn_edit.toPlainText().split("\n"),
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

        try:
            if self.company_id:
                self.firestore_service.update_company("Company_Install", self.company_id, updated_data)
            else:
                self.company_id = self.firestore_service.add_company("Company_Install", updated_data)

            self.companyUpdated.emit(self.company_id)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")