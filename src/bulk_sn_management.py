from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QPushButton,
                             QFileDialog, QMessageBox, QTableWidgetItem)
from PyQt6.QtCore import Qt
import csv

class BulkSNManagementDialog(QDialog):
    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Company ID", "Company Name", "SN List"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import SNs")
        self.export_btn = QPushButton("Export SNs")
        self.save_btn = QPushButton("Save Changes")
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

        self.import_btn.clicked.connect(self.import_sns)
        self.export_btn.clicked.connect(self.export_sns)
        self.save_btn.clicked.connect(self.save_changes)

    def load_data(self):
        companies = self.firestore_service.get_all_documents("Company_Install")
        self.table.setRowCount(len(companies))
        for row, company in enumerate(companies):
            self.table.setItem(row, 0, QTableWidgetItem(company['Id']))
            self.table.setItem(row, 1, QTableWidgetItem(company['CompanyName']))
            sn_list = self.firestore_service.get_sn_list(company['Id'])
            self.table.setItem(row, 2, QTableWidgetItem(', '.join(sn_list)))

    def import_sns(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import SN List", "", "CSV Files (*.csv)")
        if file_name:
            with open(file_name, 'r') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 3:
                        company_id, company_name, sn_list = row[0], row[1], row[2]
                        for table_row in range(self.table.rowCount()):
                            if self.table.item(table_row, 0).text() == company_id:
                                self.table.setItem(table_row, 2, QTableWidgetItem(sn_list))
                                break

    def export_sns(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export SN List", "", "CSV Files (*.csv)")
        if file_name:
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Company ID", "Company Name", "SN List"])
                for row in range(self.table.rowCount()):
                    company_id = self.table.item(row, 0).text()
                    company_name = self.table.item(row, 1).text()
                    sn_list = self.table.item(row, 2).text()
                    writer.writerow([company_id, company_name, sn_list])

    def save_changes(self):
        for row in range(self.table.rowCount()):
            company_id = self.table.item(row, 0).text()
            sn_list = self.table.item(row, 2).text().split(', ')
            self.firestore_service.update_sn_list(company_id, sn_list)
        QMessageBox.information(self, "Success", "Changes saved successfully!")