from PyQt6.QtWidgets import QStyledItemDelegate, QToolTip, QMessageBox
from PyQt6.QtCore import Qt, QEvent

class SNQuickViewDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.firestore_service = parent.firestore_service

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseMove:
            company_id = model.data(model.index(index.row(), 0), Qt.ItemDataRole.DisplayRole)
            sn_list = self.firestore_service.get_sn_list(company_id)
            preview = f"SN Count: {len(sn_list)}\nFirst 5 SNs: {', '.join(sn_list[:5])}"
            if len(sn_list) > 5:
                preview += "\n(Click to see all)"
            QToolTip.showText(event.globalPosition().toPoint(), preview)
        elif event.type() == QEvent.Type.MouseButtonPress:
            company_id = model.data(model.index(index.row(), 0), Qt.ItemDataRole.DisplayRole)
            sn_list = self.firestore_service.get_sn_list(company_id)
            QMessageBox.information(None, "All SNs", "\n".join(sn_list))
        return super().editorEvent(event, model, option, index)