import csv
import logging
import os
import sys
from datetime import datetime

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QComboBox, QRadioButton, QLineEdit, QButtonGroup, QMessageBox,
                             QFileDialog, QApplication, QCheckBox, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer

from src.company_details_view_install import CompanyDetailsViewInstall
from src.company_details_view_demolition import CompanyDetailsViewDemolition
from src.edit_field_dialog import EditFieldDialog
from src.firestore_service import FirestoreService
from src.excel_exporter import ExcelExporter
from src.table_filter import FilterableTableView
from src.site_processor import SiteProcessor
from src.excel_exporter import ExcelExporter  # Make sure to import this


class MainWindow(QMainWindow):
    def __init__(self, firestore_service):
        super().__init__()
        self.setWindowTitle("Festival Company Management")
        self.setGeometry(100, 100, 1200, 800)

        self.firestore_service = firestore_service
        self.current_sort_column = -1
        self.current_sort_order = Qt.SortOrder.AscendingOrder

        try:
            logging.info("Initializing SiteProcessor")
            self.site_processor = SiteProcessor(firestore_service, self)
            self.site_processor.processing_complete.connect(self.load_companies)

            logging.info("Setting up search timer")
            self.search_timer = QTimer(self)
            self.search_timer.setSingleShot(True)
            self.search_timer.timeout.connect(self.filter_companies)

            logging.info("Setting up central widget")
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            self.main_layout = QVBoxLayout(self.central_widget)

            logging.info("Setting up UI")
            self.setup_ui()

            logging.info("Populating festivals")
            self.populate_festivals()

            logging.info("MainWindow initialization completed successfully")
        except Exception as e:
            logging.error(f"Error during MainWindow initialization: {e}", exc_info=True)
            QMessageBox.critical(self, "Initialization Error", f"An error occurred during initialization: {str(e)}")

    def setup_ui(self):
        # Top layout
        logging.info("Starting UI setup")
        try:
            top_layout = QHBoxLayout()

            # Festival combo box
            self.festival_combo = QComboBox()
            self.festival_combo.currentIndexChanged.connect(self.on_festival_changed)
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

            self.install_radio.toggled.connect(self.on_collection_changed)
            self.demolition_radio.toggled.connect(self.on_collection_changed)

            self.main_layout.addLayout(top_layout)

            # General search input
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search companies...")
            self.search_input.textChanged.connect(self.on_search_text_changed)
            self.main_layout.addWidget(self.search_input)

            # Filter inputs layout
            self.filter_layout = QHBoxLayout()
            self.main_layout.addLayout(self.filter_layout)

            # Initialize filter inputs
            self.filter_inputs = []
            self.update_filter_inputs()

            # Company table
            self.company_table = QTableWidget()
            self.company_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.company_table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
            self.company_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.company_table.doubleClicked.connect(self.open_company_details)
            self.company_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
            self.main_layout.addWidget(self.company_table)

            # Select all checkbox
            self.select_all_checkbox = QCheckBox("Select All")
            self.select_all_checkbox.stateChanged.connect(self.select_all_changed)
            self.main_layout.addWidget(self.select_all_checkbox)

            # Button layout
            logging.info("Setting up button layout")
            button_layout = QHBoxLayout()

            logging.info("Setting up export button")
            self.export_button = QPushButton("Export to Excel")
            self.export_button.clicked.connect(self.export_to_excel)
            button_layout.addWidget(self.export_button)

            logging.info("Setting up import sites button")
            self.import_sites_button = QPushButton("Import Sites")
            self.import_sites_button.clicked.connect(self.site_processor.import_sites)
            button_layout.addWidget(self.import_sites_button)

            logging.info("Setting up refresh button")
            self.refresh_button = QPushButton("Refresh")
            self.refresh_button.clicked.connect(self.load_companies)
            button_layout.addWidget(self.refresh_button)

            logging.info("Setting up bulk edit button")
            self.bulk_edit_button = QPushButton("Bulk Edit")
            self.bulk_edit_button.clicked.connect(self.bulk_edit)
            button_layout.addWidget(self.bulk_edit_button)

            self.main_layout.addLayout(button_layout)
        except Exception as e:
            logging.error(f"Error in setup_ui: {e}", exc_info=True)
            raise

    def on_festival_changed(self, index):
        logging.info(f"Festival changed. New index: {index}")
        try:
            if index > 0:  # 0 is the "Select a festival" placeholder
                logging.info("Valid festival selected. Enabling buttons and loading companies.")
                self.set_buttons_enabled(True)
                self.load_companies()
            else:
                logging.info("No festival selected. Disabling buttons and clearing table.")
                self.set_buttons_enabled(False)
                self.company_table.setRowCount(0)  # Clear the table
            logging.info("Festival change handled successfully")
        except Exception as e:
            logging.error(f"Error in on_festival_changed: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An error occurred while changing festivals: {str(e)}")

    def set_buttons_enabled(self, enabled):
        logging.info(f"Setting buttons enabled: {enabled}")
        try:
            self.export_button.setEnabled(enabled)
            self.refresh_button.setEnabled(enabled)
            self.bulk_edit_button.setEnabled(enabled)
            self.import_sites_button.setEnabled(enabled)
            self.search_input.setEnabled(enabled)
            for filter_input in self.filter_inputs:
                filter_input.setEnabled(enabled)
            logging.info("Buttons enabled/disabled successfully")
        except Exception as e:
            logging.error(f"Error setting buttons enabled: {e}", exc_info=True)
            raise

    def on_search_text_changed(self):
        # Reset the timer every time the text changes
        self.search_timer.stop()
        self.search_timer.start(300)  # Wait for 300 ms before filtering

    def filter_companies(self):
        search_text = self.search_input.text().lower()
        for row in range(self.company_table.rowCount()):
            should_show = False
            for col in range(self.company_table.columnCount()):
                item = self.company_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.company_table.setRowHidden(row, not should_show)

    def apply_filters(self):
        search_text = self.search_input.text().lower()
        for row in range(self.company_table.rowCount()):
            should_show = True

            # Apply general search filter
            if search_text:
                row_matches_search = False
                for col in range(self.company_table.columnCount()):
                    item = self.company_table.item(row, col)
                    if item and search_text in item.text().lower():
                        row_matches_search = True
                        break
                if not row_matches_search:
                    should_show = False

            # Apply column-specific filters
            if should_show:
                for col, filter_input in enumerate(self.filter_inputs):
                    filter_text = filter_input.text().lower()
                    if filter_text:
                        item = self.company_table.item(row, col)
                        if item is None or filter_text not in item.text().lower():
                            should_show = False
                            break

            self.company_table.setRowHidden(row, not should_show)

    def select_all_changed(self, state):
        if state == Qt.CheckState.Checked:
            self.company_table.selectAll()
        else:
            self.company_table.clearSelection()

    def populate_festivals(self):
        logging.info("Starting festival population")
        try:
            festivals = self.firestore_service.get_festivals()
            logging.info(f"Fetched {len(festivals)} festivals")

            logging.info("Clearing festival combo box")
            self.festival_combo.clear()

            logging.info("Adding 'Select a festival' item")
            self.festival_combo.addItem("Select a festival")

            logging.info("Adding festivals to combo box")
            for festival in festivals:
                logging.debug(f"Adding festival: {festival}")
                self.festival_combo.addItem(str(festival))

            logging.info("Setting current index to 0")
            self.festival_combo.setCurrentIndex(0)

            logging.info("Disabling buttons")
            try:
                self.set_buttons_enabled(False)
            except AttributeError as e:
                logging.warning(f"Some buttons may not be initialized yet: {e}")

            logging.info("Festivals populated successfully")
        except Exception as e:
            logging.error(f"Error populating festivals: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load festivals: {str(e)}")


    def on_header_clicked(self, logical_index):
        if self.current_sort_column == logical_index:
            self.current_sort_order = Qt.SortOrder.DescendingOrder if self.current_sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            self.current_sort_order = Qt.SortOrder.AscendingOrder
        self.current_sort_column = logical_index
        self.sort_table(logical_index)

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

            if festival == "Select a festival":
                self.company_table.setRowCount(0)
                return

            logging.info(f"Loading companies for collection: {collection}, festival: {festival}")
            companies = self.firestore_service.get_companies(collection, festival)

            self.company_table.setSortingEnabled(False)
            self.company_table.clear()
            headers = self.get_headers_for_collection(collection)
            self.company_table.setColumnCount(len(headers))
            self.company_table.setHorizontalHeaderLabels(headers)

            self.company_table.setRowCount(len(companies))
            for row, company in enumerate(companies):
                for col, header in enumerate(headers):
                    if header == "ID":
                        value = company.get('Id', '')
                    else:
                        value = self.get_company_value(company, header, collection)
                    item = QTableWidgetItem(str(value))
                    self.company_table.setItem(row, col, item)

            self.company_table.resizeColumnsToContents()

            if not companies:
                logging.info(f"No companies found for collection: {collection}, festival: {festival}")
                QMessageBox.information(self, "No Data", "No companies found for the selected criteria.")

            self.update_filter_inputs()

            if self.current_sort_column != -1:
                if self.get_headers_for_collection(collection)[self.current_sort_column] in ["Igény", "Kiadott"]:
                    self.sort_table(self.current_sort_column)
                else:
                    self.company_table.sortItems(self.current_sort_column, self.current_sort_order)

            self.company_table.setSortingEnabled(True)
            logging.info("Companies loaded successfully")

        except Exception as e:
            logging.error(f"Error loading companies: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")

    def get_current_collection(self):
        return "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"

    def get_company_value(self, company, header, collection):
        field_mapping = self.get_field_mapping(collection)
        field = next((f for f, h in field_mapping.items() if h == header), None)
        if field is None:
            return ""

        value = company.get(field, "")
        if header == "Igény":
            return str(value) if value is not None else ""
        elif header == "Kiadott":
            return str(company.get('sn_count', 0))
        elif header in ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín", "Bázis Leszerelés"]:
            return "Van" if value else "Nincs"
        elif header in ["Last Modified", "LastAdded"]:
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            return str(value) if value else ""
        else:
            return str(value)

    def apply_filters(self):
        for row in range(self.company_table.rowCount()):
            should_show = True
            for col, filter_input in enumerate(self.filter_inputs):
                filter_text = filter_input.text().lower()
                if filter_text:
                    item = self.company_table.item(row, col)
                    if item is None or filter_text not in item.text().lower():
                        should_show = False
                        break
            self.company_table.setRowHidden(row, not should_show)

    def update_filter_inputs(self):
        # Clear existing filter inputs
        for input in self.filter_inputs:
            input.deleteLater()
        self.filter_inputs.clear()

        # Clear the filter layout
        while self.filter_layout.count():
            item = self.filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new filter inputs
        headers = self.get_headers_for_collection(self.get_current_collection())
        for header in headers:
            filter_input = QLineEdit()
            filter_input.setPlaceholderText(f"Filter {header}...")
            filter_input.textChanged.connect(self.apply_filters)
            self.filter_layout.addWidget(filter_input)
            self.filter_inputs.append(filter_input)

    def on_collection_changed(self):
        self.load_companies()
        self.update_filter_inputs()

    # Existing filter_companies method (keep for backwards compatibility)
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

    def get_headers_for_collection(self, collection):
        common_headers = ["ID", "Name", "Program"]
        if collection == "Company_Install":
            specific_headers = ["Igény", "Kiadott", "Felderítés", "Telepítés", "Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        else:  # Company_Demolition
            specific_headers = ["Bontás", "Felszerelés", "Bázis Leszerelés"]

        # Add the new "LastAdded" field
        return common_headers + ["LastAdded"] + specific_headers + ["Last Modified"]

    def update_filter_inputs(self):
        # Clear existing filter inputs
        for input in self.filter_inputs:
            input.deleteLater()
        self.filter_inputs.clear()

        # Clear the filter layout
        while self.filter_layout.count():
            item = self.filter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new filter inputs
        headers = self.get_headers_for_collection(self.get_current_collection())
        for header in headers:
            filter_input = QLineEdit()
            filter_input.setPlaceholderText(f"Filter {header}...")
            filter_input.textChanged.connect(self.apply_filters)
            self.filter_layout.addWidget(filter_input)
            self.filter_inputs.append(filter_input)

    def open_company_details(self, index):
        try:
            company_id = self.company_table.item(index.row(), 0).text()  # Assuming ID is in the first column (index 0)
            collection = self.get_current_collection()
            company_data = self.firestore_service.get_company(collection, company_id)

            if company_data is None:
                raise ValueError(f"No data found for company ID: {company_id}")

            if collection == "Company_Install":
                details_view = CompanyDetailsViewInstall(self.firestore_service, company_id, self, company_data)
            else:
                details_view = CompanyDetailsViewDemolition(self.firestore_service, company_id, self, company_data)

            details_view.companyUpdated.connect(self.load_companies)
            details_view.exec()
        except Exception as e:
            logging.error(f"Error opening company details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open company details: {str(e)}")

    def add_company(self):
        try:
            collection = self.get_current_collection()
            # Create a new company data dictionary with blank Id and LastModified
            new_company_data = {
                "Id": "",  # Blank Id field
                "CompanyName": "",
                "ProgramName": "",
                "LastModified": "",  # Blank LastModified field
                # Add other fields with default values as needed
            }
            if collection == "Company_Install":
                details_view = CompanyDetailsViewInstall(self.firestore_service, None, self, new_company_data)
            else:
                details_view = CompanyDetailsViewDemolition(self.firestore_service, None, self, new_company_data)
            details_view.companyUpdated.connect(self.load_companies)
            details_view.show()
        except Exception as e:
            logging.error(f"Error adding company: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add company: {str(e)}")

    def export_to_excel(self):
        collection = self.get_current_collection()
        ExcelExporter.export_to_excel(self, self.company_table, collection)

    def bulk_edit(self):
        selected_rows = set()
        for index in self.company_table.selectionModel().selectedRows():
            selected_rows.add(index.row())

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select rows to edit.")
            return

        collection = self.get_current_collection()
        dialog = EditFieldDialog(collection, self)
        if dialog.exec():
            field, value = dialog.get_field_and_value()
            self.apply_bulk_edit(field, value, selected_rows)

    def apply_bulk_edit(self, field, value, selected_rows):
        collection = self.get_current_collection()
        field_mapping = self.get_field_mapping(collection)
        db_field = field_mapping.get(field, field)

        success_count = 0
        fail_count = 0
        not_found_ids = []

        # Disable UI elements during update, should not be....
        self.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            for row in selected_rows:
                company_id = self.company_table.item(row, 1).text()  # Assuming ID is in column 1
                data = {db_field: value}

                try:
                    success = self.firestore_service.update_company(collection, company_id, data)
                    if success:
                        success_count += 1
                        logging.info(f"Successfully updated company: ID={company_id}")
                    else:
                        fail_count += 1
                        not_found_ids.append(company_id)
                        logging.warning(f"Failed to update company: ID={company_id}")
                except Exception as e:
                    logging.error(f"Error updating company {company_id}: {str(e)}")
                    fail_count += 1
                    not_found_ids.append(company_id)

            # Show result message
            self.show_bulk_edit_results(success_count, fail_count, not_found_ids)

        finally:
            # Re-enable UI elements and restore cursor
            self.setEnabled(True)
            QApplication.restoreOverrideCursor()

        # Reload data after all updates
        self.load_companies()

    def show_bulk_edit_results(self, success_count, fail_count, not_found_ids):
        if success_count > 0:
            QMessageBox.information(self, "Bulk Edit Result", f"Successfully updated {success_count} companies.")
        if fail_count > 0:
            error_msg = f"Failed to update {fail_count} companies.\n"
            if not_found_ids:
                error_msg += f"The following IDs were not found or couldn't be updated:\n{', '.join(not_found_ids)}"
            QMessageBox.warning(self, "Bulk Edit Result", error_msg)

    def get_display_value(self, value):
        if isinstance(value, bool):
            return "Van" if value else "Nincs"
        return str(value)

    def get_field_mapping(self, collection):
        common_fields = {
            "Id": "ID",
            "CompanyName": "Name",
            "ProgramName": "Program",
            "LastAdded": "LastAdded",
            "LastModified": "Last Modified"
        }

        if collection == "Company_Install":
            specific_fields = {
                "quantity": "Igény",
                "SN": "Kiadott",
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

    def sort_table(self, column):
        self.company_table.setSortingEnabled(False)
        header = self.company_table.horizontalHeaderItem(column).text()

        def get_key(row):
            item = self.company_table.item(row, column)
            if item is None:
                return -float('inf')  # Place empty cells at the beginning
            value = item.text().strip()
            if header in ["Igény", "Kiadott"]:
                try:
                    return int(value)
                except ValueError:
                    return -float('inf')  # Place non-numeric values at the beginning
            return value

        row_count = self.company_table.rowCount()
        rows = list(range(row_count))
        sorted_rows = sorted(rows, key=get_key, reverse=(self.current_sort_order == Qt.SortOrder.DescendingOrder))

        # Perform the row swapping
        for i, source_row in enumerate(sorted_rows):
            if i != source_row:
                self.company_table.insertRow(i)
                for col in range(self.company_table.columnCount()):
                    self.company_table.setItem(i, col, self.company_table.takeItem(source_row + 1, col))
                self.company_table.removeRow(source_row + 1)

        self.current_sort_column = column
        self.current_sort_order = Qt.SortOrder.DescendingOrder if self.current_sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder

        self.company_table.setSortingEnabled(True)
        self.company_table.horizontalHeader().setSortIndicator(column, self.current_sort_order)


    def on_header_clicked(self, logical_index):
        logging.debug(f"Header clicked: column {logical_index}")
        if self.current_sort_column == logical_index:
            self.current_sort_order = Qt.SortOrder.DescendingOrder if self.current_sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            self.current_sort_order = Qt.SortOrder.AscendingOrder
        self.current_sort_column = logical_index
        self.sort_table(logical_index)
        logging.debug(f"Sorting completed for column {logical_index}, order: {self.current_sort_order}")


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