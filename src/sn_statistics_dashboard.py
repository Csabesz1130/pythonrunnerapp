from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtChart import QChart, QChartView, QPieSeries

class SNStatisticsDashboard(QWidget):
    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.total_sn_label = QLabel()
        layout.addWidget(self.total_sn_label)

        self.chart_view = QChartView()
        layout.addWidget(self.chart_view)

    def load_data(self):
        companies = self.firestore_service.get_all_documents("Company_Install")
        total_sn = 0
        sn_distribution = {}

        for company in companies:
            sn_count = len(self.firestore_service.get_sn_list(company['Id']))
            total_sn += sn_count
            sn_distribution[company['CompanyName']] = sn_count

        self.total_sn_label.setText(f"Total SN Count: {total_sn}")

        series = QPieSeries()
        for company, count in sn_distribution.items():
            series.append(company, count)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("SN Distribution Across Companies")
        self.chart_view.setChart(chart)