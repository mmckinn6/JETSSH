"""
Enhanced JETSSH - Top-tier SSH Client
Integrates all advanced features for professional SSH management
"""

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

# Import core modules
import JETSSHKEYGEN
from PredefinedCommands import PredefinedCommands

# Import new enhanced modules
try:
    from terminal_emulator import TerminalEmulator
    from ssh_tunnel_manager import SSHTunnelManager
    from sftp_browser import SFTPBrowser
    from session_manager import SessionManager
    from command_palette import CommandPalette, KeyboardShortcutManager
    from ssh_agent_manager import SSHAgentManager
    from connection_multiplexer import ConnectionMultiplexer
    from plugin_manager import PluginManager
except ImportError as e:
    print(f"Warning: Some enhanced features not available: {e}")
    # Fallback imports if enhanced modules not available
    TerminalEmulator = None
    SSHTunnelManager = None
    SFTPBrowser = None
    SessionManager = None
    CommandPalette = None
    KeyboardShortcutManager = None
    SSHAgentManager = None
    ConnectionMultiplexer = None
    PluginManager = None

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QListWidget, QTabWidget, QTextEdit,
                             QFileDialog, QInputDialog, QMessageBox, QSplitter, QMenuBar,
                             QMenu, QAction, QStatusBar, QToolBar, QMainWindow, QDialog,
                             QDialogButtonBox, QFormLayout, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QMutex, QTimer
from PyQt5.QtGui import QTextCursor, QKeySequence, QIcon, QFont

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jetssh_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Path to the connections JSON file
CONNECTIONS_FILE = 'connections.json'


