"""
Session Management System for JETSSH
Provides session persistence, restoration, and management
"""

import json
import os
import logging
import hashlib
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
                             QPushButton, QInputDialog, QMessageBox, QDialog,
                             QLineEdit, QTextEdit, QCheckBox, QComboBox, QTreeWidget,
                             QTreeWidgetItem, QSplitter, QTabWidget, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class SessionManager(QWidget):
    """Session Manager with persistence and restoration"""

    session_restored = pyqtSignal(dict)  # session_data
    session_saved = pyqtSignal(str)      # session_name

    def __init__(self, ssh_client_app):
        super().__init__()
        self.ssh_client_app = ssh_client_app
        self.sessions_file = "jetssh_sessions.json"
        self.workspaces_file = "jetssh_workspaces.json"
        self.session_recordings_dir = "session_recordings"
        self.sessions = {}
        self.workspaces = {}
        self.current_workspace = None
        self.auto_save_enabled = True
        self.auto_save_interval = 5  # minutes

        # Create recordings directory
        os.makedirs(self.session_recordings_dir, exist_ok=True)

        self.setup_ui()
        self.load_sessions()
        self.load_workspaces()
        self.setup_auto_save()

    def setup_ui(self):
        """Setup the session manager UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Session Manager")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #dcdcdc;")
        layout.addWidget(title)

        # Tabs for different management areas
        tab_widget = QTabWidget()

        # Sessions tab
        sessions_tab = self.create_sessions_tab()
        tab_widget.addTab(sessions_tab, "Sessions")

        # Workspaces tab
        workspaces_tab = self.create_workspaces_tab()
        tab_widget.addTab(workspaces_tab, "Workspaces")

        # Recordings tab
        recordings_tab = self.create_recordings_tab()
        tab_widget.addTab(recordings_tab, "Recordings")

        # Settings tab
        settings_tab = self.create_settings_tab()
        tab_widget.addTab(settings_tab, "Settings")

        layout.addWidget(tab_widget)

    def create_sessions_tab(self):
        """Create sessions management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Quick actions
        quick_layout = QHBoxLayout()

        save_current_btn = QPushButton("💾 Save Current Session")
        save_current_btn.clicked.connect(self.save_current_session)
        save_current_btn.setStyleSheet("""
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
        quick_layout.addWidget(save_current_btn)

        restore_btn = QPushButton("🔄 Restore Session")
        restore_btn.clicked.connect(self.restore_selected_session)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        quick_layout.addWidget(restore_btn)

        quick_layout.addStretch()

        layout.addLayout(quick_layout)

        # Sessions list
        sessions_label = QLabel("Saved Sessions")
        sessions_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(sessions_label)

        self.sessions_tree = QTreeWidget()
        self.sessions_tree.setHeaderLabels([
            "Name", "Connections", "Created", "Last Used", "Size"
        ])
        self.sessions_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.sessions_tree)

        # Session operations
        session_ops_layout = QHBoxLayout()

        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self.rename_session)
        session_ops_layout.addWidget(rename_btn)

        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.clicked.connect(self.duplicate_session)
        session_ops_layout.addWidget(duplicate_btn)

        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_session)
        session_ops_layout.addWidget(export_btn)

        import_btn = QPushButton("Import")
        import_btn.clicked.connect(self.import_session)
        session_ops_layout.addWidget(import_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_session)
        delete_btn.setStyleSheet("""
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
        session_ops_layout.addWidget(delete_btn)

        layout.addLayout(session_ops_layout)

        return widget

    def create_workspaces_tab(self):
        """Create workspaces management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Current workspace
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current Workspace:"))

        self.current_workspace_label = QLabel("Default")
        self.current_workspace_label.setStyleSheet("font-weight: bold; color: #00ffff;")
        current_layout.addWidget(self.current_workspace_label)

        current_layout.addStretch()

        save_workspace_btn = QPushButton("💾 Save Workspace")
        save_workspace_btn.clicked.connect(self.save_current_workspace)
        current_layout.addWidget(save_workspace_btn)

        layout.addLayout(current_layout)

        # Workspaces list
        workspaces_label = QLabel("Saved Workspaces")
        workspaces_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(workspaces_label)

        self.workspaces_tree = QTreeWidget()
        self.workspaces_tree.setHeaderLabels([
            "Name", "Sessions", "Layout", "Created", "Description"
        ])
        self.workspaces_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.workspaces_tree)

        # Workspace operations
        workspace_ops_layout = QHBoxLayout()

        load_workspace_btn = QPushButton("Load Workspace")
        load_workspace_btn.clicked.connect(self.load_selected_workspace)
        workspace_ops_layout.addWidget(load_workspace_btn)

        rename_workspace_btn = QPushButton("Rename")
        rename_workspace_btn.clicked.connect(self.rename_workspace)
        workspace_ops_layout.addWidget(rename_workspace_btn)

        delete_workspace_btn = QPushButton("Delete")
        delete_workspace_btn.clicked.connect(self.delete_workspace)
        delete_workspace_btn.setStyleSheet("""
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
        workspace_ops_layout.addWidget(delete_workspace_btn)

        layout.addLayout(workspace_ops_layout)

        return widget

    def create_recordings_tab(self):
        """Create session recordings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Recording controls
        recording_layout = QHBoxLayout()

        self.recording_status = QLabel("⏹ Not Recording")
        self.recording_status.setStyleSheet("font-weight: bold;")
        recording_layout.addWidget(self.recording_status)

        recording_layout.addStretch()

        self.start_recording_btn = QPushButton("🔴 Start Recording")
        self.start_recording_btn.clicked.connect(self.start_recording)
        recording_layout.addWidget(self.start_recording_btn)

        self.stop_recording_btn = QPushButton("⏹ Stop Recording")
        self.stop_recording_btn.clicked.connect(self.stop_recording)
        self.stop_recording_btn.setEnabled(False)
        recording_layout.addWidget(self.stop_recording_btn)

        layout.addLayout(recording_layout)

        # Recordings list
        recordings_label = QLabel("Session Recordings")
        recordings_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(recordings_label)

        self.recordings_tree = QTreeWidget()
        self.recordings_tree.setHeaderLabels([
            "Name", "Duration", "Size", "Date", "Session"
        ])
        self.recordings_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.recordings_tree)

        # Recording operations
        recording_ops_layout = QHBoxLayout()

        play_btn = QPushButton("▶ Play")
        play_btn.clicked.connect(self.play_recording)
        recording_ops_layout.addWidget(play_btn)

        export_recording_btn = QPushButton("Export")
        export_recording_btn.clicked.connect(self.export_recording)
        recording_ops_layout.addWidget(export_recording_btn)

        delete_recording_btn = QPushButton("Delete")
        delete_recording_btn.clicked.connect(self.delete_recording)
        delete_recording_btn.setStyleSheet("""
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
        recording_ops_layout.addWidget(delete_recording_btn)

        layout.addLayout(recording_ops_layout)

        self.refresh_recordings()

        return widget

    def create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Auto-save settings
        autosave_group = QLabel("Auto-Save Settings")
        autosave_group.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(autosave_group)

        self.auto_save_checkbox = QCheckBox("Enable auto-save")
        self.auto_save_checkbox.setChecked(self.auto_save_enabled)
        self.auto_save_checkbox.toggled.connect(self.toggle_auto_save)
        layout.addWidget(self.auto_save_checkbox)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Auto-save interval (minutes):"))
        self.interval_input = QLineEdit(str(self.auto_save_interval))
        self.interval_input.textChanged.connect(self.update_auto_save_interval)
        interval_layout.addWidget(self.interval_input)
        layout.addLayout(interval_layout)

        # Session retention settings
        retention_group = QLabel("Session Retention")
        retention_group.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(retention_group)

        cleanup_layout = QHBoxLayout()
        cleanup_btn = QPushButton("Clean Old Sessions")
        cleanup_btn.clicked.connect(self.cleanup_old_sessions)
        cleanup_layout.addWidget(cleanup_btn)

        cleanup_recordings_btn = QPushButton("Clean Old Recordings")
        cleanup_recordings_btn.clicked.connect(self.cleanup_old_recordings)
        cleanup_layout.addWidget(cleanup_recordings_btn)

        layout.addLayout(cleanup_layout)

        # Session statistics
        stats_group = QLabel("Statistics")
        stats_group.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(stats_group)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        layout.addWidget(self.stats_text)

        self.update_statistics()

        layout.addStretch()

        return widget

    def setup_auto_save(self):
        """Setup auto-save timer"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_session)
        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval * 60 * 1000)

    def save_current_session(self):
        """Save current session state"""
        name, ok = QInputDialog.getText(self, "Save Session", "Session name:")
        if not ok or not name:
            return

        try:
            session_data = self.capture_current_session()
            session_data['name'] = name
            session_data['created'] = datetime.now().isoformat()
            session_data['last_used'] = datetime.now().isoformat()

            self.sessions[name] = session_data
            self.save_sessions()
            self.refresh_sessions_list()

            QMessageBox.information(self, "Success", f"Session '{name}' saved successfully")
            self.session_saved.emit(name)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save session: {str(e)}")
            logger.error(f"Session save error: {e}")

    def capture_current_session(self):
        """Capture current application state"""
        session_data = {
            'connections': [],
            'active_tabs': [],
            'tunnels': [],
            'commands_history': getattr(self.ssh_client_app, 'command_history', []),
            'window_geometry': {
                'width': self.ssh_client_app.width(),
                'height': self.ssh_client_app.height(),
                'x': self.ssh_client_app.x(),
                'y': self.ssh_client_app.y()
            },
            'predefined_commands': [],
            'timestamp': datetime.now().isoformat()
        }

        # Capture connections
        for connection in self.ssh_client_app.connections:
            session_data['connections'].append({
                'host': connection['host'],
                'user': connection['user'],
                'private_key': connection.get('private_key', ''),
                'connected': connection['host'] in self.ssh_client_app.ssh_clients
            })

        # Capture active tabs
        tab_widget = self.ssh_client_app.tab_widget
        for i in range(tab_widget.count()):
            tab_text = tab_widget.tabText(i)
            is_current = (i == tab_widget.currentIndex())

            session_data['active_tabs'].append({
                'title': tab_text,
                'index': i,
                'is_current': is_current,
                'type': 'ssh' if '(' in tab_text else 'utility'
            })

        # Capture tunnels if tunnel manager exists
        if hasattr(self.ssh_client_app, 'tunnel_manager'):
            tunnel_manager = self.ssh_client_app.tunnel_manager
            for tunnel_id, tunnel_info in tunnel_manager.active_tunnels.items():
                session_data['tunnels'].append({
                    'type': tunnel_info['type'],
                    'local_host': tunnel_info['local_host'],
                    'local_port': tunnel_info['local_port'],
                    'remote_host': tunnel_info['remote_host'],
                    'remote_port': tunnel_info['remote_port'],
                    'ssh_host': tunnel_info['ssh_host']
                })

        # Capture predefined commands
        try:
            with open('commands.json', 'r') as f:
                commands_data = json.load(f)
                session_data['predefined_commands'] = commands_data.get('commands', [])
        except:
            pass

        return session_data

    def restore_selected_session(self):
        """Restore the selected session"""
        current_item = self.sessions_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No session selected")
            return

        session_name = current_item.text(0)
        if session_name not in self.sessions:
            QMessageBox.warning(self, "Error", "Session not found")
            return

        reply = QMessageBox.question(
            self, "Restore Session",
            f"This will close current connections and restore '{session_name}'. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.restore_session(session_name)

    def restore_session(self, session_name):
        """Restore a session by name"""
        try:
            session_data = self.sessions[session_name]

            # Update last used
            session_data['last_used'] = datetime.now().isoformat()
            self.save_sessions()

            # Close current connections
            self.close_all_connections()

            # Restore window geometry
            if 'window_geometry' in session_data:
                geometry = session_data['window_geometry']
                self.ssh_client_app.resize(geometry['width'], geometry['height'])
                self.ssh_client_app.move(geometry['x'], geometry['y'])

            # Restore connections
            self.ssh_client_app.connections.clear()
            self.ssh_client_app.connection_list.clear()

            for conn_data in session_data.get('connections', []):
                connection = {
                    'host': conn_data['host'],
                    'user': conn_data['user'],
                    'private_key': conn_data.get('private_key', '')
                }
                self.ssh_client_app.connections.append(connection)

                display_key = "Using Key" if connection["private_key"] else "Using Password"
                self.ssh_client_app.connection_list.addItem(
                    f"{connection['host']} ({connection['user']}) [{display_key}]"
                )

                # Auto-connect if it was connected before
                if conn_data.get('connected', False):
                    # Add to queue for delayed connection
                    QTimer.singleShot(1000, lambda h=conn_data['host']: self.auto_connect(h))

            # Restore command history
            if 'commands_history' in session_data:
                self.ssh_client_app.command_history = session_data['commands_history']

            # Restore predefined commands
            if 'predefined_commands' in session_data:
                try:
                    commands_data = {'commands': session_data['predefined_commands']}
                    with open('commands.json', 'w') as f:
                        json.dump(commands_data, f, indent=2)
                except Exception as e:
                    logger.error(f"Failed to restore predefined commands: {e}")

            # Restore tunnels if tunnel manager exists
            if hasattr(self.ssh_client_app, 'tunnel_manager') and 'tunnels' in session_data:
                QTimer.singleShot(3000, lambda: self.restore_tunnels(session_data['tunnels']))

            self.session_restored.emit(session_data)
            QMessageBox.information(self, "Success", f"Session '{session_name}' restored successfully")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restore session: {str(e)}")
            logger.error(f"Session restore error: {e}")

    def auto_connect(self, host):
        """Auto-connect to a host (helper for session restoration)"""
        try:
            # Find the connection in the list
            for i, connection in enumerate(self.ssh_client_app.connections):
                if connection['host'] == host:
                    self.ssh_client_app.connection_list.setCurrentRow(i)
                    # Attempt to connect (this would need password/key handling)
                    # For now, just select it - user will need to manually connect
                    break
        except Exception as e:
            logger.error(f"Auto-connect error for {host}: {e}")

    def restore_tunnels(self, tunnels_data):
        """Restore SSH tunnels"""
        try:
            tunnel_manager = self.ssh_client_app.tunnel_manager
            for tunnel_data in tunnels_data:
                # Set tunnel manager form with saved data
                tunnel_manager.tunnel_type.setCurrentText(tunnel_data['type'])
                tunnel_manager.local_host.setText(tunnel_data['local_host'])
                tunnel_manager.local_port.setText(str(tunnel_data['local_port']))
                tunnel_manager.remote_host.setText(tunnel_data['remote_host'])
                if tunnel_data['remote_port']:
                    tunnel_manager.remote_port.setText(str(tunnel_data['remote_port']))

                # Find SSH connection
                for i in range(tunnel_manager.connection_combo.count()):
                    if tunnel_manager.connection_combo.itemText(i) == tunnel_data['ssh_host']:
                        tunnel_manager.connection_combo.setCurrentIndex(i)
                        break

                # Create tunnel
                tunnel_manager.create_tunnel()

        except Exception as e:
            logger.error(f"Tunnel restoration error: {e}")

    def close_all_connections(self):
        """Close all current SSH connections"""
        try:
            # Close all SSH clients
            for host, ssh_client in list(self.ssh_client_app.ssh_clients.items()):
                try:
                    ssh_client.close()
                except:
                    pass

            # Clear data structures
            self.ssh_client_app.ssh_clients.clear()
            self.ssh_client_app.channels.clear()
            self.ssh_client_app.output_boxes.clear()

            # Close all tabs except the first one (key generator)
            tab_widget = self.ssh_client_app.tab_widget
            while tab_widget.count() > 1:
                tab_widget.removeTab(1)

        except Exception as e:
            logger.error(f"Error closing connections: {e}")

    def auto_save_session(self):
        """Auto-save current session"""
        if not self.auto_save_enabled:
            return

        try:
            auto_save_name = f"AutoSave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session_data = self.capture_current_session()
            session_data['name'] = auto_save_name
            session_data['created'] = datetime.now().isoformat()
            session_data['last_used'] = datetime.now().isoformat()
            session_data['auto_save'] = True

            self.sessions[auto_save_name] = session_data
            self.save_sessions()

            # Keep only last 10 auto-saves
            auto_saves = [name for name in self.sessions.keys() if name.startswith("AutoSave_")]
            if len(auto_saves) > 10:
                auto_saves.sort()
                for old_save in auto_saves[:-10]:
                    del self.sessions[old_save]
                self.save_sessions()

            self.refresh_sessions_list()

        except Exception as e:
            logger.error(f"Auto-save error: {e}")

    def save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions file: {e}")

    def load_sessions(self):
        """Load sessions from file"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r') as f:
                    self.sessions = json.load(f)
                self.refresh_sessions_list()
        except Exception as e:
            logger.error(f"Failed to load sessions file: {e}")

    def refresh_sessions_list(self):
        """Refresh the sessions list display"""
        self.sessions_tree.clear()

        for session_name, session_data in self.sessions.items():
            connections_count = len(session_data.get('connections', []))
            created = session_data.get('created', 'Unknown')
            last_used = session_data.get('last_used', 'Never')
            size = len(json.dumps(session_data))

            # Format dates
            try:
                created_dt = datetime.fromisoformat(created)
                created_str = created_dt.strftime('%Y-%m-%d %H:%M')
            except:
                created_str = created

            try:
                last_used_dt = datetime.fromisoformat(last_used)
                last_used_str = last_used_dt.strftime('%Y-%m-%d %H:%M')
            except:
                last_used_str = last_used

            item = QTreeWidgetItem([
                session_name,
                str(connections_count),
                created_str,
                last_used_str,
                f"{size} bytes"
            ])

            # Mark auto-saves differently
            if session_data.get('auto_save', False):
                item.setBackground(0, Qt.darkGray)

            self.sessions_tree.addTopLevelItem(item)

    def save_current_workspace(self):
        """Save current workspace"""
        name, ok = QInputDialog.getText(self, "Save Workspace", "Workspace name:")
        if not ok or not name:
            return

        try:
            workspace_data = {
                'name': name,
                'created': datetime.now().isoformat(),
                'sessions': list(self.sessions.keys()),
                'layout': self.capture_layout(),
                'description': f"Workspace with {len(self.sessions)} sessions"
            }

            self.workspaces[name] = workspace_data
            self.save_workspaces()
            self.refresh_workspaces_list()

            QMessageBox.information(self, "Success", f"Workspace '{name}' saved successfully")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save workspace: {str(e)}")

    def capture_layout(self):
        """Capture current UI layout"""
        return {
            'window_size': [self.ssh_client_app.width(), self.ssh_client_app.height()],
            'window_position': [self.ssh_client_app.x(), self.ssh_client_app.y()],
            'tab_count': self.ssh_client_app.tab_widget.count(),
            'current_tab': self.ssh_client_app.tab_widget.currentIndex()
        }

    def save_workspaces(self):
        """Save workspaces to file"""
        try:
            with open(self.workspaces_file, 'w') as f:
                json.dump(self.workspaces, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workspaces file: {e}")

    def load_workspaces(self):
        """Load workspaces from file"""
        try:
            if os.path.exists(self.workspaces_file):
                with open(self.workspaces_file, 'r') as f:
                    self.workspaces = json.load(f)
                self.refresh_workspaces_list()
        except Exception as e:
            logger.error(f"Failed to load workspaces file: {e}")

    def refresh_workspaces_list(self):
        """Refresh workspaces list display"""
        self.workspaces_tree.clear()

        for workspace_name, workspace_data in self.workspaces.items():
            sessions_count = len(workspace_data.get('sessions', []))
            created = workspace_data.get('created', 'Unknown')
            description = workspace_data.get('description', '')
            layout_info = f"{workspace_data.get('layout', {}).get('tab_count', 0)} tabs"

            try:
                created_dt = datetime.fromisoformat(created)
                created_str = created_dt.strftime('%Y-%m-%d %H:%M')
            except:
                created_str = created

            item = QTreeWidgetItem([
                workspace_name,
                str(sessions_count),
                layout_info,
                created_str,
                description
            ])

            self.workspaces_tree.addTopLevelItem(item)

    def start_recording(self):
        """Start session recording"""
        name, ok = QInputDialog.getText(self, "Start Recording", "Recording name:")
        if not ok or not name:
            return

        try:
            # Implementation would start recording terminal output
            self.recording_status.setText("🔴 Recording")
            self.start_recording_btn.setEnabled(False)
            self.stop_recording_btn.setEnabled(True)

            QMessageBox.information(self, "Recording", f"Started recording '{name}'")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start recording: {str(e)}")

    def stop_recording(self):
        """Stop session recording"""
        try:
            # Implementation would stop recording
            self.recording_status.setText("⏹ Not Recording")
            self.start_recording_btn.setEnabled(True)
            self.stop_recording_btn.setEnabled(False)

            self.refresh_recordings()
            QMessageBox.information(self, "Recording", "Recording stopped")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop recording: {str(e)}")

    def refresh_recordings(self):
        """Refresh recordings list"""
        self.recordings_tree.clear()

        try:
            for filename in os.listdir(self.session_recordings_dir):
                if filename.endswith('.jsr'):  # JETSSH Session Recording
                    file_path = os.path.join(self.session_recordings_dir, filename)
                    stat_info = os.stat(file_path)

                    name = filename[:-4]  # Remove .jsr extension
                    size = f"{stat_info.st_size} bytes"
                    date = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M')

                    item = QTreeWidgetItem([
                        name,
                        "N/A",  # Duration would be calculated from recording
                        size,
                        date,
                        "Unknown"  # Session info would be stored in recording
                    ])

                    self.recordings_tree.addTopLevelItem(item)

        except Exception as e:
            logger.error(f"Failed to refresh recordings: {e}")

    def toggle_auto_save(self, enabled):
        """Toggle auto-save functionality"""
        self.auto_save_enabled = enabled
        if enabled:
            self.auto_save_timer.start(self.auto_save_interval * 60 * 1000)
        else:
            self.auto_save_timer.stop()

    def update_auto_save_interval(self, text):
        """Update auto-save interval"""
        try:
            interval = int(text)
            if interval > 0:
                self.auto_save_interval = interval
                if self.auto_save_enabled:
                    self.auto_save_timer.stop()
                    self.auto_save_timer.start(interval * 60 * 1000)
        except ValueError:
            pass

    def update_statistics(self):
        """Update session statistics"""
        try:
            stats = []
            stats.append(f"Total Sessions: {len(self.sessions)}")
            stats.append(f"Total Workspaces: {len(self.workspaces)}")

            # Count auto-saves
            auto_saves = sum(1 for s in self.sessions.values() if s.get('auto_save', False))
            stats.append(f"Auto-saves: {auto_saves}")

            # Recent activity
            recent_sessions = [
                s for s in self.sessions.values()
                if 'last_used' in s and
                   datetime.fromisoformat(s['last_used']) > datetime.now() - timedelta(days=7)
            ]
            stats.append(f"Used this week: {len(recent_sessions)}")

            # File sizes
            try:
                sessions_size = os.path.getsize(self.sessions_file) if os.path.exists(self.sessions_file) else 0
                workspaces_size = os.path.getsize(self.workspaces_file) if os.path.exists(self.workspaces_file) else 0
                stats.append(f"Data size: {sessions_size + workspaces_size} bytes")
            except:
                pass

            self.stats_text.setText('\n'.join(stats))

        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")

    def cleanup_old_sessions(self):
        """Clean up old sessions"""
        cutoff_date = datetime.now() - timedelta(days=30)
        old_sessions = []

        for name, session_data in self.sessions.items():
            if session_data.get('auto_save', False):
                try:
                    last_used = datetime.fromisoformat(session_data.get('last_used', ''))
                    if last_used < cutoff_date:
                        old_sessions.append(name)
                except:
                    old_sessions.append(name)

        if old_sessions:
            reply = QMessageBox.question(
                self, "Cleanup",
                f"Delete {len(old_sessions)} old auto-save sessions?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                for session_name in old_sessions:
                    del self.sessions[session_name]

                self.save_sessions()
                self.refresh_sessions_list()
                self.update_statistics()

                QMessageBox.information(self, "Cleanup", f"Deleted {len(old_sessions)} old sessions")
        else:
            QMessageBox.information(self, "Cleanup", "No old sessions to clean up")

    def cleanup_old_recordings(self):
        """Clean up old recordings"""
        QMessageBox.information(self, "Cleanup", "Recording cleanup feature coming soon!")

    # Placeholder methods for operations (would be implemented)
    def rename_session(self):
        """Rename selected session"""
        QMessageBox.information(self, "Rename", "Rename session feature coming soon!")

    def duplicate_session(self):
        """Duplicate selected session"""
        QMessageBox.information(self, "Duplicate", "Duplicate session feature coming soon!")

    def export_session(self):
        """Export selected session"""
        QMessageBox.information(self, "Export", "Export session feature coming soon!")

    def import_session(self):
        """Import session from file"""
        QMessageBox.information(self, "Import", "Import session feature coming soon!")

    def delete_session(self):
        """Delete selected session"""
        current_item = self.sessions_tree.currentItem()
        if not current_item:
            return

        session_name = current_item.text(0)
        reply = QMessageBox.question(
            self, "Delete Session",
            f"Delete session '{session_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.sessions[session_name]
            self.save_sessions()
            self.refresh_sessions_list()
            self.update_statistics()

    def load_selected_workspace(self):
        """Load selected workspace"""
        QMessageBox.information(self, "Load", "Load workspace feature coming soon!")

    def rename_workspace(self):
        """Rename selected workspace"""
        QMessageBox.information(self, "Rename", "Rename workspace feature coming soon!")

    def delete_workspace(self):
        """Delete selected workspace"""
        QMessageBox.information(self, "Delete", "Delete workspace feature coming soon!")

    def play_recording(self):
        """Play selected recording"""
        QMessageBox.information(self, "Play", "Play recording feature coming soon!")

    def export_recording(self):
        """Export selected recording"""
        QMessageBox.information(self, "Export", "Export recording feature coming soon!")

    def delete_recording(self):
        """Delete selected recording"""
        QMessageBox.information(self, "Delete", "Delete recording feature coming soon!")