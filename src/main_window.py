import csv
import logging
import sys

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QComboBox, QRadioButton, QLineEdit, QButtonGroup, QMessageBox,
                             QFileDialog, QApplication, QCheckBox, QAbstractItemView)
from PyQt6.QtCore import Qt

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
        self.current_sort_column = -1
        self.current_sort_order = Qt.SortOrder.AscendingOrder

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        self.populate_festivals()
        self.load_companies()

    def setup_ui(self):
        # Top layout
        top_layout = QHBoxLayout()

        # Festival combo box
        self.festival_combo = QComboBox()
        top_layout.addWidget(self.festival_combo)

        # Radio buttons for collection selection
        self.collection_group = QButtonGroup(self)
        self.install_radio = QRadioButton("Company_Install")
        self.demolition_radio = QRadioButton("Company_Demolition")
        self.install_radio.setChecked(True)
        self.collection_group.addButton(self.install_radio)
        self.collection_group.addButton(self.demolition_radio)
        top_layout.addWidget(self.install_radio)
        top_layout.addWidget(self.demolition_radio)

        # Search input and button
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search companies...")
        top_layout.addWidget(self.search_input)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.filter_companies)
        top_layout.addWidget(self.search_button)

        self.main_layout.addLayout(top_layout)

        # Select all checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.select_all_changed)
        self.main_layout.addWidget(self.select_all_checkbox)

        # Company table
        self.company_table = QTableWidget()
        self.company_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.company_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.company_table.doubleClicked.connect(self.open_company_details)
        self.company_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.main_layout.addWidget(self.company_table)

        # Button layout
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

        # Connect radio buttons to load_companies
        self.install_radio.toggled.connect(self.load_companies)
        self.demolition_radio.toggled.connect(self.load_companies)

    def select_all_changed(self, state):
        for row in range(self.company_table.rowCount()):
            self.company_table.item(row, 0).setCheckState(
                Qt.CheckState.Checked if state == Qt.CheckState.Checked else Qt.CheckState.Unchecked
            )

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            self.festival_combo.addItems(["All Festivals"] + festivals)
        except Exception as e:
            logging.error(f"Error populating festivals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load festivals: {str(e)}")

    def on_header_clicked(self, logical_index):
        if self.current_sort_column == logical_index:
            # Toggle sort order if clicking on the same column
            if self.current_sort_order == Qt.SortOrder.AscendingOrder:
                self.current_sort_order = Qt.SortOrder.DescendingOrder
            else:
                self.current_sort_order = Qt.SortOrder.AscendingOrder
        else:
            # New column, start with ascending order
            self.current_sort_column = logical_index
            self.current_sort_order = Qt.SortOrder.AscendingOrder

        self.company_table.sortItems(self.current_sort_column, self.current_sort_order)

    def filter_companies(self):
        search_text = self.search_input.text().lower()
        for row in range(self.company_table.rowCount()):
            should_show = False
            for col in range(1, self.company_table.columnCount()):
                item = self.company_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.company_table.setRowHidden(row, not should_show)

    def load_companies(self):
        try:
            collection = self.get_current_collection()
            festival = self.festival_combo.currentText()
            if festival == "All Festivals":
                festival = None

            companies = self.firestore_service.get_companies(collection, festival)

            self.company_table.clear()
            headers = self.get_headers_for_collection(collection)
            self.company_table.setColumnCount(len(headers))
            self.company_table.setHorizontalHeaderLabels(headers)
            self.company_table.setRowCount(len(companies))

            for row, company in enumerate(companies):
                for col, header in enumerate(headers):
                    value = self.get_company_value(company, header, collection)
                    item = QTableWidgetItem(str(value))
                    if col == 0:  # Checkbox column
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Unchecked)
                    self.company_table.setItem(row, col, item)

            self.company_table.resizeColumnsToContents()

            if not companies:
                logging.info(f"No companies found for collection: {collection}, festival: {festival}")
                QMessageBox.information(self, "No Data", "No companies found for the selected criteria.")

        except Exception as e:
            logging.error(f"Error loading companies: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")

    def get_current_collection(self):
        return "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"

    def get_company_value(self, company, header, collection):
        field_mapping = self.get_field_mapping(collection)
        field = next((f for f, h in field_mapping.items() if h == header), None)
        if field is None:
            return ""

        value = company.get(field, "")
        if header in ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín", "Bázis Leszerelés"]:
            return "Van" if value else "Nincs"
        elif header == "Last Modified":
            return str(value) if value else ""
        else:
            return str(value)

    def get_headers_for_collection(self, collection):
        common_headers = ["ID", "Name", "Program"]
        if collection == "Company_Install":
            specific_headers = ["Felderítés", "Telepítés", "Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        else:  # Company_Demolition
            specific_headers = ["Bontás", "Felszerelés", "Bázis Leszerelés"]
        return ["Select"] + common_headers + specific_headers + ["Last Modified"]

    def open_company_details(self, index):
        try:
            company_id = self.company_table.item(index.row(), 1).text()  # Assuming ID is in column 1
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

    def add_company(self):
        try:
            collection = self.get_current_collection()
            new_id = self.firestore_service.generate_id()
            # Create an empty company data dictionary
            new_company_data = {
                "Id": new_id,
                "CompanyName": "",
                "ProgramName": "",
                # Add other fields with default values as needed
            }
            if collection == "Company_Install":
                details_view = CompanyDetailsViewInstall(self.firestore_service, new_id, self, new_company_data)
            else:
                details_view = CompanyDetailsViewDemolition(self.firestore_service, new_id, self, new_company_data)
            details_view.companyUpdated.connect(self.load_companies)
            details_view.show()
        except Exception as e:
            logging.error(f"Error adding company: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add company: {str(e)}")

    def export_to_csv(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
            if filename:
                collection = self.get_current_collection()
                headers = self.get_headers_for_collection(collection)[1:]  # Exclude 'Select' column

                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)

                    for row in range(self.company_table.rowCount()):
                        row_data = []
                        for col in range(1, self.company_table.columnCount()):  # Start from 1 to skip 'Select' column
                            item = self.company_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)

                QMessageBox.information(self, "Export Complete", f"Data exported to {filename}")
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export to CSV: {str(e)}")

    def bulk_edit(self):
        selected_items = self.company_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select cells to edit.")
            return

        selected_rows = set(item.row() for item in selected_items)

        collection = self.get_current_collection()
        dialog = EditFieldDialog(collection, self)
        if dialog.exec():
            field, value = dialog.get_field_and_value()
            self.apply_bulk_edit(field, value, selected_rows)

    def apply_bulk_edit(self, field, value, selected_rows):
        collection = self.get_current_collection()
        field_mapping = self.get_field_mapping(collection)
        reverse_mapping = {v: k for k, v in field_mapping.items()}
        db_field = reverse_mapping.get(field, field)

        headers = self.get_headers_for_collection(collection)
        col = headers.index(field) if field in headers else -1

        for row in selected_rows:
            company_id = self.company_table.item(row, 1).text()  # Assuming ID is in column 1
            data = {db_field: value}
            success = self.firestore_service.update_company(collection, company_id, data)

            if success:
                # Update the table
                if col != -1:
                    display_value = "Van" if value is True else "Nincs" if value is False else str(value)
                    self.company_table.item(row, col).setText(display_value)
            else:
                QMessageBox.warning(self, "Update Failed", f"Failed to update company {company_id}")

        self.load_companies()  # Reload the table to reflect all changes

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

        return {**common_fields, **specific_fields}

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