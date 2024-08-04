import logging
from datetime import datetime

class ImportLogger:
    def __init__(self, log_file='import_log.txt'):
        self.log_file = log_file
        self.logger = logging.getLogger('ImportLogger')
        self.logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.current_import = None

    def start_import(self, file_name):
        self.current_import = {
            'file_name': file_name,
            'start_time': datetime.now(),
            'added': [],
            'updated': [],
            'skipped': [],
            'errors': []
        }
        self.logger.info(f"Started import of {file_name}")

    def log_added(self, record_id):
        self.current_import['added'].append(record_id)
        self.logger.info(f"Added record: {record_id}")

    def log_updated(self, record_id):
        self.current_import['updated'].append(record_id)
        self.logger.info(f"Updated record: {record_id}")

    def log_skipped(self, record_id, reason):
        self.current_import['skipped'].append((record_id, reason))
        self.logger.warning(f"Skipped record: {record_id}. Reason: {reason}")

    def log_error(self, record_id, error):
        self.current_import['errors'].append((record_id, str(error)))
        self.logger.error(f"Error processing record: {record_id}. Error: {error}")

    def end_import(self):
        end_time = datetime.now()
        duration = end_time - self.current_import['start_time']
        self.logger.info(f"Finished import of {self.current_import['file_name']}")
        self.logger.info(f"Duration: {duration}")
        self.logger.info(f"Added: {len(self.current_import['added'])}")
        self.logger.info(f"Updated: {len(self.current_import['updated'])}")
        self.logger.info(f"Skipped: {len(self.current_import['skipped'])}")
        self.logger.info(f"Errors: {len(self.current_import['errors'])}")

    def generate_report(self):
        report = f"Import Report for {self.current_import['file_name']}\n"
        report += f"Start Time: {self.current_import['start_time']}\n"
        report += f"End Time: {datetime.now()}\n"
        report += f"Added: {len(self.current_import['added'])}\n"
        report += f"Updated: {len(self.current_import['updated'])}\n"
        report += f"Skipped: {len(self.current_import['skipped'])}\n"
        report += f"Errors: {len(self.current_import['errors'])}\n"

        if self.current_import['skipped']:
            report += "\nSkipped Records:\n"
            for record_id, reason in self.current_import['skipped']:
                report += f"  {record_id}: {reason}\n"

        if self.current_import['errors']:
            report += "\nErrors:\n"
            for record_id, error in self.current_import['errors']:
                report += f"  {record_id}: {error}\n"

        return report