"""
SSH Tunnel Manager for JETSSH
Provides local and remote port forwarding capabilities
"""

import threading
import socket
import logging
import paramiko
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QListWidget, QComboBox, QMessageBox,
                             QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

logger = logging.getLogger(__name__)


class SSHTunnelManager(QWidget):
    """SSH Tunnel Manager with GUI"""

    tunnel_status_changed = pyqtSignal(str, str)  # tunnel_id, status

    def __init__(self, ssh_client_app):
        super().__init__()
        self.ssh_client_app = ssh_client_app
        self.active_tunnels = {}
        self.tunnel_threads = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the tunnel manager UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("SSH Tunnel Manager")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #dcdcdc;")
        layout.addWidget(title)

        # Tunnel creation section
        creation_layout = QVBoxLayout()
        creation_group = QLabel("Create New Tunnel")
        creation_group.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        creation_layout.addWidget(creation_group)

        # Tunnel type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tunnel Type:"))
        self.tunnel_type = QComboBox()
        self.tunnel_type.addItems(["Local Port Forward", "Remote Port Forward", "Dynamic SOCKS"])
        type_layout.addWidget(self.tunnel_type)
        creation_layout.addLayout(type_layout)

        # Local settings
        local_layout = QHBoxLayout()
        local_layout.addWidget(QLabel("Local Host:"))
        self.local_host = QLineEdit("127.0.0.1")
        local_layout.addWidget(self.local_host)
        local_layout.addWidget(QLabel("Local Port:"))
        self.local_port = QLineEdit()
        self.local_port.setPlaceholderText("8080")
        local_layout.addWidget(self.local_port)
        creation_layout.addLayout(local_layout)

        # Remote settings
        remote_layout = QHBoxLayout()
        remote_layout.addWidget(QLabel("Remote Host:"))
        self.remote_host = QLineEdit("127.0.0.1")
        remote_layout.addWidget(self.remote_host)
        remote_layout.addWidget(QLabel("Remote Port:"))
        self.remote_port = QLineEdit()
        self.remote_port.setPlaceholderText("80")
        remote_layout.addWidget(self.remote_port)
        creation_layout.addLayout(remote_layout)

        # SSH connection selection
        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("SSH Connection:"))
        self.connection_combo = QComboBox()
        self.refresh_connections()
        connection_layout.addWidget(self.connection_combo)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_connections)
        connection_layout.addWidget(refresh_btn)
        creation_layout.addLayout(connection_layout)

        # Create tunnel button
        create_btn = QPushButton("Create Tunnel")
        create_btn.clicked.connect(self.create_tunnel)
        create_btn.setStyleSheet("""
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
        creation_layout.addWidget(create_btn)

        layout.addLayout(creation_layout)

        # Active tunnels section
        active_layout = QVBoxLayout()
        active_group = QLabel("Active Tunnels")
        active_group.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        active_layout.addWidget(active_group)

        # Tunnel table
        self.tunnel_table = QTableWidget()
        self.tunnel_table.setColumnCount(6)
        self.tunnel_table.setHorizontalHeaderLabels([
            "Type", "Local", "Remote", "SSH Host", "Status", "Actions"
        ])
        self.tunnel_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        active_layout.addWidget(self.tunnel_table)

        # Control buttons
        control_layout = QHBoxLayout()

        stop_btn = QPushButton("Stop Selected")
        stop_btn.clicked.connect(self.stop_selected_tunnel)
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        control_layout.addWidget(stop_btn)

        stop_all_btn = QPushButton("Stop All")
        stop_all_btn.clicked.connect(self.stop_all_tunnels)
        stop_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        control_layout.addWidget(stop_all_btn)

        export_btn = QPushButton("Export Config")
        export_btn.clicked.connect(self.export_tunnel_config)
        control_layout.addWidget(export_btn)

        import_btn = QPushButton("Import Config")
        import_btn.clicked.connect(self.import_tunnel_config)
        control_layout.addWidget(import_btn)

        active_layout.addLayout(control_layout)
        layout.addLayout(active_layout)

        # Status monitoring timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_tunnel_status)
        self.status_timer.start(5000)  # Update every 5 seconds

    def refresh_connections(self):
        """Refresh available SSH connections"""
        self.connection_combo.clear()
        for host in self.ssh_client_app.ssh_clients.keys():
            self.connection_combo.addItem(host)

    def create_tunnel(self):
        """Create a new SSH tunnel"""
        try:
            tunnel_type = self.tunnel_type.currentText()
            local_host = self.local_host.text() or "127.0.0.1"
            local_port = int(self.local_port.text())
            remote_host = self.remote_host.text() or "127.0.0.1"
            remote_port = int(self.remote_port.text()) if self.remote_port.text() else None
            ssh_host = self.connection_combo.currentText()

            if not ssh_host:
                QMessageBox.warning(self, "Error", "No SSH connection selected")
                return

            if ssh_host not in self.ssh_client_app.ssh_clients:
                QMessageBox.warning(self, "Error", "SSH connection not active")
                return

            # Validate ports
            if not (1 <= local_port <= 65535):
                QMessageBox.warning(self, "Error", "Invalid local port")
                return

            if tunnel_type != "Dynamic SOCKS" and (not remote_port or not (1 <= remote_port <= 65535)):
                QMessageBox.warning(self, "Error", "Invalid remote port")
                return

            # Generate tunnel ID
            tunnel_id = f"{tunnel_type}_{local_host}_{local_port}_{ssh_host}"

            if tunnel_id in self.active_tunnels:
                QMessageBox.warning(self, "Error", "Tunnel already exists")
                return

            # Create tunnel based on type
            ssh_client = self.ssh_client_app.ssh_clients[ssh_host]

            if tunnel_type == "Local Port Forward":
                tunnel = LocalPortForward(
                    ssh_client, local_host, local_port, remote_host, remote_port
                )
            elif tunnel_type == "Remote Port Forward":
                tunnel = RemotePortForward(
                    ssh_client, local_host, local_port, remote_host, remote_port
                )
            elif tunnel_type == "Dynamic SOCKS":
                tunnel = DynamicPortForward(ssh_client, local_host, local_port)
            else:
                QMessageBox.warning(self, "Error", "Unknown tunnel type")
                return

            # Start tunnel
            tunnel_thread = threading.Thread(target=tunnel.start, daemon=True)
            tunnel_thread.start()

            # Store tunnel info
            self.active_tunnels[tunnel_id] = {
                'tunnel': tunnel,
                'type': tunnel_type,
                'local_host': local_host,
                'local_port': local_port,
                'remote_host': remote_host,
                'remote_port': remote_port,
                'ssh_host': ssh_host,
                'status': 'Starting'
            }
            self.tunnel_threads[tunnel_id] = tunnel_thread

            self.update_tunnel_table()
            QMessageBox.information(self, "Success", f"Tunnel {tunnel_id} created successfully")

            # Clear form
            self.local_port.clear()
            self.remote_port.clear()

        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid port number")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create tunnel: {str(e)}")
            logger.error(f"Failed to create tunnel: {e}")

    def stop_selected_tunnel(self):
        """Stop the selected tunnel"""
        current_row = self.tunnel_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "No tunnel selected")
            return

        tunnel_id = list(self.active_tunnels.keys())[current_row]
        self.stop_tunnel(tunnel_id)

    def stop_tunnel(self, tunnel_id):
        """Stop a specific tunnel"""
        if tunnel_id in self.active_tunnels:
            tunnel_info = self.active_tunnels[tunnel_id]
            tunnel_info['tunnel'].stop()
            tunnel_info['status'] = 'Stopped'

            # Clean up
            del self.active_tunnels[tunnel_id]
            if tunnel_id in self.tunnel_threads:
                del self.tunnel_threads[tunnel_id]

            self.update_tunnel_table()
            QMessageBox.information(self, "Success", f"Tunnel {tunnel_id} stopped")

    def stop_all_tunnels(self):
        """Stop all active tunnels"""
        tunnel_ids = list(self.active_tunnels.keys())
        for tunnel_id in tunnel_ids:
            self.stop_tunnel(tunnel_id)

    def update_tunnel_status(self):
        """Update the status of all tunnels"""
        for tunnel_id, tunnel_info in self.active_tunnels.items():
            tunnel = tunnel_info['tunnel']
            if tunnel.is_active():
                tunnel_info['status'] = 'Active'
            elif tunnel.has_error():
                tunnel_info['status'] = f'Error: {tunnel.get_error()}'
            else:
                tunnel_info['status'] = 'Inactive'

        self.update_tunnel_table()

    def update_tunnel_table(self):
        """Update the tunnel table display"""
        self.tunnel_table.setRowCount(len(self.active_tunnels))

        for row, (tunnel_id, tunnel_info) in enumerate(self.active_tunnels.items()):
            self.tunnel_table.setItem(row, 0, QTableWidgetItem(tunnel_info['type']))

            local_addr = f"{tunnel_info['local_host']}:{tunnel_info['local_port']}"
            self.tunnel_table.setItem(row, 1, QTableWidgetItem(local_addr))

            if tunnel_info['remote_port']:
                remote_addr = f"{tunnel_info['remote_host']}:{tunnel_info['remote_port']}"
            else:
                remote_addr = "N/A (SOCKS)"
            self.tunnel_table.setItem(row, 2, QTableWidgetItem(remote_addr))

            self.tunnel_table.setItem(row, 3, QTableWidgetItem(tunnel_info['ssh_host']))
            self.tunnel_table.setItem(row, 4, QTableWidgetItem(tunnel_info['status']))

            # Create action button
            stop_btn = QPushButton("Stop")
            stop_btn.clicked.connect(lambda checked, tid=tunnel_id: self.stop_tunnel(tid))
            stop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            self.tunnel_table.setCellWidget(row, 5, stop_btn)

    def export_tunnel_config(self):
        """Export tunnel configuration to file"""
        from PyQt5.QtWidgets import QFileDialog
        import json

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Tunnel Config", "tunnel_config.json", "JSON Files (*.json)"
        )

        if file_path:
            try:
                config = []
                for tunnel_info in self.active_tunnels.values():
                    config.append({
                        'type': tunnel_info['type'],
                        'local_host': tunnel_info['local_host'],
                        'local_port': tunnel_info['local_port'],
                        'remote_host': tunnel_info['remote_host'],
                        'remote_port': tunnel_info['remote_port'],
                        'ssh_host': tunnel_info['ssh_host']
                    })

                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=2)

                QMessageBox.information(self, "Success", "Tunnel configuration exported")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export config: {str(e)}")

    def import_tunnel_config(self):
        """Import tunnel configuration from file"""
        from PyQt5.QtWidgets import QFileDialog
        import json

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Tunnel Config", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)

                for tunnel_config in config:
                    # Set form values and create tunnel
                    self.tunnel_type.setCurrentText(tunnel_config['type'])
                    self.local_host.setText(tunnel_config['local_host'])
                    self.local_port.setText(str(tunnel_config['local_port']))
                    self.remote_host.setText(tunnel_config['remote_host'])
                    if tunnel_config['remote_port']:
                        self.remote_port.setText(str(tunnel_config['remote_port']))

                    # Find and select SSH connection
                    for i in range(self.connection_combo.count()):
                        if self.connection_combo.itemText(i) == tunnel_config['ssh_host']:
                            self.connection_combo.setCurrentIndex(i)
                            break

                    self.create_tunnel()

                QMessageBox.information(self, "Success", "Tunnel configuration imported")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import config: {str(e)}")


class BaseTunnel:
    """Base class for SSH tunnels"""

    def __init__(self, ssh_client):
        self.ssh_client = ssh_client
        self.active = False
        self.error = None
        self.server_socket = None

    def start(self):
        """Start the tunnel (to be implemented by subclasses)"""
        raise NotImplementedError

    def stop(self):
        """Stop the tunnel"""
        self.active = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

    def is_active(self):
        """Check if tunnel is active"""
        return self.active

    def has_error(self):
        """Check if tunnel has an error"""
        return self.error is not None

    def get_error(self):
        """Get error message"""
        return self.error


class LocalPortForward(BaseTunnel):
    """Local port forwarding tunnel"""

    def __init__(self, ssh_client, local_host, local_port, remote_host, remote_port):
        super().__init__(ssh_client)
        self.local_host = local_host
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port

    def start(self):
        """Start local port forwarding"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.local_host, self.local_port))
            self.server_socket.listen(5)
            self.active = True

            logger.info(f"Local port forward listening on {self.local_host}:{self.local_port}")

            while self.active:
                try:
                    client_socket, address = self.server_socket.accept()
                    threading.Thread(
                        target=self._handle_client,
                        args=(client_socket,),
                        daemon=True
                    ).start()
                except socket.error:
                    if self.active:
                        self.error = "Socket error"
                    break

        except Exception as e:
            self.error = str(e)
            logger.error(f"Local port forward error: {e}")

    def _handle_client(self, client_socket):
        """Handle client connection"""
        try:
            transport = self.ssh_client.get_transport()
            channel = transport.open_channel(
                'direct-tcpip',
                (self.remote_host, self.remote_port),
                client_socket.getpeername()
            )

            self._relay_data(client_socket, channel)

        except Exception as e:
            logger.error(f"Client handling error: {e}")
        finally:
            client_socket.close()

    def _relay_data(self, client_socket, channel):
        """Relay data between client and channel"""
        def relay(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
            except:
                pass
            finally:
                try:
                    source.close()
                    destination.close()
                except:
                    pass

        threading.Thread(target=relay, args=(client_socket, channel), daemon=True).start()
        threading.Thread(target=relay, args=(channel, client_socket), daemon=True).start()


class RemotePortForward(BaseTunnel):
    """Remote port forwarding tunnel"""

    def __init__(self, ssh_client, local_host, local_port, remote_host, remote_port):
        super().__init__(ssh_client)
        self.local_host = local_host
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port

    def start(self):
        """Start remote port forwarding"""
        try:
            transport = self.ssh_client.get_transport()
            transport.request_port_forward(self.remote_host, self.remote_port)
            self.active = True

            logger.info(f"Remote port forward: {self.remote_host}:{self.remote_port} -> {self.local_host}:{self.local_port}")

            while self.active:
                try:
                    channel = transport.accept(timeout=1)
                    if channel:
                        threading.Thread(
                            target=self._handle_channel,
                            args=(channel,),
                            daemon=True
                        ).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.active:
                        self.error = str(e)
                    break

        except Exception as e:
            self.error = str(e)
            logger.error(f"Remote port forward error: {e}")

    def _handle_channel(self, channel):
        """Handle incoming channel"""
        try:
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local_socket.connect((self.local_host, self.local_port))

            self._relay_data(channel, local_socket)

        except Exception as e:
            logger.error(f"Channel handling error: {e}")
        finally:
            channel.close()

    def _relay_data(self, channel, local_socket):
        """Relay data between channel and local socket"""
        def relay(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
            except:
                pass
            finally:
                try:
                    source.close()
                    destination.close()
                except:
                    pass

        threading.Thread(target=relay, args=(channel, local_socket), daemon=True).start()
        threading.Thread(target=relay, args=(local_socket, channel), daemon=True).start()


class DynamicPortForward(BaseTunnel):
    """Dynamic SOCKS proxy tunnel"""

    def __init__(self, ssh_client, local_host, local_port):
        super().__init__(ssh_client)
        self.local_host = local_host
        self.local_port = local_port

    def start(self):
        """Start SOCKS proxy"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.local_host, self.local_port))
            self.server_socket.listen(5)
            self.active = True

            logger.info(f"SOCKS proxy listening on {self.local_host}:{self.local_port}")

            while self.active:
                try:
                    client_socket, address = self.server_socket.accept()
                    threading.Thread(
                        target=self._handle_socks_client,
                        args=(client_socket,),
                        daemon=True
                    ).start()
                except socket.error:
                    if self.active:
                        self.error = "Socket error"
                    break

        except Exception as e:
            self.error = str(e)
            logger.error(f"SOCKS proxy error: {e}")

    def _handle_socks_client(self, client_socket):
        """Handle SOCKS client connection"""
        try:
            # Simple SOCKS4/5 implementation
            # This is a basic implementation - could be expanded for full SOCKS support
            data = client_socket.recv(4096)
            if not data:
                return

            # Basic SOCKS5 handshake
            if data[0] == 5:  # SOCKS5
                client_socket.send(b'\x05\x00')  # No authentication required

                data = client_socket.recv(4096)
                if data[1] == 1:  # CONNECT command
                    if data[3] == 1:  # IPv4
                        remote_host = socket.inet_ntoa(data[4:8])
                        remote_port = int.from_bytes(data[8:10], 'big')
                    elif data[3] == 3:  # Domain name
                        domain_len = data[4]
                        remote_host = data[5:5+domain_len].decode()
                        remote_port = int.from_bytes(data[5+domain_len:7+domain_len], 'big')
                    else:
                        client_socket.close()
                        return

                    try:
                        transport = self.ssh_client.get_transport()
                        channel = transport.open_channel(
                            'direct-tcpip',
                            (remote_host, remote_port),
                            client_socket.getpeername()
                        )

                        # Send success response
                        client_socket.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')

                        self._relay_data(client_socket, channel)

                    except Exception as e:
                        # Send failure response
                        client_socket.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
                        logger.error(f"SOCKS connection error: {e}")

        except Exception as e:
            logger.error(f"SOCKS client handling error: {e}")
        finally:
            client_socket.close()

    def _relay_data(self, client_socket, channel):
        """Relay data between client and channel"""
        def relay(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
            except:
                pass
            finally:
                try:
                    source.close()
                    destination.close()
                except:
                    pass

        threading.Thread(target=relay, args=(client_socket, channel), daemon=True).start()
        threading.Thread(target=relay, args=(channel, client_socket), daemon=True).start()