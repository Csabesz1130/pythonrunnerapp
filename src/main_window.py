import csv
import logging
import os
import sys
import time
from datetime import datetime

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QComboBox, QRadioButton, QLineEdit, QButtonGroup, QMessageBox,
                             QFileDialog, QApplication, QCheckBox, QAbstractItemView, QProgressBar, QLabel,
                             QProgressDialog)
from PyQt6.QtCore import Qt, QTimer, QThreadPool

from src.bulk_edit_worker import BulkEditWorker
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

            logging.info("Connecting signals")
            self.connect_signals()

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

            # Add progress bar and label
            progress_layout = QHBoxLayout()
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(True)
            progress_layout.addWidget(self.progress_bar)

            self.progress_label = QLabel("Ready", self)
            progress_layout.addWidget(self.progress_label)

            self.main_layout.addLayout(progress_layout)

            self.progress_bar.hide()
            self.progress_label.hide()

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
                self.load_companies(force_reload=True)
            else:
                logging.info("No festival selected. Disabling buttons and clearing table.")
                self.set_buttons_enabled(False)
                self.company_table.setRowCount(0)
                self.cached_companies = None  # Clear the cache when no festival is selected
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
        logging.debug("Search text changed, resetting search timer")
        self.search_timer.stop()
        self.search_timer.start(300)  # Wait for 300 ms before filtering

    def filter_companies(self):
        logging.debug("Filtering companies")
        search_text = self.search_input.text().lower()
        for row in range(self.company_table.rowCount()):
            should_show = False
            for col in range(self.company_table.columnCount()):
                item = self.company_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.company_table.setRowHidden(row, not should_show)
        logging.debug("Company filtering complete")

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
        logging.debug(f"Select all checkbox state changed: {state}")
        if state == Qt.CheckState.Checked:
            self.company_table.selectAll()
            logging.debug("All rows selected")
        else:
            self.company_table.clearSelection()
            logging.debug("All row selections cleared")

    def import_sites(self):
        self.site_processor.import_sites()

    def show_import_report(self, report):
        self.import_report_text.setPlainText(report)
        QMessageBox.information(self, "Import Complete", "Site data has been successfully imported/updated. Check the report for details.")

    def undo_import(self):
        self.site_processor.undo_last_import()
        self.load_companies()  # Refresh the company list after undo

    def redo_import(self):
        self.site_processor.redo_last_import()
        self.load_companies()  # Refresh the company list after redo

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

    def load_companies(self, force_reload=False):
        logging.info(f"load_companies called with force_reload={force_reload}")

        if not force_reload and hasattr(self, 'cached_companies'):
            logging.info("Using cached company data")
            self.populate_table(self.cached_companies)
            return

        try:
            collection = self.get_current_collection()
            festival = self.festival_combo.currentText()

            if festival == "Select a festival":
                self.company_table.setRowCount(0)
                return

            logging.info(f"Loading companies for collection: {collection}, festival: {festival}")

            self.progress_bar.setValue(0)
            self.progress_bar.show()
            self.progress_label.setText("Fetching companies...")
            self.progress_label.show()
            QApplication.processEvents()

            companies = self.firestore_service.get_companies(collection, festival)
            self.cached_companies = companies

            self.populate_table(companies)

            logging.info("Companies loaded successfully")

        except Exception as e:
            logging.error(f"Error loading companies: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")
        finally:
            self.progress_bar.hide()
            self.progress_label.hide()

    def populate_table(self, companies):
        logging.info(f"Populating table with {len(companies)} companies")
        self.company_table.setSortingEnabled(False)
        self.company_table.setRowCount(len(companies))

        headers = self.get_headers_for_collection(self.get_current_collection())
        self.company_table.setColumnCount(len(headers))
        self.company_table.setHorizontalHeaderLabels(headers)

        for row, company in enumerate(companies):
            for col, header in enumerate(headers):
                value = self.get_company_value(company, header, self.get_current_collection())
                item = QTableWidgetItem(str(value))
                self.company_table.setItem(row, col, item)

            if row % 100 == 0:
                QApplication.processEvents()
                logging.debug(f"Populated {row} companies")

        self.company_table.resizeColumnsToContents()
        self.update_filter_inputs()

        if self.current_sort_column != -1:
            self.sort_table(self.current_sort_column)

        self.company_table.setSortingEnabled(True)
        logging.info("Table population complete")

    def get_company_value(self, company, header, collection):
        field_mapping = self.get_field_mapping(collection)
        field = next((f for f, h in field_mapping.items() if h == header), None)
        if field is None:
            return ""

        value = company.get(field, "")
        if header in ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]:
            return "Van" if value else "Nincs"
        elif header in ["LastAdded", "Last Modified"]:
            if isinstance(value, datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            return str(value) if value else ""
        elif header == "Igény":
            return str(value) if value is not None else ""
        elif header == "Kiadott":
            return str(company.get('sn_count', 0))
        else:
            return str(value)

    def update_progress(self):
        if self.current_progress < self.target_progress:
            self.current_progress += 1
            self.progress_bar.setValue(self.current_progress)
            QApplication.processEvents()

    def set_progress_target(self, target, label_text):
        self.target_progress = target
        self.progress_label.setText(label_text)
        QApplication.processEvents()

    def hide_progress(self):
        self.progress_bar.hide()
        self.progress_label.hide()

    def finish_loading(self):
        self.company_table.resizeColumnsToContents()
        self.update_filter_inputs()

        if self.current_sort_column != -1:
            if self.get_headers_for_collection(self.get_current_collection())[self.current_sort_column] in ["Igény", "Kiadott"]:
                self.sort_table(self.current_sort_column)
            else:
                self.company_table.sortItems(self.current_sort_column, self.current_sort_order)

        self.company_table.setSortingEnabled(True)
        self.progress_bar.hide()
        logging.info("Companies loaded successfully")

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
        logging.info("Collection changed, reloading companies and updating filter inputs")
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
        logging.debug(f"open_company_details called with index: {index}")
        try:
            company_id = self.company_table.item(index.row(), 0).text()
            logging.debug(f"Company ID: {company_id}")
            collection = self.get_current_collection()
            logging.debug(f"Collection: {collection}")
            company_data = self.firestore_service.get_company(collection, company_id)

            if company_data is None:
                raise ValueError(f"No data found for company ID: {company_id}")

            if collection == "Company_Install":
                details_view = CompanyDetailsViewInstall(self.firestore_service, company_id, self, company_data)
            else:
                details_view = CompanyDetailsViewDemolition(self.firestore_service, company_id, self, company_data)

            # Disconnect any existing connections to avoid multiple triggers
            try:
                details_view.companyUpdated.disconnect()
            except TypeError:
                pass  # No connections to disconnect

            details_view.companyUpdated.connect(self.load_companies)
            logging.debug("Opening company details dialog")
            details_view.exec()
            logging.debug("Company details dialog closed")
        except Exception as e:
            logging.error(f"Error opening company details: {e}", exc_info=True)
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
        selected_rows = set(index.row() for index in self.company_table.selectionModel().selectedRows())

        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select rows to edit.")
            return

        collection = self.get_current_collection()
        dialog = EditFieldDialog(collection, self)

        if dialog.exec():
            field, value = dialog.get_field_and_value()
            if self.confirm_bulk_edit(field, value, len(selected_rows)):
                self.apply_bulk_edit(field, value, selected_rows)

    def confirm_bulk_edit(self, field, value, count):
        msg = f"Are you sure you want to set '{field}' to '{value}' for {count} selected companies?"
        reply = QMessageBox.question(self, 'Confirm Bulk Edit', msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        return reply == QMessageBox.StandardButton.Yes

    def get_display_value(self, field, value):
        if field in ['3', '4', '5', '6', '7', '8', '9']:
            return "Van" if value else "Nincs"
        return str(value)

    def validate_input(self, field, value):
        logging.debug(f"Validating input: field={field}, value={value}")

        # Validate boolean fields
        boolean_fields = ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        if field in boolean_fields:
            if value not in ["Van", "Nincs"]:
                QMessageBox.warning(self, "Invalid Input", f"'{field}' must be either 'Van' or 'Nincs'.")
                return False

        # Validate Felderítés field
        if field == "Felderítés":
            valid_values = ["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"]
            if value not in valid_values:
                QMessageBox.warning(self, "Invalid Input", f"'{field}' must be one of: {', '.join(valid_values)}")
                return False

        # Validate Telepítés field
        if field == "Telepítés":
            valid_values = ["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"]
            if value not in valid_values:
                QMessageBox.warning(self, "Invalid Input", f"'{field}' must be one of: {', '.join(valid_values)}")
                return False

        # Validate Igény field (assuming it should be a non-negative integer)
        if field == "Igény":
            try:
                int_value = int(value)
                if int_value < 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", f"'{field}' must be a non-negative integer.")
                return False

        # Add more validation rules for other fields as needed

        logging.debug("Input validation passed")
        return True

    def apply_bulk_edit(self, field, value, selected_rows):
        if not self.validate_input(field, value):
            return

        collection = self.get_current_collection()
        field_mapping = self.get_field_mapping(collection)
        db_field = field_mapping.get(field, field)

        progress_dialog = QProgressDialog("Applying bulk edit...", "Cancel", 0, len(selected_rows), self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setAutoReset(False)
        progress_dialog.setAutoClose(False)
        progress_dialog.show()

        success_count = 0
        fail_count = 0
        not_found_ids = []

        start_time = time.time()
        last_update_time = start_time

        try:
            for i, row in enumerate(selected_rows):
                if progress_dialog.wasCanceled():
                    break

                current_time = time.time()
                if current_time - last_update_time > 1:  # Rate limiting: update max once per second
                    progress_dialog.setValue(i)
                    QApplication.processEvents()
                    last_update_time = current_time

                company_id = self.company_table.item(row, 0).text()
                data = {db_field: self.convert_value_for_db(db_field, value)}

                try:
                    success = self.firestore_service.update_company_transaction(collection, company_id, data)
                    if success:
                        success_count += 1
                        self.update_table_row(row, field, value)
                        self.update_cached_company(company_id, db_field, value)
                        self.log_audit("bulk_edit", company_id, {field: value})
                    else:
                        fail_count += 1
                        not_found_ids.append(company_id)
                except Exception as e:
                    logging.error(f"Error updating company {company_id}: {str(e)}")
                    fail_count += 1
                    not_found_ids.append(company_id)

            self.show_bulk_edit_results(success_count, fail_count, not_found_ids)
        except Exception as e:
            logging.error(f"Unexpected error during bulk edit: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during bulk edit: {str(e)}")
        finally:
            progress_dialog.close()
            self.load_companies(force_reload=True)

    def convert_value_for_db(self, field, value):
        if field in ['3', '4', '5', '6', '7', '8', '9']:
            return value == "Van"
        return value

    def update_cached_company(self, company_id, field, value):
        if hasattr(self, 'cached_companies'):
            for company in self.cached_companies:
                if company.get('Id') == company_id:
                    company[field] = value
                    logging.debug(f"Updated company {company_id} in cache: {field}={value}")
                    break

    def log_audit(self, action, company_id, changes):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {action}: Company ID {company_id}, Changes: {changes}"
        with open("audit_log.txt", "a") as log_file:
            log_file.write(log_entry + "\n")
        logging.info(log_entry)

    def bulk_edit_finished(self, success_count, fail_count, not_found_ids):
        self.show_bulk_edit_results(success_count, fail_count, not_found_ids)
        self.load_companies(force_reload=True)

    def show_bulk_edit_results(self, success_count, fail_count, not_found_ids):
        logging.debug(f"Bulk edit results: success={success_count}, fail={fail_count}")
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
            "Id": "Id",
            "CompanyName": "CompanyName",
            "ProgramName": "ProgramName",
            "LastAdded": "LastAdded",
            "LastModified": "LastModified"
        }

        if collection == "Company_Install":
            specific_fields = {
                "Igény": "quantity",
                "Kiadott": "SN",
                "Felderítés": "1",
                "Telepítés": "2",
                "Elosztó": "3",
                "Áram": "4",
                "Hálózat": "5",
                "PTG": "6",
                "Szoftver": "7",
                "Param": "8",
                "Helyszín": "9",
            }
        elif collection == "Company_Demolition":
            specific_fields = {
                "Bontás": "1",
                "Felszerelés": "2",
                "Bázis Leszerelés": "3",
            }
        else:
            logging.warning(f"Unknown collection: {collection}")
            specific_fields = {}

        return {**common_fields, **specific_fields}

    def update_table_row(self, row, field, value):
        column = self.get_column_for_field(field)
        if column is not None:
            display_value = self.get_display_value(field, value)
            item = QTableWidgetItem(str(display_value))
            self.company_table.setItem(row, column, item)
            self.company_table.viewport().update()

    def get_column_for_field(self, field):
        headers = self.get_headers_for_collection(self.get_current_collection())
        try:
            return headers.index(field)
        except ValueError:
            logging.warning(f"Field {field} not found in headers")
            return None

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

    def connect_signals(self):
        logging.debug("Connecting signals")

        # Disconnect existing connections first
        self.company_table.doubleClicked.disconnect()

        # Festival combo box
        self.festival_combo.currentIndexChanged.connect(self.on_festival_changed)

        # Radio buttons for collection selection
        self.install_radio.toggled.connect(self.on_collection_changed)
        self.demolition_radio.toggled.connect(self.on_collection_changed)

        # Search input
        self.search_input.textChanged.connect(self.on_search_text_changed)

        # Company table
        self.company_table.doubleClicked.connect(self.open_company_details)
        self.company_table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        # Select all checkbox
        self.select_all_checkbox.stateChanged.connect(self.select_all_changed)

        # Buttons
        self.export_button.clicked.connect(self.export_to_excel)
        self.import_sites_button.clicked.connect(self.site_processor.import_sites)
        self.refresh_button.clicked.connect(self.load_companies)
        self.bulk_edit_button.clicked.connect(self.bulk_edit)

        # Site processor
        self.site_processor.processing_complete.connect(self.load_companies)

        logging.debug("Signals connected successfully")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        firestore_service = FirestoreService()
        window = MainWindow(firestore_service)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Unhandled exception in main thread: {e}", exc_info=True)
        QMessageBox.critical(None, "Critical Error", f"An unhandled error occurred: {str(e)}\n\nThe application will now close.")
        sys.exit(1)