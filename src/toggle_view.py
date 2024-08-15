# File: src/toggle_view.py
import logging

from PyQt6.QtWidgets import (QStackedWidget, QTableView, QHeaderView, QApplication,
                             QWidget, QVBoxLayout, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

import firestore_service
from boolean_color_delegate import BooleanColorDelegate
from company_card_widget import CompanyCardWidget
from company_details_dialog import CompanyDetailsDialog


class ToggleView(QStackedWidget):
    company_selected = pyqtSignal(dict)

    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.table_view = QTableView()
        self.card_view = QScrollArea()
        self.card_widget = QWidget()
        self.card_layout = QVBoxLayout(self.card_widget)
        self.card_view.setWidget(self.card_widget)
        self.card_view.setWidgetResizable(True)

        self.setup_table_view()
        self.addWidget(self.table_view)
        self.addWidget(self.card_view)

        self.current_view = 'table'

    def setup_table_view(self):
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setWordWrap(True)

        boolean_delegate = BooleanColorDelegate(self.table_view)

        # Set up delegates for all boolean columns
        boolean_columns = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]  # Adjust these indices based on your actual data model
        for col in boolean_columns:
            self.table_view.setItemDelegateForColumn(col, boolean_delegate)

        # Set column widths (adjust as needed)
        self.table_view.setColumnWidth(0, 200)  # Company Name
        self.table_view.setColumnWidth(1, 150)  # Program Name
        for col in range(2, 15):  # Boolean columns
            self.table_view.setColumnWidth(col, 80)
        self.table_view.setColumnWidth(15, 100)  # ID
        self.table_view.setColumnWidth(16, 150)  # Last Modified

        # Connect double-click signal
        self.table_view.doubleClicked.connect(self.on_row_double_clicked)

    def set_model(self, model):
        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()
        self.update_card_view()

    def on_cell_clicked(self, index):
        try:
            row = index.row()
            company_data = self.table_view.model().get_item(row)
            company_id = company_data.get('Id')
            if company_id:
                logging.info(f"Fetching details for company ID: {company_id}")
                detailed_company_data = self.firestore_service.get_company_details(company_id)
                if detailed_company_data:
                    logging.info(f"Displaying details for company: {detailed_company_data.get('CompanyName', 'Unknown')}")
                    CompanyDetailsDialog.show_company_details(detailed_company_data, self)
                else:
                    logging.warning(f"No details found for company ID: {company_id}")
                    QMessageBox.warning(self, "Company Not Found", f"Details for company {company_id} could not be retrieved.")
            else:
                logging.warning("Cell clicked but no company ID found")
                QMessageBox.warning(self, "Invalid Selection", "Unable to retrieve company details. Please try again.")
        except Exception as e:
            logging.error(f"Error in on_cell_clicked: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def get_selected_rows(self):
        if self.current_view == 'table':
            return self.table_view.selectionModel().selectedRows()
        else:
            return [index for index, card in enumerate(self.card_widget.findChildren(CompanyCardWidget)) if card.is_selected]

    def clear_selection(self):
        if self.current_view == 'table':
            self.table_view.clearSelection()
        else:
            for card in self.card_widget.findChildren(CompanyCardWidget):
                card.set_selected(False)

    def on_row_double_clicked(self, index):
        try:
            source_index = self.table_view.model().mapToSource(index)
            source_model = self.table_view.model().sourceModel()
            company_data = source_model.data(source_index, Qt.ItemDataRole.UserRole)

            if not company_data:
                logging.warning("No company data found for the selected row")
                return

            company_id = company_data.get('Id')
            if company_id:
                try:
                    detailed_company_data = self.firestore_service.get_company_details(company_id)
                    if detailed_company_data:
                        CompanyDetailsDialog.show_company_details(detailed_company_data, self)
                    else:
                        QMessageBox.warning(self, "Company Not Found", f"Details for company {company_id} could not be retrieved.")
                except Exception as e:
                    logging.error(f"Error fetching company details: {e}", exc_info=True)
                    QMessageBox.critical(self, "Error", f"Failed to fetch company details: {str(e)}")
            else:
                QMessageBox.warning(self, "Invalid Selection", "Unable to retrieve company details. Please try again.")
        except Exception as e:
            logging.error(f"Error in on_row_double_clicked: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def toggle_view(self):
        if self.current_view == 'table':
            self.current_view = 'card'
            self.update_card_view()
            self.setCurrentWidget(self.card_view)
        else:
            self.current_view = 'table'
            self.setCurrentWidget(self.table_view)

    def update_card_view(self):
        # Clear existing cards
        for i in reversed(range(self.card_layout.count())):
            self.card_layout.itemAt(i).widget().setParent(None)

        # Add new cards
        model = self.table_view.model()
        row, col = 0, 0
        for row_index in range(model.rowCount()):
            company_data = model.data(model.index(row_index, 0), Qt.ItemDataRole.UserRole)
            if company_data:
                card = CompanyCardWidget(company_data)
                card.clicked.connect(self.on_card_clicked)
                self.card_layout.addWidget(card, row, col)
                col += 1
                if col == 3:  # Adjust the number of columns as needed
                    col = 0
                    row += 1

    def on_card_clicked(self, company_data):
        try:
            company_id = company_data.get('Id')
            if company_id:
                logging.info(f"Fetching details for company ID: {company_id}")
                detailed_company_data = self.firestore_service.get_company_details(company_id)
                if detailed_company_data:
                    logging.info(f"Displaying details for company: {detailed_company_data.get('CompanyName', 'Unknown')}")
                    CompanyDetailsDialog.show_company_details(detailed_company_data, self)
                else:
                    logging.warning(f"No details found for company ID: {company_id}")
                    QMessageBox.warning(self, "Company Not Found", f"Details for company {company_id} could not be retrieved.")
            else:
                logging.warning("Card clicked but no company ID found")
                QMessageBox.warning(self, "Invalid Selection", "Unable to retrieve company details. Please try again.")
        except Exception as e:
            logging.error(f"Error in on_card_clicked: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def on_card_selection_changed(self, is_selected):
        # This method can be used to update any UI elements or perform actions
        # when a card's selection state changes
        sender = self.sender()
        if isinstance(sender, CompanyCardWidget):
            logging.debug(f"Card selection changed: {sender.company_data.get('CompanyName', 'Unknown')} - Selected: {is_selected}")
        # You can add more logic here if needed, such as updating a selection counter