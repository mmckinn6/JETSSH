import os
import sys
import socket
import paramiko
import threading
import re
import json
import logging
import getpass
from pathlib import Path
import JETSSHKEYGEN
from PredefinedCommands import PredefinedCommands
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QTabWidget, QTextEdit,
                             QFileDialog, QInputDialog, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QMutex
from PyQt5.QtGui import QTextCursor

# Set the Qt platform plugin to use X11 instead of Wayland
#os.environ["QT_QPA_PLATFORM"] = "xcb"

# Path to the connections JSON file
CONNECTIONS_FILE = 'connections.json'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jetssh.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SSHClientApp(QWidget):
    output_received = pyqtSignal(str, str)  # Signal to pass (host, output)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.connections = []  # Store tuples of (host, username, private_key)
        self.ssh_clients = {}
        self.channels = {}
        self.output_boxes = {}  # Map to store output boxes for each tab
        self.output_threads = {}  # Track output threads for proper cleanup
        self.mutex = QMutex()   # Mutex for thread safety
        self.shutdown_flag = threading.Event()  # Graceful shutdown flag

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

        #Enabling closing tabs

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
        # Enable closable tabs and connect close event
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        # Adding the SSH key generation tab @Nick
        self.keygen_tab = JETSSHKEYGEN.SSHKeyGeneratorTab()
        self.tab_widget.addTab(self.keygen_tab, "SSH Key Generator")

        # Add everything to the main layout
        main_layout.addLayout(sidebar_layout, 1)
        main_layout.addWidget(self.tab_widget, 3)

        self.setWindowTitle("JETSSH Client - Enhanced")
        self.resize(900, 600)

        # Load stylesheet from external file
        self.load_stylesheet()

        # Set a custom object name for the launch button to apply specific styles
        launch_button.setObjectName("launchButton")

    def load_stylesheet(self):
        """Load stylesheet from external CSS file"""
        try:
            css_path = os.path.join(os.path.dirname(__file__), 'styles.css')
            if os.path.exists(css_path):
                with open(css_path, 'r') as css_file:
                    self.setStyleSheet(css_file.read())
                logger.info("Loaded external stylesheet")
            else:
                logger.warning("External stylesheet not found, using default styles")
                self.apply_default_stylesheet()
        except Exception as e:
            logger.error(f"Error loading stylesheet: {str(e)}")
            self.apply_default_stylesheet()

    def apply_default_stylesheet(self):
        """Apply basic fallback stylesheet"""
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #dcdcdc; }
            QPushButton { background-color: #2e2e2e; color: #dcdcdc; border: 1px solid #3a3a3a; padding: 5px; }
            QTextEdit { background-color: #1e1e1e; color: #dcdcdc; border: 1px solid #3a3a3a; }
            QLineEdit { background-color: #1e1e1e; color: #00ffff; border: 1px solid #3a3a3a; }
        """)

    def add_connection(self):
        """Add a new SSH connection with validation"""
        # Input dialog to get connection details
        host, ok_host = QInputDialog.getText(self, "Host", "Enter SSH Host:")
        if not ok_host or not host or not host.strip():
            return

        host = host.strip()

        # Basic hostname validation
        if not self.validate_hostname(host):
            QMessageBox.warning(self, "Invalid Host", "Please enter a valid hostname or IP address.")
            return

        user, ok_user = QInputDialog.getText(self, "Username", "Enter SSH Username:")
        if not ok_user or not user or not user.strip():
            return

        user = user.strip()

        # Check for duplicate connections
        if any(conn['host'] == host and conn['user'] == user for conn in self.connections):
            QMessageBox.warning(self, "Duplicate Connection", "This connection already exists.")
            return

        private_key, _ = QFileDialog.getOpenFileName(
            self, "Select Private Key (Optional)", "",
            "Key Files (*.pem *.ppk *.pub *.key);;All Files (*)"
        )

        # Validate private key file if provided
        if private_key and not os.path.exists(private_key):
            QMessageBox.warning(self, "Key File Error", "Selected private key file does not exist.")
            return

        connection = {"host": host, "user": user, "private_key": private_key or ""}
        self.connections.append(connection)
        display_key = "Using Key" if private_key else "Using Password"
        self.connection_list.addItem(f"{host} ({user}) [{display_key}]")

        # Save connections to file after adding a new one
        if self.save_connections():
            logger.info(f"Added connection: {user}@{host}")

    def validate_hostname(self, hostname):
        """Basic hostname validation"""
        if not hostname or len(hostname) > 255:
            return False

        # Allow localhost and IP addresses
        if hostname in ['localhost', '127.0.0.1']:
            return True

        # Basic regex for hostname/IP validation
        import re
        hostname_pattern = re.compile(
            r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
        )
        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )

        return bool(hostname_pattern.match(hostname) or ip_pattern.match(hostname))

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

            # Use more secure host key policy
            known_hosts_path = os.path.expanduser('~/.ssh/known_hosts')
            if os.path.exists(known_hosts_path):
                ssh.load_host_keys(known_hosts_path)
            ssh.set_missing_host_key_policy(paramiko.WarningPolicy())

            if key_file:  # If key file is provided
                private_key = self.load_private_key(key_file)
                if private_key:
                    ssh.connect(host, username=username, pkey=private_key)
                else:
                    raise ValueError("Failed to load private key")
            else:  # Use password-based authentication
                ssh.connect(host, username=username, password=password)
                # Clear password from memory
                password = None

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

            predefined_commands_widget = PredefinedCommands(self)  # Pass SSH client reference
            session_layout.addWidget(predefined_commands_widget)  # Add Predefined Commands UI to the tab

            self.tab_widget.addTab(session_tab, f"{host} ({username})")
            self.tab_widget.setCurrentWidget(session_tab)

            # Map the output box to the host
            self.output_boxes[host] = output_box

            # Start a thread to read output from the channel
            output_thread = threading.Thread(target=self.read_output, args=(host,))
            output_thread.daemon = True
            output_thread.start()
            self.output_threads[host] = output_thread

        except paramiko.AuthenticationException:
            logger.error(f"Authentication failed for {username}@{host}")
            QMessageBox.critical(self, "Authentication Error", "Authentication failed. Please check your credentials.")
        except paramiko.SSHException as e:
            logger.error(f"SSH connection error for {host}: {str(e)}")
            QMessageBox.critical(self, "SSH Error", f"SSH connection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to {host}: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")

    def load_private_key(self, key_file):
        """Load private key supporting multiple key types"""
        if not os.path.exists(key_file):
            logger.error(f"Private key file not found: {key_file}")
            return None

        try:
            # Try different key types
            for key_class in [paramiko.RSAKey, paramiko.DSSKey, paramiko.ECDSAKey, paramiko.Ed25519Key]:
                try:
                    return key_class.from_private_key_file(key_file)
                except paramiko.SSHException:
                    continue
                except paramiko.PasswordRequiredException:
                    # Handle encrypted keys
                    passphrase, ok = QInputDialog.getText(
                        self, "Key Passphrase",
                        f"Enter passphrase for key {os.path.basename(key_file)}:",
                        echo=QLineEdit.Password
                    )
                    if ok and passphrase:
                        try:
                            key = key_class.from_private_key_file(key_file, password=passphrase)
                            passphrase = None  # Clear from memory
                            return key
                        except paramiko.SSHException:
                            continue

            logger.error(f"Unable to load private key: {key_file}")
            return None

        except Exception as e:
            logger.error(f"Error loading private key {key_file}: {str(e)}")
            return None

    def strip_ansi_codes(self, text):
        """ Keep only relevant ANSI codes like colors and strip unnecessary ones """
        ansi_escape_color = re.compile(r'(\x1B[@-_][0-?]*[ -/]*[@-~])')
        if '\x1b[H\x1b[J' in text:  # This is the escape sequence for clearing the screen
            text = text.replace('\x1b[H\x1b[J', '')  # Strip the clear screen code
        return ansi_escape_color.sub('', text)

    def read_output(self, host):
        """Read output from SSH channel with proper termination conditions"""
        channel = self.channels.get(host)
        if not channel:
            logger.warning(f"No channel found for host: {host}")
            return

        try:
            while (channel.active and host in self.channels and
                   not self.shutdown_flag.is_set()):
                try:
                    if channel.recv_ready():
                        output = channel.recv(1024).decode('utf-8', errors='ignore')
                        if output:
                            clean_output = self.strip_ansi_codes(output)
                            self.output_received.emit(host, clean_output)
                    else:
                        # Small sleep to prevent excessive CPU usage
                        # Use shutdown_flag for interruptible sleep
                        if self.shutdown_flag.wait(0.1):
                            break

                    # Check if channel is still active
                    if channel.exit_status_ready():
                        break

                except (socket.timeout, socket.error):
                    break
                except Exception as e:
                    logger.error(f"Error reading from channel {host}: {str(e)}")
                    break

        except Exception as e:
            logger.error(f"Critical error in read_output for {host}: {str(e)}")
        finally:
            logger.info(f"Read output thread for {host} terminated")

    def send_command(self, host):
        command = self.command_entry.text().strip()
        if not command:
            self.command_entry.clear()
            return

        if host not in self.channels:
            logger.warning(f"No active channel for host: {host}")
            QMessageBox.warning(self, "Connection Error", "No active SSH session for this host.")
            return

        try:
            channel = self.channels[host]
            if not channel.active:
                logger.warning(f"Channel for {host} is not active")
                QMessageBox.warning(self, "Connection Error", "SSH session is not active.")
                return

            # Send the command
            channel.send(command + "\n")
            logger.debug(f"Sent command to {host}: {command}")

            # Add the command to the history if it's not empty and not a duplicate
            if command and (not self.command_history or self.command_history[-1] != command):
                self.command_history.append(command)

                # Limit history size
                if len(self.command_history) > 1000:
                    self.command_history = self.command_history[-1000:]

            # Reset history index after sending a command
            self.history_index = -1

        except Exception as e:
            logger.error(f"Error sending command to {host}: {str(e)}")
            QMessageBox.critical(self, "Command Error", f"Failed to send command: {str(e)}")

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
        """Save connection details to a JSON file with proper error handling"""
        try:
            # Validate connections data
            if not isinstance(self.connections, list):
                logger.error("Invalid connections data structure")
                return False

            # Create backup of existing file
            if os.path.exists(CONNECTIONS_FILE):
                backup_file = f"{CONNECTIONS_FILE}.backup"
                try:
                    os.rename(CONNECTIONS_FILE, backup_file)
                except OSError as e:
                    logger.warning(f"Could not create backup: {e}")

            # Save with proper permissions
            with open(CONNECTIONS_FILE, 'w') as file:
                json.dump(self.connections, file, indent=2)

            # Set restrictive permissions (owner read/write only)
            try:
                os.chmod(CONNECTIONS_FILE, 0o600)
            except OSError:
                logger.warning("Could not set restrictive permissions on connections file")

            logger.info(f"Saved {len(self.connections)} connections")
            return True

        except (IOError, OSError, json.JSONEncodeError) as e:
            logger.error(f"Error saving connections: {str(e)}")
            QMessageBox.critical(self, "Save Error", f"Failed to save connections: {str(e)}")
            return False

    def load_connections(self):
        """Load connection details from the JSON file with validation"""
        self.connections = []

        if not os.path.exists(CONNECTIONS_FILE):
            logger.info("No connections file found, starting with empty list")
            return

        try:
            # Check file permissions
            file_stat = os.stat(CONNECTIONS_FILE)
            if file_stat.st_mode & 0o077:  # Check if file is readable by others
                logger.warning("Connections file has permissive permissions")

            with open(CONNECTIONS_FILE, 'r') as file:
                data = json.load(file)

            # Validate data structure
            if not isinstance(data, list):
                logger.error("Invalid connections file format")
                return

            # Validate each connection
            valid_connections = []
            for connection in data:
                if self.validate_connection(connection):
                    valid_connections.append(connection)
                else:
                    logger.warning(f"Skipping invalid connection: {connection}")

            self.connections = valid_connections

            # Populate the QListWidget with loaded connections
            for connection in self.connections:
                host = connection.get("host", "Unknown")
                user = connection.get("user", "Unknown")
                display_key = "Using Key" if connection.get("private_key") else "Using Password"
                self.connection_list.addItem(f"{host} ({user}) [{display_key}]")

            logger.info(f"Loaded {len(self.connections)} valid connections")

        except (IOError, OSError, json.JSONDecodeError) as e:
            logger.error(f"Error loading connections: {str(e)}")
            QMessageBox.warning(self, "Load Error", f"Failed to load connections: {str(e)}")

    def validate_connection(self, connection):
        """Validate connection data structure"""
        if not isinstance(connection, dict):
            return False

        required_fields = ["host", "user"]
        for field in required_fields:
            if field not in connection or not isinstance(connection[field], str):
                return False

        # Validate private_key field (can be empty string or valid path)
        private_key = connection.get("private_key", "")
        if not isinstance(private_key, str):
            return False

        return True

    def close_tab(self, index):
        """Close tab with proper resource cleanup"""
        # Get the host associated with this tab
        tab_text = self.tab_widget.tabText(index)
        if not tab_text or '(' not in tab_text:
            self.tab_widget.removeTab(index)
            return

        try:
            host = tab_text.split()[0]  # Extract host from tab title
        except (IndexError, AttributeError):
            logger.warning(f"Could not extract host from tab text: {tab_text}")
            self.tab_widget.removeTab(index)
            return

        # Don't close the SSH Key Generator tab
        if "SSH Key Generator" in tab_text:
            self.tab_widget.removeTab(index)
            return

        logger.info(f"Closing connection to {host}")

        # Close the SSH connection and associated resources
        try:
            # Close the channel first
            if host in self.channels:
                channel = self.channels.pop(host, None)
                if channel and channel.active:
                    channel.close()
                    logger.debug(f"Closed channel for {host}")

            # Wait for output thread to finish (with timeout)
            if host in self.output_threads:
                output_thread = self.output_threads.pop(host, None)
                if output_thread and output_thread.is_alive():
                    output_thread.join(timeout=2.0)
                    if output_thread.is_alive():
                        logger.warning(f"Output thread for {host} did not terminate gracefully")

            # Close SSH client
            if host in self.ssh_clients:
                ssh_client = self.ssh_clients.pop(host, None)
                if ssh_client:
                    ssh_client.close()
                    logger.debug(f"Closed SSH client for {host}")

            # Clean up GUI references
            self.output_boxes.pop(host, None)

        except Exception as e:
            logger.error(f"Error closing connection to {host}: {str(e)}")

        # Remove the tab from the widget
        self.tab_widget.removeTab(index)
        logger.info(f"Tab for {host} closed successfully")

    def closeEvent(self, event):
        """Handle application shutdown with proper cleanup"""
        logger.info("Application shutting down, cleaning up connections...")

        # Set shutdown flag
        self.shutdown_flag.set()

        # Close all connections
        hosts_to_close = list(self.ssh_clients.keys())
        for host in hosts_to_close:
            try:
                # Close channel
                if host in self.channels:
                    channel = self.channels[host]
                    if channel.active:
                        channel.close()

                # Close SSH client
                if host in self.ssh_clients:
                    ssh_client = self.ssh_clients[host]
                    ssh_client.close()

            except Exception as e:
                logger.error(f"Error closing connection to {host} during shutdown: {str(e)}")

        # Wait for all output threads to finish
        for host, thread in self.output_threads.items():
            if thread.is_alive():
                thread.join(timeout=1.0)

        logger.info("Application shutdown complete")
        event.accept()


    # File Upload Functionality
    def upload_file(self):
        selected_item = self.connection_list.currentRow()
        if selected_item < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a connection.")
            return

        connection = self.connections[selected_item]
        host = connection["host"]

        # Verify SSH connection exists
        if host not in self.ssh_clients:
            QMessageBox.warning(self, "Connection Error", "No active SSH connection for this host.")
            return

        # Open a file dialog to select files to upload
        local_file, _ = QFileDialog.getOpenFileName(self, "Select File to Upload", "", "All Files (*)")
        if not local_file or not os.path.exists(local_file):
            return

        # Validate file size (limit to 1GB)
        try:
            file_size = os.path.getsize(local_file)
            if file_size > 1024 * 1024 * 1024:  # 1GB limit
                QMessageBox.warning(self, "File Too Large", "File size exceeds 1GB limit.")
                return
        except OSError as e:
            QMessageBox.critical(self, "File Error", f"Cannot access file: {str(e)}")
            return

        # Ask the user for the destination directory on the remote server
        remote_directory, ok = QInputDialog.getText(self, "Remote Directory", "Enter the destination directory on the remote server:")
        if not ok or not remote_directory:
            return

        try:
            # Establish an SFTP connection
            sftp_client = self.ssh_clients[host].open_sftp()

            # Validate remote directory
            try:
                sftp_client.stat(remote_directory)
            except FileNotFoundError:
                QMessageBox.critical(self, "Directory Error", f"Remote directory does not exist: {remote_directory}")
                sftp_client.close()
                return

            # Get the remote file path
            remote_file = os.path.join(remote_directory, os.path.basename(local_file))

            # Check if remote file already exists
            try:
                sftp_client.stat(remote_file)
                reply = QMessageBox.question(
                    self, "File Exists",
                    f"Remote file {os.path.basename(local_file)} already exists. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    sftp_client.close()
                    return
            except FileNotFoundError:
                pass  # File doesn't exist, safe to upload

            # Upload the file
            logger.info(f"Uploading {local_file} to {host}:{remote_file}")
            sftp_client.put(local_file, remote_file)
            sftp_client.close()

            logger.info(f"Successfully uploaded {local_file} to {host}:{remote_directory}")
            QMessageBox.information(self, "Upload Successful", f"File {os.path.basename(local_file)} uploaded to {remote_directory}.")

        except paramiko.SFTPError as e:
            logger.error(f"SFTP error during upload: {str(e)}")
            QMessageBox.critical(self, "SFTP Error", f"SFTP operation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Upload error for {local_file}: {str(e)}")
            QMessageBox.critical(self, "Upload Error", f"Failed to upload file: {str(e)}")

    # File Download Functionality
    def download_file(self):
        selected_item = self.connection_list.currentRow()
        if selected_item < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a connection.")
            return

        connection = self.connections[selected_item]
        host = connection["host"]

        # Verify SSH connection exists
        if host not in self.ssh_clients:
            QMessageBox.warning(self, "Connection Error", "No active SSH connection for this host.")
            return

        # Ask the user for the remote file path
        remote_file, ok = QInputDialog.getText(self, "Remote File", "Enter the path of the file to download from the remote server:")
        if not ok or not remote_file:
            return

        # Open a file dialog to select a download location
        local_directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if not local_directory:
            return

        try:
            # Establish an SFTP connection
            sftp_client = self.ssh_clients[host].open_sftp()

            # Validate remote file exists and get its info
            try:
                file_stat = sftp_client.stat(remote_file)
                file_size = file_stat.st_size

                # Check file size (limit to 1GB)
                if file_size > 1024 * 1024 * 1024:  # 1GB limit
                    QMessageBox.warning(self, "File Too Large", "Remote file size exceeds 1GB limit.")
                    sftp_client.close()
                    return

            except FileNotFoundError:
                QMessageBox.critical(self, "File Error", f"Remote file does not exist: {remote_file}")
                sftp_client.close()
                return

            # Get the local file path
            local_file = os.path.join(local_directory, os.path.basename(remote_file))

            # Check if local file already exists
            if os.path.exists(local_file):
                reply = QMessageBox.question(
                    self, "File Exists",
                    f"Local file {os.path.basename(remote_file)} already exists. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    sftp_client.close()
                    return

            # Download the file
            logger.info(f"Downloading {host}:{remote_file} to {local_file}")
            sftp_client.get(remote_file, local_file)
            sftp_client.close()

            logger.info(f"Successfully downloaded {remote_file} from {host}")
            QMessageBox.information(self, "Download Successful", f"File {os.path.basename(remote_file)} downloaded to {local_directory}.")

        except paramiko.SFTPError as e:
            logger.error(f"SFTP error during download: {str(e)}")
            QMessageBox.critical(self, "SFTP Error", f"SFTP operation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Download error for {remote_file}: {str(e)}")
            QMessageBox.critical(self, "Download Error", f"Failed to download file: {str(e)}")


# Custom QLineEdit to handle command history navigation and terminal features
class CommandLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        # Handle Ctrl+C to send interrupt signal (like in a real terminal)
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            current_host = self.get_current_host()
            if current_host and current_host in self.parent.channels:
                # Send interrupt signal (Ctrl+C equivalent)
                self.parent.channels[current_host].send("\x03")
                logger.info(f"Sent Ctrl+C to {current_host}")
            return

        # Handle Ctrl+D to close the session
        if event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
            current_host = self.get_current_host()
            if current_host and current_host in self.parent.channels:
                # Send exit command (Ctrl+D equivalent)
                self.parent.channels[current_host].send("\x04")
                logger.info(f"Sent Ctrl+D to {current_host}")
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

    def get_current_host(self):
        """Get the host for the currently active tab"""
        if not self.parent.tab_widget:
            return None

        current_index = self.parent.tab_widget.currentIndex()
        if current_index < 0:
            return None

        tab_text = self.parent.tab_widget.tabText(current_index)
        if not tab_text or '(' not in tab_text:
            return None

        # Extract host from tab text "host (username)"
        try:
            return tab_text.split()[0]
        except (IndexError, AttributeError):
            return None


# Main entry point of the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ssh_app = SSHClientApp()
    ssh_app.show()
    sys.exit(app.exec_())
