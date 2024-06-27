import csv
import logging
import sys

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
                             QComboBox, QRadioButton, QLineEdit, QButtonGroup, QMessageBox, QFileDialog, QApplication,
                             QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal
from src.company_details_view_install import CompanyDetailsViewInstall
from src.company_details_view_demolition import CompanyDetailsViewDemolition
from src.edit_field_dialog import EditFieldDialog
from src.firestore_service import FirestoreService

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

        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.select_all_changed)
        self.main_layout.addWidget(self.select_all_checkbox)

        self.company_table = QTableWidget()
        self.company_table.cellDoubleClicked.connect(self.open_company_details)
        self.company_table.setColumnCount(1)
        self.main_layout.addWidget(self.company_table)

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

        self.install_radio.toggled.connect(self.load_companies)
        self.demolition_radio.toggled.connect(self.load_companies)

    def select_all_changed(self, state):
        for row in range(self.company_table.rowCount()):
            checkbox = self.company_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(state == Qt.CheckState.Checked)

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            self.festival_combo.addItems(["All Festivals"] + festivals)
        except Exception as e:
            logging.error(f"Error populating festivals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load festivals: {str(e)}")

    def load_companies(self):
        try:
            collection = self.get_current_collection()
            festival = self.festival_combo.currentText()
            if festival == "All Festivals":
                festival = None

            companies = self.firestore_service.get_companies(collection, festival)

            logging.debug(f"Retrieved companies: {companies}")

            headers = self.get_headers_for_collection(collection)
            self.company_table.setColumnCount(len(headers))
            self.company_table.setHorizontalHeaderLabels(headers)

            self.company_table.setRowCount(len(companies))

            for i, company in enumerate(companies):
                self.populate_table_row(i, company, collection)

            self.company_table.resizeColumnsToContents()

            if not companies:
                logging.info(f"No companies found for collection: {collection}, festival: {festival}")
                QMessageBox.information(self, "No Data", "No companies found for the selected criteria.")

        except Exception as e:
            logging.error(f"Error loading companies: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")

    def get_current_collection(self):
        return "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"

    def get_headers_for_collection(self, collection):
        common_headers = ["ID", "Name", "Program"]
        if collection == "Company_Install":
            specific_headers = ["Felderítés", "Telepítés", "Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        else:  # Company_Demolition
            specific_headers = ["Bontás", "Felszerelés", "Bázis Leszerelés"]
        return ["Select"] + common_headers + specific_headers + ["Last Modified"]

    def populate_table_row(self, row, data, collection):
        field_mapping = self.get_field_mapping(collection)
        headers = self.get_headers_for_collection(collection)

        # Add checkbox in the first column
        checkbox = QCheckBox()
        self.company_table.setCellWidget(row, 0, checkbox)

        for col, header in enumerate(headers[1:], start=1):  # Start from 1 to skip the "Select" column
            field = next((f for f, h in field_mapping.items() if h == header), None)
            if field is not None:
                value = data.get(field, "")
                if header in ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín", "Bázis Leszerelés"]:
                    display_value = "Van" if value else "Nincs"
                elif header == "Last Modified":
                    display_value = str(value) if value else ""
                else:
                    display_value = str(value)
                self.company_table.setItem(row, col, QTableWidgetItem(display_value))

    def open_company_details(self, row, column):
        try:
            company_id = self.company_table.item(row, 1).text()
            collection = self.get_current_collection()
            if collection == "Company_Install":
                details_view = CompanyDetailsViewInstall(self.firestore_service, company_id, self)
            else:
                details_view = CompanyDetailsViewDemolition(self.firestore_service, company_id, self)
            details_view.companyUpdated.connect(self.load_companies)
            details_view.show()
        except Exception as e:
            logging.error(f"Error opening company details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open company details: {str(e)}")

    def filter_companies(self):
        search_text = self.search_input.text().lower()
        for row in range(self.company_table.rowCount()):
            show_row = False
            for col in range(1, self.company_table.columnCount()):
                item = self.company_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.company_table.setRowHidden(row, not show_row)

    def add_company(self):
        try:
            collection = self.get_current_collection()
            new_id = self.firestore_service.generate_id()
            if collection == "Company_Install":
                details_view = CompanyDetailsViewInstall(self.firestore_service, new_id, self)
            else:
                details_view = CompanyDetailsViewDemolition(self.firestore_service, new_id, self)
            details_view.companyUpdated.connect(self.load_companies)
            details_view.show()
        except Exception as e:
            logging.error(f"Error adding company: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add company: {str(e)}")

    def export_to_csv(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    headers = ["Telephely név", "Telephely kód", "Összes terminál igény", "Kiadva", "Kihelyezés",
                               "Áram", "Elosztó", "Szoftver", "Teszt", "Véglegesítve", "Megjegyzés",
                               "Megjegyzés ideje", "Véglegesités ideje"]
                    writer.writerow(headers)

                    collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
                    companies = self.firestore_service.get_companies(collection)

                    for company in companies:
                        data = company.to_dict()
                        row = [
                            data.get("CompanyName", ""),  # Telephely név
                            data.get("Id", ""),  # Telephely kód
                            "",  # Összes terminál igény (not available)
                            "Van" if data.get("2") == "KIADVA" else "Nincs",  # Kiadva
                            data.get("2", ""),  # Kihelyezés
                            "Nincs" if data.get("4", False) else "Van",  # Áram
                            "Nincs" if data.get("3", False) else "Van",  # Elosztó
                            "Nincs" if data.get("7", False) else "Van",  # Szoftver
                            "Van" if data.get("2") == "HELYSZINEN_TESZTELVE" else "Nincs",  # Teszt
                            "Van" if data.get("2") == "KIRAKVA" else "Nincs",  # Véglegesítve
                            "",  # Megjegyzés (not available)
                            str(data.get("LastModified", "")),  # Megjegyzés ideje
                            str(data.get("LastModified", ""))  # Véglegesités ideje
                        ]
                        writer.writerow(row)

                QMessageBox.information(self, "Export Complete", f"Data exported to {filename}")
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export to CSV: {str(e)}")

    def bulk_edit(self):
        selected_rows = [row for row in range(self.company_table.rowCount())
                         if isinstance(self.company_table.cellWidget(row, 0), QCheckBox)
                         and self.company_table.cellWidget(row, 0).isChecked()]

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select companies to edit.")
            return

        collection = self.get_current_collection()
        dialog = EditFieldDialog(collection, self)
        if dialog.exec():
            field, value = dialog.get_field_and_value()
            self.apply_bulk_edit(field, value, selected_rows)

    def apply_bulk_edit(self, field, value, selected_rows):
        collection = self.get_current_collection()

        for row in selected_rows:
            company_id = self.company_table.item(row, 1).text()

            data = {field: value}
            success = self.firestore_service.update_company(collection, company_id, data)

            if success:
                col = self.get_column_for_field(field, collection)
                if col is not None:
                    display_value = "Van" if value is True else "Nincs" if value is False else str(value)
                    self.company_table.setItem(row, col + 1, QTableWidgetItem(display_value))
            else:
                QMessageBox.warning(self, "Update Failed", f"Failed to update company {company_id}")

        self.load_companies()

    def get_field_mapping(self, collection):
        common_fields = {
            "Id": "ID",
            "CompanyName": "Name",
            "ProgramName": "Program",
            "LastModified": "Last Modified"
        }

        if collection == "Company_Install":
            specific_fields = {
                "1": "Felderítés",
                "2": "Telepítés",
                "3": "Elosztó",
                "4": "Áram",
                "5": "Hálózat",
                "6": "PTG",
                "7": "Szoftver",
                "8": "Param",
                "9": "Helyszín",
            }
        elif collection == "Company_Demolition":
            specific_fields = {
                "1": "Bontás",
                "2": "Felszerelés",
                "3": "Bázis Leszerelés",
            }
        else:
            logging.warning(f"Unknown collection: {collection}")
            specific_fields = {}

        return {**common_fields, **specific_fields, "LastModified": "Last Modified"}

    def get_column_for_field(self, field, collection):
        headers = self.get_headers_for_collection(collection)
        field_mapping = self.get_field_mapping(collection)
        header = field_mapping.get(field)
        if header in headers:
            return headers.index(header)
        return -1

if __name__ == "__main__":
    app = QApplication(sys.argv)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        firestore_service = FirestoreService()
        window = MainWindow(firestore_service)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.error(f"An error occurred while starting the application: {e}")
        QMessageBox.critical(None, "Startup Error", f"An error occurred while starting the application: {str(e)}")
        sys.exit(1)