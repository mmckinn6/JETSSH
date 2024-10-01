import os
import sys
import paramiko
import threading
import re
import json
import JETSSHKEYGEN
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QTabWidget, QTextEdit,
                             QFileDialog, QInputDialog, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QMutex
from PyQt5.QtGui import QTextCursor

# Set the Qt platform plugin to use X11 instead of Wayland
#os.environ["QT_QPA_PLATFORM"] = "xcb"

# Path to the connections JSON file
CONNECTIONS_FILE = 'connections.json'


class SSHClientApp(QWidget):
    output_received = pyqtSignal(str, str)  # Signal to pass (host, output)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.connections = []  # Store tuples of (host, username, private_key)
        self.ssh_clients = {}
        self.channels = {}
        self.output_boxes = {}  # Map to store output boxes for each tab
        self.mutex = QMutex()   # Mutex for thread safety

        # Command history attributes
        self.command_history = []  # List to store command history
        self.history_index = -1    # Current position in the history

        # Load connections from the JSON file on startup
        self.load_connections()

        # Connect the signal to the output update method
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

        # Buttons for managing connections
        connection_button_layout = QVBoxLayout()

        # Launch button (moved above the other buttons)
        launch_button = QPushButton("Launch Session")
        launch_button.clicked.connect(self.launch_ssh_session)

        # Add and Remove buttons
        add_button = QPushButton("Add Connection")
        add_button.clicked.connect(self.add_connection)

        remove_button = QPushButton("Remove Connection")
        remove_button.clicked.connect(self.remove_connection)

        # Group the connection-related buttons
        connection_button_layout.addWidget(launch_button)  # Launch button first
        connection_button_layout.addWidget(add_button)
        connection_button_layout.addWidget(remove_button)

        # Add connection-related buttons to sidebar
        sidebar_layout.addLayout(connection_button_layout)

        # Separator to visually separate file transfer buttons
        sidebar_layout.addSpacing(20)

        # File Transfer buttons
        file_transfer_button_layout = QVBoxLayout()

        upload_button = QPushButton("Upload File")
        upload_button.clicked.connect(self.upload_file)

        download_button = QPushButton("Download File")
        download_button.clicked.connect(self.download_file)

        file_transfer_button_layout.addWidget(upload_button)
        file_transfer_button_layout.addWidget(download_button)

        # Add file transfer-related buttons to sidebar
        sidebar_layout.addLayout(file_transfer_button_layout)

        # SSH Tab Area
        self.tab_widget = QTabWidget()

        # Adding the SSH key generation tab @Nick
        self.keygen_tab = JETSSHKEYGEN.SSHKeyGeneratorTab()
        self.tab_widget.addTab(self.keygen_tab, "SSH Key Generator")

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
                color: #00ffff;
                border: 1px solid #3a3a3a;
            }
            QPushButton {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                padding: 5px;
                font-size: 14px;
                border-radius: 5px;
                box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.4);
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                box-shadow: 4px 4px 8px rgba(0, 0, 0, 0.6);
            }
            QPushButton:pressed {
                background-color: #4e4e4e;
                box-shadow: none;
            }
            QPushButton#launchButton {
                background-color: #ff8c00; /* Orange color */
                color: #ffffff;
                border-radius: 8px;
                border: 2px solid #4e4e4e;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
                box-shadow: 3px 3px 6px rgba(0, 0, 0, 0.6);
            }
            QPushButton#launchButton:hover {
                background-color: #ffa500;
                border: 2px solid #4e4e4e;
                box-shadow: 5px 5px 10px rgba(0, 0, 0, 0.8);
            }
            QPushButton#launchButton:pressed {
                background-color: #ff7f00;
                border: 2px solid #4e4e4e;
                box-shadow: none;
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

        # Set a custom object name for the launch button to apply specific styles
        launch_button.setObjectName("launchButton")

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

            output_box = QTextEdit()
            output_box.setReadOnly(True)
            splitter.addWidget(output_box)

            self.command_entry = CommandLineEdit(self)  # Replace with custom QLineEdit for history and terminal features
            self.command_entry.setPlaceholderText("Enter command...")
            self.command_entry.returnPressed.connect(lambda: self.send_command(host))

            session_layout.addWidget(splitter)
            session_layout.addWidget(self.command_entry)
            session_tab.setLayout(session_layout)

            self.tab_widget.addTab(session_tab, f"{host} ({username})")
            self.tab_widget.setCurrentWidget(session_tab)

            # Map the output box to the host
            self.output_boxes[host] = output_box

            # Start a thread to read output from the channel
            output_thread = threading.Thread(target=self.read_output, args=(host,))
            output_thread.daemon = True
            output_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")

    def strip_ansi_codes(self, text):
        """ Keep only relevant ANSI codes like colors and strip unnecessary ones """
        ansi_escape_color = re.compile(r'(\x1B[@-_][0-?]*[ -/]*[@-~])')
        if '\x1b[H\x1b[J' in text:  # This is the escape sequence for clearing the screen
            text = text.replace('\x1b[H\x1b[J', '')  # Strip the clear screen code
        return ansi_escape_color.sub('', text)

    def read_output(self, host):
        channel = self.channels[host]
        while True:
            if channel.recv_ready():
                output = channel.recv(1024).decode()
                clean_output = self.strip_ansi_codes(output)
                self.output_received.emit(host, clean_output)

    def send_command(self, host):
        command = self.command_entry.text().strip()
        if command and host in self.channels:
            channel = self.channels[host]
            channel.send(command + "\n")

            # Add the command to the history if it's not empty
            if command:
                self.command_history.append(command)

            # Reset history index after sending a command
            self.history_index = -1

        self.command_entry.clear()

    def update_output(self, host, output):
        """ Update the output box specific to the host and ensure thread safety """
        if host in self.output_boxes:
            self.mutex.lock()  # Lock for thread safety
            output_box = self.output_boxes[host]
            output_box.moveCursor(QTextCursor.End)
            output_box.insertPlainText(output)
            output_box.moveCursor(QTextCursor.End)  # Ensure it stays at the bottom
            self.mutex.unlock()  # Unlock after updating the output box

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

    # File Upload Functionality
    def upload_file(self):
        selected_item = self.connection_list.currentRow()
        if selected_item < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a connection.")
            return

        connection = self.connections[selected_item]
        host = connection["host"]

        # Open a file dialog to select files to upload
        local_file, _ = QFileDialog.getOpenFileName(self, "Select File to Upload", "", "All Files (*)")
        if local_file:
            # Ask the user for the destination directory on the remote server
            remote_directory, ok = QInputDialog.getText(self, "Remote Directory", "Enter the destination directory on the remote server:")
            if ok:
                try:
                    # Establish an SFTP connection
                    sftp_client = self.ssh_clients[host].open_sftp()

                    # Get the remote file path
                    remote_file = os.path.join(remote_directory, os.path.basename(local_file))

                    # Upload the file
                    sftp_client.put(local_file, remote_file)
                    sftp_client.close()

                    QMessageBox.information(self, "Upload Successful", f"File {os.path.basename(local_file)} uploaded to {remote_directory}.")
                except Exception as e:
                    QMessageBox.critical(self, "Upload Error", f"Failed to upload file: {str(e)}")

    # File Download Functionality
    def download_file(self):
        selected_item = self.connection_list.currentRow()
        if selected_item < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a connection.")
            return

        connection = self.connections[selected_item]
        host = connection["host"]

        # Ask the user for the remote file path
        remote_file, ok = QInputDialog.getText(self, "Remote File", "Enter the path of the file to download from the remote server:")
        if ok:
            # Open a file dialog to select a download location
            local_directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
            if local_directory:
                try:
                    # Establish an SFTP connection
                    sftp_client = self.ssh_clients[host].open_sftp()

                    # Get the local file path
                    local_file = os.path.join(local_directory, os.path.basename(remote_file))

                    # Download the file
                    sftp_client.get(remote_file, local_file)
                    sftp_client.close()

                    QMessageBox.information(self, "Download Successful", f"File {os.path.basename(remote_file)} downloaded to {local_directory}.")
                except Exception as e:
                    QMessageBox.critical(self, "Download Error", f"Failed to download file: {str(e)}")


