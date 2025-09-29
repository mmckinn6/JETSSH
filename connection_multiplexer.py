"""
Connection Multiplexer and Jump Host Manager for JETSSH
Provides advanced SSH connection management with multiplexing and jump hosts
"""

import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta
import paramiko
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
                             QTreeWidgetItem, QPushButton, QInputDialog, QMessageBox,
                             QComboBox, QLineEdit, QCheckBox, QTabWidget, QTextEdit,
                             QProgressBar, QDialog, QDialogButtonBox, QFormLayout,
                             QSpinBox, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class ConnectionMultiplexer(QWidget):
    """Advanced connection management with multiplexing and jump hosts"""

    connection_established = pyqtSignal(str, dict)  # host, connection_info
    connection_failed = pyqtSignal(str, str)        # host, error_message
    jump_host_connected = pyqtSignal(str)           # jump_host

    def __init__(self, ssh_client_app):
        super().__init__()
        self.ssh_client_app = ssh_client_app
        self.connection_pools = defaultdict(list)
        self.jump_hosts = {}
        self.active_connections = {}
        self.connection_configs = {}
        self.multiplexed_connections = {}
        self.setup_ui()
        self.load_configurations()

    def setup_ui(self):
        """Setup the connection multiplexer UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Connection Multiplexer & Jump Hosts")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #dcdcdc;")
        layout.addWidget(title)

        # Tab widget for different sections
        tab_widget = QTabWidget()

        # Connection pools tab
        pools_tab = self.create_pools_tab()
        tab_widget.addTab(pools_tab, "Connection Pools")

        # Jump hosts tab
        jump_hosts_tab = self.create_jump_hosts_tab()
        tab_widget.addTab(jump_hosts_tab, "Jump Hosts")

        # Advanced configs tab
        configs_tab = self.create_configs_tab()
        tab_widget.addTab(configs_tab, "Advanced Configs")

        # Monitoring tab
        monitoring_tab = self.create_monitoring_tab()
        tab_widget.addTab(monitoring_tab, "Monitoring")

        layout.addWidget(tab_widget)

        # Status monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_connections)
        self.monitor_timer.start(5000)  # Check every 5 seconds

    def create_pools_tab(self):
        """Create connection pools management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Pool controls
        controls_layout = QHBoxLayout()

        create_pool_btn = QPushButton("➕ Create Pool")
        create_pool_btn.clicked.connect(self.create_connection_pool)
        create_pool_btn.setStyleSheet("""
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
        controls_layout.addWidget(create_pool_btn)

        connect_pool_btn = QPushButton("🔗 Connect Pool")
        connect_pool_btn.clicked.connect(self.connect_pool)
        controls_layout.addWidget(connect_pool_btn)

        disconnect_pool_btn = QPushButton("🔌 Disconnect Pool")
        disconnect_pool_btn.clicked.connect(self.disconnect_pool)
        controls_layout.addWidget(disconnect_pool_btn)

        controls_layout.addStretch()

        auto_reconnect_checkbox = QCheckBox("Auto-reconnect")
        auto_reconnect_checkbox.setChecked(True)
        controls_layout.addWidget(auto_reconnect_checkbox)

        layout.addLayout(controls_layout)

        # Pools tree
        pools_label = QLabel("Connection Pools")
        pools_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(pools_label)

        self.pools_tree = QTreeWidget()
        self.pools_tree.setHeaderLabels([
            "Pool Name", "Connections", "Active", "Status", "Last Used"
        ])
        self.pools_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.pools_tree)

        # Pool operations
        pool_ops_layout = QHBoxLayout()

        edit_pool_btn = QPushButton("Edit Pool")
        edit_pool_btn.clicked.connect(self.edit_selected_pool)
        pool_ops_layout.addWidget(edit_pool_btn)

        clone_pool_btn = QPushButton("Clone Pool")
        clone_pool_btn.clicked.connect(self.clone_selected_pool)
        pool_ops_layout.addWidget(clone_pool_btn)

        delete_pool_btn = QPushButton("Delete Pool")
        delete_pool_btn.clicked.connect(self.delete_selected_pool)
        delete_pool_btn.setStyleSheet("""
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
        pool_ops_layout.addWidget(delete_pool_btn)

        layout.addLayout(pool_ops_layout)

        self.refresh_pools_display()

        return widget

    def create_jump_hosts_tab(self):
        """Create jump hosts management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Jump host controls
        controls_layout = QHBoxLayout()

        add_jump_host_btn = QPushButton("➕ Add Jump Host")
        add_jump_host_btn.clicked.connect(self.add_jump_host)
        add_jump_host_btn.setStyleSheet("""
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
        controls_layout.addWidget(add_jump_host_btn)

        connect_jump_btn = QPushButton("🚀 Connect via Jump")
        connect_jump_btn.clicked.connect(self.connect_via_jump_host)
        controls_layout.addWidget(connect_jump_btn)

        test_jump_btn = QPushButton("🧪 Test Jump Host")
        test_jump_btn.clicked.connect(self.test_jump_host)
        controls_layout.addWidget(test_jump_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Jump hosts tree
        jump_hosts_label = QLabel("Jump Hosts")
        jump_hosts_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(jump_hosts_label)

        self.jump_hosts_tree = QTreeWidget()
        self.jump_hosts_tree.setHeaderLabels([
            "Jump Host", "Target Hosts", "Status", "Latency", "Last Used"
        ])
        self.jump_hosts_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.jump_hosts_tree)

        # Jump host operations
        jump_ops_layout = QHBoxLayout()

        edit_jump_btn = QPushButton("Edit Jump Host")
        edit_jump_btn.clicked.connect(self.edit_jump_host)
        jump_ops_layout.addWidget(edit_jump_btn)

        chain_jumps_btn = QPushButton("Chain Jump Hosts")
        chain_jumps_btn.clicked.connect(self.create_jump_chain)
        jump_ops_layout.addWidget(chain_jumps_btn)

        delete_jump_btn = QPushButton("Delete Jump Host")
        delete_jump_btn.clicked.connect(self.delete_jump_host)
        delete_jump_btn.setStyleSheet("""
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
        jump_ops_layout.addWidget(delete_jump_btn)

        layout.addLayout(jump_ops_layout)

        self.refresh_jump_hosts_display()

        return widget

    def create_configs_tab(self):
        """Create advanced configurations tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Connection settings
        settings_label = QLabel("Advanced Connection Settings")
        settings_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(settings_label)

        # Multiplexing settings
        multiplex_layout = QFormLayout()

        self.max_connections_spin = QSpinBox()
        self.max_connections_spin.setRange(1, 50)
        self.max_connections_spin.setValue(10)
        multiplex_layout.addRow("Max Connections per Pool:", self.max_connections_spin)

        self.connection_timeout_spin = QSpinBox()
        self.connection_timeout_spin.setRange(5, 300)
        self.connection_timeout_spin.setValue(30)
        self.connection_timeout_spin.setSuffix(" seconds")
        multiplex_layout.addRow("Connection Timeout:", self.connection_timeout_spin)

        self.keepalive_interval_spin = QSpinBox()
        self.keepalive_interval_spin.setRange(10, 600)
        self.keepalive_interval_spin.setValue(60)
        self.keepalive_interval_spin.setSuffix(" seconds")
        multiplex_layout.addRow("Keep-alive Interval:", self.keepalive_interval_spin)

        self.retry_attempts_spin = QSpinBox()
        self.retry_attempts_spin.setRange(1, 10)
        self.retry_attempts_spin.setValue(3)
        multiplex_layout.addRow("Retry Attempts:", self.retry_attempts_spin)

        self.enable_compression_checkbox = QCheckBox("Enable SSH Compression")
        self.enable_compression_checkbox.setChecked(True)
        multiplex_layout.addRow("Compression:", self.enable_compression_checkbox)

        self.enable_agent_forwarding_checkbox = QCheckBox("Enable Agent Forwarding")
        self.enable_agent_forwarding_checkbox.setChecked(True)
        multiplex_layout.addRow("Agent Forwarding:", self.enable_agent_forwarding_checkbox)

        layout.addLayout(multiplex_layout)

        # SSH options
        ssh_options_label = QLabel("SSH Options")
        ssh_options_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(ssh_options_label)

        self.ssh_options_text = QTextEdit()
        self.ssh_options_text.setMaximumHeight(100)
        self.ssh_options_text.setPlaceholderText("StrictHostKeyChecking=no\nServerAliveInterval=60\nTCPKeepAlive=yes")
        layout.addWidget(self.ssh_options_text)

        # Save/Load configs
        config_buttons_layout = QHBoxLayout()

        save_config_btn = QPushButton("💾 Save Configuration")
        save_config_btn.clicked.connect(self.save_configuration)
        config_buttons_layout.addWidget(save_config_btn)

        load_config_btn = QPushButton("📂 Load Configuration")
        load_config_btn.clicked.connect(self.load_configuration)
        config_buttons_layout.addWidget(load_config_btn)

        reset_config_btn = QPushButton("🔄 Reset to Defaults")
        reset_config_btn.clicked.connect(self.reset_configuration)
        config_buttons_layout.addWidget(reset_config_btn)

        layout.addLayout(config_buttons_layout)

        layout.addStretch()

        return widget

    def create_monitoring_tab(self):
        """Create connection monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Monitoring controls
        monitoring_controls = QHBoxLayout()

        self.monitoring_enabled_checkbox = QCheckBox("Enable Monitoring")
        self.monitoring_enabled_checkbox.setChecked(True)
        self.monitoring_enabled_checkbox.toggled.connect(self.toggle_monitoring)
        monitoring_controls.addWidget(self.monitoring_enabled_checkbox)

        monitoring_controls.addStretch()

        refresh_monitoring_btn = QPushButton("🔄 Refresh")
        refresh_monitoring_btn.clicked.connect(self.refresh_monitoring)
        monitoring_controls.addWidget(refresh_monitoring_btn)

        export_logs_btn = QPushButton("📊 Export Logs")
        export_logs_btn.clicked.connect(self.export_monitoring_logs)
        monitoring_controls.addWidget(export_logs_btn)

        layout.addLayout(monitoring_controls)

        # Active connections tree
        active_label = QLabel("Active Connections")
        active_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(active_label)

        self.active_connections_tree = QTreeWidget()
        self.active_connections_tree.setHeaderLabels([
            "Host", "Pool", "Status", "Uptime", "Data Sent", "Data Received", "Last Activity"
        ])
        self.active_connections_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.active_connections_tree)

        # Connection statistics
        stats_label = QLabel("Connection Statistics")
        stats_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(stats_label)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        layout.addWidget(self.stats_text)

        self.refresh_monitoring()

        return widget

    def create_connection_pool(self):
        """Create a new connection pool"""
        dialog = ConnectionPoolDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            pool_data = dialog.get_pool_data()
            pool_name = pool_data['name']

            if pool_name in self.connection_pools:
                QMessageBox.warning(self, "Error", "Pool name already exists")
                return

            self.connection_pools[pool_name] = {
                'connections': pool_data['connections'],
                'max_connections': pool_data.get('max_connections', 5),
                'active_connections': [],
                'created': datetime.now(),
                'last_used': None,
                'auto_reconnect': pool_data.get('auto_reconnect', True)
            }

            self.refresh_pools_display()
            QMessageBox.information(self, "Success", f"Connection pool '{pool_name}' created")

    def connect_pool(self):
        """Connect all connections in selected pool"""
        current_item = self.pools_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No pool selected")
            return

        pool_name = current_item.text(0)
        if pool_name not in self.connection_pools:
            QMessageBox.warning(self, "Error", "Pool not found")
            return

        pool_data = self.connection_pools[pool_name]

        # Start connection threads
        self.connect_pool_async(pool_name, pool_data)

    def connect_pool_async(self, pool_name, pool_data):
        """Connect pool connections asynchronously"""
        def connect_worker():
            connected_count = 0
            for connection_config in pool_data['connections']:
                try:
                    if self.connect_single_host(connection_config, pool_name):
                        connected_count += 1
                except Exception as e:
                    logger.error(f"Failed to connect to {connection_config.get('host', 'unknown')}: {e}")

            pool_data['last_used'] = datetime.now()
            self.refresh_pools_display()

            if connected_count > 0:
                QMessageBox.information(
                    self, "Pool Connected",
                    f"Connected {connected_count}/{len(pool_data['connections'])} hosts in pool '{pool_name}'"
                )
            else:
                QMessageBox.warning(self, "Pool Connection Failed", f"Failed to connect any hosts in pool '{pool_name}'")

        thread = threading.Thread(target=connect_worker, daemon=True)
        thread.start()

    def connect_single_host(self, connection_config, pool_name=None):
        """Connect to a single host"""
        try:
            host = connection_config['host']
            username = connection_config['username']

            # Handle jump host if specified
            if connection_config.get('jump_host'):
                ssh_client = self.connect_via_jump_host_direct(connection_config)
            else:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Configure connection parameters
                connect_params = {
                    'hostname': host,
                    'username': username,
                    'timeout': self.connection_timeout_spin.value()
                }

                # Authentication
                if connection_config.get('private_key'):
                    try:
                        private_key = paramiko.RSAKey.from_private_key_file(connection_config['private_key'])
                        connect_params['pkey'] = private_key
                    except:
                        # Try other key types
                        for key_class in [paramiko.DSSKey, paramiko.ECDSAKey, paramiko.Ed25519Key]:
                            try:
                                private_key = key_class.from_private_key_file(connection_config['private_key'])
                                connect_params['pkey'] = private_key
                                break
                            except:
                                continue
                elif connection_config.get('password'):
                    connect_params['password'] = connection_config['password']

                # Advanced options
                if self.enable_compression_checkbox.isChecked():
                    connect_params['compress'] = True

                ssh_client.connect(**connect_params)

            # Store connection
            connection_id = f"{host}_{username}_{int(time.time())}"
            self.active_connections[connection_id] = {
                'ssh_client': ssh_client,
                'host': host,
                'username': username,
                'pool': pool_name,
                'connected_at': datetime.now(),
                'bytes_sent': 0,
                'bytes_received': 0,
                'last_activity': datetime.now()
            }

            # Add to pool's active connections
            if pool_name and pool_name in self.connection_pools:
                self.connection_pools[pool_name]['active_connections'].append(connection_id)

            self.connection_established.emit(host, connection_config)
            return True

        except Exception as e:
            self.connection_failed.emit(connection_config.get('host', 'unknown'), str(e))
            logger.error(f"Connection failed: {e}")
            return False

    def connect_via_jump_host_direct(self, connection_config):
        """Connect via jump host directly"""
        jump_host_config = connection_config['jump_host']
        target_host = connection_config['host']
        target_username = connection_config['username']

        # Connect to jump host first
        jump_ssh = paramiko.SSHClient()
        jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        jump_connect_params = {
            'hostname': jump_host_config['host'],
            'username': jump_host_config['username'],
            'timeout': self.connection_timeout_spin.value()
        }

        if jump_host_config.get('private_key'):
            private_key = paramiko.RSAKey.from_private_key_file(jump_host_config['private_key'])
            jump_connect_params['pkey'] = private_key
        elif jump_host_config.get('password'):
            jump_connect_params['password'] = jump_host_config['password']

        jump_ssh.connect(**jump_connect_params)

        # Create transport through jump host
        jump_transport = jump_ssh.get_transport()
        dest_addr = (target_host, connection_config.get('port', 22))
        local_addr = ('127.0.0.1', 0)
        channel = jump_transport.open_channel('direct-tcpip', dest_addr, local_addr)

        # Connect to target through channel
        target_ssh = paramiko.SSHClient()
        target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        target_connect_params = {
            'username': target_username,
            'sock': channel,
            'timeout': self.connection_timeout_spin.value()
        }

        if connection_config.get('private_key'):
            private_key = paramiko.RSAKey.from_private_key_file(connection_config['private_key'])
            target_connect_params['pkey'] = private_key
        elif connection_config.get('password'):
            target_connect_params['password'] = connection_config['password']

        target_ssh.connect(**target_connect_params)

        return target_ssh

    def add_jump_host(self):
        """Add a new jump host configuration"""
        dialog = JumpHostDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            jump_host_data = dialog.get_jump_host_data()
            jump_host_name = jump_host_data['name']

            self.jump_hosts[jump_host_name] = jump_host_data
            self.refresh_jump_hosts_display()
            QMessageBox.information(self, "Success", f"Jump host '{jump_host_name}' added")

    def connect_via_jump_host(self):
        """Connect to target via selected jump host"""
        current_item = self.jump_hosts_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No jump host selected")
            return

        jump_host_name = current_item.text(0)
        if jump_host_name not in self.jump_hosts:
            QMessageBox.warning(self, "Error", "Jump host not found")
            return

        # Get target host details
        target_host, ok = QInputDialog.getText(self, "Target Host", "Enter target hostname:")
        if not ok or not target_host:
            return

        target_username, ok = QInputDialog.getText(self, "Target Username", "Enter target username:")
        if not ok or not target_username:
            return

        # Create connection config
        connection_config = {
            'host': target_host,
            'username': target_username,
            'jump_host': self.jump_hosts[jump_host_name]
        }

        # Connect
        if self.connect_single_host(connection_config):
            QMessageBox.information(self, "Success", f"Connected to {target_host} via {jump_host_name}")
        else:
            QMessageBox.warning(self, "Error", "Failed to connect via jump host")

    def test_jump_host(self):
        """Test connection to selected jump host"""
        current_item = self.jump_hosts_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No jump host selected")
            return

        jump_host_name = current_item.text(0)
        if jump_host_name not in self.jump_hosts:
            QMessageBox.warning(self, "Error", "Jump host not found")
            return

        jump_host_config = self.jump_hosts[jump_host_name]

        def test_worker():
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                start_time = time.time()

                connect_params = {
                    'hostname': jump_host_config['host'],
                    'username': jump_host_config['username'],
                    'timeout': 10
                }

                if jump_host_config.get('private_key'):
                    private_key = paramiko.RSAKey.from_private_key_file(jump_host_config['private_key'])
                    connect_params['pkey'] = private_key
                elif jump_host_config.get('password'):
                    connect_params['password'] = jump_host_config['password']

                ssh.connect(**connect_params)

                # Test command execution
                stdin, stdout, stderr = ssh.exec_command('echo "Jump host test successful"')
                result = stdout.read().decode().strip()

                latency = (time.time() - start_time) * 1000  # ms

                ssh.close()

                QMessageBox.information(
                    self, "Jump Host Test",
                    f"Jump host '{jump_host_name}' test successful!\n"
                    f"Latency: {latency:.1f}ms\n"
                    f"Response: {result}"
                )

            except Exception as e:
                QMessageBox.critical(
                    self, "Jump Host Test",
                    f"Jump host '{jump_host_name}' test failed:\n{str(e)}"
                )

        thread = threading.Thread(target=test_worker, daemon=True)
        thread.start()

    def monitor_connections(self):
        """Monitor active connections"""
        if not self.monitoring_enabled_checkbox.isChecked():
            return

        # Check connection health
        dead_connections = []
        for conn_id, conn_info in self.active_connections.items():
            try:
                ssh_client = conn_info['ssh_client']
                transport = ssh_client.get_transport()

                if not transport or not transport.is_active():
                    dead_connections.append(conn_id)
                else:
                    # Update last activity
                    conn_info['last_activity'] = datetime.now()

            except Exception as e:
                logger.error(f"Connection monitoring error for {conn_id}: {e}")
                dead_connections.append(conn_id)

        # Remove dead connections
        for conn_id in dead_connections:
            self.remove_dead_connection(conn_id)

        # Update displays
        self.refresh_monitoring()

    def remove_dead_connection(self, connection_id):
        """Remove a dead connection"""
        if connection_id in self.active_connections:
            conn_info = self.active_connections[connection_id]
            pool_name = conn_info.get('pool')

            # Remove from pool's active connections
            if pool_name and pool_name in self.connection_pools:
                pool_data = self.connection_pools[pool_name]
                if connection_id in pool_data['active_connections']:
                    pool_data['active_connections'].remove(connection_id)

            # Close SSH client
            try:
                conn_info['ssh_client'].close()
            except:
                pass

            del self.active_connections[connection_id]

    def refresh_pools_display(self):
        """Refresh connection pools display"""
        self.pools_tree.clear()

        for pool_name, pool_data in self.connection_pools.items():
            total_connections = len(pool_data['connections'])
            active_connections = len(pool_data['active_connections'])
            status = "Connected" if active_connections > 0 else "Disconnected"
            last_used = pool_data.get('last_used')
            last_used_str = last_used.strftime('%Y-%m-%d %H:%M') if last_used else "Never"

            item = QTreeWidgetItem([
                pool_name,
                str(total_connections),
                str(active_connections),
                status,
                last_used_str
            ])

            # Add connection details as children
            for i, conn_config in enumerate(pool_data['connections']):
                child = QTreeWidgetItem([
                    f"{conn_config['host']} ({conn_config['username']})",
                    "", "", "", ""
                ])
                item.addChild(child)

            self.pools_tree.addTopLevelItem(item)

    def refresh_jump_hosts_display(self):
        """Refresh jump hosts display"""
        self.jump_hosts_tree.clear()

        for jump_host_name, jump_host_data in self.jump_hosts.items():
            target_hosts_count = len(jump_host_data.get('target_hosts', []))
            status = "Available"  # Would check actual status
            latency = "N/A"  # Would measure actual latency
            last_used = "Never"  # Would track usage

            item = QTreeWidgetItem([
                jump_host_name,
                str(target_hosts_count),
                status,
                latency,
                last_used
            ])

            self.jump_hosts_tree.addTopLevelItem(item)

    def refresh_monitoring(self):
        """Refresh monitoring display"""
        self.active_connections_tree.clear()

        for conn_id, conn_info in self.active_connections.items():
            host = conn_info['host']
            pool = conn_info.get('pool', 'None')
            status = "Connected"

            uptime = datetime.now() - conn_info['connected_at']
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds

            bytes_sent = conn_info.get('bytes_sent', 0)
            bytes_received = conn_info.get('bytes_received', 0)

            last_activity = conn_info['last_activity']
            last_activity_str = last_activity.strftime('%H:%M:%S')

            item = QTreeWidgetItem([
                host,
                pool,
                status,
                uptime_str,
                f"{bytes_sent} B",
                f"{bytes_received} B",
                last_activity_str
            ])

            self.active_connections_tree.addTopLevelItem(item)

        # Update statistics
        self.update_connection_statistics()

    def update_connection_statistics(self):
        """Update connection statistics"""
        stats = []
        stats.append(f"Total Active Connections: {len(self.active_connections)}")
        stats.append(f"Total Pools: {len(self.connection_pools)}")
        stats.append(f"Total Jump Hosts: {len(self.jump_hosts)}")

        # Pool statistics
        total_pool_connections = sum(len(pool['active_connections']) for pool in self.connection_pools.values())
        stats.append(f"Pooled Connections: {total_pool_connections}")

        # Connection age statistics
        if self.active_connections:
            ages = [(datetime.now() - conn['connected_at']).total_seconds()
                   for conn in self.active_connections.values()]
            avg_age = sum(ages) / len(ages)
            stats.append(f"Average Connection Age: {avg_age/3600:.1f} hours")

        self.stats_text.setText('\n'.join(stats))

    def save_configuration(self):
        """Save current configuration"""
        # Implementation would save to file
        QMessageBox.information(self, "Save", "Configuration saved successfully")

    def load_configuration(self):
        """Load configuration from file"""
        # Implementation would load from file
        QMessageBox.information(self, "Load", "Configuration loaded successfully")

    def load_configurations(self):
        """Load saved configurations on startup"""
        # Implementation would load saved configs
        pass

    # Placeholder methods for other operations
    def disconnect_pool(self):
        QMessageBox.information(self, "Disconnect", "Pool disconnection feature")

    def edit_selected_pool(self):
        QMessageBox.information(self, "Edit", "Edit pool feature")

    def clone_selected_pool(self):
        QMessageBox.information(self, "Clone", "Clone pool feature")

    def delete_selected_pool(self):
        QMessageBox.information(self, "Delete", "Delete pool feature")

    def edit_jump_host(self):
        QMessageBox.information(self, "Edit", "Edit jump host feature")

    def create_jump_chain(self):
        QMessageBox.information(self, "Chain", "Jump host chaining feature")

    def delete_jump_host(self):
        QMessageBox.information(self, "Delete", "Delete jump host feature")

    def reset_configuration(self):
        QMessageBox.information(self, "Reset", "Configuration reset feature")

    def toggle_monitoring(self, enabled):
        if not enabled:
            self.monitor_timer.stop()
        else:
            self.monitor_timer.start(5000)

    def export_monitoring_logs(self):
        QMessageBox.information(self, "Export", "Export logs feature")


class ConnectionPoolDialog(QDialog):
    """Dialog for creating/editing connection pools"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Connection Pool")
        self.resize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Pool name
        form_layout = QFormLayout()
        self.pool_name_edit = QLineEdit()
        form_layout.addRow("Pool Name:", self.pool_name_edit)

        self.max_connections_spin = QSpinBox()
        self.max_connections_spin.setRange(1, 50)
        self.max_connections_spin.setValue(5)
        form_layout.addRow("Max Connections:", self.max_connections_spin)

        layout.addLayout(form_layout)

        # Connections list
        connections_label = QLabel("Connections:")
        layout.addWidget(connections_label)

        self.connections_tree = QTreeWidget()
        self.connections_tree.setHeaderLabels(["Host", "Username", "Auth Method"])
        layout.addWidget(self.connections_tree)

        # Add/Remove connections
        conn_buttons = QHBoxLayout()
        add_conn_btn = QPushButton("Add Connection")
        add_conn_btn.clicked.connect(self.add_connection)
        conn_buttons.addWidget(add_conn_btn)

        remove_conn_btn = QPushButton("Remove Connection")
        remove_conn_btn.clicked.connect(self.remove_connection)
        conn_buttons.addWidget(remove_conn_btn)

        layout.addLayout(conn_buttons)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_connection(self):
        """Add a connection to the pool"""
        # Simple implementation - would be more sophisticated
        host, ok = QInputDialog.getText(self, "Host", "Enter hostname:")
        if not ok or not host:
            return

        username, ok = QInputDialog.getText(self, "Username", "Enter username:")
        if not ok or not username:
            return

        item = QTreeWidgetItem([host, username, "Key/Password"])
        self.connections_tree.addTopLevelItem(item)

    def remove_connection(self):
        """Remove selected connection"""
        current = self.connections_tree.currentItem()
        if current:
            root = self.connections_tree.invisibleRootItem()
            root.removeChild(current)

    def get_pool_data(self):
        """Get pool data from dialog"""
        connections = []
        root = self.connections_tree.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            connections.append({
                'host': child.text(0),
                'username': child.text(1),
                'auth_method': child.text(2)
            })

        return {
            'name': self.pool_name_edit.text(),
            'max_connections': self.max_connections_spin.value(),
            'connections': connections
        }


class JumpHostDialog(QDialog):
    """Dialog for creating/editing jump hosts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Jump Host")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)

        self.host_edit = QLineEdit()
        form_layout.addRow("Hostname:", self.host_edit)

        self.username_edit = QLineEdit()
        form_layout.addRow("Username:", self.username_edit)

        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["Private Key", "Password"])
        form_layout.addRow("Authentication:", self.auth_combo)

        self.key_path_edit = QLineEdit()
        form_layout.addRow("Key Path:", self.key_path_edit)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_jump_host_data(self):
        """Get jump host data from dialog"""
        return {
            'name': self.name_edit.text(),
            'host': self.host_edit.text(),
            'username': self.username_edit.text(),
            'auth_method': self.auth_combo.currentText(),
            'private_key': self.key_path_edit.text() if self.auth_combo.currentText() == "Private Key" else None,
            'target_hosts': []
        }