from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import pyqtSignal
import logging

class LoginDialog(QDialog):
    login_successful = pyqtSignal(dict)

    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.user = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Login")
        layout = QVBoxLayout(self)

        self.username_label = QLabel("Username:")
        layout.addWidget(self.username_label)

        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Enter your username")
        layout.addWidget(self.username_input)

        self.password_label = QLabel("Password:")
        layout.addWidget(self.password_label)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)

    def attempt_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both username and password.")
            return

        try:
            user = self.firestore_service.authenticate_user(username, password)
            if user:
                self.user = user
                self.login_successful.emit(user)
                self.accept()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
        except Exception as e:
            logging.error(f"Error during login: {e}")
            QMessageBox.critical(self, "Login Error", f"An error occurred during login: {str(e)}")

    def get_user(self):
        return self.user