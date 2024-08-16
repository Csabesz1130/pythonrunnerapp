import csv
import sys

from PyQt6.QtGui import QKeySequence, QShortcut, QAction, QFont, QUndoStack
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QTableView, QLineEdit, QWidget, QPushButton, QHBoxLayout, \
    QMessageBox, QApplication, QLabel, QSpinBox, QDialog, QComboBox, QFileDialog, QRadioButton
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QThread, QSortFilterProxyModel

from add_company_dialog import AddCompanyDialog
from auto_complete_line_edit import AutoCompleteLineEdit
from bulk_edit_dialog import BulkEditDialog
from company_details_view import CompanyDetailsView
from data_cache import DataCache
from dynamic_firestore_model import DynamicFirestoreModel
from festival_selection_dialog import FestivalSelectionDialog
from firestore_service import FirestoreService
from paginated_firestore_model import PaginatedFirestoreModel
from pythonrunnerapp.src.dynamic_filter_proxy_model import DynamicFilterProxyModel
from pythonrunnerapp.src.firestore_listener import FirestoreListener
from pythonrunnerapp.src.company_details_view_install import CompanyDetailsViewInstall
from pythonrunnerapp.src.company_details_view_demolition import CompanyDetailsViewDemolition
from pythonrunnerapp.src.edit_field_dialog import EditFieldDialog
from boolean_color_delegate import BooleanColorDelegate
from sn_statistics_dashboard import SNStatisticsDashboard
from add_company_dialog import AddCompanyDialog
from telephely_importer import TelephalyImporter
import logging

from toggle_view import ToggleView