class EnhancedSSHClientApp(QMainWindow):
    """Enhanced SSH Client Application with all top-tier features"""

    output_received = pyqtSignal(str, str)  # Signal to pass (host, output)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JETSSH - Enhanced SSH Client")
        self.resize(1400, 900)

        # Core data structures
        self.connections = []
        self.ssh_clients = {}
        self.channels = {}
        self.output_boxes = {}
        self.output_threads = {}
        self.mutex = QMutex()
        self.shutdown_flag = threading.Event()

        # Command history
        self.command_history = []
        self.history_index = -1

        # Enhanced features
        self.tunnel_manager = None
        self.sftp_browser = None
        self.session_manager = None
        self.command_palette = None
        self.shortcut_manager = None
        self.ssh_agent_manager = None
        self.connection_multiplexer = None
        self.plugin_manager = None

        # Initialize UI
        self.init_ui()
        self.init_enhanced_features()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()

        # Load data
        self.load_connections()

        # Connect signals
        self.output_received.connect(self.update_output)

        # Apply styling
        self.apply_enhanced_styling()

        logger.info("Enhanced JETSSH application initialized")

    def init_ui(self):
        """Initialize the main UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)

        # Sidebar for connections and tools
        sidebar_widget = self.create_sidebar()
        main_splitter.addWidget(sidebar_widget)

        # Main tab area
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        # Add default tabs
        self.add_default_tabs()

        main_splitter.addWidget(self.tab_widget)

        # Set splitter proportions
        main_splitter.setSizes([300, 1100])

        main_layout.addWidget(main_splitter)

    def create_sidebar(self):
        """Create the enhanced sidebar"""
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)

        # Connection management section
        connections_label = QLabel("SSH Connections")
        connections_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        sidebar_layout.addWidget(connections_label)

        # Connection list
        self.connection_list = QListWidget()
        sidebar_layout.addWidget(self.connection_list)

        # Connection buttons
        conn_buttons_layout = QVBoxLayout()

        launch_button = QPushButton("🚀 Launch Session")
        launch_button.setObjectName("launchButton")
        launch_button.clicked.connect(self.launch_ssh_session)
        conn_buttons_layout.addWidget(launch_button)

        add_button = QPushButton("➕ Add Connection")
        add_button.clicked.connect(self.add_connection)
        conn_buttons_layout.addWidget(add_button)

        remove_button = QPushButton("➖ Remove Connection")
        remove_button.clicked.connect(self.remove_connection)
        conn_buttons_layout.addWidget(remove_button)

        sidebar_layout.addLayout(conn_buttons_layout)

        # Separator
        sidebar_layout.addSpacing(20)

        # Quick tools section
        tools_label = QLabel("Quick Tools")
        tools_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        sidebar_layout.addWidget(tools_label)

        tools_layout = QVBoxLayout()

        sftp_button = QPushButton("📁 SFTP Browser")
        sftp_button.clicked.connect(self.open_sftp_browser)
        tools_layout.addWidget(sftp_button)

        tunnel_button = QPushButton("🚇 Tunnel Manager")
        tunnel_button.clicked.connect(self.open_tunnel_manager)
        tools_layout.addWidget(tunnel_button)

        session_button = QPushButton("💾 Session Manager")
        session_button.clicked.connect(self.open_session_manager)
        tools_layout.addWidget(session_button)

        agent_button = QPushButton("🔑 SSH Agent")
        agent_button.clicked.connect(self.open_ssh_agent_manager)
        tools_layout.addWidget(agent_button)

        multiplex_button = QPushButton("🔗 Connection Pool")
        multiplex_button.clicked.connect(self.open_connection_multiplexer)
        tools_layout.addWidget(multiplex_button)

        plugins_button = QPushButton("🧩 Plugins")
        plugins_button.clicked.connect(self.open_plugin_manager)
        tools_layout.addWidget(plugins_button)

        sidebar_layout.addLayout(tools_layout)

        sidebar_layout.addStretch()

        return sidebar_widget

    def add_default_tabs(self):
        """Add default tabs to the application"""
        # SSH Key Generator tab
        if JETSSHKEYGEN:
            self.keygen_tab = JETSSHKEYGEN.SSHKeyGeneratorTab()
            self.tab_widget.addTab(self.keygen_tab, "🔑 SSH Key Generator")

    def init_enhanced_features(self):
        """Initialize enhanced features if available"""
        try:
            # Initialize command palette
            if CommandPalette:
                self.command_palette = CommandPalette(self)
                logger.info("Command palette initialized")

            # Initialize keyboard shortcuts
            if KeyboardShortcutManager:
                self.shortcut_manager = KeyboardShortcutManager(self)
                logger.info("Keyboard shortcuts initialized")

            # Initialize tunnel manager
            if SSHTunnelManager:
                self.tunnel_manager = SSHTunnelManager(self)
                logger.info("Tunnel manager initialized")

            # Initialize session manager
            if SessionManager:
                self.session_manager = SessionManager(self)
                logger.info("Session manager initialized")

            # Initialize SSH agent manager
            if SSHAgentManager:
                self.ssh_agent_manager = SSHAgentManager(self)
                logger.info("SSH agent manager initialized")

            # Initialize connection multiplexer
            if ConnectionMultiplexer:
                self.connection_multiplexer = ConnectionMultiplexer(self)
                logger.info("Connection multiplexer initialized")

            # Initialize plugin manager
            if PluginManager:
                self.plugin_manager = PluginManager(self)
                logger.info("Plugin manager initialized")

        except Exception as e:
            logger.error(f"Error initializing enhanced features: {e}")

    def setup_menu_bar(self):
        """Setup the enhanced menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        new_connection_action = QAction('&New Connection...', self)
        new_connection_action.setShortcut(QKeySequence.New)
        new_connection_action.triggered.connect(self.add_connection)
        file_menu.addAction(new_connection_action)

        file_menu.addSeparator()

        import_action = QAction('&Import Connections...', self)
        import_action.triggered.connect(self.import_connections)
        file_menu.addAction(import_action)

        export_action = QAction('&Export Connections...', self)
        export_action.triggered.connect(self.export_connections)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction('&Quit', self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu('&Edit')

        preferences_action = QAction('&Preferences...', self)
        preferences_action.setShortcut('Ctrl+,')
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)

        # Session menu
        session_menu = menubar.addMenu('&Session')

        save_session_action = QAction('&Save Session...', self)
        save_session_action.setShortcut('Ctrl+S')
        save_session_action.triggered.connect(self.save_current_session)
        session_menu.addAction(save_session_action)

        restore_session_action = QAction('&Restore Session...', self)
        restore_session_action.setShortcut('Ctrl+R')
        restore_session_action.triggered.connect(self.restore_session)
        session_menu.addAction(restore_session_action)

        # Tools menu
        tools_menu = menubar.addMenu('&Tools')

        sftp_action = QAction('&SFTP Browser', self)
        sftp_action.setShortcut('Ctrl+E')
        sftp_action.triggered.connect(self.open_sftp_browser)
        tools_menu.addAction(sftp_action)

        tunnel_action = QAction('&Tunnel Manager', self)
        tunnel_action.setShortcut('Ctrl+T')
        tunnel_action.triggered.connect(self.open_tunnel_manager)
        tools_menu.addAction(tunnel_action)

        agent_action = QAction('SSH &Agent Manager', self)
        agent_action.triggered.connect(self.open_ssh_agent_manager)
        tools_menu.addAction(agent_action)

        tools_menu.addSeparator()

        command_palette_action = QAction('&Command Palette', self)
        command_palette_action.setShortcut('Ctrl+Shift+P')
        command_palette_action.triggered.connect(self.show_command_palette)
        tools_menu.addAction(command_palette_action)

        # Plugins menu
        plugins_menu = menubar.addMenu('&Plugins')

        plugin_manager_action = QAction('&Plugin Manager', self)
        plugin_manager_action.triggered.connect(self.open_plugin_manager)
        plugins_menu.addAction(plugin_manager_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About JETSSH', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """Setup the main toolbar"""
        toolbar = QToolBar('Main Toolbar')
        self.addToolBar(toolbar)

        # Quick connection
        new_conn_action = QAction('🔗', self)
        new_conn_action.setToolTip('New Connection')
        new_conn_action.triggered.connect(self.add_connection)
        toolbar.addAction(new_conn_action)

        # SFTP Browser
        sftp_action = QAction('📁', self)
        sftp_action.setToolTip('SFTP Browser')
        sftp_action.triggered.connect(self.open_sftp_browser)
        toolbar.addAction(sftp_action)

        # Tunnel Manager
        tunnel_action = QAction('🚇', self)
        tunnel_action.setToolTip('Tunnel Manager')
        tunnel_action.triggered.connect(self.open_tunnel_manager)
        toolbar.addAction(tunnel_action)

        toolbar.addSeparator()

        # Session operations
        save_action = QAction('💾', self)
        save_action.setToolTip('Save Session')
        save_action.triggered.connect(self.save_current_session)
        toolbar.addAction(save_action)

        # Command Palette
        palette_action = QAction('🎯', self)
        palette_action.setToolTip('Command Palette (Ctrl+Shift+P)')
        palette_action.triggered.connect(self.show_command_palette)
        toolbar.addAction(palette_action)

    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Connection count
        self.connection_status = QLabel("Connections: 0")
        self.status_bar.addWidget(self.connection_status)

        # SSH Agent status
        self.agent_status = QLabel("SSH Agent: Disconnected")
        self.status_bar.addPermanentWidget(self.agent_status)

        # Update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(5000)  # Update every 5 seconds

    def apply_enhanced_styling(self):
        """Apply enhanced styling to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #dcdcdc;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #dcdcdc;
                font-family: 'Segoe UI', Consolas, Monaco, monospace;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                selection-background-color: #3a3a3a;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QLineEdit {
                background-color: #2e2e2e;
                color: #00ffff;
                border: 1px solid #3a3a3a;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #4e4e4e;
            }
            QPushButton#launchButton {
                background-color: #ff8c00;
                color: #ffffff;
                border: 2px solid #ff8c00;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#launchButton:hover {
                background-color: #ffa500;
                border-color: #ffa500;
            }
            QListWidget {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                alternate-background-color: #252525;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2e2e2e;
                padding: 12px 20px;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3a3a3a;
                color: #ffffff;
                border-bottom: 2px solid #0078d4;
            }
            QTabBar::tab:hover {
                background-color: #353535;
            }
            QMenuBar {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border-bottom: 1px solid #3a3a3a;
            }
            QMenuBar::item:selected {
                background-color: #3a3a3a;
            }
            QMenu {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QToolBar {
                background-color: #2e2e2e;
                border: none;
                spacing: 4px;
                padding: 4px;
            }
            QStatusBar {
                background-color: #2e2e2e;
                color: #888;
                border-top: 1px solid #3a3a3a;
            }
            QSplitter::handle {
                background-color: #3a3a3a;
                width: 2px;
                height: 2px;
            }
            QScrollBar:vertical {
                border: 1px solid #3a3a3a;
                background-color: #1e1e1e;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 7px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }
        """)

    def add_connection(self):
        """Add a new SSH connection"""
        dialog = ConnectionDialog(self)
        if dialog.exec_() == dialog.Accepted:
            connection_data = dialog.get_connection_data()
            self.connections.append(connection_data)

            # Update display
            auth_method = "Key" if connection_data.get("private_key") else "Password"
            display_text = f"{connection_data['host']} ({connection_data['user']}) [{auth_method}]"
            self.connection_list.addItem(display_text)

            # Save connections
            self.save_connections()

            logger.info(f"Added connection: {connection_data['host']}")

    def remove_connection(self):
        """Remove selected connection"""
        selected_item = self.connection_list.currentRow()
        if selected_item >= 0:
            connection = self.connections[selected_item]
            reply = QMessageBox.question(
                self, "Remove Connection",
                f"Remove connection to {connection['host']}?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                del self.connections[selected_item]
                self.connection_list.takeItem(selected_item)
                self.save_connections()
                logger.info(f"Removed connection: {connection['host']}")

    def launch_ssh_session(self):
        """Launch SSH session with enhanced terminal"""
        selected_item = self.connection_list.currentRow()
        if selected_item < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a connection.")
            return

        connection = self.connections[selected_item]
        host = connection["host"]
        username = connection["user"]
        key_file = connection.get("private_key")

        # Get authentication
        if not key_file:
            password, ok = QInputDialog.getText(
                self, "Password",
                f"Enter SSH password for {username}@{host}:",
                echo=QLineEdit.Password
            )
            if not ok or not password:
                return
        else:
            password = None

        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.WarningPolicy())

            # Try SSH agent first if available
            agent_keys = []
            if self.ssh_agent_manager and self.ssh_agent_manager.agent_client:
                try:
                    agent_keys = self.ssh_agent_manager.agent_client.get_keys()
                except:
                    pass

            # Connect with agent keys or provided authentication
            connected = False

            # Try agent keys first
            for agent_key in agent_keys:
                try:
                    ssh.connect(host, username=username, pkey=agent_key)
                    connected = True
                    logger.info(f"Connected to {host} using SSH agent key")
                    break
                except:
                    continue

            # Try provided key file
            if not connected and key_file:
                try:
                    # Try different key types
                    for key_class in [paramiko.RSAKey, paramiko.DSSKey, paramiko.ECDSAKey, paramiko.Ed25519Key]:
                        try:
                            private_key = key_class.from_private_key_file(key_file)
                            ssh.connect(host, username=username, pkey=private_key)
                            connected = True
                            logger.info(f"Connected to {host} using private key")
                            break
                        except:
                            continue
                    if connected:
                        pass  # Already connected
                except Exception as e:
                    logger.error(f"Key authentication failed: {e}")

            # Try password authentication
            if not connected and password:
                ssh.connect(host, username=username, password=password)
                connected = True
                logger.info(f"Connected to {host} using password")

            if not connected:
                raise Exception("All authentication methods failed")

            # Store SSH client
            self.ssh_clients[host] = ssh

            # Open shell channel
            channel = ssh.invoke_shell()
            self.channels[host] = channel

            # Create session tab with enhanced terminal
            self.create_ssh_session_tab(host, username, channel)

            logger.info(f"SSH session launched for {username}@{host}")

        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
            logger.error(f"SSH connection failed: {e}")

    def create_ssh_session_tab(self, host, username, channel):
        """Create an enhanced SSH session tab"""
        session_tab = QWidget()
        session_layout = QVBoxLayout(session_tab)

        # Create enhanced terminal or fallback
        if TerminalEmulator:
            terminal = TerminalEmulator(self)
            session_layout.addWidget(terminal)

            # Store terminal for output
            self.output_boxes[host] = terminal
        else:
            # Fallback to basic terminal
            splitter = QSplitter(Qt.Vertical)

            output_box = QTextEdit()
            output_box.setReadOnly(True)
            output_box.setFont(QFont("Consolas", 10))
            splitter.addWidget(output_box)

            self.output_boxes[host] = output_box
            session_layout.addWidget(splitter)

        # Command input
        self.command_entry = CommandLineEdit(self)
        self.command_entry.setPlaceholderText("Enter command...")
        self.command_entry.returnPressed.connect(lambda: self.send_command(host))
        session_layout.addWidget(self.command_entry)

        # Add predefined commands panel
        if PredefinedCommands:
            predefined_commands_widget = PredefinedCommands(self)
            session_layout.addWidget(predefined_commands_widget)

        # Add tab
        tab_title = f"{host} ({username})"
        self.tab_widget.addTab(session_tab, tab_title)
        self.tab_widget.setCurrentWidget(session_tab)

        # Start output reading thread
        output_thread = threading.Thread(target=self.read_output, args=(host,), daemon=True)
        output_thread.start()
        self.output_threads[host] = output_thread

    def send_command(self, host):
        """Send command to SSH session"""
        command = self.command_entry.text().strip()
        if command and host in self.channels:
            channel = self.channels[host]
            channel.send(command + "\n")

            # Add to command history
            if command:
                self.command_history.append(command)
            self.history_index = -1

        self.command_entry.clear()

    def read_output(self, host):
        """Read output from SSH channel"""
        channel = self.channels[host]
        while not self.shutdown_flag.is_set() and channel.active:
            try:
                if channel.recv_ready():
                    output = channel.recv(1024).decode('utf-8', errors='ignore')
                    if output:
                        self.output_received.emit(host, output)
            except Exception as e:
                logger.error(f"Output reading error for {host}: {e}")
                break

    def update_output(self, host, output):
        """Update terminal output"""
        if host in self.output_boxes:
            self.mutex.lock()
            output_widget = self.output_boxes[host]

            if hasattr(output_widget, 'append_output'):
                # Enhanced terminal
                output_widget.append_output(output)
            else:
                # Basic terminal
                output_widget.moveCursor(QTextCursor.End)
                output_widget.insertPlainText(output)
                output_widget.moveCursor(QTextCursor.End)

            self.mutex.unlock()

    def close_tab(self, index):
        """Close a tab and cleanup resources"""
        if index <= 0:  # Don't close the first tab (key generator)
            return

        tab_text = self.tab_widget.tabText(index)

        # Extract host from tab text
        if '(' in tab_text:
            host = tab_text.split()[0]

            # Close SSH connection
            if host in self.ssh_clients:
                try:
                    self.ssh_clients[host].close()
                except:
                    pass
                del self.ssh_clients[host]

            # Clean up channels and output boxes
            if host in self.channels:
                del self.channels[host]
            if host in self.output_boxes:
                del self.output_boxes[host]
            if host in self.output_threads:
                del self.output_threads[host]

        # Remove the tab
        self.tab_widget.removeTab(index)

    # Enhanced feature methods
    def open_sftp_browser(self):
        """Open SFTP browser in new tab"""
        if not SFTPBrowser:
            QMessageBox.warning(self, "Feature Unavailable", "SFTP Browser feature not available")
            return

        # Check if already open
        for i in range(self.tab_widget.count()):
            if "SFTP Browser" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        try:
            sftp_browser = SFTPBrowser(self)
            self.tab_widget.addTab(sftp_browser, "📁 SFTP Browser")
            self.tab_widget.setCurrentWidget(sftp_browser)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open SFTP browser: {str(e)}")

    def open_tunnel_manager(self):
        """Open tunnel manager in new tab"""
        if not self.tunnel_manager:
            QMessageBox.warning(self, "Feature Unavailable", "Tunnel Manager feature not available")
            return

        # Check if already open
        for i in range(self.tab_widget.count()):
            if "Tunnel Manager" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        self.tab_widget.addTab(self.tunnel_manager, "🚇 Tunnel Manager")
        self.tab_widget.setCurrentWidget(self.tunnel_manager)

    def open_session_manager(self):
        """Open session manager in new tab"""
        if not self.session_manager:
            QMessageBox.warning(self, "Feature Unavailable", "Session Manager feature not available")
            return

        # Check if already open
        for i in range(self.tab_widget.count()):
            if "Session Manager" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        self.tab_widget.addTab(self.session_manager, "💾 Session Manager")
        self.tab_widget.setCurrentWidget(self.session_manager)

    def open_ssh_agent_manager(self):
        """Open SSH agent manager in new tab"""
        if not self.ssh_agent_manager:
            QMessageBox.warning(self, "Feature Unavailable", "SSH Agent Manager feature not available")
            return

        # Check if already open
        for i in range(self.tab_widget.count()):
            if "SSH Agent" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        self.tab_widget.addTab(self.ssh_agent_manager, "🔑 SSH Agent Manager")
        self.tab_widget.setCurrentWidget(self.ssh_agent_manager)

    def open_connection_multiplexer(self):
        """Open connection multiplexer in new tab"""
        if not self.connection_multiplexer:
            QMessageBox.warning(self, "Feature Unavailable", "Connection Multiplexer feature not available")
            return

        # Check if already open
        for i in range(self.tab_widget.count()):
            if "Connection Pool" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        self.tab_widget.addTab(self.connection_multiplexer, "🔗 Connection Pool")
        self.tab_widget.setCurrentWidget(self.connection_multiplexer)

    def open_plugin_manager(self):
        """Open plugin manager in new tab"""
        if not self.plugin_manager:
            QMessageBox.warning(self, "Feature Unavailable", "Plugin Manager feature not available")
            return

        # Check if already open
        for i in range(self.tab_widget.count()):
            if "Plugin Manager" in self.tab_widget.tabText(i):
                self.tab_widget.setCurrentIndex(i)
                return

        self.tab_widget.addTab(self.plugin_manager, "🧩 Plugin Manager")
        self.tab_widget.setCurrentWidget(self.plugin_manager)

    def show_command_palette(self):
        """Show the command palette"""
        if self.command_palette:
            self.command_palette.show_palette()
        else:
            QMessageBox.warning(self, "Feature Unavailable", "Command Palette feature not available")

    def save_current_session(self):
        """Save current session"""
        if self.session_manager:
            self.session_manager.save_current_session()
        else:
            QMessageBox.warning(self, "Feature Unavailable", "Session Manager feature not available")

    def restore_session(self):
        """Restore a session"""
        if self.session_manager:
            self.open_session_manager()
        else:
            QMessageBox.warning(self, "Feature Unavailable", "Session Manager feature not available")

    def update_status_bar(self):
        """Update status bar information"""
        # Update connection count
        active_connections = len(self.ssh_clients)
        self.connection_status.setText(f"Connections: {active_connections}")

        # Update SSH agent status
        if self.ssh_agent_manager and self.ssh_agent_manager.agent_client:
            self.agent_status.setText("SSH Agent: Connected")
        else:
            self.agent_status.setText("SSH Agent: Disconnected")

    # File operations
    def save_connections(self):
        """Save connections to file"""
        try:
            with open(CONNECTIONS_FILE, 'w') as file:
                json.dump(self.connections, file, indent=2)
        except Exception as e:
            logger.error(f"Failed to save connections: {e}")

    def load_connections(self):
        """Load connections from file"""
        try:
            if os.path.exists(CONNECTIONS_FILE):
                with open(CONNECTIONS_FILE, 'r') as file:
                    self.connections = json.load(file)

                # Populate connection list
                for connection in self.connections:
                    auth_method = "Key" if connection.get("private_key") else "Password"
                    display_text = f"{connection['host']} ({connection['user']}) [{auth_method}]"
                    self.connection_list.addItem(display_text)
        except Exception as e:
            logger.error(f"Failed to load connections: {e}")

    # Menu action handlers
    def import_connections(self):
        """Import connections from file"""
        QMessageBox.information(self, "Import", "Import connections feature")

    def export_connections(self):
        """Export connections to file"""
        QMessageBox.information(self, "Export", "Export connections feature")

    def show_preferences(self):
        """Show application preferences"""
        QMessageBox.information(self, "Preferences", "Preferences feature")

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About JETSSH Enhanced",
                         "JETSSH Enhanced v2.0\n\n"
                         "Professional SSH Client with:\n"
                         "• Advanced terminal emulation\n"
                         "• SSH tunneling and port forwarding\n"
                         "• Integrated SFTP file browser\n"
                         "• Session management and persistence\n"
                         "• SSH agent integration\n"
                         "• Connection multiplexing\n"
                         "• Plugin architecture\n"
                         "• Command palette\n\n"
                         "Built with PyQt5 and Paramiko")

    def closeEvent(self, event):
        """Handle application close event"""
        # Set shutdown flag
        self.shutdown_flag.set()

        # Close all SSH connections
        for ssh_client in self.ssh_clients.values():
            try:
                ssh_client.close()
            except:
                pass

        # Save any pending data
        self.save_connections()

        event.accept()


