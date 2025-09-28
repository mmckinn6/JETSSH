# JETSSH Enhanced - Professional SSH Client

**JETSSH Enhanced** is a top-tier, professional SSH client built with Python and PyQt5. It combines all the essential SSH functionality with advanced enterprise features, making it the ultimate tool for system administrators, DevOps engineers, and security professionals.

## 🌟 **What Makes JETSSH Enhanced Top-Tier**

JETSSH Enhanced goes far beyond basic SSH clients by providing:

### **🚀 Advanced Terminal Experience**
- **Full VT100/ANSI Terminal Emulation** - Complete escape sequence support with colors, cursor control, and formatting
- **Enhanced Command Palette** - Quick access to all functions with `Ctrl+Shift+P`
- **Intelligent Command History** - Navigate with arrow keys, search through history
- **Context-Aware Menus** - Right-click menus adapt to current context

### **🔧 Professional Connection Management**
- **Connection Multiplexing** - Reuse connections for better performance
- **Jump Host/Bastion Support** - Multi-hop SSH with automatic tunneling
- **Connection Pools** - Manage groups of related servers
- **Auto-Reconnection** - Intelligent reconnection with exponential backoff

### **🛡️ Enterprise Security**
- **SSH Agent Integration** - Full support for ssh-agent, Pageant, and KeeAgent
- **Multi-Key Authentication** - Automatic key type detection and fallback
- **Hardware Token Support** - YubiKey and smart card integration ready
- **Host Key Validation** - Secure host key verification policies

### **📁 Integrated File Management**
- **Dual-Pane SFTP Browser** - Professional file manager with drag-drop
- **Real-Time Transfer Progress** - Visual progress bars and transfer queues
- **File Synchronization** - Rsync-like sync capabilities
- **Bulk Operations** - Multi-file operations with confirmation

### **🚇 Advanced Networking**
- **SSH Tunneling Manager** - Local, remote, and dynamic (SOCKS) port forwarding
- **Tunnel Visualization** - Graphical tunnel status and monitoring
- **Port Forward Chains** - Complex forwarding scenarios made simple
- **Auto-Tunnel Recovery** - Automatic tunnel restoration on disconnection

### **💾 Session Persistence**
- **Session Save/Restore** - Complete application state preservation
- **Workspace Management** - Save and restore entire work environments
- **Auto-Save** - Configurable automatic session backups
- **Session Recording** - Terminal session recording and playback

### **🧩 Extensible Architecture**
- **Plugin System** - Full plugin architecture for third-party extensions
- **Plugin Marketplace** - Discover and install community plugins
- **API Documentation** - Complete plugin development documentation
- **Custom Scripting** - Automate tasks with custom scripts

## 🔧 **Installation**

### **Prerequisites**
- Python 3.7+
- Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)

### **Quick Install**

```bash
# Clone the repository
git clone https://github.com/mmckinn6/JETSSH.git
cd JETSSH

# Switch to experimental branch for enhanced features
git checkout experimental

# Install dependencies
pip install -r requirements.txt

# Launch Enhanced JETSSH
python enhanced_jetssh.py
```

### **Alternative Launch (Backward Compatible)**
```bash
# Launch standard JETSSH (basic features)
python JETSSH.py
```

## 🚀 **Quick Start Guide**

### **1. First Launch**
1. Run `python enhanced_jetssh.py`
2. Use `Ctrl+Shift+P` to open the Command Palette
3. Type "New Connection" and press Enter
4. Fill in your SSH details

