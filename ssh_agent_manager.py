"""
SSH Agent Manager for JETSSH
Provides SSH agent integration and key management
"""

import os
import socket
import struct
import logging
import platform
from pathlib import Path
import paramiko
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                             QPushButton, QMessageBox, QInputDialog, QTextEdit,
                             QCheckBox, QComboBox, QProgressBar, QTreeWidget,
                             QTreeWidgetItem, QHeaderView, QDialog, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class SSHAgentManager(QWidget):
    """SSH Agent Manager with key loading and management"""

    agent_status_changed = pyqtSignal(bool)  # connected
    key_loaded = pyqtSignal(str)             # key_path

    def __init__(self, ssh_client_app):
        super().__init__()
        self.ssh_client_app = ssh_client_app
        self.agent_client = None
        self.loaded_keys = {}
        self.pageant_client = None
        self.setup_ui()
        self.setup_agent_detection()

    def setup_ui(self):
        """Setup the SSH agent manager UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("SSH Agent Manager")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #dcdcdc;")
        layout.addWidget(title)

        # Agent status section
        status_layout = QHBoxLayout()

        self.status_label = QLabel("🔴 Not Connected")
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.connect_btn = QPushButton("Connect to Agent")
        self.connect_btn.clicked.connect(self.connect_to_agent)
        status_layout.addWidget(self.connect_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_agent_status)
        status_layout.addWidget(self.refresh_btn)

        layout.addLayout(status_layout)

        # Agent type selection
        agent_type_layout = QHBoxLayout()
        agent_type_layout.addWidget(QLabel("Agent Type:"))

        self.agent_type_combo = QComboBox()
        self.agent_type_combo.addItems(["Auto-detect", "OpenSSH Agent", "Pageant", "KeeAgent"])
        self.agent_type_combo.currentTextChanged.connect(self.on_agent_type_changed)
        agent_type_layout.addWidget(self.agent_type_combo)

        agent_type_layout.addStretch()

        # Auto-connect option
        self.auto_connect_checkbox = QCheckBox("Auto-connect on startup")
        self.auto_connect_checkbox.setChecked(True)
        agent_type_layout.addWidget(self.auto_connect_checkbox)

        layout.addLayout(agent_type_layout)

        # Loaded keys section
        keys_label = QLabel("Loaded Keys")
        keys_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(keys_label)

        self.keys_tree = QTreeWidget()
        self.keys_tree.setHeaderLabels([
            "Fingerprint", "Type", "Size", "Comment", "Status"
        ])
        self.keys_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.keys_tree)

        # Key operations
        key_ops_layout = QHBoxLayout()

        add_key_btn = QPushButton("➕ Add Key")
        add_key_btn.clicked.connect(self.add_key_to_agent)
        add_key_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        key_ops_layout.addWidget(add_key_btn)

        remove_key_btn = QPushButton("➖ Remove Key")
        remove_key_btn.clicked.connect(self.remove_key_from_agent)
        key_ops_layout.addWidget(remove_key_btn)

        lock_agent_btn = QPushButton("🔒 Lock Agent")
        lock_agent_btn.clicked.connect(self.lock_agent)
        key_ops_layout.addWidget(lock_agent_btn)

        unlock_agent_btn = QPushButton("🔓 Unlock Agent")
        unlock_agent_btn.clicked.connect(self.unlock_agent)
        key_ops_layout.addWidget(unlock_agent_btn)

        key_ops_layout.addStretch()

        clear_all_btn = QPushButton("🗑️ Clear All")
        clear_all_btn.clicked.connect(self.clear_all_keys)
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        key_ops_layout.addWidget(clear_all_btn)

        layout.addLayout(key_ops_layout)

        # Key discovery section
        discovery_label = QLabel("Key Discovery")
        discovery_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(discovery_label)

        discovery_layout = QHBoxLayout()

        scan_btn = QPushButton("🔍 Scan for Keys")
        scan_btn.clicked.connect(self.scan_for_keys)
        discovery_layout.addWidget(scan_btn)

        auto_load_btn = QPushButton("⚡ Auto-load Keys")
        auto_load_btn.clicked.connect(self.auto_load_keys)
        discovery_layout.addWidget(auto_load_btn)

        discovery_layout.addStretch()

        layout.addLayout(discovery_layout)

        # Found keys display
        self.found_keys_tree = QTreeWidget()
        self.found_keys_tree.setHeaderLabels([
            "Path", "Type", "Size", "Encrypted", "Actions"
        ])
        self.found_keys_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.found_keys_tree.setMaximumHeight(150)
        layout.addWidget(self.found_keys_tree)

        # Agent information
        info_label = QLabel("Agent Information")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(info_label)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        layout.addWidget(self.info_text)

        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds

    def setup_agent_detection(self):
        """Setup agent detection and auto-connect"""
        if self.auto_connect_checkbox.isChecked():
            QTimer.singleShot(1000, self.connect_to_agent)

    def connect_to_agent(self):
        """Connect to SSH agent"""
        agent_type = self.agent_type_combo.currentText()

        try:
            if agent_type == "Auto-detect":
                self.agent_client = self.detect_and_connect_agent()
            elif agent_type == "OpenSSH Agent":
                self.agent_client = self.connect_openssh_agent()
            elif agent_type == "Pageant":
                self.agent_client = self.connect_pageant()
            elif agent_type == "KeeAgent":
                self.agent_client = self.connect_keeagent()

            if self.agent_client:
                self.status_label.setText("🟢 Connected")
                self.connect_btn.setText("Disconnect")
                self.connect_btn.clicked.disconnect()
                self.connect_btn.clicked.connect(self.disconnect_from_agent)
                self.agent_status_changed.emit(True)
                self.refresh_loaded_keys()
                self.update_agent_info()
                QMessageBox.information(self, "Success", f"Connected to {agent_type}")
            else:
                self.status_label.setText("🔴 Connection Failed")
                QMessageBox.warning(self, "Error", "Failed to connect to SSH agent")

        except Exception as e:
            self.status_label.setText("🔴 Connection Error")
            QMessageBox.critical(self, "Error", f"Failed to connect to agent: {str(e)}")
            logger.error(f"Agent connection error: {e}")

    def detect_and_connect_agent(self):
        """Auto-detect and connect to available SSH agent"""
        # Try different agent types in order of preference
        agents_to_try = [
            ("OpenSSH Agent", self.connect_openssh_agent),
            ("Pageant", self.connect_pageant),
            ("KeeAgent", self.connect_keeagent)
        ]

        for agent_name, connect_func in agents_to_try:
            try:
                agent = connect_func()
                if agent:
                    logger.info(f"Auto-detected and connected to {agent_name}")
                    return agent
            except Exception as e:
                logger.debug(f"Failed to connect to {agent_name}: {e}")

        return None

    def connect_openssh_agent(self):
        """Connect to OpenSSH agent"""
        try:
            # Try environment variable first
            ssh_auth_sock = os.environ.get('SSH_AUTH_SOCK')
            if ssh_auth_sock and os.path.exists(ssh_auth_sock):
                agent = paramiko.Agent()
                keys = agent.get_keys()
                return agent

            # On Windows, try named pipe
            if platform.system() == "Windows":
                try:
                    agent = paramiko.Agent()
                    keys = agent.get_keys()
                    return agent
                except:
                    pass

            return None

        except Exception as e:
            logger.error(f"OpenSSH agent connection error: {e}")
            return None

    def connect_pageant(self):
        """Connect to Pageant (Windows)"""
        if platform.system() != "Windows":
            return None

        try:
            import win32gui
            import win32con

            # Find Pageant window
            pageant_window = win32gui.FindWindow("Pageant", "Pageant")
            if not pageant_window:
                return None

            # Create Pageant client
            self.pageant_client = PageantClient()
            if self.pageant_client.is_available():
                return self.pageant_client

            return None

        except ImportError:
            logger.warning("win32gui not available, cannot connect to Pageant")
            return None
        except Exception as e:
            logger.error(f"Pageant connection error: {e}")
            return None

    def connect_keeagent(self):
        """Connect to KeeAgent"""
        # KeeAgent uses the same protocol as Pageant on Windows
        # and can also work through SSH_AUTH_SOCK on Unix
        if platform.system() == "Windows":
            return self.connect_pageant()
        else:
            return self.connect_openssh_agent()

    def disconnect_from_agent(self):
        """Disconnect from SSH agent"""
        try:
            if self.agent_client:
                if hasattr(self.agent_client, 'close'):
                    self.agent_client.close()
                self.agent_client = None

            if self.pageant_client:
                self.pageant_client = None

            self.status_label.setText("🔴 Disconnected")
            self.connect_btn.setText("Connect to Agent")
            self.connect_btn.clicked.disconnect()
            self.connect_btn.clicked.connect(self.connect_to_agent)
            self.agent_status_changed.emit(False)
            self.keys_tree.clear()
            self.info_text.clear()

        except Exception as e:
            logger.error(f"Agent disconnection error: {e}")

    def refresh_agent_status(self):
        """Refresh agent status and loaded keys"""
        if self.agent_client:
            try:
                self.refresh_loaded_keys()
                self.update_agent_info()
            except Exception as e:
                logger.error(f"Agent refresh error: {e}")
                self.disconnect_from_agent()

    def refresh_loaded_keys(self):
        """Refresh the list of loaded keys"""
        self.keys_tree.clear()

        if not self.agent_client:
            return

        try:
            if isinstance(self.agent_client, PageantClient):
                keys = self.agent_client.get_keys()
            else:
                keys = self.agent_client.get_keys()

            for key in keys:
                try:
                    # Get key information
                    key_type = key.get_name()
                    key_size = key.get_bits() if hasattr(key, 'get_bits') else "Unknown"
                    fingerprint = self.get_key_fingerprint(key)
                    comment = getattr(key, 'comment', 'No comment')

                    item = QTreeWidgetItem([
                        fingerprint,
                        key_type,
                        str(key_size),
                        comment,
                        "Loaded"
                    ])

                    self.keys_tree.addTopLevelItem(item)

                except Exception as e:
                    logger.error(f"Error processing key: {e}")

        except Exception as e:
            logger.error(f"Error refreshing keys: {e}")

    def get_key_fingerprint(self, key):
        """Get SSH key fingerprint"""
        try:
            import hashlib
            import base64

            # Get public key data
            public_key_data = key.asbytes()

            # Calculate MD5 fingerprint (traditional format)
            md5_hash = hashlib.md5(public_key_data).hexdigest()
            fingerprint = ':'.join(md5_hash[i:i+2] for i in range(0, len(md5_hash), 2))

            return fingerprint

        except Exception as e:
            logger.error(f"Error calculating fingerprint: {e}")
            return "Unknown"

    def add_key_to_agent(self):
        """Add a key to the SSH agent"""
        from PyQt5.QtWidgets import QFileDialog

        key_file, _ = QFileDialog.getOpenFileName(
            self, "Select SSH Private Key",
            str(Path.home() / ".ssh"),
            "SSH Keys (id_rsa id_dsa id_ecdsa id_ed25519 *.pem *.key);;All Files (*)"
        )

        if not key_file:
            return

        try:
            # Check if key is encrypted
            if self.is_key_encrypted(key_file):
                passphrase, ok = QInputDialog.getText(
                    self, "Key Passphrase",
                    f"Enter passphrase for {os.path.basename(key_file)}:",
                    QLineEdit.Password
                )
                if not ok:
                    return
            else:
                passphrase = None

            # Load and add key
            if self.load_key_to_agent(key_file, passphrase):
                self.refresh_loaded_keys()
                self.key_loaded.emit(key_file)
                QMessageBox.information(self, "Success", f"Key {os.path.basename(key_file)} added to agent")
            else:
                QMessageBox.warning(self, "Error", "Failed to add key to agent")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add key: {str(e)}")
            logger.error(f"Add key error: {e}")

    def is_key_encrypted(self, key_file):
        """Check if SSH key is encrypted"""
        try:
            with open(key_file, 'r') as f:
                content = f.read()
                return "ENCRYPTED" in content or "Proc-Type: 4,ENCRYPTED" in content
        except:
            return False

    def load_key_to_agent(self, key_file, passphrase=None):
        """Load a key into the SSH agent"""
        try:
            # For OpenSSH agent, we need to use ssh-add command
            if isinstance(self.agent_client, paramiko.Agent):
                return self.ssh_add_key(key_file, passphrase)
            elif isinstance(self.agent_client, PageantClient):
                return self.pageant_add_key(key_file, passphrase)

            return False

        except Exception as e:
            logger.error(f"Load key error: {e}")
            return False

    def ssh_add_key(self, key_file, passphrase=None):
        """Add key using ssh-add command"""
        try:
            import subprocess

            env = os.environ.copy()
            if passphrase:
                # Use SSH_ASKPASS for non-interactive passphrase
                env['SSH_ASKPASS'] = 'echo'
                env['DISPLAY'] = ':0'

            cmd = ['ssh-add', key_file]

            if passphrase:
                process = subprocess.Popen(
                    cmd, env=env, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate(input=passphrase.encode())
            else:
                process = subprocess.run(
                    cmd, env=env, capture_output=True, text=True
                )
                stdout, stderr = process.stdout, process.stderr

            return process.returncode == 0

        except Exception as e:
            logger.error(f"ssh-add error: {e}")
            return False

    def pageant_add_key(self, key_file, passphrase=None):
        """Add key to Pageant"""
        try:
            # Load key with paramiko first
            if key_file.endswith('.pem') or 'rsa' in key_file:
                key = paramiko.RSAKey.from_private_key_file(key_file, password=passphrase)
            elif 'dsa' in key_file:
                key = paramiko.DSSKey.from_private_key_file(key_file, password=passphrase)
            elif 'ecdsa' in key_file:
                key = paramiko.ECDSAKey.from_private_key_file(key_file, password=passphrase)
            elif 'ed25519' in key_file:
                key = paramiko.Ed25519Key.from_private_key_file(key_file, password=passphrase)
            else:
                # Try to auto-detect
                key = paramiko.RSAKey.from_private_key_file(key_file, password=passphrase)

            # Add to Pageant (this would require low-level Windows API calls)
            return self.pageant_client.add_key(key)

        except Exception as e:
            logger.error(f"Pageant add key error: {e}")
            return False

    def remove_key_from_agent(self):
        """Remove selected key from agent"""
        current_item = self.keys_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No key selected")
            return

        fingerprint = current_item.text(0)

        reply = QMessageBox.question(
            self, "Remove Key",
            f"Remove key with fingerprint {fingerprint} from agent?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if self.remove_key_by_fingerprint(fingerprint):
                    self.refresh_loaded_keys()
                    QMessageBox.information(self, "Success", "Key removed from agent")
                else:
                    QMessageBox.warning(self, "Error", "Failed to remove key")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove key: {str(e)}")

    def remove_key_by_fingerprint(self, fingerprint):
        """Remove key by fingerprint"""
        try:
            if isinstance(self.agent_client, paramiko.Agent):
                # Use ssh-add -d for OpenSSH agent
                import subprocess
                result = subprocess.run(['ssh-add', '-d'], capture_output=True, text=True)
                return result.returncode == 0
            elif isinstance(self.agent_client, PageantClient):
                return self.pageant_client.remove_key_by_fingerprint(fingerprint)

            return False

        except Exception as e:
            logger.error(f"Remove key error: {e}")
            return False

    def lock_agent(self):
        """Lock the SSH agent"""
        try:
            import subprocess
            result = subprocess.run(['ssh-add', '-x'], capture_output=True, text=True)
            if result.returncode == 0:
                QMessageBox.information(self, "Success", "Agent locked")
                self.refresh_loaded_keys()
            else:
                QMessageBox.warning(self, "Error", "Failed to lock agent")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to lock agent: {str(e)}")

    def unlock_agent(self):
        """Unlock the SSH agent"""
        try:
            import subprocess
            result = subprocess.run(['ssh-add', '-X'], capture_output=True, text=True)
            if result.returncode == 0:
                QMessageBox.information(self, "Success", "Agent unlocked")
                self.refresh_loaded_keys()
            else:
                QMessageBox.warning(self, "Error", "Failed to unlock agent")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to unlock agent: {str(e)}")

    def clear_all_keys(self):
        """Clear all keys from agent"""
        reply = QMessageBox.question(
            self, "Clear All Keys",
            "Remove all keys from agent?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if isinstance(self.agent_client, paramiko.Agent):
                    import subprocess
                    result = subprocess.run(['ssh-add', '-D'], capture_output=True, text=True)
                    success = result.returncode == 0
                elif isinstance(self.agent_client, PageantClient):
                    success = self.pageant_client.clear_all_keys()
                else:
                    success = False

                if success:
                    self.refresh_loaded_keys()
                    QMessageBox.information(self, "Success", "All keys cleared from agent")
                else:
                    QMessageBox.warning(self, "Error", "Failed to clear keys")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear keys: {str(e)}")

    def scan_for_keys(self):
        """Scan for SSH keys in common locations"""
        self.found_keys_tree.clear()

        # Common SSH key locations
        ssh_dir = Path.home() / ".ssh"
        common_names = [
            "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
            "identity", "ssh_host_rsa_key", "ssh_host_dsa_key"
        ]

        found_keys = []

        # Scan SSH directory
        if ssh_dir.exists():
            for key_file in ssh_dir.glob("*"):
                if key_file.is_file() and not key_file.name.endswith(".pub"):
                    if (key_file.name in common_names or
                        key_file.suffix in ['.pem', '.key'] or
                        self.looks_like_ssh_key(key_file)):
                        found_keys.append(key_file)

        # Display found keys
        for key_path in found_keys:
            try:
                key_type = self.detect_key_type(key_path)
                key_size = self.get_key_size(key_path)
                is_encrypted = self.is_key_encrypted(str(key_path))

                item = QTreeWidgetItem([
                    str(key_path),
                    key_type,
                    str(key_size),
                    "Yes" if is_encrypted else "No",
                    ""
                ])

                # Add load button
                load_btn = QPushButton("Load")
                load_btn.clicked.connect(lambda checked, path=str(key_path): self.load_found_key(path))
                load_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 4px 8px;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)

                self.found_keys_tree.addTopLevelItem(item)
                self.found_keys_tree.setItemWidget(item, 4, load_btn)

            except Exception as e:
                logger.error(f"Error processing found key {key_path}: {e}")

        if found_keys:
            QMessageBox.information(self, "Scan Complete", f"Found {len(found_keys)} SSH keys")
        else:
            QMessageBox.information(self, "Scan Complete", "No SSH keys found")

    def looks_like_ssh_key(self, file_path):
        """Check if file looks like an SSH key"""
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                return (first_line.startswith("-----BEGIN") and
                        ("PRIVATE KEY" in first_line or "RSA PRIVATE KEY" in first_line))
        except:
            return False

    def detect_key_type(self, key_path):
        """Detect SSH key type"""
        try:
            with open(key_path, 'r') as f:
                content = f.read()
                if "RSA PRIVATE KEY" in content:
                    return "RSA"
                elif "DSA PRIVATE KEY" in content:
                    return "DSA"
                elif "EC PRIVATE KEY" in content:
                    return "ECDSA"
                elif "OPENSSH PRIVATE KEY" in content:
                    return "Ed25519"
                else:
                    return "Unknown"
        except:
            return "Unknown"

    def get_key_size(self, key_path):
        """Get SSH key size"""
        try:
            # Try to load key to get size
            for key_class in [paramiko.RSAKey, paramiko.DSSKey, paramiko.ECDSAKey, paramiko.Ed25519Key]:
                try:
                    key = key_class.from_private_key_file(str(key_path))
                    return getattr(key, 'get_bits', lambda: "Unknown")()
                except:
                    continue
            return "Unknown"
        except:
            return "Unknown"

    def load_found_key(self, key_path):
        """Load a found key into the agent"""
        try:
            if self.is_key_encrypted(key_path):
                passphrase, ok = QInputDialog.getText(
                    self, "Key Passphrase",
                    f"Enter passphrase for {os.path.basename(key_path)}:",
                    QLineEdit.Password
                )
                if not ok:
                    return
            else:
                passphrase = None

            if self.load_key_to_agent(key_path, passphrase):
                self.refresh_loaded_keys()
                QMessageBox.information(self, "Success", f"Key {os.path.basename(key_path)} loaded")
            else:
                QMessageBox.warning(self, "Error", "Failed to load key")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load key: {str(e)}")

    def auto_load_keys(self):
        """Auto-load common SSH keys"""
        ssh_dir = Path.home() / ".ssh"
        common_keys = ["id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"]

        loaded_count = 0

        for key_name in common_keys:
            key_path = ssh_dir / key_name
            if key_path.exists():
                try:
                    # Try loading without passphrase first
                    if not self.is_key_encrypted(str(key_path)):
                        if self.load_key_to_agent(str(key_path)):
                            loaded_count += 1
                    else:
                        # For encrypted keys, ask for passphrase
                        passphrase, ok = QInputDialog.getText(
                            self, "Key Passphrase",
                            f"Enter passphrase for {key_name} (or cancel to skip):",
                            QLineEdit.Password
                        )
                        if ok and passphrase:
                            if self.load_key_to_agent(str(key_path), passphrase):
                                loaded_count += 1

                except Exception as e:
                    logger.error(f"Auto-load error for {key_name}: {e}")

        self.refresh_loaded_keys()
        QMessageBox.information(self, "Auto-load Complete", f"Loaded {loaded_count} keys")

    def update_agent_info(self):
        """Update agent information display"""
        info_lines = []

        if self.agent_client:
            try:
                if isinstance(self.agent_client, paramiko.Agent):
                    info_lines.append("Agent Type: OpenSSH Agent")
                    auth_sock = os.environ.get('SSH_AUTH_SOCK', 'Not set')
                    info_lines.append(f"SSH_AUTH_SOCK: {auth_sock}")
                elif isinstance(self.agent_client, PageantClient):
                    info_lines.append("Agent Type: Pageant")
                    info_lines.append("Platform: Windows")

                keys = self.agent_client.get_keys()
                info_lines.append(f"Loaded Keys: {len(keys)}")

                # Agent capabilities
                info_lines.append("")
                info_lines.append("Capabilities:")
                info_lines.append("  ✓ Key loading")
                info_lines.append("  ✓ Key removal")
                info_lines.append("  ✓ Authentication")

                if isinstance(self.agent_client, paramiko.Agent):
                    info_lines.append("  ✓ Agent locking")

            except Exception as e:
                info_lines.append(f"Error getting agent info: {e}")

        else:
            info_lines.append("No agent connected")

        self.info_text.setText('\n'.join(info_lines))

    def on_agent_type_changed(self, agent_type):
        """Handle agent type change"""
        if self.agent_client:
            self.disconnect_from_agent()

    def auto_refresh(self):
        """Auto-refresh agent status"""
        if self.agent_client:
            try:
                # Test agent connection
                keys = self.agent_client.get_keys()
                # If we get here, agent is still connected
            except:
                # Agent disconnected
                self.disconnect_from_agent()

    def get_agent_for_connection(self):
        """Get agent client for SSH connections"""
        return self.agent_client


class PageantClient:
    """Client for communicating with Pageant on Windows"""

    def __init__(self):
        self.available = False
        if platform.system() == "Windows":
            try:
                import win32gui
                self.pageant_window = win32gui.FindWindow("Pageant", "Pageant")
                self.available = bool(self.pageant_window)
            except ImportError:
                pass

    def is_available(self):
        """Check if Pageant is available"""
        return self.available

    def get_keys(self):
        """Get keys from Pageant"""
        # This would implement the Pageant protocol
        # For now, return empty list
        return []

    def add_key(self, key):
        """Add key to Pageant"""
        # This would implement key addition via Pageant protocol
        return False

    def remove_key_by_fingerprint(self, fingerprint):
        """Remove key by fingerprint"""
        # This would implement key removal via Pageant protocol
        return False

    def clear_all_keys(self):
        """Clear all keys from Pageant"""
        # This would implement clearing all keys via Pageant protocol
        return False