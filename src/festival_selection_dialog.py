from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel

class FestivalSelectionDialog(QDialog):
    def __init__(self, festivals, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Festival")
        self.festivals = festivals
        self.selected_festival = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Please select a festival:")
        layout.addWidget(label)

        self.festival_combo = QComboBox()
        self.festival_combo.addItems(self.festivals)
        layout.addWidget(self.festival_combo)

        select_button = QPushButton("Select")
        select_button.clicked.connect(self.accept)
        layout.addWidget(select_button)

    def get_selected_festival(self):
        return self.festival_combo.currentText()