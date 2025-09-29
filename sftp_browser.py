"""
Integrated SFTP File Browser for JETSSH
Provides dual-pane file management with drag-drop support
"""

import os
import stat
import logging
import threading
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
                             QTreeWidgetItem, QPushButton, QSplitter, QLineEdit,
                             QProgressBar, QMessageBox, QMenu, QAction, QFileDialog,
                             QInputDialog, QTextEdit, QTabWidget, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QThread
from PyQt5.QtGui import QIcon, QFont, QDrag, QPixmap, QPainter

logger = logging.getLogger(__name__)


class SFTPBrowser(QWidget):
    """Integrated SFTP File Browser with dual-pane interface"""

    file_transfer_progress = pyqtSignal(str, int)  # filename, percentage
    transfer_completed = pyqtSignal(str, bool)     # filename, success

    def __init__(self, ssh_client_app):
        super().__init__()
        self.ssh_client_app = ssh_client_app
        self.sftp_clients = {}
        self.current_transfers = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup the SFTP browser UI"""
        layout = QVBoxLayout(self)

        # Title and connection selector
        header_layout = QHBoxLayout()
        title = QLabel("SFTP File Browser")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #dcdcdc;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # SSH connection selector
        self.connection_selector = QLineEdit()
        self.connection_selector.setPlaceholderText("Select SSH connection...")
        self.connection_selector.setReadOnly(True)
        header_layout.addWidget(QLabel("Connection:"))
        header_layout.addWidget(self.connection_selector)

        connect_btn = QPushButton("Connect SFTP")
        connect_btn.clicked.connect(self.connect_sftp)
        header_layout.addWidget(connect_btn)

        layout.addLayout(header_layout)

        # Main splitter for dual-pane
        main_splitter = QSplitter(Qt.Horizontal)

        # Left pane - Local files
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)

        left_header = QLabel("Local Files")
        left_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        left_layout.addWidget(left_header)

        # Local path bar
        local_path_layout = QHBoxLayout()
        self.local_path = QLineEdit()
        self.local_path.setText(os.getcwd())
        self.local_path.returnPressed.connect(self.navigate_local)
        local_path_layout.addWidget(QLabel("Path:"))
        local_path_layout.addWidget(self.local_path)

        local_up_btn = QPushButton("Up")
        local_up_btn.clicked.connect(self.local_up)
        local_path_layout.addWidget(local_up_btn)

        local_home_btn = QPushButton("Home")
        local_home_btn.clicked.connect(self.local_home)
        local_path_layout.addWidget(local_home_btn)

        left_layout.addLayout(local_path_layout)

        # Local file tree
        self.local_tree = FileTreeWidget(self, "local")
        self.local_tree.setHeaderLabels(["Name", "Size", "Modified", "Type"])
        self.local_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        left_layout.addWidget(self.local_tree)

        # Local operations
        local_ops_layout = QHBoxLayout()
        local_new_folder_btn = QPushButton("New Folder")
        local_new_folder_btn.clicked.connect(self.create_local_folder)
        local_ops_layout.addWidget(local_new_folder_btn)

        local_delete_btn = QPushButton("Delete")
        local_delete_btn.clicked.connect(self.delete_local_item)
        local_ops_layout.addWidget(local_delete_btn)

        local_refresh_btn = QPushButton("Refresh")
        local_refresh_btn.clicked.connect(self.refresh_local)
        local_ops_layout.addWidget(local_refresh_btn)

        left_layout.addLayout(local_ops_layout)

        main_splitter.addWidget(left_pane)

        # Right pane - Remote files
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)

        right_header = QLabel("Remote Files (SFTP)")
        right_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        right_layout.addWidget(right_header)

        # Remote path bar
        remote_path_layout = QHBoxLayout()
        self.remote_path = QLineEdit()
        self.remote_path.setText("/")
        self.remote_path.returnPressed.connect(self.navigate_remote)
        remote_path_layout.addWidget(QLabel("Path:"))
        remote_path_layout.addWidget(self.remote_path)

        remote_up_btn = QPushButton("Up")
        remote_up_btn.clicked.connect(self.remote_up)
        remote_path_layout.addWidget(remote_up_btn)

        remote_home_btn = QPushButton("Home")
        remote_home_btn.clicked.connect(self.remote_home)
        remote_path_layout.addWidget(remote_home_btn)

        right_layout.addLayout(remote_path_layout)

        # Remote file tree
        self.remote_tree = FileTreeWidget(self, "remote")
        self.remote_tree.setHeaderLabels(["Name", "Size", "Modified", "Type", "Permissions"])
        self.remote_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        right_layout.addWidget(self.remote_tree)

        # Remote operations
        remote_ops_layout = QHBoxLayout()
        remote_new_folder_btn = QPushButton("New Folder")
        remote_new_folder_btn.clicked.connect(self.create_remote_folder)
        remote_ops_layout.addWidget(remote_new_folder_btn)

        remote_delete_btn = QPushButton("Delete")
        remote_delete_btn.clicked.connect(self.delete_remote_item)
        remote_ops_layout.addWidget(remote_delete_btn)

        remote_refresh_btn = QPushButton("Refresh")
        remote_refresh_btn.clicked.connect(self.refresh_remote)
        remote_ops_layout.addWidget(remote_refresh_btn)

        right_layout.addLayout(remote_ops_layout)

        main_splitter.addWidget(right_pane)
        layout.addWidget(main_splitter)

        # Transfer panel
        transfer_layout = QVBoxLayout()
        transfer_header = QLabel("File Transfers")
        transfer_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        transfer_layout.addWidget(transfer_header)

        # Transfer controls
        transfer_controls = QHBoxLayout()

        upload_btn = QPushButton("⬆ Upload Selected")
        upload_btn.clicked.connect(self.upload_selected)
        upload_btn.setStyleSheet("""
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
        transfer_controls.addWidget(upload_btn)

        download_btn = QPushButton("⬇ Download Selected")
        download_btn.clicked.connect(self.download_selected)
        download_btn.setStyleSheet("""
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
        transfer_controls.addWidget(download_btn)

        sync_btn = QPushButton("⚡ Sync Folders")
        sync_btn.clicked.connect(self.sync_folders)
        transfer_controls.addWidget(sync_btn)

        transfer_controls.addStretch()

        cancel_btn = QPushButton("Cancel Transfers")
        cancel_btn.clicked.connect(self.cancel_transfers)
        cancel_btn.setStyleSheet("""
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
        transfer_controls.addWidget(cancel_btn)

        transfer_layout.addLayout(transfer_controls)

        # Progress bars and transfer info
        self.progress_widget = QWidget()
        self.progress_layout = QVBoxLayout(self.progress_widget)
        transfer_layout.addWidget(self.progress_widget)

        layout.addLayout(transfer_layout)

        # Initialize local view
        self.refresh_local()

        # Setup timers
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds

    def get_current_ssh_connection(self):
        """Get the currently selected SSH connection"""
        current_tab = self.ssh_client_app.tab_widget.currentWidget()
        if current_tab:
            tab_text = self.ssh_client_app.tab_widget.tabText(
                self.ssh_client_app.tab_widget.currentIndex()
            )
            if '(' in tab_text:
                host = tab_text.split()[0]
                if host in self.ssh_client_app.ssh_clients:
                    return host
        return None

    def connect_sftp(self):
        """Connect to SFTP using current SSH connection"""
        host = self.get_current_ssh_connection()
        if not host:
            QMessageBox.warning(self, "Error", "No active SSH connection found")
            return

        try:
            if host not in self.sftp_clients:
                ssh_client = self.ssh_client_app.ssh_clients[host]
                sftp_client = ssh_client.open_sftp()
                self.sftp_clients[host] = sftp_client

            self.connection_selector.setText(host)
            self.refresh_remote()
            QMessageBox.information(self, "Success", f"Connected to SFTP on {host}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect SFTP: {str(e)}")
            logger.error(f"SFTP connection error: {e}")

    def navigate_local(self):
        """Navigate to local path"""
        path = self.local_path.text()
        if os.path.exists(path) and os.path.isdir(path):
            os.chdir(path)
            self.refresh_local()
        else:
            QMessageBox.warning(self, "Error", "Invalid local path")

    def navigate_remote(self):
        """Navigate to remote path"""
        if not self.get_sftp_client():
            return

        path = self.remote_path.text()
        try:
            sftp = self.get_sftp_client()
            sftp.chdir(path)
            self.refresh_remote()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot navigate to remote path: {str(e)}")

    def local_up(self):
        """Navigate up in local directory"""
        current = os.getcwd()
        parent = os.path.dirname(current)
        if parent != current:
            os.chdir(parent)
            self.local_path.setText(parent)
            self.refresh_local()

    def local_home(self):
        """Navigate to local home directory"""
        home = os.path.expanduser("~")
        os.chdir(home)
        self.local_path.setText(home)
        self.refresh_local()

    def remote_up(self):
        """Navigate up in remote directory"""
        if not self.get_sftp_client():
            return

        try:
            sftp = self.get_sftp_client()
            current = sftp.getcwd() or "/"
            parent = os.path.dirname(current)
            if parent != current:
                sftp.chdir(parent)
                self.remote_path.setText(parent)
                self.refresh_remote()
        except Exception as e:
            logger.error(f"Remote up navigation error: {e}")

    def remote_home(self):
        """Navigate to remote home directory"""
        if not self.get_sftp_client():
            return

        try:
            sftp = self.get_sftp_client()
            sftp.chdir(".")  # Go to default directory
            home_path = sftp.getcwd()
            self.remote_path.setText(home_path)
            self.refresh_remote()
        except Exception as e:
            logger.error(f"Remote home navigation error: {e}")

    def get_sftp_client(self):
        """Get current SFTP client"""
        host = self.connection_selector.text()
        return self.sftp_clients.get(host)

    def refresh_local(self):
        """Refresh local file listing"""
        self.local_tree.clear()
        current_path = os.getcwd()
        self.local_path.setText(current_path)

        try:
            for item_name in sorted(os.listdir(current_path)):
                item_path = os.path.join(current_path, item_name)
                try:
                    stat_info = os.stat(item_path)
                    size = stat_info.st_size if os.path.isfile(item_path) else ""
                    modified = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
                    item_type = "Folder" if os.path.isdir(item_path) else "File"

                    item = QTreeWidgetItem([
                        item_name,
                        self.format_size(size) if size else "",
                        modified,
                        item_type
                    ])

                    item.setData(0, Qt.UserRole, item_path)

                    if os.path.isdir(item_path):
                        item.setIcon(0, self.get_folder_icon())
                    else:
                        item.setIcon(0, self.get_file_icon())

                    self.local_tree.addTopLevelItem(item)

                except (OSError, PermissionError):
                    continue

        except PermissionError:
            QMessageBox.warning(self, "Error", "Permission denied accessing local directory")

    def refresh_remote(self):
        """Refresh remote file listing"""
        sftp = self.get_sftp_client()
        if not sftp:
            return

        self.remote_tree.clear()

        try:
            current_path = sftp.getcwd() or "/"
            self.remote_path.setText(current_path)

            for item_name in sorted(sftp.listdir(".")):
                try:
                    item_path = item_name
                    stat_info = sftp.stat(item_path)

                    is_dir = stat.S_ISDIR(stat_info.st_mode)
                    size = stat_info.st_size if not is_dir else ""
                    modified = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
                    item_type = "Folder" if is_dir else "File"
                    permissions = oct(stat_info.st_mode)[-3:]

                    item = QTreeWidgetItem([
                        item_name,
                        self.format_size(size) if size else "",
                        modified,
                        item_type,
                        permissions
                    ])

                    item.setData(0, Qt.UserRole, os.path.join(current_path, item_name))

                    if is_dir:
                        item.setIcon(0, self.get_folder_icon())
                    else:
                        item.setIcon(0, self.get_file_icon())

                    self.remote_tree.addTopLevelItem(item)

                except Exception as e:
                    logger.error(f"Error listing remote item {item_name}: {e}")
                    continue

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot list remote directory: {str(e)}")

    def format_size(self, size):
        """Format file size in human readable format"""
        if not size:
            return ""

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def get_folder_icon(self):
        """Get folder icon"""
        # Create a simple folder icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.fillRect(2, 6, 12, 8, Qt.yellow)
        painter.end()
        return QIcon(pixmap)

    def get_file_icon(self):
        """Get file icon"""
        # Create a simple file icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.fillRect(3, 2, 10, 12, Qt.white)
        painter.end()
        return QIcon(pixmap)

    def upload_selected(self):
        """Upload selected local files"""
        selected_items = self.local_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "No local files selected")
            return

        sftp = self.get_sftp_client()
        if not sftp:
            QMessageBox.warning(self, "Error", "No SFTP connection")
            return

        for item in selected_items:
            local_path = item.data(0, Qt.UserRole)
            filename = os.path.basename(local_path)

            if os.path.isfile(local_path):
                self.start_file_transfer(local_path, filename, "upload")

    def download_selected(self):
        """Download selected remote files"""
        selected_items = self.remote_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "No remote files selected")
            return

        sftp = self.get_sftp_client()
        if not sftp:
            QMessageBox.warning(self, "Error", "No SFTP connection")
            return

        for item in selected_items:
            if item.text(3) == "File":  # Only download files, not folders
                remote_path = item.data(0, Qt.UserRole)
                filename = os.path.basename(remote_path)
                local_path = os.path.join(os.getcwd(), filename)

                self.start_file_transfer(remote_path, local_path, "download")

    def start_file_transfer(self, source_path, dest_path, transfer_type):
        """Start a file transfer in a separate thread"""
        transfer_id = f"{transfer_type}_{source_path}_{datetime.now().timestamp()}"

        # Create progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_label = QLabel(f"{transfer_type.title()}: {os.path.basename(source_path)}")

        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress_bar)

        cancel_btn = QPushButton("Cancel")
        progress_layout.addWidget(cancel_btn)

        self.progress_layout.addWidget(progress_widget)

        # Store transfer info
        self.current_transfers[transfer_id] = {
            'progress_bar': progress_bar,
            'progress_widget': progress_widget,
            'cancelled': False
        }

        # Setup cancel button
        cancel_btn.clicked.connect(lambda: self.cancel_transfer(transfer_id))

        # Start transfer thread
        transfer_thread = FileTransferThread(
            self.get_sftp_client(), source_path, dest_path, transfer_type, transfer_id
        )
        transfer_thread.progress_updated.connect(self.update_transfer_progress)
        transfer_thread.transfer_completed.connect(self.transfer_finished)
        transfer_thread.start()

    def update_transfer_progress(self, transfer_id, percentage):
        """Update transfer progress"""
        if transfer_id in self.current_transfers:
            self.current_transfers[transfer_id]['progress_bar'].setValue(percentage)

    def transfer_finished(self, transfer_id, success, error_msg):
        """Handle transfer completion"""
        if transfer_id in self.current_transfers:
            transfer_info = self.current_transfers[transfer_id]

            if success:
                transfer_info['progress_bar'].setValue(100)
                QTimer.singleShot(2000, lambda: self.remove_transfer_widget(transfer_id))
            else:
                QMessageBox.critical(self, "Transfer Error", f"Transfer failed: {error_msg}")
                self.remove_transfer_widget(transfer_id)

            # Refresh both panes
            self.refresh_local()
            self.refresh_remote()

    def cancel_transfer(self, transfer_id):
        """Cancel a file transfer"""
        if transfer_id in self.current_transfers:
            self.current_transfers[transfer_id]['cancelled'] = True
            self.remove_transfer_widget(transfer_id)

    def remove_transfer_widget(self, transfer_id):
        """Remove transfer progress widget"""
        if transfer_id in self.current_transfers:
            widget = self.current_transfers[transfer_id]['progress_widget']
            self.progress_layout.removeWidget(widget)
            widget.deleteLater()
            del self.current_transfers[transfer_id]

    def cancel_transfers(self):
        """Cancel all active transfers"""
        transfer_ids = list(self.current_transfers.keys())
        for transfer_id in transfer_ids:
            self.cancel_transfer(transfer_id)

    def create_local_folder(self):
        """Create new local folder"""
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            try:
                folder_path = os.path.join(os.getcwd(), name)
                os.makedirs(folder_path)
                self.refresh_local()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot create folder: {str(e)}")

    def create_remote_folder(self):
        """Create new remote folder"""
        sftp = self.get_sftp_client()
        if not sftp:
            return

        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if ok and name:
            try:
                sftp.mkdir(name)
                self.refresh_remote()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot create remote folder: {str(e)}")

    def delete_local_item(self):
        """Delete selected local item"""
        selected_items = self.local_tree.selectedItems()
        if not selected_items:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected_items)} selected item(s)?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for item in selected_items:
                try:
                    path = item.data(0, Qt.UserRole)
                    if os.path.isdir(path):
                        os.rmdir(path)
                    else:
                        os.remove(path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Cannot delete {path}: {str(e)}")

            self.refresh_local()

    def delete_remote_item(self):
        """Delete selected remote item"""
        sftp = self.get_sftp_client()
        if not sftp:
            return

        selected_items = self.remote_tree.selectedItems()
        if not selected_items:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected_items)} selected remote item(s)?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for item in selected_items:
                try:
                    filename = item.text(0)
                    if item.text(3) == "Folder":
                        sftp.rmdir(filename)
                    else:
                        sftp.remove(filename)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Cannot delete {filename}: {str(e)}")

            self.refresh_remote()

    def sync_folders(self):
        """Synchronize local and remote folders"""
        QMessageBox.information(self, "Sync", "Folder synchronization feature coming soon!")

    def auto_refresh(self):
        """Auto-refresh file listings"""
        if self.get_sftp_client():
            self.refresh_remote()


