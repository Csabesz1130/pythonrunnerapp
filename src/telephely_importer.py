# File: src/utils/telephely_importer.py

import logging
import pandas as pd
from PyQt6.QtWidgets import QProgressDialog
from PyQt6.QtCore import Qt

class TelephalyImporter:
    def __init__(self, firestore_service):
        self.firestore_service = firestore_service
        self.logger = logging.getLogger(self.__class__.__name__)

    def import_from_excel(self, file_path, festival, parent_widget=None):
        try:
            df = pd.read_excel(file_path)
            total_rows = len(df)
            imported_count = 0
            error_count = 0

            progress = QProgressDialog("Importing data...", "Cancel", 0, total_rows, parent_widget)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            for index, row in df.iterrows():
                if progress.wasCanceled():
                    self.logger.info("Import cancelled by user")
                    break

                try:
                    company_data = self._prepare_company_data(row, festival)
                    self._update_or_create_company(company_data)
                    imported_count += 1
                except ValueError as ve:
                    self.logger.warning(f"Invalid data in row {index + 2}: {str(ve)}")
                    error_count += 1
                except Exception as e:
                    self.logger.error(f"Error processing row {index + 2}: {str(e)}")
                    error_count += 1

                progress.setValue(index + 1)

            progress.close()
            self.logger.info(f"Import completed. Imported: {imported_count}, Errors: {error_count}")
            return imported_count, error_count
        except Exception as e:
            self.logger.error(f"Error during import: {str(e)}", exc_info=True)
            return 0, total_rows

    def _prepare_company_data(self, row, festival):
        try:
            return {
                'Id': str(row['ID']),
                'CompanyName': str(row['Telephely név']),
                'CompanyCode': str(row['Telephely kód']),
                'quantity': int(row['Összes terminál igény']),
                'ProgramName': festival,
                # Add default values for other fields here
                '1': 'TELEPÍTHETŐ',  # Default value for Felderítés
                '2': 'KIADVA',       # Default value for Telepítés
                '3': False,          # Default value for Elosztó
                '4': False,          # Default value for Áram
                '5': False,          # Default value for Hálózat
                '6': False,          # Default value for PTG
                '7': False,          # Default value for Szoftver
                '8': False,          # Default value for Param
                '9': False,          # Default value for Helyszín
            }
        except KeyError as ke:
            raise ValueError(f"Missing required column: {ke}")
        except ValueError as ve:
            raise ValueError(f"Invalid data type: {ve}")

    def _update_or_create_company(self, company_data):
        try:
            self.firestore_service.update_or_create_company("Company_Install", company_data)
            self.logger.debug(f"Updated/Created company: {company_data['Id']}")
        except Exception as e:
            self.logger.error(f"Error updating/creating company {company_data['Id']}: {str(e)}")
            raise