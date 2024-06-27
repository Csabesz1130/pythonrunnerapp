import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLineEdit, QComboBox, QRadioButton, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt

class CompanyListView(QWidget):
    company_selected = pyqtSignal(str, str)  # Emits company_id and collection

    def __init__(self, firestore_service):
        super().__init__()
        self.firestore_service = firestore_service
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Top controls
        top_layout = QHBoxLayout()

        self.festival_combo = QComboBox()
        self.festival_combo.addItem("All Festivals")
        self.festival_combo.currentTextChanged.connect(self.load_companies)
        top_layout.addWidget(self.festival_combo)

        self.install_radio = QRadioButton("Company_Install")
        self.demolition_radio = QRadioButton("Company_Demolition")
        self.install_radio.setChecked(True)
        self.install_radio.toggled.connect(self.load_companies)
        self.demolition_radio.toggled.connect(self.load_companies)
        top_layout.addWidget(self.install_radio)
        top_layout.addWidget(self.demolition_radio)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search companies...")
        self.search_bar.textChanged.connect(self.filter_companies)
        top_layout.addWidget(self.search_bar)

        layout.addLayout(top_layout)

        # Company table
        self.company_table = QTableWidget()
        self.company_table.setColumnCount(13)  # Max columns for Company_Install
        self.company_table.cellDoubleClicked.connect(self.on_company_selected)
        layout.addWidget(self.company_table)

        # Bottom controls
        bottom_layout = QHBoxLayout()

        self.add_company_button = QPushButton("Add Company")
        self.add_company_button.clicked.connect(self.add_company)
        bottom_layout.addWidget(self.add_company_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_companies)
        bottom_layout.addWidget(self.refresh_button)

        layout.addLayout(bottom_layout)

        # Load initial data
        self.populate_festivals()
        self.load_companies()

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            self.festival_combo.addItems(festivals)
        except Exception as e:
            logging.error(f"Error populating festivals: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load festivals: {str(e)}")

    def load_companies(self):
        collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
        festival = self.festival_combo.currentText()
        if festival == "All Festivals":
            festival = None  # Fetch all companies if "All Festivals" is selected

        try:
            companies = self.firestore_service.get_companies(collection, festival)

            self.company_table.setRowCount(0)  # Clear the table
            self.company_table.setRowCount(len(companies))

            column_headers = {
                "Company_Install": [
                    "ID", "CompanyName", "ProgramName", "eloszto", "aram", "halozat",
                    "PTG", "szoftver", "param", "helyszin", "telepites", "felderites", "LastModified"
                ],
                "Company_Demolition": [
                    "ID", "CompanyName", "ProgramName", "1", "2", "3", "LastModified"
                ]
            }

            header_display_names = {
                "Company_Install": [
                    "ID", "Company Name", "Program Name", "Elosztó", "Áram", "Hálózat",
                    "PTG", "Szoftver", "Param", "Helyszín", "Telepítés", "Felderítés", "Last Modified"
                ],
                "Company_Demolition": [
                    "ID", "Company Name", "Program Name", "Bontás", "Felszerelés", "Bázis Leszerelés", "Last Modified"
                ]
            }

            # Set table headers based on selected collection
            self.company_table.setColumnCount(len(header_display_names[collection]))
            self.company_table.setHorizontalHeaderLabels(header_display_names[collection])

            for i, company in enumerate(companies):
                data = company.to_dict()
                data['ID'] = company.id  # Add the document ID to the data dictionary

                for j, header in enumerate(column_headers[collection]):
                    value = data.get(header, "")
                    if header == "LastModified":
                        value = value.strftime("%Y-%m-%d %H:%M:%S") if value else ""
                    elif header in ["eloszto", "aram", "halozat", "PTG", "szoftver", "param", "helyszin", "3"]:
                        value = "Yes" if value else "No"
                    elif header in ["telepites", "felderites", "1", "2"]:
                        # These fields are likely to be string values, so we don't need to modify them
                        pass
                    self.company_table.setItem(i, j, QTableWidgetItem(str(value)))

            self.company_table.resizeColumnsToContents()

        except Exception as e:
            logging.error(f"Error loading companies: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load companies: {str(e)}")

    def filter_companies(self):
        search_text = self.search_bar.text().lower()
        for row in range(self.company_table.rowCount()):
            should_show = False
            for col in range(self.company_table.columnCount()):
                item = self.company_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            self.company_table.setRowHidden(row, not should_show)

    def on_company_selected(self, row, column):
        company_id = self.company_table.item(row, 0).text()
        collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
        self.company_selected.emit(company_id, collection)

    def add_company(self):
        collection = "Company_Install" if self.install_radio.isChecked() else "Company_Demolition"
        self.company_selected.emit(None, collection)  # None indicates a new company

    def refresh(self):
        self.load_companies()