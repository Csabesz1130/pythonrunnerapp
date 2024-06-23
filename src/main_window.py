import sys
import csv
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QComboBox, QRadioButton, QLineEdit,
                             QButtonGroup, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt
from src.firestore_service import FirestoreService
from src.company_details_view import CompanyDetailsView

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Festival Company Management")
        self.setGeometry(100, 100, 1200, 800)

        credentials_path = r"C:\Users\Balogh Csaba\IdeaProjects\pythonrunnerapp\resources\runnerapp-232cc-firebase-adminsdk-2csiq-7074e046ed.json"
        self.firestore_service = FirestoreService(credentials_path)

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
        self.company_table.setColumnCount(9)
        self.company_table.setHorizontalHeaderLabels(["ID", "Name", "Program", "Eloszto", "Aram", "Halozat", "Telepites", "Felderites", "Last Modified"])
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

        self.main_layout.addLayout(button_layout)

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            if not festivals:
                raise ValueError("No festivals found in the database.")
            self.festival_combo.addItems(["All Festivals"] + festivals)
            self.festival_combo.currentTextChanged.connect(self.load_companies)
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
                self.company_table.setItem(i, 0, QTableWidgetItem(str(data.get("Id", ""))))
                self.company_table.setItem(i, 1, QTableWidgetItem(data.get("CompanyName", "")))
                self.company_table.setItem(i, 2, QTableWidgetItem(data.get("ProgramName", "")))
                self.company_table.setItem(i, 3, QTableWidgetItem("Yes" if data.get("eloszto", False) else "No"))
                self.company_table.setItem(i, 4, QTableWidgetItem("Yes" if data.get("aram", False) else "No"))
                self.company_table.setItem(i, 5, QTableWidgetItem("Yes" if data.get("halozat", False) else "No"))
                self.company_table.setItem(i, 6, QTableWidgetItem(data.get("telepites", "KIADVA")))
                self.company_table.setItem(i, 7, QTableWidgetItem(data.get("felderites", "TELEPÍTHETŐ")))
                self.company_table.setItem(i, 8, QTableWidgetItem(str(data.get("LastModified", ""))))

            self.company_table.resizeColumnsToContents()
        except Exception as e:
            logging.error(f"Error loading companies: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")

    def filter_companies(self):
        search_text = self.search_input.text().lower()
        for row in range(self.company_table.rowCount()):
            show_row = False
            for column in range(self.company_table.columnCount()):
                item = self.company_table.item(row, column)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.company_table.setRowHidden(row, not show_row)

    def open_company_details(self, row, column):
        try:
            company_id = self.company_table.item(row, 0).text()
            collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
            company_data = self.firestore_service.get_company(collection, company_id)
            details_view = CompanyDetailsView(self.firestore_service, collection, company_id, company_data, self)
            if details_view.exec() == CompanyDetailsView.DialogCode.Accepted:
                self.load_companies()  # Refresh the list after editing
        except Exception as e:
            logging.error(f"Error opening company details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open company details: {str(e)}")

    def add_company(self):
        try:
            collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
            details_view = CompanyDetailsView(self.firestore_service, collection, parent=self)
            if details_view.exec() == CompanyDetailsView.DialogCode.Accepted:
                self.load_companies()
        except Exception as e:
            logging.error(f"Error adding company: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add company: {str(e)}")

    def export_to_csv(self):
        try:
            filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
            if filename:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    headers = [self.company_table.horizontalHeaderItem(i).text() for i in range(self.company_table.columnCount())]
                    writer.writerow(headers)
                    for row in range(self.company_table.rowCount()):
                        if not self.company_table.isRowHidden(row):
                            row_data = [self.company_table.item(row, col).text() for col in range(self.company_table.columnCount())]
                            writer.writerow(row_data)
                QMessageBox.information(self, "Export Complete", f"Data exported to {filename}")
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export to CSV: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())