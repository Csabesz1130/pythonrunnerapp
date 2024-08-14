# File: src/data/dynamic_firestore_model.py

import logging
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex

class DynamicFirestoreModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def update_data(self, data):
        try:
            self.beginResetModel()
            self._data = data
            self._headers = list(data[0].keys()) if data else []
            self.endResetModel()
            self.logger.info(f"Model updated with {len(self._data)} rows and {len(self._headers)} columns")
        except Exception as e:
            self.logger.error(f"Error updating model data: {str(e)}", exc_info=True)

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._data)):
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            try:
                item = self._data[index.row()]
                column_name = self._headers[index.column()]
                return str(item.get(column_name, ""))
            except Exception as e:
                self.logger.error(f"Error retrieving data at row {index.row()}, column {index.column()}: {str(e)}")
                return None

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            try:
                return self._headers[section]
            except IndexError:
                self.logger.error(f"Error retrieving header for section {section}")
                return None
        return None

    def add_item(self, item):
        try:
            self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
            self._data.append(item)
            self.endInsertRows()
            self.logger.info(f"New item added to model. Total rows: {len(self._data)}")
        except Exception as e:
            self.logger.error(f"Error adding new item to model: {str(e)}", exc_info=True)

    def remove_item(self, row):
        try:
            if 0 <= row < len(self._data):
                self.beginRemoveRows(QModelIndex(), row, row)
                del self._data[row]
                self.endRemoveRows()
                self.logger.info(f"Item removed from model at row {row}. Total rows: {len(self._data)}")
            else:
                self.logger.warning(f"Attempted to remove invalid row: {row}")
        except Exception as e:
            self.logger.error(f"Error removing item from model: {str(e)}", exc_info=True)

    def update_item(self, row, item):
        try:
            if 0 <= row < len(self._data):
                self._data[row] = item
                self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
                self.logger.info(f"Item updated in model at row {row}")
            else:
                self.logger.warning(f"Attempted to update invalid row: {row}")
        except Exception as e:
            self.logger.error(f"Error updating item in model: {str(e)}", exc_info=True)

    def clear(self):
        try:
            self.beginResetModel()
            self._data = []
            self._headers = []
            self.endResetModel()
            self.logger.info("Model cleared")
        except Exception as e:
            self.logger.error(f"Error clearing model: {str(e)}", exc_info=True)

    def get_item(self, row):
        try:
            if 0 <= row < len(self._data):
                return self._data[row]
            else:
                self.logger.warning(f"Attempted to get item from invalid row: {row}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting item from model: {str(e)}", exc_info=True)
            return None