from PyQt6.QtCore import Qt, QAbstractTableModel

class DynamicFirestoreModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = []

    def update_data(self, data):
        self.beginResetModel()
        self._data = data
        self._headers = list(data[0].keys()) if data else []
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None

        item = self._data[index.row()]
        column = self._headers[index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            return str(item.get(column, ""))
        elif role == Qt.ItemDataRole.UserRole:
            return item

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None