class FileTreeWidget(QTreeWidget):
    """Custom tree widget with drag-drop support"""

    def __init__(self, parent, tree_type):
        super().__init__(parent)
        self.parent_browser = parent
        self.tree_type = tree_type
        self.setDragDropMode(QTreeWidget.DragDrop)
        self.setDefaultDropAction(Qt.CopyAction)

    def startDrag(self, supportedActions):
        """Start drag operation"""
        item = self.currentItem()
        if item:
            drag = QDrag(self)
            mime_data = QMimeData()

            file_path = item.data(0, Qt.UserRole)
            mime_data.setText(file_path)
            mime_data.setData("application/x-tree-type", self.tree_type.encode())

            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)

    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop operation"""
        source_type = event.mimeData().data("application/x-tree-type").data().decode()
        source_path = event.mimeData().text()

        if source_type != self.tree_type:  # Cross-pane transfer
            filename = os.path.basename(source_path)

            if self.tree_type == "remote" and source_type == "local":
                # Upload
                self.parent_browser.start_file_transfer(source_path, filename, "upload")
            elif self.tree_type == "local" and source_type == "remote":
                # Download
                dest_path = os.path.join(os.getcwd(), filename)
                self.parent_browser.start_file_transfer(source_path, dest_path, "download")

        event.acceptProposedAction()


class FileTransferThread(QThread):
    """Thread for handling file transfers"""

    progress_updated = pyqtSignal(str, int)
    transfer_completed = pyqtSignal(str, bool, str)

    def __init__(self, sftp_client, source_path, dest_path, transfer_type, transfer_id):
        super().__init__()
        self.sftp_client = sftp_client
        self.source_path = source_path
        self.dest_path = dest_path
        self.transfer_type = transfer_type
        self.transfer_id = transfer_id

    def run(self):
        """Execute file transfer"""
        try:
            if self.transfer_type == "upload":
                self.upload_file()
            elif self.transfer_type == "download":
                self.download_file()

            self.transfer_completed.emit(self.transfer_id, True, "")

        except Exception as e:
            self.transfer_completed.emit(self.transfer_id, False, str(e))
            logger.error(f"File transfer error: {e}")

    def upload_file(self):
        """Upload file with progress tracking"""
        file_size = os.path.getsize(self.source_path)
        transferred = 0

        def progress_callback(transferred_bytes, total_bytes):
            percentage = int((transferred_bytes / total_bytes) * 100)
            self.progress_updated.emit(self.transfer_id, percentage)

        self.sftp_client.put(self.source_path, self.dest_path, callback=progress_callback)

    def download_file(self):
        """Download file with progress tracking"""
        def progress_callback(transferred_bytes, total_bytes):
            percentage = int((transferred_bytes / total_bytes) * 100)
            self.progress_updated.emit(self.transfer_id, percentage)

        self.sftp_client.get(self.source_path, self.dest_path, callback=progress_callback)