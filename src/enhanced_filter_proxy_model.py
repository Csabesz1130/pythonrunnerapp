from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtWidgets import QLineEdit, QComboBox, QHBoxLayout

class EnhancedFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sn_filter = ""
        self.min_sn_count = 0

    def filterAcceptsRow(self, source_row, source_parent):
        # Existing filter logic
        if not super().filterAcceptsRow(source_row, source_parent):
            return False

        # SN filter
        if self.sn_filter:
            index = self.sourceModel().index(source_row, 0, source_parent)
            company_id = self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole)
            sn_list = self.sourceModel().firestore_service.get_sn_list(company_id)
            if not any(self.sn_filter in sn for sn in sn_list):
                return False

        # SN count filter
        if self.min_sn_count > 0:
            index = self.sourceModel().index(source_row, self.sourceModel().columnCount() - 1, source_parent)
            sn_count = self.sourceModel().data(index, Qt.ItemDataRole.DisplayRole)
            if sn_count < self.min_sn_count:
                return False

        return True

    def set_sn_filter(self, filter_text):
        self.sn_filter = filter_text
        self.invalidateFilter()

    def set_min_sn_count(self, count):
        self.min_sn_count = count
        self.invalidateFilter()

# In MainWindow class:
def setup_ui(self):
    # ... existing code ...
    filter_layout = QHBoxLayout()
    self.search_input = QLineEdit()
    self.search_input.setPlaceholderText("Search...")
    self.sn_search_input = QLineEdit()
    self.sn_search_input.setPlaceholderText("Search SN...")
    self.min_sn_count_input = QComboBox()
    self.min_sn_count_input.addItems(["All", "1+", "5+", "10+", "50+", "100+"])
    filter_layout.addWidget(self.search_input)
    filter_layout.addWidget(self.sn_search_input)
    filter_layout.addWidget(self.min_sn_count_input)
    self.layout().addLayout(filter_layout)

    self.search_input.textChanged.connect(self.apply_filter)
    self.sn_search_input.textChanged.connect(self.apply_filter)
    self.min_sn_count_input.currentTextChanged.connect(self.apply_filter)

def apply_filter(self):
    self.proxy_model.setFilterFixedString(self.search_input.text())
    self.proxy_model.set_sn_filter(self.sn_search_input.text())
    min_sn_text = self.min_sn_count_input.currentText()
    min_sn_count = int(min_sn_text[:-1]) if min_sn_text != "All" else 0
    self.proxy_model.set_min_sn_count(min_sn_count)

def setup_models(self):
    # ... existing code ...
    self.proxy_model = EnhancedFilterProxyModel(self)
    self.proxy_model.setSourceModel(self.source_model)
    self.table_view.setModel(self.proxy_model)