class CommandLineEdit(QLineEdit):
    """Enhanced command line input with history navigation"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        """Handle key press events"""
        # Ctrl+C - Send interrupt signal
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            if self.parent.channels:
                # Send interrupt to current session
                current_tab = self.parent.tab_widget.currentIndex()
                if current_tab > 0:  # Not the key generator tab
                    tab_text = self.parent.tab_widget.tabText(current_tab)
                    if '(' in tab_text:
                        host = tab_text.split()[0]
                        if host in self.parent.channels:
                            self.parent.channels[host].send("\x03")
            return

        # Ctrl+D - Send EOF signal
        if event.key() == Qt.Key_D and event.modifiers() == Qt.ControlModifier:
            if self.parent.channels:
                current_tab = self.parent.tab_widget.currentIndex()
                if current_tab > 0:
                    tab_text = self.parent.tab_widget.tabText(current_tab)
                    if '(' in tab_text:
                        host = tab_text.split()[0]
                        if host in self.parent.channels:
                            self.parent.channels[host].send("\x04")
            return

        # Up/Down arrow keys for command history
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

        super().keyPressEvent(event)


class ConnectionDialog(QDialog):
    """Enhanced connection dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add SSH Connection")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        """Setup the connection dialog UI"""
        layout = QVBoxLayout(self)

        # Connection details
        from PyQt5.QtWidgets import QFormLayout
        form_layout = QFormLayout()

        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("hostname or IP address")
        form_layout.addRow("Host:", self.host_edit)

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("username")
        form_layout.addRow("Username:", self.user_edit)

        self.port_edit = QLineEdit("22")
        form_layout.addRow("Port:", self.port_edit)

        # Authentication method
        from PyQt5.QtWidgets import QComboBox
        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["Password", "Private Key", "SSH Agent"])
        self.auth_combo.currentTextChanged.connect(self.on_auth_method_changed)
        form_layout.addRow("Authentication:", self.auth_combo)

        # Private key selection
        key_layout = QHBoxLayout()
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Path to private key file")
        self.key_browse_btn = QPushButton("Browse...")
        self.key_browse_btn.clicked.connect(self.browse_key_file)
        key_layout.addWidget(self.key_edit)
        key_layout.addWidget(self.key_browse_btn)
        form_layout.addRow("Private Key:", key_layout)

        layout.addLayout(form_layout)

        # Dialog buttons
        from PyQt5.QtWidgets import QDialogButtonBox
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Initial state
        self.on_auth_method_changed("Password")

    def on_auth_method_changed(self, method):
        """Handle authentication method change"""
        show_key_fields = (method == "Private Key")
        self.key_edit.setVisible(show_key_fields)
        self.key_browse_btn.setVisible(show_key_fields)

    def browse_key_file(self):
        """Browse for private key file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Private Key",
            str(Path.home() / ".ssh"),
            "SSH Keys (id_rsa id_dsa id_ecdsa id_ed25519 *.pem *.key);;All Files (*)"
        )
        if file_path:
            self.key_edit.setText(file_path)

    def get_connection_data(self):
        """Get connection data from dialog"""
        return {
            'host': self.host_edit.text(),
            'user': self.user_edit.text(),
            'port': int(self.port_edit.text()) if self.port_edit.text().isdigit() else 22,
            'auth_method': self.auth_combo.currentText(),
            'private_key': self.key_edit.text() if self.auth_combo.currentText() == "Private Key" else None
        }


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("JETSSH Enhanced")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("JETSSH")

    # Create and show main window
    ssh_app = EnhancedSSHClientApp()
    ssh_app.show()

    logger.info("JETSSH Enhanced application started")

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()