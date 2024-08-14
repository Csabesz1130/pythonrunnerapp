# File: toggle_view.py

import logging
from PyQt6.QtWidgets import QStackedWidget, QWidget, QVBoxLayout, QScrollArea, QTableView
from PyQt6.QtCore import pyqtSignal, Qt
from company_card_widget import CompanyCardWidget

class ToggleView(QStackedWidget):
    company_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.current_view = 'table'
        self.setup_ui()
        self.selected_companies = set()

    def setup_ui(self):
        self.table_view = QTableView()
        self.table_view.setSelectionMode(QTableView.SelectionMode.MultiSelection)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.addWidget(self.table_view)

        self.card_scroll_area = QScrollArea()
        self.card_widget = QWidget()
        self.card_layout = QVBoxLayout(self.card_widget)
        self.card_scroll_area.setWidget(self.card_widget)
        self.card_scroll_area.setWidgetResizable(True)
        self.addWidget(self.card_scroll_area)

    def set_model(self, model):
        self.model = model
        self.table_view.setModel(model)
        self.update_view()

    def toggle_view(self):
        self.current_view = 'card' if self.current_view == 'table' else 'table'
        self.update_view()

    def update_view(self):
        if self.current_view == 'card':
            self.update_card_view()
        else:
            self.setCurrentWidget(self.table_view)

    def update_card_view(self):
        for i in reversed(range(self.card_layout.count())):
            self.card_layout.itemAt(i).widget().setParent(None)

        for row in range(self.model.rowCount()):
            company_data = self.get_company_data_from_model(row)
            card = CompanyCardWidget(company_data)
            card.clicked.connect(self.on_card_clicked)
            card.selection_changed.connect(lambda selected, data=company_data: self.on_card_selection_changed(selected, data))
            self.card_layout.addWidget(card)

        self.setCurrentWidget(self.card_scroll_area)

    def get_company_data_from_model(self, row):
        return {self.model.headerData(col, Qt.Orientation.Horizontal): self.model.data(self.model.index(row, col))
                for col in range(self.model.columnCount())}

    def on_card_clicked(self, company_data):
        self.company_selected.emit(company_data)

    def on_card_selection_changed(self, selected, company_data):
        company_id = company_data.get('Id')
        if selected:
            self.selected_companies.add(company_id)
        else:
            self.selected_companies.discard(company_id)

    def get_selected_rows(self):
        if self.current_view == 'table':
            return self.table_view.selectionModel().selectedRows()
        else:
            return [self.model.index(row, 0) for row in range(self.model.rowCount())
                    if self.model.data(self.model.index(row, 0)) in self.selected_companies]

    def clear_selection(self):
        if self.current_view == 'table':
            self.table_view.clearSelection()
        else:
            self.selected_companies.clear()
            for i in range(self.card_layout.count()):
                card = self.card_layout.itemAt(i).widget()
                if isinstance(card, CompanyCardWidget):
                    card.is_selected = False
                    card.setProperty("selected", False)
                    card.style().unpolish(card)
                    card.style().polish(card)
                    card.update()