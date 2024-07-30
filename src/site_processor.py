import logging

import pandas as pd
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

class SiteProcessor(QObject):
    processing_complete = pyqtSignal()

    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service

    def import_sites(self):
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                site_data = {
                    "Id": str(row["ID"]),
                    "CompanyName": str(row["Telephely név"]),
                    "CompanyCode": str(row["Telephely kód"]),
                    "quantity": int(row["Összes terminál igény"]),
                    "ProgramName": self.parent().festival_combo.currentText(),
                    "1": "TELEPÍTHETŐ",
                    "2": "KIADVA",
                    "3": False,
                    "4": False,
                    "5": False,
                    "6": False,
                    "7": False,
                    "8": False,
                    "9": False,
                    "LastModified": self.firestore_service.server_timestamp(),
                    "LastAdded": self.firestore_service.server_timestamp(),
                }

                existing_company = self.firestore_service.get_company("Company_Install", site_data["Id"])
                if existing_company:
                    self.firestore_service.update_company("Company_Install", site_data["Id"], site_data)
                else:
                    self.firestore_service.add_company("Company_Install", site_data)

            self.processing_complete.emit()
            QMessageBox.information(None, "Import Complete", "Site data has been successfully imported/updated.")
        except Exception as e:
            logging.error(f"Error importing site data: {e}", exc_info=True)
            QMessageBox.critical(None, "Import Error", f"An error occurred while importing site data: {str(e)}")