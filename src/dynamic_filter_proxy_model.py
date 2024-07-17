from PyQt6.QtCore import Qt, QSortFilterProxyModel

class DynamicFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = {}

    def setFilter(self, column, pattern):
        if pattern:
            self.filters[column] = pattern
        elif column in self.filters:
            del self.filters[column]
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        for column, pattern in self.filters.items():
            index = self.sourceModel().index(source_row, column, source_parent)
            text = self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole)
            if text is None or pattern.lower() not in str(text).lower():
                return False
        return True