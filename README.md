# JETSSH

JETSSH is a production-ready SSH client built with PyQt and Paramiko, designed for cross-platform use on Windows, Linux, and macOS. It offers real-time terminal-like interaction, secure file transfer (SCP/SFTP), SSH key generation, and an intuitive dark-themed GUI with enterprise-grade security features.

## ✨ Features

### 🖥️ **Core SSH Functionality**
- **Real-Time Terminal Interface**: Execute commands with live output and terminal-like interaction
- **Multi-Key Authentication**: Support for RSA, DSA, ECDSA, and Ed25519 key types
- **Secure Host Key Validation**: Enhanced security with proper host key verification
- **Command History**: Navigate through command history with up/down arrows
- **Multiple Sessions**: Manage multiple SSH connections simultaneously with tabbed interface

### 🔐 **SSH Key Management**
- **Built-in Key Generator**: Generate SSH keys directly within the application
- **Multiple Key Types**: Support for RSA (1024-4096 bits), DSA, ECDSA (256/384/521 bits), and Ed25519
- **Encrypted Keys**: Support for passphrase-protected private keys
- **Secure Storage**: Automatic file permission setting (0o600) for private keys

### 📁 **File Transfer (SFTP)**
- **Drag-and-Drop Interface**: Easy file upload and download
- **File Size Validation**: 1GB file size limits with progress feedback
- **Overwrite Protection**: Confirmation prompts for existing files
- **Directory Validation**: Automatic remote directory verification

### ⚙️ **Predefined Commands**
- **Custom Command Library**: Save frequently used commands
- **One-Click Execution**: Execute saved commands on active SSH sessions
- **Command Validation**: Safety checks for potentially dangerous commands
- **Import/Export**: JSON-based command storage and backup

### 🛡️ **Security & Reliability**
- **Enterprise-Grade Security**: Secure memory handling and credential management
- **Comprehensive Logging**: Structured logging to file and console
- **Error Recovery**: Robust error handling with detailed user feedback
- **Resource Management**: Automatic cleanup and graceful shutdown

### 🎨 **User Interface**
- **Modern Dark Theme**: Professional dark UI with external CSS styling
- **Responsive Design**: Adaptive layout for different screen sizes
- **Intuitive Navigation**: Clean, organized interface with logical grouping
- **Real-time Feedback**: Status indicators and progress notifications

## 🔧 Installation

### Prerequisites
- Python 3.7 or higher
- PyQt5
- Paramiko

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mmckinn6/JETSSH.git
   cd JETSSH
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the application:**
   ```bash
   python JETSSH.py
   ```

### Platform-Specific Notes

**Windows:**
- Tested on Windows 10/11 with Python 3.7+
- No additional configuration required

**Linux:**
- Ensure Qt5 development libraries are installed
- May require: `sudo apt-get install python3-pyqt5` (Ubuntu/Debian)

**macOS:**
- Install via Homebrew: `brew install pyqt5`
- May need to set `QT_QPA_PLATFORM=cocoa` for some systems

## 🚀 Usage

### SSH Connections

1. **Add a Connection:**
   - Click "Add Connection"
   - Enter hostname/IP and username
   - Optionally select a private key file
   - Connection validates hostname format automatically

2. **Launch Session:**
   - Select a connection from the list
   - Click "Launch Session"
   - Enter password or key passphrase when prompted

3. **Execute Commands:**
   - Type commands in the input field
   - Use Up/Down arrows for command history
   - Ctrl+C and Ctrl+D work as expected

### SSH Key Generation

1. Navigate to the "SSH Key Generator" tab
2. Select key type (RSA, DSA, ECDSA, Ed25519)
3. Choose key length (where applicable)
4. Optionally set a passphrase
5. Click "Generate SSH Key"
6. Save both private and public keys

### File Transfer

1. **Upload Files:**
   - Select active connection
   - Click "Upload File"
   - Choose local file and remote destination
   - Confirm overwrite if file exists

2. **Download Files:**
   - Select active connection
   - Click "Download File"
   - Enter remote file path
   - Choose local destination

### Predefined Commands

1. **Add Commands:**
   - Use the predefined commands panel in any SSH session
   - Click "Add Command" to create new entries
   - Commands are validated for safety

2. **Execute Commands:**
   - Select a command from the list
   - Click "Execute Command"
   - Dangerous commands require confirmation

## 📁 Project Structure

```
JETSSH/
├── JETSSH.py              # Main application entry point
├── JETSSHKEYGEN.py        # SSH key generation module
├── PredefinedCommands.py  # Command management module
├── styles.css             # External stylesheet
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── LICENSE               # MIT License
```

## 🔒 Security Features

- **Host Key Verification**: Uses `WarningPolicy()` instead of insecure `AutoAddPolicy()`
- **Multi-Key Support**: Automatic detection and loading of different key types
- **Secure File Permissions**: Automatic setting of restrictive permissions (0o600)
- **Memory Security**: Secure clearing of passwords and passphrases
- **Input Validation**: Comprehensive validation of user inputs and file operations
- **Error Boundaries**: Isolated error handling prevents cascading failures

## 📝 Logging

JETSSH creates detailed logs in `jetssh.log` including:
- Connection attempts and results
- File transfer operations
- Error conditions and recovery
- Security events and warnings

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with appropriate tests
4. Commit with descriptive messages: `git commit -m 'Add feature description'`
5. Push to your branch: `git push origin feature-name`
6. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add comprehensive error handling
- Include logging for significant operations
- Test on multiple platforms when possible
- Update documentation for new features

## 🐛 Known Issues & Limitations

- Large file transfers (>1GB) are blocked for performance reasons
- Some terminal applications (like `top`) may not display correctly
- Windows may require running as administrator for certain SSH operations

## 📋 Changelog

### Version 2.0 (Latest)
- ✅ **Security Overhaul**: Enhanced host key validation and multi-key support
- ✅ **Bug Fixes**: Fixed infinite loops, channel targeting, and thread safety
- ✅ **UI Improvements**: External CSS, better validation, enhanced UX
- ✅ **Robustness**: Comprehensive error handling and logging system
- ✅ **Features**: SSH key generation, predefined commands, file validation

### Version 1.0
- Basic SSH client functionality
- File transfer capabilities
- Tabbed interface
- Basic connection management

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact & Support

- **Author**: [mmckinn6](https://github.com/mmckinn6)
- **Contributor**: [nwylds](https://github.com/nwylds)
- **Issues**: [GitHub Issues](https://github.com/mmckinn6/JETSSH/issues)

For questions, bug reports, or feature requests, please open an issue on GitHub.

---

**JETSSH** - *Secure, Reliable, Cross-Platform SSH Client*