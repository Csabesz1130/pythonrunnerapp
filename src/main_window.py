import csv
import logging
from tkinter import dialog

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QComboBox, QRadioButton, QLineEdit, QButtonGroup, QMessageBox,
                             QFileDialog, QDialog, QFormLayout, QCheckBox)
from PyQt6.QtCore import Qt
from src.company_details_view import CompanyDetailsView

class BulkEditDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Edit")
        self.setGeometry(200, 200, 300, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.field_combo = QComboBox()
        self.field_combo.addItems(["eloszto", "aram", "halozat", "PTG", "szoftver", "param", "helyszin", "telepites", "felderites"])
        layout.addRow("Field to edit:", self.field_combo)

        self.value_input = QLineEdit()
        layout.addRow("New value:", self.value_input)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.accept)
        layout.addRow(self.apply_button)

    def get_field_and_value(self):
        return self.field_combo.currentText(), self.value_input.text()

class MainWindow(QMainWindow):
    def __init__(self, firestore_service):
        super().__init__()
        self.setWindowTitle("Festival Company Management")
        self.setGeometry(100, 100, 1200, 800)

        self.firestore_service = firestore_service

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        self.populate_festivals()
        self.load_companies()

    def setup_ui(self):
        # Top layout for filters and search
        top_layout = QHBoxLayout()

        self.festival_combo = QComboBox()
        top_layout.addWidget(self.festival_combo)

        self.collection_group = QButtonGroup(self)
        self.install_radio = QRadioButton("Company_Install")
        self.demolition_radio = QRadioButton("Company_Demolition")
        self.install_radio.setChecked(True)
        self.collection_group.addButton(self.install_radio)
        self.collection_group.addButton(self.demolition_radio)
        top_layout.addWidget(self.install_radio)
        top_layout.addWidget(self.demolition_radio)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search companies...")
        top_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.filter_companies)
        top_layout.addWidget(self.search_button)

        self.main_layout.addLayout(top_layout)

        # Company table
        self.company_table = QTableWidget()
        self.company_table.setColumnCount(10)  # Added one more column for checkboxes
        self.company_table.setHorizontalHeaderLabels(["Select", "ID", "Name", "Program", "Eloszto", "Aram", "Halozat", "Telepites", "Felderites", "Last Modified"])
        self.company_table.cellDoubleClicked.connect(self.open_company_details)
        self.main_layout.addWidget(self.company_table)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.add_company_button = QPushButton("Add Company")
        self.add_company_button.clicked.connect(self.add_company)
        button_layout.addWidget(self.add_company_button)

        self.export_button = QPushButton("Export List")
        self.export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(self.export_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_companies)
        button_layout.addWidget(self.refresh_button)

        self.bulk_edit_button = QPushButton("Bulk Edit")
        self.bulk_edit_button.clicked.connect(self.bulk_edit)
        button_layout.addWidget(self.bulk_edit_button)

        self.main_layout.addLayout(button_layout)

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            self.festival_combo.addItems(["All Festivals"] + festivals)
        except Exception as e:
            logging.error(f"Error populating festivals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load festivals: {str(e)}")

    def load_companies(self):
        try:
            collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
            festival = self.festival_combo.currentText()
            companies = self.firestore_service.get_companies(collection, festival)

            self.company_table.setRowCount(len(companies))
            for i, company in enumerate(companies):
                data = company.to_dict()

                # Add checkbox
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                checkbox.setCheckState(Qt.CheckState.Unchecked)
                self.company_table.setItem(i, 0, checkbox)

                self.company_table.setItem(i, 1, QTableWidgetItem(str(data.get("Id", ""))))
                self.company_table.setItem(i, 2, QTableWidgetItem(data.get("CompanyName", "")))
                self.company_table.setItem(i, 3, QTableWidgetItem(data.get("ProgramName", "")))
                self.company_table.setItem(i, 4, QTableWidgetItem("Yes" if data.get("eloszto", False) else "No"))
                self.company_table.setItem(i, 5, QTableWidgetItem("Yes" if data.get("aram", False) else "No"))
                self.company_table.setItem(i, 6, QTableWidgetItem("Yes" if data.get("halozat", False) else "No"))
                self.company_table.setItem(i, 7, QTableWidgetItem(data.get("telepites", "KIADVA")))
                self.company_table.setItem(i, 8, QTableWidgetItem(data.get("felderites", "TELEPÍTHETŐ")))
                self.company_table.setItem(i, 9, QTableWidgetItem(str(data.get("LastModified", ""))))
        except Exception as e:
            logging.error(f"Error loading companies: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")

    def open_company_details(self, row, column):
        try:
            company_id = self.company_table.item(row, 1).text()
            collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
            details_view = CompanyDetailsView(self.firestore_service, collection, company_id, self)
            details_view.companyUpdated.connect(self.load_companies)
            details_view.show()
        except Exception as e:
            logging.error(f"Error opening company details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open company details: {str(e)}")

    def filter_companies(self):
        search_text = self.search_input.text().lower()
        festival = self.festival_combo.currentText()
        collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"

        for row in range(self.company_table.rowCount()):
            show_row = True

            # Apply search filter
            if search_text:
                show_row = False
                for col in range(1, self.company_table.columnCount()):  # Start from 1 to skip checkbox column
                    item = self.company_table.item(row, col)
                    if item and search_text in item.text().lower():
                        show_row = True
                        break

            # Apply festival filter
            if festival != "All Festivals":
                program_item = self.company_table.item(row, 3)  # Assuming ProgramName is in column 3
                if program_item and program_item.text() != festival:
                    show_row = False

            self.company_table.setRowHidden(row, not show_row)

    def add_company(self):
        try:
            collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
            details_view = CompanyDetailsView(self.firestore_service, collection, parent=self)
            details_view.companyUpdated.connect(self.load_companies)
            details_view.show()
        except Exception as e:
            logging.error(f"Error adding company: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add company: {str(e)}")

    def export_to_csv(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
            if filename:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    headers = [self.company_table.horizontalHeaderItem(i).text() for i in range(1, self.company_table.columnCount())]  # Skip checkbox column
                    writer.writerow(headers)
                    for row in range(self.company_table.rowCount()):
                        if not self.company_table.isRowHidden(row):
                            row_data = [self.company_table.item(row, col).text() for col in range(1, self.company_table.columnCount())]  # Skip checkbox column
                            writer.writerow(row_data)
                QMessageBox.information(self, "Export Complete", f"Data exported to {filename}")
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export to CSV: {str(e)}")

    def bulk_edit(self):
        dialog = BulkEditDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            field, value = dialog.get_field_and_value()
            selected_companies = []

        for row in range(self.company_table.rowCount()):
            if self.company_table.item(row, 0).checkState() == Qt.CheckState.Checked:
                company_id = self.company_table.item(row, 1).text()
                selected_companies.append(company_id)

        if not selected_companies:
            QMessageBox.warning(self, "Warning", "No companies selected for bulk edit.")
            return

        collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
        success_count = 0
        error_count = 0
        error_messages = []

        for company_id in selected_companies:
            try:
                data = {field: value}
                if field in ["eloszto", "aram", "halozat", "PTG", "szoftver", "param", "helyszin"]:
                    data[field] = value.lower() == "yes"
                self.firestore_service.update_company(collection, company_id, data)
                success_count += 1
            except Exception as e:
                error_count += 1
                error_messages.append(f"Error updating company {company_id}: {str(e)}")
                logging.error(f"Error updating company {company_id}: {e}")

        self.load_companies()  # Refresh the table

        message = f"Bulk edit completed.\nSuccessful updates: {success_count}\nFailed updates: {error_count}"
        if error_count > 0:
            message += "\n\nErrors encountered:"
            for error in error_messages[:5]:  # Show first 5 errors
                message += f"\n- {error}"
            if len(error_messages) > 5:
                message += f"\n... and {len(error_messages) - 5} more errors."

        if error_count > 0:
            QMessageBox.warning(self, "Bulk Edit Results", message)
        else:
            QMessageBox.information(self, "Bulk Edit Results", message)