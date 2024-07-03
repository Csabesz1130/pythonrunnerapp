import re
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QComboBox, QTableView)

class TableFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = {}

    def setFilter(self, column, pattern):
        if pattern:
            self.filters[column] = pattern
        elif column in self.filters:
            del self.filters[column]
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        for column, pattern in self.filters.items():
            index = self.sourceModel().index(source_row, column, source_parent)
            if not self.filterAcceptsColumn(column, source_parent):
                continue
            text = self.sourceModel().data(index)
            if text is None or not re.search(pattern, str(text), re.IGNORECASE):
                return False
        return True

class FilterWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_boxes = []
        self.main_layout = QVBoxLayout(self)
        self.filter_layout = QHBoxLayout()
        self.main_layout.addLayout(self.filter_layout)

        self.add_filter_button = QPushButton("Add Filter")
        self.add_filter_button.clicked.connect(self.add_filter)
        self.main_layout.addWidget(self.add_filter_button)

    def add_filter(self):
        filter_box = QWidget()
        layout = QHBoxLayout(filter_box)

        column_combo = QComboBox()
        column_combo.addItems([f"Column {i}" for i in range(self.parent().model().columnCount())])
        layout.addWidget(column_combo)

        filter_input = QLineEdit()
        layout.addWidget(filter_input)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_filter(filter_box))
        layout.addWidget(remove_button)

        self.filter_boxes.append(filter_box)
        self.filter_layout.addWidget(filter_box)

        filter_input.textChanged.connect(lambda text: self.update_filter(column_combo.currentIndex(), text))
        column_combo.currentIndexChanged.connect(lambda index: self.update_filter(index, filter_input.text()))

    def remove_filter(self, filter_box):
        self.filter_boxes.remove(filter_box)
        filter_box.deleteLater()
        self.update_all_filters()

    def update_filter(self, column, text):
        self.parent().filter_proxy_model.setFilter(column, text)

    def update_all_filters(self):
        self.parent().filter_proxy_model.filters.clear()
        for filter_box in self.filter_boxes:
            column_combo = filter_box.layout().itemAt(0).widget()
            filter_input = filter_box.layout().itemAt(1).widget()
            self.update_filter(column_combo.currentIndex(), filter_input.text())

class FilterableTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_proxy_model = TableFilterProxyModel(self)
        self.filter_widget = FilterWidget(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.filter_widget)
        layout.addWidget(self)

        self.setLayout(layout)

    def setModel(self, model):
        super().setModel(model)
        self.filter_proxy_model.setSourceModel(model)
        super().setModel(self.filter_proxy_model)
        self.filter_widget.add_filter()  # Add an initial filter