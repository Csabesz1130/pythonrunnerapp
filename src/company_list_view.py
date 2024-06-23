from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QComboBox
from PyQt6.QtCore import pyqtSignal

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
        companies = self.firestore_service.get_companies("Company_Install")
        self.company_table.setRowCount(len(companies))
        for i, company in enumerate(companies):
            data = company.to_dict()
            self.company_table.setItem(i, 0, QTableWidgetItem(company.id))
            self.company_table.setItem(i, 1, QTableWidgetItem(data.get("name", "")))
            self.company_table.setItem(i, 2, QTableWidgetItem(data.get("program", "")))
            self.company_table.setItem(i, 3, QTableWidgetItem("Yes" if data.get("eloszto", False) else "No"))
            self.company_table.setItem(i, 4, QTableWidgetItem("Yes" if data.get("aram", False) else "No"))
            self.company_table.setItem(i, 5, QTableWidgetItem("Yes" if data.get("halozat", False) else "No"))
            self.company_table.setItem(i, 6, QTableWidgetItem(data.get("telepites", "KIADVA")))
            self.company_table.setItem(i, 7, QTableWidgetItem(data.get("felderites", "TELEPÍTHETŐ")))
            self.company_table.setItem(i, 8, QTableWidgetItem(str(data.get("last_modified", ""))))

    def on_company_selected(self, row, column):
        company_id = self.company_table.item(row, 0).text()
        self.company_selected.emit(company_id)