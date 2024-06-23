import logging

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
                             QCheckBox, QComboBox, QTextEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt

class CompanyDetailsView(QDialog):
    def __init__(self, firestore_service, collection, company_id, company_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Company Details")
        self.setGeometry(200, 200, 600, 800)
        self.firestore_service = firestore_service
        self.collection = collection
        self.company_id = company_id
        self.company_data = company_data
        self.setup_ui()
        self.populate_data()
        self.set_edit_mode(False)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Company Name:", self.name_edit)

        self.program_edit = QLineEdit()
        form_layout.addRow("Program:", self.program_edit)

        self.eloszto_check = QCheckBox()
        form_layout.addRow("Elosztó:", self.eloszto_check)

        self.aram_check = QCheckBox()
        form_layout.addRow("Áram:", self.aram_check)

        self.halozat_check = QCheckBox()
        form_layout.addRow("Halozat:", self.halozat_check)

        self.telepites_combo = QComboBox()
        self.telepites_combo.addItems(["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"])
        form_layout.addRow("Telepítés:", self.telepites_combo)

        self.felderites_combo = QComboBox()
        self.felderites_combo.addItems(["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"])
        form_layout.addRow("Felderítés:", self.felderites_combo)

        main_layout.addLayout(form_layout)

        self.comments_text = QTextEdit()
        self.comments_text.setReadOnly(True)
        main_layout.addWidget(QLabel("Comments:"))
        main_layout.addWidget(self.comments_text)

        self.new_comment_text = QTextEdit()
        self.new_comment_text.setPlaceholderText("Add a new comment...")
        main_layout.addWidget(QLabel("New Comment:"))
        main_layout.addWidget(self.new_comment_text)

        button_layout = QHBoxLayout()
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(lambda: self.set_edit_mode(True))
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

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_company_data)
        button_layout.addWidget(self.refresh_button)

        self.add_comment_button = QPushButton("Add Comment")
        self.add_comment_button.clicked.connect(self.add_comment)
        button_layout.addWidget(self.add_comment_button)

        main_layout.addLayout(button_layout)

    def populate_data(self):
        self.name_edit.setText(self.company_data.get("name", ""))
        self.program_edit.setText(self.company_data.get("program", ""))
        self.eloszto_check.setChecked(self.company_data.get("eloszto", False))
        self.aram_check.setChecked(self.company_data.get("aram", False))
        self.halozat_check.setChecked(self.company_data.get("halozat", False))
        self.ptg_check.setChecked(self.company_data.get("PTG", False))
        self.szoftver_check.setChecked(self.company_data.get("szoftver", False))
        self.param_check.setChecked(self.company_data.get("param", False))
        self.helyszin_check.setChecked(self.company_data.get("helyszin", False))
        self.telepites_combo.setCurrentText(self.company_data.get("telepites", "KIADVA"))
        self.felderites_combo.setCurrentText(self.company_data.get("felderites", "TELEPÍTHETŐ"))

        self.comments_text.clear()
        for comment in self.company_data.get("comments", []):
            self.comments_text.append(f"{comment['author']} - {comment['timestamp']}:\n{comment['text']}\n")

    def save_company(self):
        try:
            data = {
                "name": self.name_edit.text(),
                "program": self.program_edit.text(),
                "eloszto": self.eloszto_check.isChecked(),
                "aram": self.aram_check.isChecked(),
                "halozat": self.halozat_check.isChecked(),
                "PTG": self.ptg_check.isChecked(),
                "szoftver": self.szoftver_check.isChecked(),
                "param": self.param_check.isChecked(),
                "helyszin": self.helyszin_check.isChecked(),
                "telepites": self.telepites_combo.currentText(),
                "felderites": self.felderites_combo.currentText(),
            }

            self.firestore_service.update_company(self.collection, self.company_id, data)
            self.set_edit_mode(False)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
            self.accept()
        except Exception as e:
            logging.error(f"Error saving company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save company data: {str(e)}")

    def cancel_edit(self):
        if self.company_id:
            self.load_company_data()
        else:
            self.close()
        self.set_edit_mode(False)

    def delete_company(self):
        if not self.company_id:
            return

        reply = QMessageBox.question(self, "Delete Company", "Are you sure you want to delete this company?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.firestore_service.delete_company(self.collection, self.company_id)
                QMessageBox.information(self, "Success", "Company deleted successfully!")
                self.close()
            except Exception as e:
                logging.error(f"Error deleting company: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete company: {str(e)}")

    def add_comment(self):
        comment_text = self.new_comment_text.toPlainText().strip()
        if not comment_text:
            return

        try:
            comment_data = {
                "author": "Current User",  # Replace with actual user when authentication is implemented
                "text": comment_text,
                "timestamp": self.firestore_service.server_timestamp()
            }
            self.firestore_service.add_comment(self.collection, self.company_id, comment_data)
            self.new_comment_text.clear()
            self.load_company_data()  # Refresh to show the new comment
            QMessageBox.information(self, "Success", "Comment added successfully!")
        except Exception as e:
            logging.error(f"Error adding comment: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add comment: {str(e)}")