from PyQt6.QtCore import Qt, QSortFilterProxyModel
import logging

class DynamicFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.filter_text = ""

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filter_text:
            return True

        source_model = self.sourceModel()
        company_data = source_model.data(source_model.index(source_row, 0), Qt.ItemDataRole.UserRole)

        # Check CompanyName
        if self.filter_text.lower() in company_data.get('CompanyName', '').lower():
            return True

        # Check CompanyCode if it exists
        if self.filter_text.lower() in company_data.get('CompanyCode', '').lower():
            return True

        # Check SN numbers
        company_id = company_data.get('Id')
        if company_id:
            sn_list = self.firestore_service.get_sn_list(company_id)
            if any(self.filter_text.lower() in sn.lower() for sn in sn_list):
                return True

        return False

    def setFilterFixedString(self, pattern):
        self.filter_text = pattern
        self.invalidateFilter()