class MainWindow(QMainWindow):
    COLUMN_NAMES = {
        "10": "Quantity",
        "6": "SN Count",
        "5": "Status",
        "11": "Last Modified",
        "9": "Felderítés",
        "1": "Telepítés",
        "7": "Szoftver",
        "2": "Param",
        "8": "Elosztó",
        "3": "Áram",
        "4": "Hálózat"
    }

    def __init__(self, firestore_service: FirestoreService):
        super().__init__()
        self.firestore_service = firestore_service
        self.undo_stack = QUndoStack(self)
        self.current_festival = None
        self.page_size = 100
        self.current_page = 0
        self.total_pages = 0
        self.setup_ui()
        self.setup_models()
        self.select_initial_festival()

    def setup_ui(self):
        self.setWindowTitle("Festival Company Management")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top controls
        top_layout = QHBoxLayout()

        self.festival_combo = QComboBox()
        self.festival_combo.addItems(self.firestore_service.get_festivals())
        self.festival_combo.currentTextChanged.connect(self.change_festival)
        top_layout.addWidget(self.festival_combo)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search companies...")
        self.search_input.textChanged.connect(self.on_search_changed)
        top_layout.addWidget(self.search_input)

        self.company_install_radio = QRadioButton("Company_Install")
        self.company_demolition_radio = QRadioButton("Company_Demolition")
        self.company_install_radio.setChecked(True)
        self.company_install_radio.toggled.connect(self.on_collection_changed)
        self.company_demolition_radio.toggled.connect(self.on_collection_changed)
        top_layout.addWidget(self.company_install_radio)
        top_layout.addWidget(self.company_demolition_radio)

        main_layout.addLayout(top_layout)

        # ToggleView
        self.toggle_view = ToggleView(self.firestore_service)
        main_layout.addWidget(self.toggle_view)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.previous_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        main_layout.addLayout(pagination_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        self.add_company_button = QPushButton("Add Company")
        self.add_company_button.clicked.connect(self.add_company)
        self.bulk_edit_button = QPushButton("Bulk Edit")
        self.bulk_edit_button.clicked.connect(self.bulk_edit)
        button_layout.addWidget(self.add_company_button)
        button_layout.addWidget(self.bulk_edit_button)
        main_layout.addLayout(button_layout)

        # Menu Bar
        self.setup_menu_bar()

        logging.info("UI setup completed")

    def toggle_view_action(self):
        # This method will be called when the "Toggle View" menu item is clicked
        if hasattr(self, 'toggle_view'):
            self.toggle_view.toggle_view()
        else:
            logging.warning("toggle_view attribute not found")

    def on_collection_changed(self):
        if self.company_install_radio.isChecked():
            self.current_collection = "Company_Install"
        else:
            self.current_collection = "Company_Demolition"
        self.load_data()

    def filter_column(self, column):
        index = self.table_view.model().index(self.filter_row, column)
        filter_text = self.table_view.model().data(index, Qt.ItemDataRole.EditRole)

        if isinstance(self.table_view.model(), QSortFilterProxyModel):
            source_model = self.table_view.model().sourceModel()
        else:
            source_model = self.table_view.model()

        if isinstance(source_model, DynamicFirestoreModel):
            source_model.set_filter(column, filter_text)
            self.table_view.model().invalidateFilter()

        logging.info(f"Filtering column {column} with text: {filter_text}")

    def show_about(self):
        QMessageBox.about(self, "About", "Company Management System\nVersion 1.0\n\nDeveloped by Your Name/Company")

    def setup_models(self):
        self.source_model = DynamicFirestoreModel()
        self.proxy_model = DynamicFilterProxyModel(self.firestore_service)
        self.proxy_model.setSourceModel(self.source_model)
        self.toggle_view.set_model(self.proxy_model)

    def load_data(self):
        if not self.current_festival:
            return

        try:
            start = self.current_page * self.page_size
            end = start + self.page_size
            data = self.firestore_service.get_companies_paginated(self.current_festival, start, end)

            if not data:
                logging.warning(f"No data returned for page {self.current_page + 1}")
                self.source_model.update_data([])
                self.total_pages = 1
                self.current_page = 0
            else:
                self.source_model.update_data(data)
                total_companies = self.firestore_service.get_total_companies(self.current_festival)
                self.total_pages = max(1, -(-total_companies // self.page_size))  # Ceiling division

            self.update_pagination_controls()
            logging.info(f"Loaded page {self.current_page + 1} of {self.total_pages}")
        except Exception as e:
            logging.error(f"Error loading page data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load page data: {str(e)}")

    def setup_auto_refresh(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def auto_refresh(self):
        logging.info("Auto-refreshing data")
        self.load_page_data()

    def toggle_view(self):
        self.toggle_view.toggle_view()

    def import_company(self):
        try:
            if not self.current_festival:
                QMessageBox.warning(self, "Warning", "Please select a festival before importing data.")
                return

            file_name, _ = QFileDialog.getOpenFileName(self, "Import Company Data", "", "Excel Files (*.xlsx *.xls);;All Files (*)")
            if file_name:
                importer = TelephalyImporter(self.firestore_service)
                imported_count, error_count = importer.import_from_excel(file_name, self.current_festival, self)

                if imported_count > 0:
                    self.load_page_data()  # Refresh the view
                    QMessageBox.information(self, "Import Complete",
                                            f"Company data has been imported.\n"
                                            f"Imported: {imported_count}\n"
                                            f"Errors: {error_count}\n\n"
                                            f"Please check the log for details on any errors.")
                else:
                    QMessageBox.warning(self, "Import Warning",
                                        f"No data was imported.\n"
                                        f"Errors: {error_count}\n\n"
                                        f"Please check the log for details.")
            else:
                logging.info("Company data import cancelled by user")
        except Exception as e:
            logging.error(f"Error during Company data import: {e}", exc_info=True)
            QMessageBox.critical(self, "Import Error", f"An unexpected error occurred: {str(e)}\n\nPlease check the log for details.")

    def setup_menu_bar(self):
        menubar = self.menuBar()
        self.file_menu = menubar.addMenu("File")
        self.edit_menu = menubar.addMenu("Edit")
        self.view_menu = menubar.addMenu("View")
        self.help_menu = menubar.addMenu("Help")

        # File menu actions
        self.file_menu.addAction("Export Data", self.export_data)
        self.file_menu.addAction("Import Data", self.import_company)
        self.file_menu.addAction("Exit", self.close)

        # Edit menu actions
        undo_action = self.undo_stack.createUndoAction(self, "Undo")
        redo_action = self.undo_stack.createRedoAction(self, "Redo")
        self.edit_menu.addAction(undo_action)
        self.edit_menu.addAction(redo_action)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)

        # View menu actions
        self.view_menu.addAction("Change View", self.toggle_view_action)

        # Help menu actions
        self.help_menu.addAction("About", self.show_about)

    def prompt_for_festival(self):
        festivals = self.firestore_service.get_festivals()
        self.festival_combo.addItems(festivals)
        if festivals:
            self.festival_combo.setCurrentIndex(0)
            self.on_festival_changed(festivals[0])

    def on_festival_changed(self, festival):
        self.current_festival = festival
        self.current_page = 0
        self.load_page_data()

    @pyqtSlot(str)
    def on_search_changed(self, text):
        try:
            self.proxy_model.setFilterFixedString(text)
        except Exception as e:
            logging.error(f"Error during search: {e}", exc_info=True)
            QMessageBox.critical(self, "Search Error", f"An error occurred during search: {str(e)}")

    def load_page_data(self):
        if not self.current_festival:
            return

        try:
            start = self.current_page * self.page_size
            end = start + self.page_size
            data = self.firestore_service.get_companies_paginated(self.current_festival, start, end)

            if not data:
                logging.warning(f"No data returned for page {self.current_page + 1}")
                self.source_model.update_data([])
                self.total_pages = 1
                self.current_page = 0
            else:
                self.source_model.update_data(data)
                total_companies = self.firestore_service.get_total_companies(self.current_festival)
                self.total_pages = max(1, -(-total_companies // self.page_size))  # Ceiling division

            self.update_pagination_controls()
            logging.info(f"Loaded page {self.current_page + 1} of {self.total_pages}")

            # Reset the filter after loading new data
            current_filter = self.search_input.text()
            self.proxy_model.setFilterFixedString(current_filter)
        except Exception as e:
            logging.error(f"Error loading page data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load page data: {str(e)}")

    def setup_connections(self):
        self.festival_combo.currentTextChanged.connect(self.on_festival_changed)
        self.search_input.textChanged.connect(self.on_search_changed)
        self.prev_button.clicked.connect(self.previous_page)
        self.next_button.clicked.connect(self.next_page)
        self.add_company_button.clicked.connect(self.add_company)
        self.bulk_edit_button.clicked.connect(self.bulk_edit)
        self.festival_combo.currentTextChanged.connect(self.on_festival_changed)

    def select_initial_festival(self):
        try:
            logging.info("Selecting initial festival")
            festivals = self.firestore_service.get_festivals()
            if not festivals:
                logging.error("No festivals retrieved")
                QMessageBox.critical(self, "Error", "Unable to retrieve festivals. Please check your connection and try again.")
                return

            dialog = FestivalSelectionDialog(festivals, self)
            if dialog.exec():
                selected_festival = dialog.get_selected_festival()
                logging.info(f"Initial festival selected: {selected_festival}")
                self.current_festival = selected_festival
                self.festival_combo.setCurrentText(selected_festival)
                QTimer.singleShot(100, self.load_initial_data)
            else:
                logging.warning("No festival selected, closing application")
                self.close()
        except Exception as e:
            logging.error(f"Error in select_initial_festival: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def load_initial_data(self):
        try:
            logging.info(f"Loading initial data for festival: {self.current_festival}")
            self.load_page_data()
            self.update_pagination_controls()
        except Exception as e:
            logging.error(f"Error in load_initial_data: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {str(e)}")

    def focus_search(self):
        self.search_input.setFocus()

    def export_data(self):
        try:
            file_name, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv);;All Files (*)")
            if file_name:
                # Implement the actual export logic here
                # This is a placeholder implementation
                data = self.get_current_data()
                with open(file_name, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(data[0].keys())  # Write headers
                    for row in data:
                        writer.writerow(row.values())
                QMessageBox.information(self, "Export", f"Data exported to {file_name}")
                logging.info(f"Data exported to file: {file_name}")
            else:
                logging.info("Data export cancelled by user")
        except Exception as e:
            logging.error(f"Error during data export: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")

    def get_current_data(self):
        # This method should return the current data in the model
        # Implement according to your data structure
        data = []
        for row in range(self.proxy_model.rowCount()):
            row_data = {}
            for column in range(self.proxy_model.columnCount()):
                header = self.proxy_model.headerData(column, Qt.Orientation.Horizontal)
                value = self.proxy_model.data(self.proxy_model.index(row, column))
                row_data[header] = value
            data.append(row_data)
        return data

    def undo_action(self):
        # Implement undo functionality
        QMessageBox.information(self, "Undo", "Undo functionality not yet implemented.")
        logging.info("Undo action triggered")

    def redo_action(self):
        # Implement redo functionality
        QMessageBox.information(self, "Redo", "Redo functionality not yet implemented.")
        logging.info("Redo action triggered")

    def load_festivals(self):
        festivals = self.firestore_service.get_festivals()
        self.festival_combo.clear()
        self.festival_combo.addItems(festivals)
        if festivals:
            self.festival_combo.setCurrentIndex(0)

    def update_pagination_controls(self):
        self.page_label.setText(f"Page {self.current_page + 1} of {self.total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1)

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page_data()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_page_data()

    def change_festival(self, festival):
        logging.info(f"Changing festival to: {festival}")
        self.current_festival = festival
        self.current_page = 0
        self.load_page_data()
        self.update_pagination_controls()

    def add_company(self):
        dialog = AddCompanyDialog(self.firestore_service, self)
        dialog.companyAdded.connect(self.on_company_added)
        dialog.exec()

    def on_company_added(self, new_company):
        self.model.add_item(new_company)
        self.table_view.resizeColumnsToContents()

    @pyqtSlot(int)
    def go_to_page(self, page):
        self.model.load_page(page - 1)
        self.update_pagination_controls()

    def exception_hook(exc_type, exc_value, exc_traceback):
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(None, "Error", "An unexpected error occurred. Please check the log for details.")

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(self, "Error", "An unexpected error occurred. Please check the log for details.")

    def process_updates(self):
        if not self.pending_updates:
            return

        logging.debug(f"Processing {len(self.pending_updates)} updates")
        try:
            for data, change_type in self.pending_updates:
                if change_type == 'REMOVED':
                    self.source_model.remove_item(data['Id'])
                else:
                    self.source_model.update_single_item(data)

            self.pending_updates.clear()
            self.table_view.reset()  # Force refresh of the view
            logging.debug("Updates processed and view refreshed")
        except Exception as e:
            logging.error(f"Error processing updates: {e}", exc_info=True)

    def setup_listener(self):
        try:
            self.listener = FirestoreListener(self.firestore_service, "Company_Install")
            self.listener.data_changed.connect(self.queue_update)
            self.listener.start_listening()
        except Exception as e:
            logging.error(f"Error setting up Firestore listener: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to set up real-time updates: {str(e)}")

    @pyqtSlot(dict, str)
    def queue_update(self, data, change_type):
        logging.debug(f"Queuing {change_type} update for ID: {data.get('Id', 'Unknown ID')}")
        self.pending_updates.append((data, change_type))

    def setup_update_timer(self):
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.process_updates)
        self.update_timer.start(5000)  # Process updates every 5 seconds

    @pyqtSlot()
    def refresh_data(self):
        self.cache.clear()
        self.model.load_page(self.model.current_page)

    def show_sn_dashboard(self):
        dashboard = SNStatisticsDashboard(self.firestore_service)
        dashboard.setWindowTitle("SN Statistics Dashboard")
        dashboard.resize(800, 600)  # Set an initial size
        dashboard.show()

    def open_company_details(self, index):
        try:
            row = self.proxy_model.mapToSource(index).row()
            company_data = self.source_model._data[row]
            company_id = company_data.get('Id')

            if not company_id:
                raise ValueError("Company ID not found in data")

            logging.debug(f"Opening details for company ID: {company_id}")

            # Determine the collection based on the company data
            collection = "Company_Install" if 'quantity' in company_data else "Company_Demolition"

            details_view = CompanyDetailsView(self.firestore_service, company_id, collection, self)
            details_view.companyUpdated.connect(self.load_page_data)  # Refresh after update
            details_view.exec()
        except Exception as e:
            logging.error(f"Error opening company details: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open company details: {str(e)}")

    def bulk_edit(self):
        selected_rows = self.toggle_view.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select companies to edit.")
            return
        try:
            dialog = BulkEditDialog(self.proxy_model, selected_rows, self.firestore_service, self)
            if dialog.exec():
                self.load_page_data()
                self.toggle_view.clear_selection()
        except Exception as e:
            logging.error(f"Error during bulk edit: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An error occurred during bulk edit: {str(e)}")


    @pyqtSlot()
    def add_company(self):
        dialog = AddCompanyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                new_company = {
                    "CompanyName": dialog.name_edit.text(),
                    "ProgramName": dialog.program_edit.text(),
                    # Add other default fields as necessary
                }
                # Add to Firestore
                doc_ref = self.firestore_service.db.collection("Company_Install").add(new_company)
                new_company["Id"] = doc_ref[1].id  # Assuming the ID is returned by Firestore

                # Add to model
                self.model.add_item(new_company)
                QMessageBox.information(self, "Success", "Company added successfully!")
            except Exception as e:
                logging.error(f"Error adding company: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add company: {str(e)}")

    def apply_bulk_edit(self, field, value, selected_rows):
        success_count = 0
        for index in selected_rows:
            company_id = self.proxy_model.data(self.proxy_model.index(index.row(), 0))
            try:
                success = self.firestore_service.update_company("Company_Install", company_id, {field: value})
                if success:
                    success_count += 1
                    logging.debug(f"Successfully updated company: {company_id}")
                else:
                    logging.warning(f"Failed to update company: {company_id}")
            except Exception as e:
                logging.error(f"Error updating company {company_id}: {e}", exc_info=True)

        QMessageBox.information(self, "Bulk Edit Result",
                                f"Successfully updated {success_count} out of {len(selected_rows)} companies.")
        self.refresh_data()

    def closeEvent(self, event):
        logging.debug("Closing main window")
        try:
            if hasattr(self, 'listener') and self.listener:
                self.listener.stop_listening()
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
            # Wait for background threads to finish
            QApplication.processEvents()
            QThread.msleep(500)  # Wait for 500ms
        except Exception as e:
            logging.error(f"Error during application shutdown: {e}", exc_info=True)
        super().closeEvent(event)