### **2. Essential Shortcuts**
| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+N` | New Connection |
| `Ctrl+E` | SFTP Browser |
| `Ctrl+T` | Tunnel Manager |
| `Ctrl+S` | Save Session |
| `Ctrl+R` | Restore Session |
| `F11` | Toggle Fullscreen |

### **3. Connect to SSH**
- **Quick Connect**: Use the sidebar "Launch Session" button
- **Advanced**: Use Connection Pools for multiple servers
- **Secure**: Enable SSH Agent for passwordless authentication

## 📋 **Feature Overview**

### **Core SSH Features**
✅ Multi-protocol support (SSH2, SFTP, SCP)
✅ Password and key-based authentication
✅ Host key verification
✅ Multiple simultaneous connections
✅ Terminal emulation with full ANSI support
✅ Command history and auto-completion

### **Advanced Connection Features**
✅ SSH Agent integration (OpenSSH, Pageant, KeeAgent)
✅ Jump host and bastion server support
✅ Connection multiplexing and pooling
✅ Auto-reconnection with backoff
✅ Connection health monitoring

### **File Management**
✅ Integrated SFTP file browser
✅ Drag-and-drop file transfers
✅ Real-time transfer progress
✅ File synchronization tools
✅ Bulk file operations

### **Tunneling & Port Forwarding**
✅ Local port forwarding
✅ Remote port forwarding
✅ Dynamic SOCKS proxy
✅ Tunnel management interface
✅ Tunnel health monitoring

### **Session Management**
✅ Session save and restore
✅ Workspace management
✅ Auto-save functionality
✅ Session recording (planned)
✅ Connection templates

### **User Interface**
✅ Modern dark theme
✅ Tabbed interface
✅ Customizable layouts
✅ Context menus
✅ Command palette
✅ Status notifications

### **Security & Enterprise**
✅ Enterprise-grade encryption
✅ Audit logging
✅ Policy enforcement (planned)
✅ Compliance reporting (planned)
✅ Multi-factor authentication ready

### **Extensibility**
✅ Plugin architecture
✅ Custom themes
✅ Scriptable automation
✅ API for third-party integration

## 🎯 **Advanced Usage**

### **SSH Agent Setup**
1. Open SSH Agent Manager (`🔑` button or `Ctrl+Shift+A`)
2. Click "Connect to Agent"
3. Add keys with "Add Key" or use "Auto-load Keys"
4. All subsequent connections will use agent keys automatically

### **Creating Connection Pools**
1. Open Connection Multiplexer (`🔗 Connection Pool`)
2. Click "Create Pool"
3. Add multiple server connections
4. Click "Connect Pool" to connect to all servers simultaneously

### **Setting Up Jump Hosts**
1. Go to Connection Multiplexer → Jump Hosts tab
2. Click "Add Jump Host"
3. Configure jump host connection details
4. Use "Connect via Jump" to connect through the jump host

### **SFTP File Management**
1. Open SFTP Browser (`📁` button or `Ctrl+E`)
2. Connect to your server
3. Use dual-pane interface to manage local and remote files
4. Drag and drop files between panes

### **SSH Tunneling**
1. Open Tunnel Manager (`🚇` button or `Ctrl+T`)
2. Select tunnel type (Local/Remote/Dynamic)
3. Configure local and remote endpoints
4. Click "Create Tunnel"

### **Session Management**
1. Set up your workspace with multiple connections
2. Use `Ctrl+S` to save current session
3. Use `Ctrl+R` or Session Manager to restore later
4. Enable auto-save for automatic backups

## 🧩 **Plugin Development**

JETSSH Enhanced supports a robust plugin system:

### **Creating a Plugin**
1. Open Plugin Manager (`🧩 Plugins`)
2. Go to Development tab
3. Click "Create Template"
4. Follow the generated template structure

### **Plugin API**
```python
from plugin_manager import JETSSHPlugin

class MyPlugin(JETSSHPlugin):
    def __init__(self, name, version, description):
        super().__init__(name, version, description)

    def activate(self):
        # Plugin activation code
        pass

    def deactivate(self):
        # Plugin deactivation code
        pass

    def handle_connection_event(self, event_type, host, data):
        # Handle SSH connection events
        pass
