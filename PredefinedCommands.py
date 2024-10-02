import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget,
                             QInputDialog, QLabel, QMessageBox)


class PredefinedCommands(QWidget):
    def __init__(self, ssh_client_app):
        super().__init__()
        self.ssh_client_app = ssh_client_app  # Pass the main SSHClientApp instance
        self.init_ui()
        self.commands = []
        self.load_commands()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Command List
        self.command_list = QListWidget()
        layout.addWidget(QLabel("Predefined Commands"))
        layout.addWidget(self.command_list)

        # Buttons for managing commands
        add_command_button = QPushButton("Add Command")
        add_command_button.clicked.connect(self.add_command)
        layout.addWidget(add_command_button)

        remove_command_button = QPushButton("Remove Command")
        remove_command_button.clicked.connect(self.remove_command)
        layout.addWidget(remove_command_button)

        execute_command_button = QPushButton("Execute Command")
        execute_command_button.clicked.connect(self.execute_command)
        layout.addWidget(execute_command_button)

        # Load predefined commands on startup
        self.load_commands()

    def load_commands(self):
        """Load predefined commands from JSON file."""
        self.command_list.clear()  # Clear the existing command list to prevent duplication
        try:
            with open('commands.json', 'r') as file:
                data = json.load(file)
                self.commands = data['commands']
                for command in self.commands:
                    self.command_list.addItem(command['name'])
        except FileNotFoundError:
            QMessageBox.information(self, "Info", "No predefined commands found.")

    def save_commands(self):
        """Save predefined commands to JSON file."""
        with open('commands.json', 'w') as file:
            json.dump({"commands": self.commands}, file)

    def add_command(self):
        """Add a new predefined command."""
        name, ok = QInputDialog.getText(self, "Add Command", "Command Name:")
        if ok and name:
            command, ok = QInputDialog.getText(self, "Add Command", "Command:")
            if ok and command:
                description, ok = QInputDialog.getText(self, "Add Command", "Description (optional):")
                new_command = {"name": name, "command": command, "description": description}
                self.commands.append(new_command)
                self.save_commands()
                self.command_list.addItem(name)

    def remove_command(self):
        """Remove selected command."""
        selected_item = self.command_list.currentItem()
        if selected_item:
            command_name = selected_item.text()
            self.commands = [cmd for cmd in self.commands if cmd['name'] != command_name]
            self.save_commands()
            self.command_list.takeItem(self.command_list.row(selected_item))

    def execute_command(self):
        """Execute selected command."""
        selected_item = self.command_list.currentItem()
        if selected_item:
            command_name = selected_item.text()
            for command in self.commands:
                if command['name'] == command_name:
                    # Send the command to the active SSH session
                    self.send_command_to_active_session(command['command'])
                    break

    def send_command_to_active_session(self, command):
        """Send command to the active SSH session."""
        # Retrieve the active session from the SSH client app
        current_index = self.ssh_client_app.tab_widget.currentIndex()
        current_tab_text = self.ssh_client_app.tab_widget.tabText(current_index)

        # Extract the host part from the tab text
        host = current_tab_text.split()[0]  # Split by space and take the first part

        # Debug: Print out the extracted host and available channels
        print(f"Extracted host: {host}")
        print(f"Available channels: {self.ssh_client_app.channels.keys()}")

        # Check if there's an active SSH session for the host
        if host in self.ssh_client_app.channels:
            channel = self.ssh_client_app.channels[host]
            try:
                # Send the command to the active channel
                channel.send(command + "\n")
                print(f"Command sent: {command}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to send command: {str(e)}")
        else:
            QMessageBox.warning(self, "Error", "No active SSH session found.")
