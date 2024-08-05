from PyQt6.QtCore import QRunnable, pyqtSignal, QObject

class BulkEditWorkerSignals(QObject):
    finished = pyqtSignal(int, int, list)  # success_count, fail_count, not_found_ids
    progress = pyqtSignal(int)

class BulkEditWorker(QRunnable):
    def __init__(self, firestore_service, collection, field, value, selected_rows, company_table):
        super().__init__()
        self.firestore_service = firestore_service
        self.collection = collection
        self.field = field
        self.value = value
        self.selected_rows = selected_rows
        self.company_table = company_table
        self.signals = BulkEditWorkerSignals()

    def run(self):
        success_count = 0
        fail_count = 0
        not_found_ids = []
        total_rows = len(self.selected_rows)

        for i, row in enumerate(self.selected_rows):
            company_id = self.company_table.item(row, 0).text()
            data = {self.field: self.value}

            try:
                success = self.firestore_service.update_company(self.collection, company_id, data)
                if success:
                    success_count += 1
                else:
                    fail_count += 1
                    not_found_ids.append(company_id)
            except Exception:
                fail_count += 1
                not_found_ids.append(company_id)

            # Emit progress
            self.signals.progress.emit(int((i + 1) / total_rows * 100))

        self.signals.finished.emit(success_count, fail_count, not_found_ids)