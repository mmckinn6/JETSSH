"""
Command Palette System for JETSSH
Provides quick access to all application functions via keyboard shortcuts
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
                             QListWidgetItem, QLabel, QWidget, QShortcut, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence, QFont, QIcon, QPixmap, QPainter

logger = logging.getLogger(__name__)


class CommandPalette(QDialog):
    """Command palette for quick access to all functions"""

    command_executed = pyqtSignal(str, dict)  # command_id, parameters

    def __init__(self, ssh_client_app):
        super().__init__(ssh_client_app)
        self.ssh_client_app = ssh_client_app
        self.commands = {}
        self.filtered_commands = []
        self.setup_ui()
        self.setup_commands()
        self.setup_shortcuts()

    def setup_ui(self):
        """Setup the command palette UI"""
        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.resize(600, 400)

        # Center on parent
        if self.parent():
            parent_geo = self.parent().geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.move(x, y)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(1, 1, 1, 1)

        # Title bar
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #3a3a3a;
                border: none;
                padding: 8px;
            }
            QLabel {
                color: #dcdcdc;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(10, 5, 10, 5)

        title_label = QLabel("🎯 Command Palette")
        title_layout.addWidget(title_label)

        hint_label = QLabel("Ctrl+Shift+P to open • Esc to close")
        hint_label.setStyleSheet("color: #888; font-size: 10px; font-weight: normal;")
        title_layout.addStretch()
        title_layout.addWidget(hint_label)

        layout.addWidget(title_widget)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command...")
        self.search_input.textChanged.connect(self.filter_commands)
        self.search_input.returnPressed.connect(self.execute_selected_command)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border: none;
                padding: 12px;
                font-size: 14px;
                border-bottom: 1px solid #3a3a3a;
            }
        """)
        layout.addWidget(self.search_input)

        # Commands list
        self.commands_list = QListWidget()
        self.commands_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
        """)
        self.commands_list.itemDoubleClicked.connect(self.execute_selected_command)
        layout.addWidget(self.commands_list)

        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #3a3a3a;
                color: #888;
                padding: 5px 10px;
                font-size: 10px;
                border-top: 1px solid #2a2a2a;
            }
        """)
        layout.addWidget(self.status_label)

        # Apply main styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
            }
        """)

    def setup_commands(self):
        """Setup all available commands"""
        self.commands = {
            # Connection Management
            "connect_new": {
                "title": "New SSH Connection",
                "description": "Add and connect to a new SSH server",
                "category": "Connection",
                "keywords": ["ssh", "connect", "new", "add"],
                "shortcut": "Ctrl+N",
                "icon": "🔗",
                "action": "add_connection"
            },
            "connect_existing": {
                "title": "Connect to Saved Server",
                "description": "Connect to a previously saved SSH server",
                "category": "Connection",
                "keywords": ["ssh", "connect", "saved", "launch"],
                "shortcut": "Ctrl+L",
                "icon": "⚡",
                "action": "launch_ssh_session"
            },
            "disconnect_current": {
                "title": "Disconnect Current Session",
                "description": "Disconnect from the current SSH session",
                "category": "Connection",
                "keywords": ["disconnect", "close", "exit"],
                "shortcut": "Ctrl+D",
                "icon": "🔌",
                "action": "close_current_tab"
            },
            "disconnect_all": {
                "title": "Disconnect All Sessions",
                "description": "Disconnect from all active SSH sessions",
                "category": "Connection",
                "keywords": ["disconnect", "close", "all", "exit"],
                "shortcut": "Ctrl+Shift+D",
                "icon": "🚫",
                "action": "close_all_tabs"
            },

            # File Operations
            "upload_file": {
                "title": "Upload File",
                "description": "Upload a file to the remote server",
                "category": "File Transfer",
                "keywords": ["upload", "file", "transfer", "sftp"],
                "shortcut": "Ctrl+U",
                "icon": "⬆️",
                "action": "upload_file"
            },
            "download_file": {
                "title": "Download File",
                "description": "Download a file from the remote server",
                "category": "File Transfer",
                "keywords": ["download", "file", "transfer", "sftp"],
                "shortcut": "Ctrl+Shift+U",
                "icon": "⬇️",
                "action": "download_file"
            },
            "open_sftp_browser": {
                "title": "Open SFTP File Browser",
                "description": "Open the integrated SFTP file browser",
                "category": "File Transfer",
                "keywords": ["sftp", "browser", "files", "explorer"],
                "shortcut": "Ctrl+E",
                "icon": "📁",
                "action": "open_sftp_browser"
            },

            # Session Management
            "save_session": {
                "title": "Save Current Session",
                "description": "Save the current session state",
                "category": "Session",
                "keywords": ["save", "session", "state"],
                "shortcut": "Ctrl+S",
                "icon": "💾",
                "action": "save_session"
            },
            "restore_session": {
                "title": "Restore Session",
                "description": "Restore a previously saved session",
                "category": "Session",
                "keywords": ["restore", "session", "load"],
                "shortcut": "Ctrl+R",
                "icon": "🔄",
                "action": "restore_session"
            },
            "session_manager": {
                "title": "Open Session Manager",
                "description": "Open the session management interface",
                "category": "Session",
                "keywords": ["session", "manager", "history"],
                "shortcut": "Ctrl+M",
                "icon": "📋",
                "action": "open_session_manager"
            },

            # SSH Tunnels
            "create_tunnel": {
                "title": "Create SSH Tunnel",
                "description": "Create a new SSH tunnel (port forwarding)",
                "category": "Tunnels",
                "keywords": ["tunnel", "port", "forward", "proxy"],
                "shortcut": "Ctrl+T",
                "icon": "🚇",
                "action": "create_tunnel"
            },
            "tunnel_manager": {
                "title": "Open Tunnel Manager",
                "description": "Manage active SSH tunnels",
                "category": "Tunnels",
                "keywords": ["tunnel", "manager", "port", "forwarding"],
                "shortcut": "Ctrl+Shift+T",
                "icon": "🛠️",
                "action": "open_tunnel_manager"
            },

            # Key Management
            "generate_key": {
                "title": "Generate SSH Key",
                "description": "Generate a new SSH key pair",
                "category": "Security",
                "keywords": ["ssh", "key", "generate", "rsa", "ed25519"],
                "shortcut": "Ctrl+K",
                "icon": "🔑",
                "action": "generate_ssh_key"
            },

            # Commands
            "add_command": {
                "title": "Add Predefined Command",
                "description": "Add a new predefined command",
                "category": "Commands",
                "keywords": ["command", "predefined", "script", "add"],
                "shortcut": "Ctrl+Shift+A",
                "icon": "➕",
                "action": "add_predefined_command"
            },
            "execute_command": {
                "title": "Execute Predefined Command",
                "description": "Execute a predefined command",
                "category": "Commands",
                "keywords": ["command", "execute", "run", "script"],
                "shortcut": "Ctrl+Shift+E",
                "icon": "▶️",
                "action": "execute_predefined_command"
            },

            # Terminal Operations
            "clear_terminal": {
                "title": "Clear Terminal",
                "description": "Clear the current terminal output",
                "category": "Terminal",
                "keywords": ["clear", "terminal", "screen"],
                "shortcut": "Ctrl+Shift+C",
                "icon": "🧹",
                "action": "clear_terminal"
            },
            "copy_output": {
                "title": "Copy Terminal Output",
                "description": "Copy all terminal output to clipboard",
                "category": "Terminal",
                "keywords": ["copy", "output", "clipboard"],
                "shortcut": "Ctrl+Shift+O",
                "icon": "📋",
                "action": "copy_terminal_output"
            },
            "find_in_terminal": {
                "title": "Find in Terminal",
                "description": "Search for text in terminal output",
                "category": "Terminal",
                "keywords": ["find", "search", "terminal"],
                "shortcut": "Ctrl+F",
                "icon": "🔍",
                "action": "find_in_terminal"
            },

            # Application
            "preferences": {
                "title": "Preferences",
                "description": "Open application preferences",
                "category": "Application",
                "keywords": ["preferences", "settings", "config"],
                "shortcut": "Ctrl+,",
                "icon": "⚙️",
                "action": "open_preferences"
            },
            "about": {
                "title": "About JETSSH",
                "description": "Show application information",
                "category": "Application",
                "keywords": ["about", "info", "version"],
                "shortcut": "F1",
                "icon": "ℹ️",
                "action": "show_about"
            },
            "quit": {
                "title": "Quit Application",
                "description": "Exit JETSSH",
                "category": "Application",
                "keywords": ["quit", "exit", "close"],
                "shortcut": "Ctrl+Q",
                "icon": "❌",
                "action": "quit_application"
            },

            # Advanced Features
            "monitor_logs": {
                "title": "Monitor System Logs",
                "description": "Monitor system logs in real-time",
                "category": "Monitoring",
                "keywords": ["logs", "monitor", "tail", "system"],
                "shortcut": "Ctrl+Shift+L",
                "icon": "📊",
                "action": "monitor_logs"
            },
            "process_monitor": {
                "title": "Process Monitor",
                "description": "Monitor running processes",
                "category": "Monitoring",
                "keywords": ["process", "monitor", "htop", "ps"],
                "shortcut": "Ctrl+Shift+P",
                "icon": "🖥️",
                "action": "process_monitor"
            },

            # Workspace
            "save_workspace": {
                "title": "Save Workspace",
                "description": "Save current workspace layout",
                "category": "Workspace",
                "keywords": ["workspace", "save", "layout"],
                "shortcut": "Ctrl+Shift+S",
                "icon": "💼",
                "action": "save_workspace"
            },
            "load_workspace": {
                "title": "Load Workspace",
                "description": "Load a saved workspace",
                "category": "Workspace",
                "keywords": ["workspace", "load", "restore"],
                "shortcut": "Ctrl+Shift+L",
                "icon": "📂",
                "action": "load_workspace"
            }
        }

        self.refresh_commands_list()

    def setup_shortcuts(self):
        """Setup global keyboard shortcuts"""
        # Command palette shortcut
        self.palette_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self.ssh_client_app)
        self.palette_shortcut.activated.connect(self.show_palette)

        # Setup individual command shortcuts
        for command_id, command_data in self.commands.items():
            if "shortcut" in command_data:
                try:
                    shortcut = QShortcut(QKeySequence(command_data["shortcut"]), self.ssh_client_app)
                    shortcut.activated.connect(lambda cmd_id=command_id: self.execute_command(cmd_id))
                except Exception as e:
                    logger.warning(f"Failed to create shortcut for {command_id}: {e}")

    def show_palette(self):
        """Show the command palette"""
        self.search_input.clear()
        self.refresh_commands_list()
        self.search_input.setFocus()
        self.show()

    def filter_commands(self):
        """Filter commands based on search input"""
        search_text = self.search_input.text().lower()

        if not search_text:
            self.filtered_commands = list(self.commands.keys())
        else:
            self.filtered_commands = []
            for command_id, command_data in self.commands.items():
                # Search in title, description, keywords
                searchable_text = (
                    command_data["title"] + " " +
                    command_data["description"] + " " +
                    " ".join(command_data.get("keywords", []))
                ).lower()

                if search_text in searchable_text:
                    self.filtered_commands.append(command_id)

        self.refresh_commands_list()

    def refresh_commands_list(self):
        """Refresh the commands list display"""
        self.commands_list.clear()

        commands_to_show = self.filtered_commands if hasattr(self, 'filtered_commands') else list(self.commands.keys())

        # Group by category
        categories = {}
        for command_id in commands_to_show:
            command_data = self.commands[command_id]
            category = command_data.get("category", "Other")
            if category not in categories:
                categories[category] = []
            categories[category].append(command_id)

        # Add commands by category
        for category in sorted(categories.keys()):
            # Add category header
            if len(categories) > 1:  # Only show headers if multiple categories
                header_item = QListWidgetItem(f"━━━ {category} ━━━")
                header_item.setFlags(Qt.NoItemFlags)  # Not selectable
                header_item.setData(Qt.UserRole, None)
                header_font = QFont()
                header_font.setBold(True)
                header_item.setFont(header_font)
                header_item.setBackground(Qt.darkGray)
                self.commands_list.addItem(header_item)

            # Add commands in category
            for command_id in sorted(categories[category], key=lambda x: self.commands[x]["title"]):
                command_data = self.commands[command_id]
                item_widget = CommandListItem(command_id, command_data)
                list_item = QListWidgetItem()
                list_item.setData(Qt.UserRole, command_id)
                list_item.setSizeHint(item_widget.sizeHint())
                self.commands_list.addItem(list_item)
                self.commands_list.setItemWidget(list_item, item_widget)

        # Select first item if available
        if self.commands_list.count() > 0:
            first_selectable = 0
            while (first_selectable < self.commands_list.count() and
                   self.commands_list.item(first_selectable).data(Qt.UserRole) is None):
                first_selectable += 1

            if first_selectable < self.commands_list.count():
                self.commands_list.setCurrentRow(first_selectable)

        # Update status
        count = len(commands_to_show)
        total = len(self.commands)
        if count == total:
            self.status_label.setText(f"{count} commands available")
        else:
            self.status_label.setText(f"{count} of {total} commands shown")

    def execute_selected_command(self):
        """Execute the currently selected command"""
        current_item = self.commands_list.currentItem()
        if current_item:
            command_id = current_item.data(Qt.UserRole)
            if command_id:
                self.execute_command(command_id)
                self.hide()

    def execute_command(self, command_id):
        """Execute a command by ID"""
        if command_id not in self.commands:
            logger.warning(f"Unknown command: {command_id}")
            return

        command_data = self.commands[command_id]
        action = command_data.get("action")

        try:
            # Execute the appropriate action
            if action == "add_connection":
                self.ssh_client_app.add_connection()
            elif action == "launch_ssh_session":
                self.ssh_client_app.launch_ssh_session()
            elif action == "close_current_tab":
                current_index = self.ssh_client_app.tab_widget.currentIndex()
                if current_index > 0:  # Don't close the key generator tab
                    self.ssh_client_app.close_tab(current_index)
            elif action == "close_all_tabs":
                # Close all tabs except the first one
                while self.ssh_client_app.tab_widget.count() > 1:
                    self.ssh_client_app.close_tab(1)
            elif action == "upload_file":
                self.ssh_client_app.upload_file()
            elif action == "download_file":
                self.ssh_client_app.download_file()
            elif action == "open_sftp_browser":
                self.open_sftp_browser()
            elif action == "save_session":
                self.save_current_session()
            elif action == "restore_session":
                self.restore_session()
            elif action == "open_session_manager":
                self.open_session_manager()
            elif action == "create_tunnel":
                self.create_tunnel()
            elif action == "open_tunnel_manager":
                self.open_tunnel_manager()
            elif action == "generate_ssh_key":
                # Switch to SSH key generator tab
                for i in range(self.ssh_client_app.tab_widget.count()):
                    if "SSH Key Generator" in self.ssh_client_app.tab_widget.tabText(i):
                        self.ssh_client_app.tab_widget.setCurrentIndex(i)
                        break
            elif action == "clear_terminal":
                self.clear_current_terminal()
            elif action == "copy_terminal_output":
                self.copy_terminal_output()
            elif action == "find_in_terminal":
                self.find_in_terminal()
            elif action == "quit_application":
                QApplication.quit()
            else:
                # For actions not yet implemented, show a message
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, "Command",
                    f"Command '{command_data['title']}' executed!\n\n"
                    f"Feature implementation: {action}"
                )

            self.command_executed.emit(command_id, command_data)

        except Exception as e:
            logger.error(f"Error executing command {command_id}: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self, "Command Error",
                f"Failed to execute command '{command_data['title']}':\n{str(e)}"
            )

    def open_sftp_browser(self):
        """Open SFTP browser in a new tab"""
        # Check if SFTP browser tab already exists
        for i in range(self.ssh_client_app.tab_widget.count()):
            if "SFTP Browser" in self.ssh_client_app.tab_widget.tabText(i):
                self.ssh_client_app.tab_widget.setCurrentIndex(i)
                return

        # Create new SFTP browser tab
        try:
            from sftp_browser import SFTPBrowser
            sftp_browser = SFTPBrowser(self.ssh_client_app)
            self.ssh_client_app.tab_widget.addTab(sftp_browser, "SFTP Browser")
            self.ssh_client_app.tab_widget.setCurrentWidget(sftp_browser)
        except ImportError as e:
            logger.error(f"Failed to import SFTP browser: {e}")

    def open_session_manager(self):
        """Open session manager in a new tab"""
        # Check if session manager tab already exists
        for i in range(self.ssh_client_app.tab_widget.count()):
            if "Session Manager" in self.ssh_client_app.tab_widget.tabText(i):
                self.ssh_client_app.tab_widget.setCurrentIndex(i)
                return

        # Create new session manager tab
        try:
            from session_manager import SessionManager
            session_manager = SessionManager(self.ssh_client_app)
            self.ssh_client_app.tab_widget.addTab(session_manager, "Session Manager")
            self.ssh_client_app.tab_widget.setCurrentWidget(session_manager)
        except ImportError as e:
            logger.error(f"Failed to import session manager: {e}")

    def open_tunnel_manager(self):
        """Open tunnel manager in a new tab"""
        # Check if tunnel manager tab already exists
        for i in range(self.ssh_client_app.tab_widget.count()):
            if "Tunnel Manager" in self.ssh_client_app.tab_widget.tabText(i):
                self.ssh_client_app.tab_widget.setCurrentIndex(i)
                return

        # Create new tunnel manager tab
        try:
            from ssh_tunnel_manager import SSHTunnelManager
            tunnel_manager = SSHTunnelManager(self.ssh_client_app)
            self.ssh_client_app.tab_widget.addTab(tunnel_manager, "Tunnel Manager")
            self.ssh_client_app.tab_widget.setCurrentWidget(tunnel_manager)
        except ImportError as e:
            logger.error(f"Failed to import tunnel manager: {e}")

    def save_current_session(self):
        """Save current session via session manager"""
        try:
            from session_manager import SessionManager
            session_manager = SessionManager(self.ssh_client_app)
            session_manager.save_current_session()
        except ImportError as e:
            logger.error(f"Failed to import session manager: {e}")

    def restore_session(self):
        """Restore session via session manager"""
        self.open_session_manager()

    def create_tunnel(self):
        """Create new tunnel via tunnel manager"""
        self.open_tunnel_manager()

    def clear_current_terminal(self):
        """Clear current terminal output"""
        current_widget = self.ssh_client_app.tab_widget.currentWidget()
        if hasattr(current_widget, 'children'):
            for child in current_widget.children():
                if hasattr(child, 'clear') and hasattr(child, 'toPlainText'):
                    child.clear()
                    break

    def copy_terminal_output(self):
        """Copy terminal output to clipboard"""
        current_widget = self.ssh_client_app.tab_widget.currentWidget()
        if hasattr(current_widget, 'children'):
            for child in current_widget.children():
                if hasattr(child, 'toPlainText'):
                    text = child.toPlainText()
                    clipboard = QApplication.clipboard()
                    clipboard.setText(text)
                    break

    def find_in_terminal(self):
        """Find text in terminal"""
        current_widget = self.ssh_client_app.tab_widget.currentWidget()
        if hasattr(current_widget, 'children'):
            for child in current_widget.children():
                if hasattr(child, 'show_find_dialog'):
                    child.show_find_dialog()
                    break

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key_Down:
            current_row = self.commands_list.currentRow()
            if current_row < self.commands_list.count() - 1:
                next_row = current_row + 1
                # Skip non-selectable items (category headers)
                while (next_row < self.commands_list.count() and
                       self.commands_list.item(next_row).data(Qt.UserRole) is None):
                    next_row += 1
                if next_row < self.commands_list.count():
                    self.commands_list.setCurrentRow(next_row)
        elif event.key() == Qt.Key_Up:
            current_row = self.commands_list.currentRow()
            if current_row > 0:
                prev_row = current_row - 1
                # Skip non-selectable items (category headers)
                while (prev_row >= 0 and
                       self.commands_list.item(prev_row).data(Qt.UserRole) is None):
                    prev_row -= 1
                if prev_row >= 0:
                    self.commands_list.setCurrentRow(prev_row)
        else:
            super().keyPressEvent(event)


class CommandListItem(QWidget):
    """Custom widget for command list items"""

    def __init__(self, command_id, command_data):
        super().__init__()
        self.command_id = command_id
        self.command_data = command_data
        self.setup_ui()

    def setup_ui(self):
        """Setup the command item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Icon
        icon_label = QLabel(self.command_data.get("icon", "🔧"))
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        # Command info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Title
        title_label = QLabel(self.command_data["title"])
        title_label.setStyleSheet("font-weight: bold; color: #dcdcdc;")
        info_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(self.command_data["description"])
        desc_label.setStyleSheet("color: #888; font-size: 11px;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        layout.addLayout(info_layout)

        # Shortcut
        if "shortcut" in self.command_data:
            shortcut_label = QLabel(self.command_data["shortcut"])
            shortcut_label.setStyleSheet("""
                color: #888;
                font-size: 10px;
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                padding: 2px 6px;
            """)
            shortcut_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(shortcut_label)

        layout.addStretch()


class KeyboardShortcutManager:
    """Manages all keyboard shortcuts for the application"""

    def __init__(self, ssh_client_app):
        self.ssh_client_app = ssh_client_app
        self.shortcuts = {}
        self.setup_default_shortcuts()

    def setup_default_shortcuts(self):
        """Setup default keyboard shortcuts"""
        default_shortcuts = {
            "Ctrl+Tab": "next_tab",
            "Ctrl+Shift+Tab": "previous_tab",
            "Ctrl+W": "close_tab",
            "Ctrl+Shift+W": "close_all_tabs",
            "Ctrl+1": "tab_1",
            "Ctrl+2": "tab_2",
            "Ctrl+3": "tab_3",
            "Ctrl+4": "tab_4",
            "Ctrl+5": "tab_5",
            "Ctrl+6": "tab_6",
            "Ctrl+7": "tab_7",
            "Ctrl+8": "tab_8",
            "Ctrl+9": "tab_9",
            "Ctrl+0": "last_tab",
            "F11": "toggle_fullscreen",
            "Ctrl+Plus": "zoom_in",
            "Ctrl+Minus": "zoom_out",
            "Ctrl+0": "zoom_reset"
        }

        for shortcut_key, action in default_shortcuts.items():
            try:
                shortcut = QShortcut(QKeySequence(shortcut_key), self.ssh_client_app)
                shortcut.activated.connect(lambda a=action: self.execute_action(a))
                self.shortcuts[shortcut_key] = shortcut
            except Exception as e:
                logger.warning(f"Failed to create shortcut {shortcut_key}: {e}")

    def execute_action(self, action):
        """Execute shortcut action"""
        try:
            if action == "next_tab":
                self.next_tab()
            elif action == "previous_tab":
                self.previous_tab()
            elif action == "close_tab":
                self.close_current_tab()
            elif action == "close_all_tabs":
                self.close_all_tabs()
            elif action.startswith("tab_"):
                tab_num = int(action.split("_")[1])
                self.goto_tab(tab_num - 1)
            elif action == "last_tab":
                self.goto_last_tab()
            elif action == "toggle_fullscreen":
                self.toggle_fullscreen()
            elif action == "zoom_in":
                self.zoom_in()
            elif action == "zoom_out":
                self.zoom_out()
            elif action == "zoom_reset":
                self.zoom_reset()

        except Exception as e:
            logger.error(f"Error executing shortcut action {action}: {e}")

    def next_tab(self):
        """Switch to next tab"""
        tab_widget = self.ssh_client_app.tab_widget
        current = tab_widget.currentIndex()
        next_index = (current + 1) % tab_widget.count()
        tab_widget.setCurrentIndex(next_index)

    def previous_tab(self):
        """Switch to previous tab"""
        tab_widget = self.ssh_client_app.tab_widget
        current = tab_widget.currentIndex()
        prev_index = (current - 1) % tab_widget.count()
        tab_widget.setCurrentIndex(prev_index)

    def close_current_tab(self):
        """Close current tab"""
        tab_widget = self.ssh_client_app.tab_widget
        current = tab_widget.currentIndex()
        if current > 0:  # Don't close the first tab (key generator)
            self.ssh_client_app.close_tab(current)

    def close_all_tabs(self):
        """Close all tabs except the first one"""
        tab_widget = self.ssh_client_app.tab_widget
        while tab_widget.count() > 1:
            self.ssh_client_app.close_tab(1)

    def goto_tab(self, index):
        """Go to specific tab by index"""
        tab_widget = self.ssh_client_app.tab_widget
        if 0 <= index < tab_widget.count():
            tab_widget.setCurrentIndex(index)

    def goto_last_tab(self):
        """Go to last tab"""
        tab_widget = self.ssh_client_app.tab_widget
        tab_widget.setCurrentIndex(tab_widget.count() - 1)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.ssh_client_app.isFullScreen():
            self.ssh_client_app.showNormal()
        else:
            self.ssh_client_app.showFullScreen()

    def zoom_in(self):
        """Increase font size"""
        # Implementation would increase font size in terminals
        pass

    def zoom_out(self):
        """Decrease font size"""
        # Implementation would decrease font size in terminals
        pass

    def zoom_reset(self):
        """Reset font size to default"""
        # Implementation would reset font size to default
        pass