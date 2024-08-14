from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QComboBox, QLineEdit, QPushButton,
                             QProgressDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QUndoCommand, QUndoStack
from validators import validate_bulk_edit
import logging

class BulkEditCommand(QUndoCommand):
    def __init__(self, model, firestore_service, row, column, field, old_value, new_value):
        super().__init__(f"Edit {field}")
        self.model = model
        self.firestore_service = firestore_service
        self.row = row
        self.column = column
        self.field = field
        self.old_value = old_value
        self.new_value = new_value

    def redo(self):
        logging.info(f"Redoing bulk edit for row {self.row}, field {self.field}")
        self.model.setData(self.model.index(self.row, self.column), self.new_value)
        company_id = self.model.data(self.model.index(self.row, 0))
        self.firestore_service.update_company("Company_Install", company_id, {self.field: self.new_value})
        logging.info(f"Redo complete for company {company_id}, field {self.field}")

    def undo(self):
        logging.info(f"Undoing bulk edit for row {self.row}, field {self.field}")
        self.model.setData(self.model.index(self.row, self.column), self.old_value)
        company_id = self.model.data(self.model.index(self.row, 0))
        self.firestore_service.update_company("Company_Install", company_id, {self.field: self.old_value})
        logging.info(f"Undo complete for company {company_id}, field {self.field}")

class BulkEditDialog(QDialog):
    def __init__(self, model, selected_rows, firestore_service, undo_stack, parent=None):
        super().__init__(parent)
        self.model = model
        self.selected_rows = selected_rows
        self.firestore_service = firestore_service
        self.undo_stack = undo_stack
        self.setup_ui()
        logging.info("BulkEditDialog initialized")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.setWindowTitle("Bulk Edit")

        self.field_combo = QComboBox()
        self.field_combo.addItems([self.model.headerData(i, Qt.Orientation.Horizontal) for i in range(self.model.columnCount())])
        layout.addWidget(self.field_combo)

        self.value_input = QLineEdit()
        layout.addWidget(self.value_input)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_bulk_edit)
        layout.addWidget(self.apply_button)

        logging.info("BulkEditDialog UI setup complete")

    def apply_bulk_edit(self):
        logging.info("Starting bulk edit process")
        field = self.field_combo.currentText()
        value = self.value_input.text()

        errors = validate_bulk_edit(field, value)
        if errors:
            error_message = "\n".join(errors)
            logging.warning(f"Bulk edit validation failed: {error_message}")
            QMessageBox.warning(self, "Validation Error", error_message)
            return

        column = self.field_combo.currentIndex()

        progress = QProgressDialog("Applying bulk edit...", "Cancel", 0, len(self.selected_rows), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        macro_command = QUndoCommand("Bulk Edit")

        try:
            for i, row in enumerate(self.selected_rows):
                if progress.wasCanceled():
                    logging.info("Bulk edit cancelled by user")
                    break

                old_value = self.model.data(self.model.index(row, column))
                company_id = self.model.data(self.model.index(row, 0))  # Assuming ID is in the first column

                logging.info(f"Applying bulk edit to company {company_id}, field {field}, new value: {value}")

                # Create individual edit command
                edit_command = BulkEditCommand(self.model, self.firestore_service, row, column, field, old_value, value)
                edit_command.setParent(macro_command)

                progress.setValue(i + 1)
                QTimer.singleShot(0, lambda: None)  # Allow GUI to update

            # Push the macro command to the undo stack
            self.undo_stack.push(macro_command)
            logging.info(f"Bulk edit complete. {len(self.selected_rows)} companies updated.")

            QMessageBox.information(self, "Success", "Bulk edit applied successfully!")
            self.accept()

        except Exception as e:
            logging.error(f"Error during bulk edit: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An error occurred during bulk edit: {str(e)}")

        finally:
            progress.close()
            logging.info("Bulk edit dialog closed")