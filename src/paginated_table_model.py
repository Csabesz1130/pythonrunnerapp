# File: paginated_table_model.py

from PyQt6.QtCore import QAbstractTableModel, Qt

class PaginatedTableModel(QAbstractTableModel):
    def __init__(self, firestore_service, collection, page_size=100):
        super().__init__()
        self.firestore_service = firestore_service
        self.collection = collection
        self.page_size = page_size
        self.current_page = 0
        self.total_items = 0
        self.data = []

    def load_page(self, page):
        self.current_page = page
        start = page * self.page_size
        end = start + self.page_size
        self.data = self.firestore_service.get_companies_paginated(self.collection, start, end)
        self.layoutChanged.emit()

    def rowCount(self, parent=None):
        return len(self.data)

    def columnCount(self, parent=None):
        return len(self.data[0]) if self.data else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(list(self.data[index.row()].values())[index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return list(self.data[0].keys())[section] if self.data else ""
        return None