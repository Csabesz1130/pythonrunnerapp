from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QColor
from datetime import datetime
import logging

class DynamicFirestoreModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._headers = []
        self._collection = ""
        self._field_mapping = {}
        self._reverse_mapping = {}

    def get_field_mapping(self, collection):
        common_fields = {
            "Id": "ID",
            "CompanyName": "Cégnév",
            "ProgramName": "Program",
            "CreatedAt": "Létrehozva",
            "LastModified": "Utoljára módosítva"
        }

        if collection == "Company_Install":
            specific_fields = {
                "quantity": "Igény",
                "SN": "Kiadott",
                "felderites": "Felderítés",
                "telepites": "Telepítés",
                "eloszto": "Elosztó",
                "aram": "Áram",
                "halozat": "Hálózat",
                "PTG": "PTG",
                "Szoftver": "Szoftver",
                "Param": "Param",
                "Helyszin": "Helyszín",
                # Mapping for numeric fields
                "1": "Felderítés státusz",
                "2": "Telepítés státusz",
                "3": "Elosztó státusz",
                "4": "Áram státusz",
                "5": "Hálózat státusz",
                "6": "SN szám",
                "7": "Szoftver státusz",
                "8": "Param státusz",
                "9": "Helyszín státusz",
                "10": "Mennyiség",
                "11": "Utolsó frissítés"
            }
        elif collection == "Company_Demolition":
            specific_fields = {
                "1": "Bontás",
                "2": "Felszerelés",
                "3": "Bázis Leszerelés",
            }
        else:
            logging.warning(f"Unknown collection: {collection}")
            specific_fields = {}

        return {**common_fields, **specific_fields}

    def update_data(self, data, collection):
            self.beginResetModel()
            self._data = data
            self._collection = collection
            self._field_mapping = self.get_field_mapping(collection)

            if data:
                # Use a dictionary to maintain order and remove duplicates
                header_dict = {}
                for key in data[0].keys():
                    mapped_name = self._field_mapping.get(key, key)
                    header_dict[mapped_name] = key

                self._headers = list(header_dict.keys())

                # Create a reverse mapping for data access
                self._reverse_mapping = {v: k for k, v in header_dict.items()}
            else:
                self._headers = []
                self._reverse_mapping = {}

            self.endResetModel()
            logging.info(f"Model updated for collection {collection}. Rows: {len(self._data)}, Columns: {len(self._headers)}")
            logging.info(f"Headers: {self._headers}")

    def data(self, index, role):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._data) or col >= len(self._headers):
            return None

        try:
            header = self._headers[col]
            key = self._reverse_mapping.get(header, header)
            value = self._data[row].get(key, '')

            if role in [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]:
                if isinstance(value, bool):
                    return "Van" if value else "Nincs"
                elif isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    return str(value) if value is not None else ''

            elif role == Qt.ItemDataRole.BackgroundRole:
                if isinstance(value, bool):
                    return QColor(Qt.GlobalColor.green) if value else QColor(Qt.GlobalColor.red)
                elif isinstance(value, str):
                    lower_value = value.lower()
                    if lower_value in ['true', 'van', 'kirakható', 'telepíthető', 'kiadva', 'kirakva']:
                        return QColor(Qt.GlobalColor.green)
                    elif lower_value in ['false', 'nincs', 'nem_kirakható', 'nem telepíthető', 'statusz_nelkul']:
                        return QColor(Qt.GlobalColor.red)

        except Exception as e:
            logging.error(f"Error accessing data: {e}")

        return None

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal and section < len(self._headers):
                return self._headers[section]
            elif orientation == Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def update_single_item(self, item):
        item_id = item.get('Id')
        if not item_id:
            return

        for row, existing_item in enumerate(self._data):
            if existing_item.get('Id') == item_id:
                self._data[row].update(item)
                self.dataChanged.emit(self.index(row, 0), self.index(row, len(self._headers) - 1))
                return

        self.beginInsertRows(self.index(0, 0).parent(), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

    def remove_item(self, item_id):
        for row, item in enumerate(self._data):
            if item.get('Id') == item_id:
                self.beginRemoveRows(self.index(0, 0).parent(), row, row)
                del self._data[row]
                self.endRemoveRows()
                return