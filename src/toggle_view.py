from PyQt6.QtWidgets import (QStackedWidget, QTableView, QHeaderView, QApplication,
                             QWidget, QVBoxLayout, QScrollArea, QMessageBox, QGridLayout, QLineEdit,
                             QStyledItemDelegate)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from boolean_color_delegate import BooleanColorDelegate
from company_card_widget import CompanyCardWidget
from company_details_dialog import CompanyDetailsDialog
import logging

class HeaderLikeLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #CCCCCC;
                background-color: #F0F0F0;
                padding: 4px;
                font-weight: bold;
            }
        """)

class FilterHeaderDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = HeaderLikeLineEdit(parent)
        return editor

class ToggleView(QStackedWidget):
    company_selected = pyqtSignal(dict)

    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service

        # Table View
        self.table_view = QTableView()
        self.setup_table_view()
        self.addWidget(self.table_view)

        # Card View
        self.card_scroll_area = QScrollArea()
        self.card_widget = QWidget()
        self.card_layout = QGridLayout(self.card_widget)
        self.card_scroll_area.setWidget(self.card_widget)
        self.card_scroll_area.setWidgetResizable(True)
        self.addWidget(self.card_scroll_area)

        self.current_view = 'table'
        self.filter_row = 0
        self.model_set = False

    def setup_table_view(self):
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setWordWrap(True)

        # Style the header
        header = self.table_view.horizontalHeader()
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 4px;
                border: 1px solid #CCCCCC;
                font-weight: bold;
            }
        """)

        # Set up boolean delegate for specific columns
        boolean_delegate = BooleanColorDelegate(self.table_view)
        boolean_columns = [2, 3, 4, 5, 6, 7, 8, 9]  # Adjust these indices based on your data model
        for col in boolean_columns:
            self.table_view.setItemDelegateForColumn(col, boolean_delegate)

        # Connect double-click signal for row details
        self.table_view.doubleClicked.connect(self.on_row_double_clicked)

    def set_model(self, model):
        self.table_view.setModel(model)
        self.model_set = True
        self.setup_filter_row()
        self.update_view()

    def update_view(self):
        if self.current_view == 'table':
            self.table_view.resizeColumnsToContents()
            if self.model_set:
                self.table_view.setRowHidden(self.filter_row, False)
        else:
            self.update_card_view()

    def filter_column(self, column):
        if not self.model_set:
            return
        index = self.table_view.model().index(self.filter_row, column)
        filter_text = self.table_view.model().data(index, Qt.ItemDataRole.EditRole)
        # Implement filtering logic here
        print(f"Filtering column {column} with text: {filter_text}")

    def toggle_view(self):
        if self.current_view == 'table':
            self.current_view = 'card'
            self.update_card_view()
            self.setCurrentWidget(self.card_scroll_area)
        else:
            self.current_view = 'table'
            self.setCurrentWidget(self.table_view)
        self.update_view()

    def update_card_view(self):
        # Clear existing cards
        while self.card_layout.count():
            child = self.card_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

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

        # Ensure the layout updates
        self.card_widget.setLayout(self.card_layout)
        self.card_scroll_area.setWidget(self.card_widget)

    def on_row_double_clicked(self, index):
        try:
            source_index = self.table_view.model().mapToSource(index)
            source_model = self.table_view.model().sourceModel()
            company_data = source_model.data(source_index, Qt.ItemDataRole.UserRole)

            if not company_data:
                logging.warning("No company data found for the selected row")
                return

            self.show_company_details(company_data)
        except Exception as e:
            logging.error(f"Error in on_row_double_clicked: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def on_card_clicked(self, company_data):
        self.show_company_details(company_data)

    def show_company_details(self, company_data):
        company_id = company_data.get('Id')
        if company_id:
            try:
                logging.info(f"Fetching details for company ID: {company_id}")
                detailed_company_data = self.firestore_service.get_company_details(company_id)
                if detailed_company_data:
                    logging.info(f"Displaying details for company: {detailed_company_data.get('CompanyName', 'Unknown')}")
                    CompanyDetailsDialog.show_company_details(detailed_company_data, self)
                else:
                    logging.warning(f"No details found for company ID: {company_id}")
                    QMessageBox.warning(self, "Company Not Found", f"Details for company {company_id} could not be retrieved.")
            except Exception as e:
                logging.error(f"Error fetching company details: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Error", f"An error occurred while fetching company details: {str(e)}")
        else:
            logging.warning("Company selected but no company ID found")
            QMessageBox.warning(self, "Invalid Selection", "Unable to retrieve company details. Please try again.")

    def setup_filter_row(self):
        if not self.model_set:
            return

        # Add a row for filters
        self.table_view.model().insertRow(self.filter_row)

        # Set the delegate for the filter row
        filter_delegate = FilterHeaderDelegate(self.table_view)
        self.table_view.setItemDelegateForRow(self.filter_row, filter_delegate)

        # Set up filter inputs
        for col in range(self.table_view.model().columnCount()):
            filter_input = HeaderLikeLineEdit()
            filter_input.setPlaceholderText(f"Filter {self.table_view.model().headerData(col, Qt.Orientation.Horizontal)}")
            self.table_view.setIndexWidget(self.table_view.model().index(self.filter_row, col), filter_input)
            filter_input.textChanged.connect(lambda text, column=col: self.filter_column(column))

        # Ensure the filter row is always visible
        self.table_view.setRowHidden(self.filter_row, False)

    def get_selected_companies(self):
        if self.current_view == 'table':
            return [self.table_view.model().data(index, Qt.ItemDataRole.UserRole)
                    for index in self.table_view.selectionModel().selectedRows()]
        else:
            return [card.company_data for card in self.card_widget.findChildren(CompanyCardWidget) if card.isSelected()]