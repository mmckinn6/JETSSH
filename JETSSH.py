import os
import sys
import paramiko
import threading
import re
import json  # For connection persistence
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QTabWidget, QTextEdit,
                             QFileDialog, QInputDialog, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui

# Set the Qt platform plugin to use X11 instead of Wayland
os.environ["QT_QPA_PLATFORM"] = "xcb"

# Path to the connections JSON file
CONNECTIONS_FILE = 'connections.json'


class SSHClientApp(QWidget):
    output_received = pyqtSignal(str)  # Define a signal to receive output

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.connections = []  # Store tuples of (host, username, private_key)
        self.ssh_clients = {}
        self.channels = {}

        # Command history attributes
        self.command_history = []  # List to store command history
        self.history_index = -1    # Current position in the history

        # Load connections from the JSON file on startup
        self.load_connections()

        # Connect the signal to the output box update method
        self.output_received.connect(self.update_output)

    def init_ui(self):
        # Set up the main layout
        main_layout = QHBoxLayout(self)

        # Sidebar layout (for managing connections)
        sidebar_layout = QVBoxLayout()

        # Connection List
        self.connection_list = QListWidget()
        sidebar_layout.addWidget(QLabel("Connections"))
        sidebar_layout.addWidget(self.connection_list)

        # Buttons for adding and removing connections
        add_button = QPushButton("Add Connection")
        add_button.clicked.connect(self.add_connection)

        remove_button = QPushButton("Remove Connection")
        remove_button.clicked.connect(self.remove_connection)

        launch_button = QPushButton("Launch Session")
        launch_button.clicked.connect(self.launch_ssh_session)

        sidebar_layout.addWidget(add_button)
        sidebar_layout.addWidget(remove_button)
        sidebar_layout.addWidget(launch_button)

        # SSH Tab Area
        self.tab_widget = QTabWidget()

        # Add everything to the main layout
        main_layout.addLayout(sidebar_layout, 1)
        main_layout.addWidget(self.tab_widget, 3)

        self.setWindowTitle("JETSSH Client")
        self.resize(900, 600)

        # Apply stylesheet for UI
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #dcdcdc;
                font-family: Consolas, Monaco, monospace;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: #00ffff;  # Neon blue for command input
                border: 1px solid #3a3a3a;
            }
            QPushButton {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QListWidget {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
            }
            QLabel {
                color: #dcdcdc;
                font-size: 14px;
            }
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
            }
            QTabBar::tab {
                background-color: #2e2e2e;
                padding: 10px;
                color: #dcdcdc;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QScrollBar:vertical {
                border: 1px solid #3a3a3a;
                background-color: #1e1e1e;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 5px;
                min-height: 20px;
            }
        """)

    def add_connection(self):
        # Input dialog to get connection details
        host, ok_host = QInputDialog.getText(self, "Host", "Enter SSH Host:")
        user, ok_user = QInputDialog.getText(self, "Username", "Enter SSH Username:")
        if ok_host and ok_user and host and user:
            private_key, _ = QFileDialog.getOpenFileName(self, "Select Private Key (Optional)", "", "Key Files (*.pem *.ppk)")
            self.connections.append({"host": host, "user": user, "private_key": private_key})  # Add to connection list
            display_key = "Using Key" if private_key else "Using Password"
            self.connection_list.addItem(f"{host} ({user}) [{display_key}]")

            # Save connections to file after adding a new one
            self.save_connections()
        else:
            QMessageBox.warning(self, "Input Error", "Host and Username are required.")

    def remove_connection(self):
        selected_item = self.connection_list.currentRow()
        if selected_item >= 0:
            del self.connections[selected_item]
            self.connection_list.takeItem(selected_item)

            # Save connections to file after removal
            self.save_connections()

    def launch_ssh_session(self):
        selected_item = self.connection_list.currentRow()
        if selected_item < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a connection.")
            return

        connection = self.connections[selected_item]
        host = connection["host"]
        username = connection["user"]
        key_file = connection["private_key"]

        # Use password if no key is provided
        if not key_file:
            password, ok = QInputDialog.getText(self, "Password", f"Enter SSH password for {username}@{host}:", echo=QLineEdit.Password)
            if not ok or not password:
                QMessageBox.warning(self, "Input Error", "Password is required.")
                return

        try:
            # Create an SSH client instance
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if key_file:  # If key file is provided
                private_key = paramiko.RSAKey.from_private_key_file(key_file)
                ssh.connect(host, username=username, pkey=private_key)
            else:  # Use password-based authentication
                ssh.connect(host, username=username, password=password)

            self.ssh_clients[host] = ssh  # Store the SSH client

            # Open a new channel for the session
            channel = ssh.invoke_shell()
            self.channels[host] = channel

            # Create a new tab for the SSH session
            session_tab = QWidget()
            session_layout = QVBoxLayout()

            splitter = QSplitter(Qt.Vertical)

            self.output_box = QTextEdit()
            self.output_box.setReadOnly(True)
            splitter.addWidget(self.output_box)

            self.command_log = QTextEdit()  # New widget to keep command history
            self.command_log.setReadOnly(True)
            splitter.addWidget(self.command_log)

            self.command_entry = CommandLineEdit(self)  # Replace with custom QLineEdit for history
            self.command_entry.setPlaceholderText("Enter command...")
            self.command_entry.returnPressed.connect(lambda: self.send_command(host))

            session_layout.addWidget(splitter)
            session_layout.addWidget(self.command_entry)
            session_tab.setLayout(session_layout)

            self.tab_widget.addTab(session_tab, f"{host} ({username})")
            self.tab_widget.setCurrentWidget(session_tab)

            # Start a thread to read output from the channel
            output_thread = threading.Thread(target=self.read_output, args=(host,))
            output_thread.daemon = True
            output_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")

    def strip_ansi_codes(self, text):
        """ Remove ANSI escape codes from the output """
        ansi_escape = re.compile(r'(?:\x1B[@-_][0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def read_output(self, host):
        channel = self.channels[host]
        while True:
            if channel.recv_ready():
                output = channel.recv(1024).decode()
                clean_output = self.strip_ansi_codes(output)  # Clean the output
                self.output_received.emit(clean_output)  # Emit signal with cleaned output

    def send_command(self, host):
        command = self.command_entry.text().strip()
        if command and host in self.channels:
            channel = self.channels[host]
            command_with_newline = command + "\n"
            channel.send(command_with_newline)

            # Add command to the command log
            self.command_log.append(command)

            # Add command to history and reset index
            self.command_history.append(command)
            self.history_index = -1

        self.command_entry.clear()

    def update_output(self, output):
        """ Update the output box with new data and auto-scroll """
        self.output_box.moveCursor(QtGui.QTextCursor.End)
        self.output_box.insertPlainText(output)
        self.output_box.moveCursor(QtGui.QTextCursor.End)  # Ensure it stays at the bottom

    def save_connections(self):
        """ Save connection details to a JSON file """
        with open(CONNECTIONS_FILE, 'w') as file:
            json.dump(self.connections, file)

    def load_connections(self):
        """ Load connection details from the JSON file """
        if os.path.exists(CONNECTIONS_FILE):
            with open(CONNECTIONS_FILE, 'r') as file:
                self.connections = json.load(file)

            # Populate the QListWidget with loaded connections
            for connection in self.connections:
                host = connection["host"]
                user = connection["user"]
                display_key = "Using Key" if connection["private_key"] else "Using Password"
                self.connection_list.addItem(f"{host} ({user}) [{display_key}]")


# Custom QLineEdit to handle command history navigation
class CommandLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        # Check for Up/Down arrow keys for history navigation
        if event.key() == Qt.Key_Up:
            if self.parent.history_index == -1 and self.parent.command_history:
                self.parent.history_index = len(self.parent.command_history) - 1
            elif self.parent.history_index > 0:
                self.parent.history_index -= 1
            if self.parent.command_history:
                self.setText(self.parent.command_history[self.parent.history_index])
        elif event.key() == Qt.Key_Down:
            if self.parent.history_index < len(self.parent.command_history) - 1:
                self.parent.history_index += 1
                self.setText(self.parent.command_history[self.parent.history_index])
            else:
                self.clear()
                self.parent.history_index = -1
        else:
            super().keyPressEvent(event)  # Call the default event handler


# Main entry point of the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ssh_app = SSHClientApp()
    ssh_app.show()
    sys.exit(app.exec_())
