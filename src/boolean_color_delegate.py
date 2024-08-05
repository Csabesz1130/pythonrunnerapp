from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt

class BooleanColorDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        value = index.data(Qt.ItemDataRole.UserRole)
        if isinstance(value, bool):
            if value:
                background_color = QColor(144, 238, 144)  # Light green
                text = "True"
            else:
                background_color = QColor(255, 182, 193)  # Light red
                text = "False"

            painter.save()
            painter.fillRect(option.rect, background_color)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(option.rect, Qt.AlignmentFlag.AlignCenter, text)
            painter.restore()
        else:
            super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        return None  # Make it read-only