from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis, QPieSeries, QBarSet, \
    QBarSeries, QBarCategoryAxis
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import Qt

class SNStatisticsDashboard(QWidget):
    def __init__(self, firestore_service):
        super().__init__()
        self.firestore_service = firestore_service
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs for different charts
        self.create_company_distribution_tab()
        self.create_installation_status_tab()
        self.create_sn_statistics_tab()
        self.create_boolean_field_analysis_tab()

    def create_company_distribution_tab(self):
        chart_view = QChartView()
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.tab_widget.addTab(chart_view, "Company Distribution")
        self.company_distribution_chart = chart_view.chart()

    def create_installation_status_tab(self):
        chart_view = QChartView()
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.tab_widget.addTab(chart_view, "Installation Status")
        self.installation_status_chart = chart_view.chart()

    def create_sn_statistics_tab(self):
        chart_view = QChartView()
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.tab_widget.addTab(chart_view, "SN Statistics")
        self.sn_statistics_chart = chart_view.chart()

    def create_boolean_field_analysis_tab(self):
        chart_view = QChartView()
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.tab_widget.addTab(chart_view, "Boolean Field Analysis")
        self.boolean_field_chart = chart_view.chart()

    def load_data(self):
        # Fetch data from Firestore
        companies = self.firestore_service.get_all_documents("Company_Install")

        self.update_company_distribution_chart(companies)
        self.update_installation_status_chart(companies)
        self.update_sn_statistics_chart(companies)
        self.update_boolean_field_chart(companies)

    def update_company_distribution_chart(self, companies):
        program_counts = {}
        for company in companies:
            program = company.get('ProgramName', 'Unknown')
            program_counts[program] = program_counts.get(program, 0) + 1

        series = QPieSeries()
        for program, count in program_counts.items():
            series.append(f"{program} ({count})", count)

        self.company_distribution_chart.addSeries(series)
        self.company_distribution_chart.setTitle("Company Distribution by Program")

    def update_installation_status_chart(self, companies):
        status_counts = {'TELEPÍTHETŐ': 0, 'KIRAKHATÓ': 0, 'NEM KIRAKHATÓ': 0}
        for company in companies:
            status = company.get('felderites', 'Unknown')
            if status in status_counts:
                status_counts[status] += 1

        series = QBarSeries()
        bar_set = QBarSet("Installation Status")
        for count in status_counts.values():
            bar_set.append(count)
        series.append(bar_set)

        self.installation_status_chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(list(status_counts.keys()))
        self.installation_status_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        self.installation_status_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.installation_status_chart.setTitle("Installation Status Distribution")

    def update_sn_statistics_chart(self, companies):
        sn_counts = [len(self.firestore_service.get_sn_list(company['Id'])) for company in companies]

        series = QBarSeries()
        bar_set = QBarSet("SN Count")
        for count in sn_counts:
            bar_set.append(count)
        series.append(bar_set)

        self.sn_statistics_chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append([str(i) for i in range(len(companies))])
        self.sn_statistics_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        self.sn_statistics_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.sn_statistics_chart.setTitle("SN Count per Company")

    def update_boolean_field_chart(self, companies):
        boolean_fields = ["Elosztó", "Áram", "Hálózat", "PTG", "Szoftver", "Param", "Helyszín"]
        field_counts = {field: sum(1 for company in companies if company.get(field.lower(), False)) for field in boolean_fields}

        series = QBarSeries()
        bar_set = QBarSet("True Count")
        for count in field_counts.values():
            bar_set.append(count)
        series.append(bar_set)

        self.boolean_field_chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(boolean_fields)
        self.boolean_field_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        self.boolean_field_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.boolean_field_chart.setTitle("Boolean Field Analysis")