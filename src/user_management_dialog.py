from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QComboBox, QMessageBox, QListWidget, QLabel, QGridLayout)
from PyQt6.QtCore import pyqtSignal
import logging

class UserManagementDialog(QDialog):
    user_added = pyqtSignal(dict)

    def __init__(self, firestore_service, parent=None):
        super().__init__(parent)
        self.firestore_service = firestore_service
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        self.setWindowTitle("User Management")
        layout = QVBoxLayout(self)

        # User creation section
        creation_layout = QGridLayout()
        layout.addLayout(creation_layout)

        creation_layout.addWidget(QLabel("Username:"), 0, 0)
        self.username_input = QLineEdit()
        creation_layout.addWidget(self.username_input, 0, 1)

        creation_layout.addWidget(QLabel("Password:"), 1, 0)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        creation_layout.addWidget(self.password_input, 1, 1)

        creation_layout.addWidget(QLabel("Role:"), 2, 0)
        self.role_combo = QComboBox()
        self.role_combo.addItems(['user', 'superuser'])
        creation_layout.addWidget(self.role_combo, 2, 1)

        self.create_user_button = QPushButton("Create User")
        self.create_user_button.clicked.connect(self.create_user)
        creation_layout.addWidget(self.create_user_button, 3, 0, 1, 2)

        # User list section
        layout.addWidget(QLabel("Existing Users:"))
        self.user_list = QListWidget()
        layout.addWidget(self.user_list)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)

    def load_users(self):
        try:
            users = self.firestore_service.get_all_users()
            self.user_list.clear()
            for user in users:
                self.user_list.addItem(f"{user['username']} - {user['role']}")
        except Exception as e:
            logging.error(f"Error loading users: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load users: {str(e)}")

    def create_user(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password are required.")
            return

        try:
            success, message = self.firestore_service.create_user(username, password, role)
            if success:
                QMessageBox.information(self, "Success", message)
                self.user_added.emit({'username': username, 'role': role})
                self.username_input.clear()
                self.password_input.clear()
                self.load_users()
            else:
                QMessageBox.warning(self, "Error", message)
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create user: {str(e)}")

    def delete_user(self, username):
        try:
            success, message = self.firestore_service.delete_user(username)
            if success:
                QMessageBox.information(self, "Success", message)
                self.load_users()
            else:
                QMessageBox.warning(self, "Error", message)
        except Exception as e:
            logging.error(f"Error deleting user: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")