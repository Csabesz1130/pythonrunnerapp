# File: company_details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                             QTextEdit, QPushButton, QFormLayout, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging

class CompanyDetailsDialog(QDialog):
    def __init__(self, company_data, parent=None):
        super().__init__(parent)
        self.company_data = company_data
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Company Details")
        self.setMinimumSize(700, 500)

        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Company information
        info_layout = QFormLayout()
        self.add_info_field(info_layout, "Company Name", 'CompanyName')
        self.add_info_field(info_layout, "Program Name", 'ProgramName')
        self.add_info_field(info_layout, "Quantity", 'quantity')
        self.add_info_field(info_layout, "Felderítés", 'felderites')
        self.add_info_field(info_layout, "Telepítés", 'telepites')

        # Boolean fields
        boolean_fields = [
            ("Elosztó", "3"), ("Áram", "4"), ("Hálózat", "5"),
            ("PTG", "6"), ("Szoftver", "7"), ("Param", "8"), ("Helyszín", "9")
        ]
        for label, key in boolean_fields:
            value = "Yes" if self.company_data.get(key, False) else "No"
            self.add_info_field(info_layout, label, key, value)

        scroll_layout.addLayout(info_layout)

        # SN Numbers
        sn_label = QLabel("SN Numbers:")
        sn_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        scroll_layout.addWidget(sn_label)
        sn_list = QListWidget()
        sn_list.addItems(self.company_data.get('SN', []))
        sn_list.setMaximumHeight(100)
        scroll_layout.addWidget(sn_list)

        # Comments
        comments_label = QLabel("Comments:")
        comments_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        scroll_layout.addWidget(comments_label)
        comments_text = QTextEdit()
        comments_text.setReadOnly(True)
        for comment in self.company_data.get('Comments', []):
            comments_text.append(f"{comment['timestamp']}: {comment['comment']}")
        comments_text.setMaximumHeight(150)
        scroll_layout.addWidget(comments_text)

        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

    def add_info_field(self, layout, label, key, custom_value=None):
        value = custom_value if custom_value is not None else self.company_data.get(key, 'N/A')
        label_widget = QLabel(f"{label}:")
        label_widget.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        value_widget = QLabel(str(value))
        layout.addRow(label_widget, value_widget)

    @staticmethod
    def show_company_details(company_data, parent=None):
        dialog = CompanyDetailsDialog(company_data, parent)
        return dialog.exec()

# Usage example:
# if CompanyDetailsDialog.show_company_details(company_data, self):
#     # The dialog was shown and closed successfully
#     pass