# src/data/paginated_firestore_model.py

from PyQt6.QtCore import Qt, QAbstractTableModel

class PaginatedFirestoreModel(QAbstractTableModel):
    def __init__(self, firestore_service, cache, page_size=100):
        super().__init__()
        self.firestore_service = firestore_service
        self.cache = cache
        self.page_size = page_size
        self.data = []
        self.total_items = 0
        self.current_page = 0

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

    def load_page(self, page):
        self.current_page = page
        start = page * self.page_size
        end = start + self.page_size

        cached_data = self.cache.get(f"page_{page}")
        if cached_data:
            self.data = cached_data
        else:
            self.data = self.firestore_service.get_companies_paginated("Company_Install", start, end)
            self.cache.set(f"page_{page}", self.data)

        self.layoutChanged.emit()

    def update_data(self, new_data):
        self.data = new_data
        self.cache.set(f"page_{self.current_page}", new_data)
        self.layoutChanged.emit()