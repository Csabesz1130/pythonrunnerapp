import logging

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox, \
    QMessageBox
from PyQt6.QtCore import pyqtSignal
from fitz import self
from google.cloud.firestore_v1 import collection


class CompanyListView(QWidget):
    company_selected = pyqtSignal(str)

    def __init__(self, firestore_service):
        super().__init__()
        self.firestore_service = firestore_service
        self.setup_ui()
        self.load_companies()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search companies...")
        layout.addWidget(self.search_bar)

        self.company_table = QTableWidget()
        self.company_table.setColumnCount(9)
        self.company_table.setHorizontalHeaderLabels(["ID", "Name", "Program", "Eloszto", "Aram", "Halozat", "Telepites", "Felderites", "Last Modified"])
        self.company_table.cellDoubleClicked.connect(self.on_company_selected)
        layout.addWidget(self.company_table)

        self.add_company_button = QPushButton("Add Company")
        layout.addWidget(self.add_company_button)

    def load_companies(self):
        collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
    festival = self.festival_combo.currentText()
    if festival == "All Festivals":
        festival = None  # Fetch all companies if "All Festivals" is selected

    try:
        companies = self.firestore_service.get_companies(collection, festival)

        self.company_table.setRowCount(0)  # Clear the table
        self.company_table.setRowCount(len(companies))

        column_headers = {  # Mapping for dynamic column headers, mappolás az "1", statusz mappok alapján
            "Company_Install": [
                "ID", "Company Name", "Program Name", "Elosztó", "Áram", "Hálózat",
                "PTG", "Szoftver", "Param", "Helyszín", "Telepítés", "Felderítés", "Last Modified"
            ],
            "Company_Demolition": [
                "ID", "Company Name", "Program Name", "Bontás", "Felszerelés", "Bázis Leszerelés", "Last Modified"
            ]
        }

        # Set table headers based on selected collection
        self.company_table.setColumnCount(len(column_headers[collection]))
        self.company_table.setHorizontalHeaderLabels(column_headers[collection])

        for i, company in enumerate(companies):
            data = company.to_dict()

            for j, header in enumerate(column_headers[collection]):
                value = data.get(header, "")
                if header == "Last Modified":
                    value = value.strftime("%Y-%m-%d %H:%M:%S") if value else ""
                elif header in ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín", "Bázis Leszerelés"]:
                    value = "Yes" if value else "No"
                self.company_table.setItem(i, j, QTableWidgetItem(str(value)))

        self.company_table.resizeColumnsToContents()

    except Exception as e:
        logging.error(f"Error loading companies: {e}")
        QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")


    def on_company_selected(self, row, column):
        company_id = self.company_table.item(row, 0).text()
        self.company_selected.emit(company_id)