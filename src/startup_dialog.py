from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QComboBox)
from PyQt6.QtCore import pyqtSignal
import logging

class StartupDialog(QDialog):
    startup_successful = pyqtSignal(dict, str)

    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.user = None
        self.selected_festival = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Festival Management System - Login")
        layout = QVBoxLayout(self)

        # Festival selection
        festival_layout = QHBoxLayout()
        festival_label = QLabel("Select Festival:")
        self.festival_combo = QComboBox()
        self.populate_festivals()
        festival_layout.addWidget(festival_label)
        festival_layout.addWidget(self.festival_combo)
        layout.addLayout(festival_layout)

        # Username
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        # Password
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Login button
        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def populate_festivals(self):
        try:
            festivals = self.firestore_service.get_festivals()
            self.festival_combo.addItems(festivals)
        except Exception as e:
            logging.error(f"Error populating festivals: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load festivals: {str(e)}")

    def attempt_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        self.selected_festival = self.festival_combo.currentText()

        if not username or not password or not self.selected_festival:
            QMessageBox.warning(self, "Login Failed", "Please select a festival and enter both username and password.")
            return

        try:
            user = self.firestore_service.authenticate_user(username, password)
            if user:
                self.user = user
                self.startup_successful.emit(user, self.selected_festival)
                self.accept()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
        except Exception as e:
            logging.error(f"Error during login: {e}")
            QMessageBox.critical(self, "Login Error", f"An error occurred during login: {str(e)}")

    def get_user(self):
        return self.user

    def get_selected_festival(self):
        return self.selected_festival