# File: sn_statistics_dashboard.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class SNStatisticsDashboard(QWidget):
    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.total_sn_label = None
        self.canvas = None
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.total_sn_label = QLabel(self)
        layout.addWidget(self.total_sn_label)

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def load_data(self):
        companies = self.firestore_service.get_all_documents("Company_Install")
        total_sn = 0
        sn_distribution = {}

        for company in companies:
            sn_count = len(self.firestore_service.get_sn_list(company['Id']))
            total_sn += sn_count
            sn_distribution[company['CompanyName']] = sn_count

        self.total_sn_label.setText(f"Total SN Count: {total_sn}")

        # Create pie chart
        ax = self.figure.add_subplot(111)
        wedges, texts, autotexts = ax.pie(sn_distribution.values(),
                                          labels=sn_distribution.keys(),
                                          autopct='%1.1f%%',
                                          textprops=dict(color="w"))

        ax.set_title("SN Distribution Across Companies")

        # Add legend
        ax.legend(wedges, sn_distribution.keys(),
                  title="Companies",
                  loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1))

        plt.setp(autotexts, size=8, weight="bold")
        self.figure.tight_layout()
        self.canvas.draw()