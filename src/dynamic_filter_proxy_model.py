import logging

from PyQt6.QtCore import Qt, QSortFilterProxyModel

class DynamicFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filter_text:
            return True

        for column in range(self.sourceModel().columnCount()):
            index = self.sourceModel().index(source_row, column, source_parent)
            data = self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole)
            if data is not None:
                try:
                    if self.filter_text.lower() in str(data).lower():
                        return True
                except Exception as e:
                    logging.warning(f"Error comparing filter text: {e}")
        return False

    def setFilterFixedString(self, pattern):
        self.filter_text = pattern
        self.invalidateFilter()