from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QTableView, QLineEdit, QWidget, QPushButton, QHBoxLayout, QMessageBox, QApplication
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QThread
from pythonrunnerapp.src.dynamic_firestore_model import DynamicFirestoreModel
from pythonrunnerapp.src.dynamic_filter_proxy_model import DynamicFilterProxyModel
#from src.firestore_listener import FirestoreListener
from pythonrunnerapp.src.firestore_listener import FirestoreListener
from pythonrunnerapp.src.company_details_view_install import CompanyDetailsViewInstall
from pythonrunnerapp.src.company_details_view_demolition import CompanyDetailsViewDemolition
from pythonrunnerapp.src.edit_field_dialog import EditFieldDialog
import logging

class MainWindow(QMainWindow):
    def __init__(self, firestore_service):
        super().__init__()
        self.firestore_service = firestore_service
        self.pending_updates = []
        self.listener = None  # Initialize listener attribute
        self.setup_ui()
        self.setup_models()
        self.setup_listener()
        self.setup_update_timer()

    def setup_ui(self):
        self.setWindowTitle("Company Management System")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search_input)

        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.MultiSelection)
        self.table_view.doubleClicked.connect(self.open_company_details)
        layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Company")
        self.add_button.clicked.connect(self.add_company)
        button_layout.addWidget(self.add_button)

        self.bulk_edit_button = QPushButton("Bulk Edit")
        self.bulk_edit_button.clicked.connect(self.bulk_edit)
        button_layout.addWidget(self.bulk_edit_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_data)
        button_layout.addWidget(self.refresh_button)

        layout.addLayout(button_layout)

    def setup_models(self):
        try:
            self.source_model = DynamicFirestoreModel(self)
            self.proxy_model = DynamicFilterProxyModel(self)
            self.proxy_model.setSourceModel(self.source_model)
            self.table_view.setModel(self.proxy_model)

            all_data = self.firestore_service.get_all_documents("Company_Install")
            self.source_model.update_data(all_data)
        except Exception as e:
            logging.error(f"Error setting up models: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to set up data models: {str(e)}")

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

    def process_updates(self):
        if not self.pending_updates:
            return

        logging.debug(f"Processing {len(self.pending_updates)} updates")
        try:
            self.source_model.beginResetModel()
            while self.pending_updates:
                data, change_type = self.pending_updates.pop(0)
                if change_type == 'REMOVED':
                    self.source_model.remove_item(data['Id'])
                else:
                    self.source_model.update_single_item(data)
            self.source_model.endResetModel()
            self.proxy_model.invalidate()
        except Exception as e:
            logging.error(f"Error processing updates: {e}", exc_info=True)

    def setup_update_timer(self):
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.process_updates)
        self.update_timer.start(5000)  # Process updates every 5 seconds

    @pyqtSlot(str)
    def on_search_changed(self, text):
        logging.debug(f"Search text changed: {text}")
        self.proxy_model.setFilterFixedString(text)

    def open_company_details(self, index):
        try:
            company_id = self.proxy_model.data(self.proxy_model.index(index.row(), 0))
            logging.debug(f"Opening details for company ID: {company_id}")
            company_data = self.firestore_service.get_company("Company_Install", company_id)
            if company_data:
                details_view = CompanyDetailsViewInstall(self.firestore_service, company_id, self, company_data)
                details_view.companyUpdated.connect(self.refresh_data)
                details_view.exec()
            else:
                QMessageBox.warning(self, "Not Found", f"Company with ID {company_id} not found.")
        except Exception as e:
            logging.error(f"Error opening company details: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open company details: {str(e)}")

    def add_company(self):
        try:
            logging.debug("Adding new company")
            new_company_data = {"Id": self.firestore_service.generate_id()}
            details_view = CompanyDetailsViewInstall(self.firestore_service, None, self, new_company_data)
            details_view.companyUpdated.connect(self.refresh_data)
            details_view.exec()
        except Exception as e:
            logging.error(f"Error adding company: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to add company: {str(e)}")

    def bulk_edit(self):
        selected_rows = self.table_view.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select rows to edit.")
            return

        try:
            logging.debug(f"Bulk editing {len(selected_rows)} companies")
            dialog = EditFieldDialog("Company_Install", self)
            if dialog.exec():
                field, value = dialog.get_field_and_value()
                self.apply_bulk_edit(field, value, selected_rows)
        except Exception as e:
            logging.error(f"Error in bulk edit: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to perform bulk edit: {str(e)}")

    def process_updates(self):
        if not self.pending_updates:
            return

        logging.debug(f"Processing {len(self.pending_updates)} updates")
        try:
            self.source_model.beginResetModel()
            while self.pending_updates:
                data, change_type = self.pending_updates.pop(0)
                if change_type == 'REMOVED':
                    self.source_model.remove_item(data['Id'])
                else:
                    self.source_model.update_single_item(data)
            self.source_model.endResetModel()
            self.proxy_model.invalidate()
        except Exception as e:
            logging.error(f"Error processing updates: {e}", exc_info=True)

    def setup_update_timer(self):
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.process_updates)
        self.update_timer.start(5000)  # Process updates every 5 seconds

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

        QMessageBox.information(self, "Bulk Edit Result", f"Successfully updated {success_count} out of {len(selected_rows)} companies.")
        self.refresh_data()

    def refresh_data(self):
        try:
            logging.debug("Refreshing data")
            all_data = self.firestore_service.get_all_documents("Company_Install")
            self.source_model.update_data(all_data)
        except Exception as e:
            logging.error(f"Error refreshing data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to refresh data: {str(e)}")

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