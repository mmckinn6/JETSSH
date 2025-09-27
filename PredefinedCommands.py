import json
import os
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget,
                             QInputDialog, QLabel, QMessageBox, QHBoxLayout)

logger = logging.getLogger(__name__)

COMMANDS_FILE = 'commands.json'

class PredefinedCommands(QWidget):
    def __init__(self, ssh_client_app):
        super().__init__()
        self.ssh_client_app = ssh_client_app  # Pass the main SSHClientApp instance
        self.init_ui()
        self.commands = []
        self.load_commands()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Create a layout for the toggle button
        toggle_layout = QHBoxLayout()

        # Toggle button to show/hide the command panel
        self.toggle_button = QPushButton("Hide Commands")
        self.toggle_button.clicked.connect(self.toggle_command_panel)
        toggle_layout.addWidget(self.toggle_button)
        layout.addLayout(toggle_layout)

        # Command List
        self.command_list = QListWidget()
        layout.addWidget(QLabel("Predefined Commands"))
        layout.addWidget(self.command_list)

        # Buttons for managing commands
        self.add_command_button = QPushButton("Add Command")
        self.add_command_button.clicked.connect(self.add_command)
        layout.addWidget(self.add_command_button)

        self.remove_command_button = QPushButton("Remove Command")
        self.remove_command_button.clicked.connect(self.remove_command)
        layout.addWidget(self.remove_command_button)

        self.execute_command_button = QPushButton("Execute Command")
        self.execute_command_button.clicked.connect(self.execute_command)
        layout.addWidget(self.execute_command_button)

        # Load predefined commands on startup
        self.load_commands()

    def toggle_command_panel(self):
        """Toggle the visibility of the predefined commands panel."""
        is_visible = self.command_list.isVisible()

        # Toggle visibility
        self.command_list.setVisible(not is_visible)
        self.add_command_button.setVisible(not is_visible)
        self.remove_command_button.setVisible(not is_visible)
        self.execute_command_button.setVisible(not is_visible)

        # Update toggle button text
        if is_visible:
            self.toggle_button.setText("Show Commands")
        else:
            self.toggle_button.setText("Hide Commands")

    def load_commands(self):
        """Load predefined commands from JSON file with validation."""
        self.command_list.clear()  # Clear the existing command list to prevent duplication
        self.commands = []

        if not os.path.exists(COMMANDS_FILE):
            logger.info("No commands file found, starting with empty list")
            return

        try:
            with open(COMMANDS_FILE, 'r') as file:
                data = json.load(file)

                # Validate data structure
                if not isinstance(data, dict) or 'commands' not in data:
                    logger.error("Invalid commands file format")
                    QMessageBox.warning(self, "Error", "Invalid commands file format.")
                    return

                if not isinstance(data['commands'], list):
                    logger.error("Commands data is not a list")
                    QMessageBox.warning(self, "Error", "Invalid commands data structure.")
                    return

                # Validate each command
                valid_commands = []
                for command in data['commands']:
                    if self.validate_command(command):
                        valid_commands.append(command)
                    else:
                        logger.warning(f"Skipping invalid command: {command}")

                self.commands = valid_commands

                # Add to UI
                for command in self.commands:
                    self.command_list.addItem(command['name'])

                logger.info(f"Loaded {len(self.commands)} valid commands")

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in commands file: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to parse commands file: {str(e)}")
        except (IOError, OSError) as e:
            logger.error(f"Error reading commands file: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to read commands file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error loading commands: {str(e)}")
            QMessageBox.critical(self, "Error", f"Unexpected error loading commands: {str(e)}")

    def validate_command(self, command):
        """Validate command data structure"""
        if not isinstance(command, dict):
            return False

        required_fields = ['name', 'command']
        for field in required_fields:
            if field not in command or not isinstance(command[field], str):
                return False

        # Optional description field
        if 'description' in command and not isinstance(command['description'], str):
            return False

        return True

    def save_commands(self):
        """Save predefined commands to JSON file with error handling."""
        try:
            # Validate commands data
            if not isinstance(self.commands, list):
                logger.error("Invalid commands data structure")
                return False

            # Create backup if file exists
            if os.path.exists(COMMANDS_FILE):
                backup_file = f"{COMMANDS_FILE}.backup"
                try:
                    os.rename(COMMANDS_FILE, backup_file)
                except OSError as e:
                    logger.warning(f"Could not create backup: {e}")

            # Save commands
            with open(COMMANDS_FILE, 'w') as file:
                json.dump({"commands": self.commands}, file, indent=2)

            logger.info(f"Saved {len(self.commands)} commands")
            return True

        except (IOError, OSError, json.JSONEncodeError) as e:
            logger.error(f"Error saving commands: {str(e)}")
            QMessageBox.critical(self, "Save Error", f"Failed to save commands: {str(e)}")
            return False

    def add_command(self):
        """Add a new predefined command with validation."""
        name, ok = QInputDialog.getText(self, "Add Command", "Command Name:")
        if not ok or not name or not name.strip():
            return

        name = name.strip()

        # Check for duplicate names
        if any(cmd['name'] == name for cmd in self.commands):
            QMessageBox.warning(self, "Duplicate Name", "A command with this name already exists.")
            return

        command, ok = QInputDialog.getText(self, "Add Command", "Command:")
        if not ok or not command or not command.strip():
            return

        command = command.strip()

        # Validate command for basic security (no dangerous patterns)
        dangerous_patterns = ['rm -rf', 'mkfs', 'dd if=', '>/dev/', 'format', 'fdisk']
        if any(pattern in command.lower() for pattern in dangerous_patterns):
            reply = QMessageBox.question(
                self, "Potentially Dangerous Command",
                "This command appears to be potentially dangerous. Are you sure you want to add it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        description, ok = QInputDialog.getText(self, "Add Command", "Description (optional):")
        if not ok:
            description = ""

        new_command = {
            "name": name,
            "command": command,
            "description": description.strip() if description else ""
        }

        self.commands.append(new_command)
        if self.save_commands():
            self.command_list.addItem(name)
            logger.info(f"Added command: {name}")
        else:
            # Remove from memory if save failed
            self.commands.pop()

    def remove_command(self):
        """Remove selected command."""
        selected_item = self.command_list.currentItem()
        if selected_item:
            command_name = selected_item.text()
            self.commands = [cmd for cmd in self.commands if cmd['name'] != command_name]
            self.save_commands()
            self.command_list.takeItem(self.command_list.row(selected_item))

    def execute_command(self):
        """Execute selected command with validation."""
        selected_item = self.command_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Error", "Please select a command to execute.")
            return

        command_name = selected_item.text()
        command_to_execute = None

        # Find the command
        for command in self.commands:
            if command['name'] == command_name:
                command_to_execute = command['command']
                break

        if not command_to_execute:
            QMessageBox.warning(self, "Error", "Selected command not found.")
            return

        # Confirm execution for potentially dangerous commands
        dangerous_patterns = ['rm ', 'delete', 'format', 'mkfs', 'dd ']
        if any(pattern in command_to_execute.lower() for pattern in dangerous_patterns):
            reply = QMessageBox.question(
                self, "Confirm Execution",
                f"Are you sure you want to execute this command?\n\n{command_to_execute}",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Send the command to the active SSH session
        self.send_command_to_active_session(command_to_execute)

    def send_command_to_active_session(self, command):
        """Send command to the active SSH session with validation."""
        if not command or not command.strip():
            QMessageBox.warning(self, "Error", "No command to execute.")
            return

        try:
            # Retrieve the active session from the SSH client app
            current_index = self.ssh_client_app.tab_widget.currentIndex()
            if current_index < 0:
                QMessageBox.warning(self, "Error", "No active tab found.")
                return

            current_tab_text = self.ssh_client_app.tab_widget.tabText(current_index)
            if not current_tab_text or '(' not in current_tab_text:
                QMessageBox.warning(self, "Error", "Current tab is not an SSH session.")
                return

            # Extract the host part from the tab text
            try:
                host = current_tab_text.split()[0]  # Split by space and take the first part
            except (IndexError, AttributeError):
                QMessageBox.warning(self, "Error", "Could not determine host from tab.")
                return

            # Check if there's an active SSH session for the host
            if host not in self.ssh_client_app.channels:
                QMessageBox.warning(self, "Error", "No active SSH session found for this host.")
                return

            channel = self.ssh_client_app.channels[host]
            if not channel.active:
                QMessageBox.warning(self, "Error", "SSH session is not active.")
                return

            # Send the command to the active channel
            channel.send(command + "\n")
            logger.info(f"Executed predefined command on {host}: {command}")

        except Exception as e:
            logger.error(f"Error sending predefined command: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to send command: {str(e)}")
