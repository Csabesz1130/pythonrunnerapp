from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
                             QCheckBox, QPushButton, QTextEdit, QMessageBox, QLabel,
                             QListWidget, QHBoxLayout, QInputDialog)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIntValidator
import logging

class CompanyDetailsView(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, company_id, collection, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.company_id = company_id
        self.collection = collection
        self.company_data = {}
        self.fields = {}
        self.setup_ui()
        self.load_company_data()

    def setup_ui(self):
        self.setWindowTitle("Company Details")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)

        # Company Information
        form_layout = QFormLayout()
        self.fields['CompanyName'] = QLineEdit()
        form_layout.addRow("Company Name:", self.fields['CompanyName'])

        self.fields['ProgramName'] = QComboBox()
        self.populate_programs()
        form_layout.addRow("Program:", self.fields['ProgramName'])

        self.fields['quantity'] = QLineEdit()
        self.fields['quantity'].setValidator(QIntValidator())
        form_layout.addRow("Quantity:", self.fields['quantity'])

        # Status Fields
        self.fields['felderites'] = QComboBox()
        self.fields['felderites'].addItems(["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"])
        form_layout.addRow("Felderítés:", self.fields['felderites'])

        self.fields['telepites'] = QComboBox()
        self.fields['telepites'].addItems(["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"])
        form_layout.addRow("Telepítés:", self.fields['telepites'])

        # Boolean Fields
        boolean_fields = ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        for field in boolean_fields:
            self.fields[field] = QCheckBox()
            form_layout.addRow(f"{field}:", self.fields[field])

        layout.addLayout(form_layout)

        # SN List
        sn_layout = QVBoxLayout()
        sn_layout.addWidget(QLabel("SN List:"))
        self.sn_list = QListWidget()
        sn_layout.addWidget(self.sn_list)

        sn_button_layout = QHBoxLayout()
        self.add_sn_button = QPushButton("Add SN")
        self.remove_sn_button = QPushButton("Remove SN")
        sn_button_layout.addWidget(self.add_sn_button)
        sn_button_layout.addWidget(self.remove_sn_button)
        sn_layout.addLayout(sn_button_layout)

        layout.addLayout(sn_layout)

        # Comments
        layout.addWidget(QLabel("Comments:"))
        self.comments_text = QTextEdit()
        self.comments_text.setReadOnly(True)
        layout.addWidget(self.comments_text)

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_company)
        layout.addWidget(self.save_button)

        # Connect SN management buttons
        self.add_sn_button.clicked.connect(self.add_sn)
        self.remove_sn_button.clicked.connect(self.remove_sn)

    def populate_programs(self):
        try:
            programs = self.firestore_service.get_programs()
            self.fields['ProgramName'].addItems(programs)
        except Exception as e:
            logging.error(f"Error populating programs: {e}")
            QMessageBox.warning(self, "Warning", "Failed to load programs. Some data may be missing.")

    def load_company_data(self):
        if self.company_id:
            try:
                self.company_data = self.firestore_service.get_company_details(self.company_id)
                if self.company_data:
                    self.populate_fields()
                else:
                    QMessageBox.warning(self, "Not Found", f"Company with ID {self.company_id} not found.")
            except Exception as e:
                logging.error(f"Error loading company data: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")

    def populate_fields(self):
        self.fields['CompanyName'].setText(self.company_data.get('CompanyName', ''))
        self.fields['ProgramName'].setCurrentText(self.company_data.get('ProgramName', ''))
        self.fields['quantity'].setText(str(self.company_data.get('quantity', '')))
        self.fields['felderites'].setCurrentText(self.company_data.get('felderites', ''))
        self.fields['telepites'].setCurrentText(self.company_data.get('telepites', ''))

        boolean_fields = ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        for field in boolean_fields:
            self.fields[field].setChecked(self.company_data.get(field.lower(), False))

        # Populate SN List
        self.sn_list.clear()
        self.sn_list.addItems(self.company_data.get('SN', []))

        # Populate Comments
        self.comments_text.clear()
        for comment in self.company_data.get('Comments', []):
            self.comments_text.append(f"{comment['timestamp']}: {comment['comment']}")

    def save_company(self):
        updated_data = {
            'CompanyName': self.fields['CompanyName'].text(),
            'ProgramName': self.fields['ProgramName'].currentText(),
            'quantity': int(self.fields['quantity'].text()) if self.fields['quantity'].text() else None,
            'felderites': self.fields['felderites'].currentText(),
            'telepites': self.fields['telepites'].currentText(),
        }

        boolean_fields = ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        for field in boolean_fields:
            updated_data[field.lower()] = self.fields[field].isChecked()

        # Get SN list
        updated_data['SN'] = [self.sn_list.item(i).text() for i in range(self.sn_list.count())]

        try:
            if self.company_id:
                self.firestore_service.update_company(self.collection, self.company_id, updated_data)
            else:
                self.company_id = self.firestore_service.add_company(self.collection, updated_data)

            self.companyUpdated.emit(self.company_id)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
            self.accept()
        except Exception as e:
            logging.error(f"Error saving company data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")

    def add_sn(self):
        sn, ok = QInputDialog.getText(self, "Add SN", "Enter new SN:")
        if ok and sn:
            self.sn_list.addItem(sn)

    def remove_sn(self):
        current_item = self.sn_list.currentItem()
        if current_item:
            self.sn_list.takeItem(self.sn_list.row(current_item))
        else:
            QMessageBox.warning(self, "No Selection", "Please select an SN to remove.")