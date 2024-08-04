from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import pandas as pd
import logging
from src.import_logger import ImportLogger
from src.import_undo_redo_manager import ImportUndoRedoManager

class SiteProcessor(QObject):
    processing_complete = pyqtSignal(str)

    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.import_logger = ImportLogger()
        self.undo_redo_manager = ImportUndoRedoManager(firestore_service)

    def import_sites(self):
        logging.info("Starting site import process")
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            logging.info("No file selected, import cancelled")
            return

        try:
            logging.info(f"Importing sites from file: {file_path}")
            self.import_logger.start_import(file_path)
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                try:
                    site_data = {
                        "Id": str(row["ID"]),
                        "CompanyName": str(row["Telephely név"]),
                        "CompanyCode": str(row["Telephely kód"]),
                        "quantity": int(row["Összes terminál igény"]),
                        "ProgramName": self.parent().festival_combo.currentText(),
                        "LastModified": self.firestore_service.server_timestamp(),
                        "LastAdded": self.firestore_service.server_timestamp(),
                        "1": "TELEPÍTHETŐ",
                        "2": "KIADVA",
                        "3": False,
                        "4": False,
                        "5": False,
                        "6": False,
                        "7": False,
                        "8": False,
                        "9": False,
                    }

                    existing_company = self.firestore_service.get_company("Company_Install", site_data["Id"])
                    if existing_company:
                        self.undo_redo_manager.record_action('update', "Company_Install", site_data["Id"], existing_company, site_data)
                        self.firestore_service.update_company("Company_Install", site_data["Id"], site_data)
                        self.import_logger.log_updated(site_data["Id"])
                    else:
                        self.undo_redo_manager.record_action('add', "Company_Install", site_data["Id"], None, site_data)
                        self.firestore_service.add_company("Company_Install", site_data)
                        self.import_logger.log_added(site_data["Id"])
                except Exception as e:
                    self.import_logger.log_error(site_data["Id"], str(e))

            self.import_logger.end_import()
            report = self.import_logger.generate_report()
            self.processing_complete.emit(report)
            logging.info("Site import process completed")
        except Exception as e:
            logging.error(f"Error importing site data: {e}", exc_info=True)
            QMessageBox.critical(None, "Import Error", f"An error occurred while importing site data: {str(e)}")