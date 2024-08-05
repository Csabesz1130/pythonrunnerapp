# File: dynamic_filter_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit
from PyQt6.QtCore import Qt

class DynamicFilterWidget(QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.filters = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        for column in range(self.model.columnCount()):
            header = self.model.headerData(column, Qt.Orientation.Horizontal)
            filter_input = QLineEdit()
            filter_input.setPlaceholderText(f"Filter {header}...")
            filter_input.textChanged.connect(lambda text, col=column: self.update_filter(col, text))
            layout.addWidget(filter_input)

    def update_filter(self, column, text):
        if text:
            self.filters[column] = text
        elif column in self.filters:
            del self.filters[column]
        self.model.layoutChanged.emit()

    def filterAcceptsRow(self, source_row, source_parent):
        for column, text in self.filters.items():
            index = self.model.index(source_row, column, source_parent)
            if text.lower() not in str(self.model.data(index)).lower():
                return False
        return True