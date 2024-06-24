import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
                             QCheckBox, QComboBox, QTextEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class CompanyDetailsView(QDialog):
    companyUpdated = pyqtSignal(str)

    def __init__(self, firestore_service, collection, company_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Company Details")
        self.setGeometry(200, 200, 600, 800)
        self.firestore_service = firestore_service
        self.collection = collection
        self.company_id = company_id
        self.company_data = {}
        self.setup_ui()
        self.load_company_data()
        self.set_edit_mode(True if not company_id else False)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.id_label = QLabel()
        form_layout.addRow("ID:", self.id_label)

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

        self.last_modified_label = QLabel()
        form_layout.addRow("Last Modified:", self.last_modified_label)

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

        self.add_comment_button = QPushButton("Add Comment")
        self.add_comment_button.clicked.connect(self.add_comment)
        button_layout.addWidget(self.add_comment_button)

        main_layout.addLayout(button_layout)

    def load_company_data(self):
        try:
            if self.company_id:
                self.company_data = self.firestore_service.get_company(self.collection, self.company_id)
                if self.company_data:
                    self.update_ui_with_data()
                else:
                    logging.warning(f"No company found with ID: {self.company_id}")
                    QMessageBox.information(self, "Information", f"No company found with ID: {self.company_id}")
                    self.close()
            else:
                self.set_edit_mode(True)  # New company, enable editing mode
        except Exception as e:
            logging.error(f"Error loading company data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load company data: {str(e)}")

    def update_ui_with_data(self):
        self.id_label.setText(str(self.company_data.get("Id", "")))
        self.name_edit.setText(self.company_data.get("CompanyName", ""))
        self.program_edit.setText(self.company_data.get("ProgramName", ""))
        self.eloszto_check.setChecked(self.company_data.get("eloszto", False))
        self.aram_check.setChecked(self.company_data.get("aram", False))
        self.halozat_check.setChecked(self.company_data.get("halozat", False))
        self.telepites_combo.setCurrentText(self.company_data.get("telepites", "KIADVA"))
        self.felderites_combo.setCurrentText(self.company_data.get("felderites", "TELEPÍTHETŐ"))

        last_modified = self.company_data.get("LastModified")
        if last_modified:
            self.last_modified_label.setText(last_modified.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.last_modified_label.setText("")

        self.comments_text.clear()
        for comment in self.company_data.get("comments", []):
            self.comments_text.append(f"{comment['author']} - {comment['timestamp']}:\n{comment['text']}\n")

    def set_edit_mode(self, editable):
        self.name_edit.setReadOnly(not editable)
        self.program_edit.setReadOnly(not editable)
        self.eloszto_check.setEnabled(editable)
        self.aram_check.setEnabled(editable)
        self.halozat_check.setEnabled(editable)
        self.telepites_combo.setEnabled(editable)
        self.felderites_combo.setEnabled(editable)
        self.save_button.setEnabled(editable)
        self.cancel_button.setEnabled(editable)
        self.edit_button.setEnabled(not editable)
        self.delete_button.setEnabled(not editable)

    def save_company(self):
        try:
            data = {
                "CompanyName": self.name_edit.text(),
                "ProgramName": self.program_edit.text(),
                "eloszto": self.eloszto_check.isChecked(),
                "aram": self.aram_check.isChecked(),
                "halozat": self.halozat_check.isChecked(),
                "telepites": self.telepites_combo.currentText(),
                "felderites": self.felderites_combo.currentText(),
            }

            if self.company_id:
                self.firestore_service.update_company(self.collection, self.company_id, data)
            else:
                self.company_id = self.firestore_service.add_company(self.collection, data)

            self.set_edit_mode(False)
            self.load_company_data()  # Refresh data after save
            self.companyUpdated.emit(self.company_id)
            QMessageBox.information(self, "Success", "Company data saved successfully!")
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
                self.companyUpdated.emit(self.company_id)
                self.accept()  # Close the dialog
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