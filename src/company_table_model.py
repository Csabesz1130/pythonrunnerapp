from PyQt6.QtCore import Qt, QAbstractTableModel

class CompanyTableModel(QAbstractTableModel):
    def __init__(self, data, headers, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            col = index.column()
            company = self._data[row]
            header = self._headers[col]

            # Handle specific fields that need to be converted to "Van" or "Nincs"
            if header in ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín", "Bázis Leszerelés"]:
                return "Van" if company.get(header, False) else "Nincs"

            # Handle the "Last Modified" field
            if header == "Last Modified":
                value = company.get(header, "")
                return str(value) if value else ""

            # For other fields, just return the value as a string
            return str(company.get(header, ""))

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def sort(self, column, order):
        """Sort table by given column number."""
        self.layoutAboutToBeChanged.emit()
        self._data = sorted(self._data, key=lambda x: x.get(self._headers[column], ""), reverse=(order == Qt.SortOrder.DescendingOrder))
        self.layoutChanged.emit()