# Custom QLineEdit to handle command history navigation and terminal features
class CommandLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        # Handle Ctrl+C to send interrupt signal (like in a real terminal)
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            if self.parent.channels:
                # Send interrupt signal (Ctrl+C equivalent)
                self.parent.channels[list(self.parent.channels.keys())[0]].send("\x03")
            return

        # Handle Ctrl+D to close the session
        if event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
            if self.parent.channels:
                # Send exit command (Ctrl+D equivalent)
                self.parent.channels[list(self.parent.channels.keys())[0]].send("\x04")
            return

        # Check for Up/Down arrow keys for history navigation
        if event.key() == Qt.Key_Up:
            if self.parent.command_history:
                if self.parent.history_index == -1:
                    self.parent.history_index = len(self.parent.command_history) - 1
                elif self.parent.history_index > 0:
                    self.parent.history_index -= 1
                self.setText(self.parent.command_history[self.parent.history_index])
            return
        elif event.key() == Qt.Key_Down:
            if self.parent.command_history:
                if self.parent.history_index < len(self.parent.command_history) - 1:
                    self.parent.history_index += 1
                    self.setText(self.parent.command_history[self.parent.history_index])
                else:
                    self.clear()
                    self.parent.history_index = -1
            return

        super().keyPressEvent(event)  # Call the default event handler


# Main entry point of the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ssh_app = SSHClientApp()
    ssh_app.show()
    sys.exit(app.exec_())