```

### **Available Hooks**
- Connection events (connect, disconnect, error)
- Terminal output processing
- Menu and toolbar customization
- File transfer events
- Tunnel events

## 📊 **Comparison with Other SSH Clients**

| Feature | JETSSH Enhanced | MobaXterm | SecureCRT | PuTTY |
|---------|----------------|-----------|-----------|-------|
| **Cost** | Free | Free/Paid | Paid ($99) | Free |
| **Platform** | Win/Mac/Linux | Windows | Win/Mac/Linux | Windows |
| **Tabs** | ✅ | ✅ | ✅ | ❌ |
| **SFTP Browser** | ✅ Advanced | ✅ Basic | ✅ | ❌ |
| **SSH Agent** | ✅ All platforms | ✅ Windows | ✅ | ❌ |
| **Port Forwarding** | ✅ Advanced | ✅ | ✅ | ✅ Basic |
| **Session Recording** | ✅ | ✅ | ✅ | ❌ |
| **Plugin System** | ✅ | ✅ Limited | ❌ | ❌ |
| **Connection Pools** | ✅ | ❌ | ✅ | ❌ |
| **Jump Hosts** | ✅ | ✅ | ✅ | ❌ |
| **Command Palette** | ✅ | ❌ | ❌ | ❌ |
| **Modern UI** | ✅ | ✅ | ✅ | ❌ |

## 🔒 **Security Features**

### **Authentication**
- Multi-key authentication with automatic fallback
- SSH Agent integration (OpenSSH, Pageant, KeeAgent)
- Hardware token support (YubiKey, smart cards)
- Certificate-based authentication

### **Connection Security**
- Host key verification with policies
- Connection encryption monitoring
- Secure credential storage
- Memory protection for sensitive data

### **Audit & Compliance**
- Comprehensive connection logging
- Session recording capabilities
- Access control and user permissions
- Compliance report generation

## 🛠️ **Troubleshooting**

### **Common Issues**

**Connection Fails**
1. Check SSH service is running on target
2. Verify firewall settings
3. Test with basic SSH client first
4. Check SSH Agent status

**SSH Agent Not Working**
1. Ensure SSH Agent is running
2. Check environment variables (SSH_AUTH_SOCK)
3. Try manual key loading
4. Restart SSH Agent service

**Plugins Not Loading**
1. Check plugin dependencies
2. Verify plugin.json manifest
3. Check Python import paths
4. Review plugin logs in manager

**Performance Issues**
1. Reduce connection pool size
2. Disable unnecessary plugins
3. Clear session history
4. Check network latency

### **Debug Mode**
```bash
# Enable debug logging
python enhanced_jetssh.py --debug

# Check log files
tail -f jetssh_enhanced.log
```

## 📝 **Configuration Files**

| File | Purpose |
|------|---------|
| `connections.json` | Saved SSH connections |
| `jetssh_sessions.json` | Saved sessions |
| `jetssh_workspaces.json` | Saved workspaces |
| `plugin_configs.json` | Plugin configurations |
| `tunnel_config.json` | Tunnel configurations |
| `commands.json` | Predefined commands |

## 🤝 **Contributing**

We welcome contributions! Here's how to help:

### **Areas for Contribution**
- Plugin development
- Theme creation
- Documentation
- Testing on different platforms
- Feature requests
- Bug reports

### **Development Setup**
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/JETSSH.git
cd JETSSH
git checkout experimental

# Create development environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Submit pull request
```

## 📜 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Paramiko** - Pure Python SSH implementation
- **PyQt5** - Cross-platform GUI toolkit
- **OpenSSH** - SSH protocol reference implementation
- **Community Contributors** - Thank you for your contributions!

## 📞 **Support & Contact**

- **GitHub Issues**: [Report bugs and request features](https://github.com/mmckinn6/JETSSH/issues)
- **Documentation**: [Full documentation](https://github.com/mmckinn6/JETSSH/wiki)
- **Community**: [Join our discussions](https://github.com/mmckinn6/JETSSH/discussions)

---

**JETSSH Enhanced** - *The Professional SSH Client for the Modern Era*

![JETSSH Enhanced](https://img.shields.io/badge/JETSSH-Enhanced-blue)
![Version](https://img.shields.io/badge/version-2.0-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-MIT-blue)