import os
import io
import paramiko
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QFileDialog, QMessageBox, QComboBox, QFormLayout, QTextEdit)
from PyQt5.QtCore import Qt

class SSHKeyGeneratorTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Key type and length selection
        form_layout = QFormLayout()
        
        # Key type selection
        form_layout.addRow(QLabel("Key Type:"))
        self.key_type = QComboBox()
        self.key_type.addItems(["RSA", "DSA", "ECDSA", "Ed25519"])
        self.key_type.currentTextChanged.connect(self.update_key_length_options)
        form_layout.addRow("Select Key Type:", self.key_type)

        # Key length input (will dynamically update based on the key type)
        form_layout.addRow(QLabel("Key Length (Bits):"))
        self.key_length_input = QComboBox()
        self.update_key_length_options()  # Initialize key length options
        form_layout.addRow("Enter Key Length:", self.key_length_input)

        # Optional passphrase input
        self.passphrase_input = QLineEdit()
        self.passphrase_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Passphrase (Optional):", self.passphrase_input)

        layout.addLayout(form_layout)

        # Button to generate SSH key
        self.generate_button = QPushButton("Generate SSH Key")
        self.generate_button.clicked.connect(self.generate_ssh_key)
        layout.addWidget(self.generate_button)

        # Private and Public Key display areas
        layout.addWidget(QLabel("Private Key:"))
        self.private_key_text = QTextEdit()
        self.private_key_text.setReadOnly(True)
        layout.addWidget(self.private_key_text)

        layout.addWidget(QLabel("Public Key:"))
        self.public_key_text = QTextEdit()
        self.public_key_text.setReadOnly(True)
        layout.addWidget(self.public_key_text)

        # Button to save keys
        self.save_private_button = QPushButton("Save Private Key")
        self.save_private_button.setEnabled(False)
        self.save_private_button.clicked.connect(self.save_private_key)
        layout.addWidget(self.save_private_button)

        self.save_public_button = QPushButton("Save Public Key")
        self.save_public_button.setEnabled(False)
        self.save_public_button.clicked.connect(self.save_public_key)
        layout.addWidget(self.save_public_button)

        self.setLayout(layout)

    def update_key_length_options(self):
        """ Update available key length options based on the selected key type """
        self.key_length_input.clear()
        key_type = self.key_type.currentText()

        if key_type == "RSA":
            self.key_length_input.addItems(["1024", "2048", "3072", "4096"])
        elif key_type == "DSA":
            self.key_length_input.addItems(["1024"])
        elif key_type == "ECDSA":
            self.key_length_input.addItems(["256", "384", "521"])
        elif key_type == "Ed25519":
            self.key_length_input.addItem("N/A")  # Ed25519 has a fixed key length



    def generate_ssh_key(self):
        key_type = self.key_type.currentText()
        key_length = int(self.key_length_input.currentText()) if self.key_type.currentText() != "Ed25519" else None
        passphrase = self.passphrase_input.text().encode() if self.passphrase_input.text() else None

        try:
            # Generate the key based on the selected type and length
            if key_type == "RSA":
                self.private_key = paramiko.RSAKey.generate(bits=key_length)
            elif key_type == "DSA":
                self.private_key = paramiko.DSSKey.generate(bits=key_length)
            elif key_type == "ECDSA":
                self.private_key = paramiko.ECDSAKey.generate(bits=key_length)
            elif key_type == "Ed25519":
                self.private_key = paramiko.Ed25519Key.generate()

            # Capture private key into a string using a file-like object
            private_key_io = io.StringIO()
            self.private_key.write_private_key(private_key_io, password=passphrase)
            private_key_string = private_key_io.getvalue()
            self.private_key_text.setText(private_key_string)
        
            # Generate public key and display it
            public_key_string = f"{self.private_key.get_name()} {self.private_key.get_base64()}"
            self.public_key_text.setText(public_key_string)

            # Enable the save buttons
            self.save_private_button.setEnabled(True)
            self.save_public_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate SSH key: {str(e)}")


    def save_private_key(self):
        """ Save the private key to a file """
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Private Key", "", "Key Files (*.pem);;All Files (*)", options=options)
            if file_name:
                with open(file_name, 'w') as key_file:
                    key_file.write(self.private_key_text.toPlainText())
                QMessageBox.information(self, "Success", "Private key saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save private key: {str(e)}")

    def save_public_key(self):
        """ Save the public key to a file """
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Public Key", "", "Key Files (*.pub);;All Files (*)", options=options)
            if file_name:
                with open(file_name, 'w') as key_file:
                    key_file.write(self.public_key_text.toPlainText())
                QMessageBox.information(self, "Success", "Public key saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save public key: {str(e)}")
