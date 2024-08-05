# File: bulk_edit_dialog.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QUndoCommand

class BulkEditDialog(QDialog):
    def __init__(self, model, selected_rows, parent=None):
        super().__init__(parent)
        self.model = model
        self.selected_rows = selected_rows
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.field_combo = QComboBox()
        self.field_combo.addItems([self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(self.model.columnCount())])
        layout.addWidget(self.field_combo)

        self.value_input = QLineEdit()
        layout.addWidget(self.value_input)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_bulk_edit)
        layout.addWidget(self.apply_button)

    def apply_bulk_edit(self):
        field = self.field_combo.currentText()
        value = self.value_input.text()
        column = self.field_combo.currentIndex()

        with QUndoCommand("Bulk Edit"):
            for row in self.selected_rows:
                old_value = self.model.data(self.model.index(row, column))
                self.model.setData(self.model.index(row, column), value)
                QUndoCommand(f"Edit {field} for row {row}",
                             lambda: self.model.setData(self.model.index(row, column), old_value),
                             lambda: self.model.setData(self.model.index(row, column), value))

        self.accept()