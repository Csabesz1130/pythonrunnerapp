# File: company_card_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QMouseEvent, QColor, QPalette

class CompanyCardWidget(QWidget):
    clicked = pyqtSignal(dict)
    selection_changed = pyqtSignal(bool)

    def __init__(self, company_data, parent=None):
        super().__init__(parent)
        self.company_data = company_data
        self.is_selected = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Company name with larger font
        name_label = QLabel(self.company_data.get('CompanyName', 'N/A'))
        name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(name_label)

        # Program name
        layout.addWidget(QLabel(f"Program: {self.company_data.get('ProgramName', 'N/A')}"))

        # Quantity
        layout.addWidget(QLabel(f"Quantity: {self.company_data.get('quantity', 'N/A')}"))

        # Company Code
        layout.addWidget(QLabel(f"Company Code: {self.company_data.get('CompanyCode', 'N/A')}"))

        # Status fields
        status_layout = QHBoxLayout()
        status_label = QLabel("Status:")
        status_value = QLabel(self.company_data.get('2', 'Unknown'))  # Assuming '2' is the status field
        self.set_status_color(status_value)
        status_layout.addWidget(status_label)
        status_layout.addWidget(status_value)
        layout.addLayout(status_layout)

        # Felderítés
        layout.addWidget(QLabel(f"Felderítés: {self.company_data.get('1', 'N/A')}"))

        # Boolean fields
        boolean_fields = [
            ("Elosztó", "3"),
            ("Áram", "4"),
            ("Hálózat", "5"),
            ("PTG", "6"),
            ("Szoftver", "7"),
            ("Param", "8"),
            ("Helyszín", "9")
        ]
        for label, key in boolean_fields:
            value = "Van" if self.company_data.get(key, False) else "Nincs"
            layout.addWidget(QLabel(f"{label}: {value}"))

        # Last Modified
        layout.addWidget(QLabel(f"Last Modified: {self.company_data.get('LastModified', 'N/A')}"))

        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
                padding: 10px;
                margin: 5px;
            }
            QWidget[selected="true"] {
                background-color: #e0e0ff;
                border: 2px solid #0000ff;
            }
        """)

    def set_status_color(self, label):
        status = label.text().lower()
        if 'active' in status or 'kiadva' in status:
            color = QColor(0, 255, 0, 50)  # Light green
        elif 'pending' in status or 'kihelyezesre_var' in status:
            color = QColor(255, 255, 0, 50)  # Light yellow
        elif 'inactive' in status or 'statusz_nelkul' in status:
            color = QColor(255, 0, 0, 50)  # Light red
        else:
            color = QColor(200, 200, 200, 50)  # Light gray

        palette = label.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        label.setAutoFillBackground(True)
        label.setPalette(palette)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_selection()
        super().mousePressEvent(event)

    def toggle_selection(self):
        self.set_selected(not self.is_selected)

    def set_selected(self, selected):
        self.is_selected = selected
        self.setProperty("selected", self.is_selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        self.selection_changed.emit(self.is_selected)
        if self.is_selected:
            self.clicked.emit(self.company_data)

    def get_company_data(self):
        return self.company_data