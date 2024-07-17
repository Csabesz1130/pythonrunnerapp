from PyQt6.QtCore import Qt, QAbstractTableModel
import logging

class DynamicFirestoreModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = []

    def update_data(self, data):
        self.beginResetModel()
        self._data = data
        self._headers = self.get_all_keys()
        self.endResetModel()

    def update_single_item(self, item):
        item_id = item.get('Id')
        if not item_id:
            logging.warning(f"Received item without ID: {item}")
            return

        for row, existing_item in enumerate(self._data):
            if existing_item.get('Id') == item_id:
                self._data[row].update(item)
                self.dataChanged.emit(self.index(row, 0), self.index(row, len(self._headers) - 1))
                return

        # If item not found, append it
        self.beginInsertRows(self.index(0, 0).parent(), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

        # Check for new headers
        new_headers = set(item.keys()) - set(self._headers)
        if new_headers:
            self.beginInsertColumns(self.index(0, 0).parent(), len(self._headers), len(self._headers) + len(new_headers) - 1)
            self._headers.extend(sorted(new_headers))
            self.endInsertColumns()

    def get_all_keys(self):
        keys = set()
        for item in self._data:
            keys.update(item.keys())
        return sorted(list(keys))

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._headers)

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            item = self._data[index.row()]
            key = self._headers[index.column()]
            value = item.get(key, '')

            # Handle boolean values
            if isinstance(value, bool):
                return "Van" if value else "Nincs"

            # Handle CreatedAt (assuming it's a timestamp or string)
            if key == "CreatedAt" and value:
                # You might need to adjust this depending on the exact format of CreatedAt
                return str(value)[:10]  # Display only the date part

            # Handle Elosztó and other boolean fields
            if key in ["Elosztó", "3", "4", "5", "6", "7", "8", "9"]:
                if isinstance(value, bool):
                    return "Van" if value else "Nincs"
                elif isinstance(value, str):
                    return "Van" if value.lower() in ['true', 'yes', 'van'] else "Nincs"

            # For all other cases, return the string representation
            return str(value) if value is not None else ''

        return None

    def headerData(self, section, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        key = self._headers[column]
        reverse = order == Qt.SortOrder.DescendingOrder
        self._data.sort(key=lambda x: x.get(key, ''), reverse=reverse)
        self.layoutChanged.emit()

    def remove_item(self, item_id):
        for row, item in enumerate(self._data):
            if item.get('Id') == item_id:
                self.beginRemoveRows(self.index(0, 0).parent(), row, row)
                del self._data[row]
                self.endRemoveRows()
                return
        logging.warning(f"Attempted to remove non-existent item with ID: {item_id}")