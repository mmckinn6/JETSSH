"""
Plugin Architecture and Manager for JETSSH
Provides extensible plugin system for third-party integrations
"""

import os
import sys
import json
import logging
import importlib
import importlib.util
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget,
                             QTreeWidgetItem, QPushButton, QMessageBox, QInputDialog,
                             QTextEdit, QTabWidget, QCheckBox, QComboBox, QDialog,
                             QDialogButtonBox, QFormLayout, QLineEdit, QHeaderView,
                             QFileDialog, QProgressBar, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)


class JETSSHPlugin(ABC):
    """Base class for JETSSH plugins"""

    def __init__(self, name: str, version: str, description: str):
        self.name = name
        self.version = version
        self.description = description
        self.enabled = False
        self.ssh_client_app = None
        self.plugin_manager = None

    @abstractmethod
    def initialize(self, ssh_client_app, plugin_manager):
        """Initialize the plugin with SSH client app and plugin manager"""
        self.ssh_client_app = ssh_client_app
        self.plugin_manager = plugin_manager

    @abstractmethod
    def activate(self):
        """Activate the plugin"""
        pass

    @abstractmethod
    def deactivate(self):
        """Deactivate the plugin"""
        pass

    def get_menu_items(self) -> List[Dict[str, Any]]:
        """Return menu items to be added to the application menu"""
        return []

    def get_toolbar_items(self) -> List[Dict[str, Any]]:
        """Return toolbar items to be added to the application toolbar"""
        return []

    def get_context_menu_items(self, context: str) -> List[Dict[str, Any]]:
        """Return context menu items for specific contexts"""
        return []

    def handle_connection_event(self, event_type: str, host: str, data: Dict[str, Any]):
        """Handle SSH connection events"""
        pass

    def handle_terminal_output(self, host: str, output: str):
        """Handle terminal output for processing"""
        pass

    def get_settings_widget(self):
        """Return a settings widget for the plugin"""
        return None

    def get_info(self) -> Dict[str, Any]:
        """Return plugin information"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'enabled': self.enabled
        }


class PluginManager(QWidget):
    """Plugin Manager for loading and managing plugins"""

    plugin_loaded = pyqtSignal(str)      # plugin_name
    plugin_activated = pyqtSignal(str)   # plugin_name
    plugin_deactivated = pyqtSignal(str) # plugin_name

    def __init__(self, ssh_client_app):
        super().__init__()
        self.ssh_client_app = ssh_client_app
        self.plugins_dir = Path("plugins")
        self.loaded_plugins: Dict[str, JETSSHPlugin] = {}
        self.plugin_configs = {}
        self.plugin_metadata = {}

        # Create plugins directory
        self.plugins_dir.mkdir(exist_ok=True)

        self.setup_ui()
        self.load_plugin_configs()
        self.discover_and_load_plugins()

    def setup_ui(self):
        """Setup the plugin manager UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Plugin Manager")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #dcdcdc;")
        layout.addWidget(title)

        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)

        # Left side - Plugin list and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Plugin controls
        controls_layout = QHBoxLayout()

        install_btn = QPushButton("📦 Install Plugin")
        install_btn.clicked.connect(self.install_plugin)
        install_btn.setStyleSheet("""
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
        controls_layout.addWidget(install_btn)

        create_btn = QPushButton("🛠️ Create Plugin")
        create_btn.clicked.connect(self.create_plugin_template)
        controls_layout.addWidget(create_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_plugins)
        controls_layout.addWidget(refresh_btn)

        controls_layout.addStretch()

        left_layout.addLayout(controls_layout)

        # Plugins tree
        plugins_label = QLabel("Installed Plugins")
        plugins_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        left_layout.addWidget(plugins_label)

        self.plugins_tree = QTreeWidget()
        self.plugins_tree.setHeaderLabels([
            "Plugin", "Version", "Status", "Author", "Actions"
        ])
        self.plugins_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.plugins_tree.itemSelectionChanged.connect(self.on_plugin_selected)
        left_layout.addWidget(self.plugins_tree)

        # Plugin operations
        plugin_ops_layout = QHBoxLayout()

        self.enable_btn = QPushButton("Enable")
        self.enable_btn.clicked.connect(self.toggle_plugin)
        plugin_ops_layout.addWidget(self.enable_btn)

        configure_btn = QPushButton("Configure")
        configure_btn.clicked.connect(self.configure_plugin)
        plugin_ops_layout.addWidget(configure_btn)

        uninstall_btn = QPushButton("Uninstall")
        uninstall_btn.clicked.connect(self.uninstall_plugin)
        uninstall_btn.setStyleSheet("""
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
        plugin_ops_layout.addWidget(uninstall_btn)

        left_layout.addLayout(plugin_ops_layout)

        main_splitter.addWidget(left_widget)

        # Right side - Plugin details and marketplace
        right_widget = QTabWidget()

        # Plugin details tab
        details_tab = self.create_details_tab()
        right_widget.addTab(details_tab, "Details")

        # Plugin marketplace tab
        marketplace_tab = self.create_marketplace_tab()
        right_widget.addTab(marketplace_tab, "Marketplace")

        # Plugin development tab
        development_tab = self.create_development_tab()
        right_widget.addTab(development_tab, "Development")

        main_splitter.addWidget(right_widget)

        layout.addWidget(main_splitter)

        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #3a3a3a;
                color: #888;
                padding: 5px 10px;
                border-top: 1px solid #2a2a2a;
            }
        """)
        layout.addWidget(self.status_label)

    def create_details_tab(self):
        """Create plugin details tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Plugin info
        self.plugin_info_text = QTextEdit()
        self.plugin_info_text.setReadOnly(True)
        self.plugin_info_text.setStyleSheet("""
            QTextEdit {
                background-color: #2e2e2e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                padding: 8px;
            }
        """)
        layout.addWidget(self.plugin_info_text)

        # Plugin logs
        logs_label = QLabel("Plugin Logs")
        logs_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #00ffff;")
        layout.addWidget(logs_label)

        self.plugin_logs_text = QTextEdit()
        self.plugin_logs_text.setReadOnly(True)
        self.plugin_logs_text.setMaximumHeight(150)
        self.plugin_logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.plugin_logs_text)

        return widget

    def create_marketplace_tab(self):
        """Create plugin marketplace tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search and filter
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search plugins...")
        self.search_input.textChanged.connect(self.filter_marketplace_plugins)
        search_layout.addWidget(self.search_input)

        self.category_filter = QComboBox()
        self.category_filter.addItems(["All", "Terminal", "File Management", "Security", "Development", "Monitoring"])
        self.category_filter.currentTextChanged.connect(self.filter_marketplace_plugins)
        search_layout.addWidget(self.category_filter)

        layout.addLayout(search_layout)

        # Available plugins
        marketplace_label = QLabel("Available Plugins")
        marketplace_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(marketplace_label)

        self.marketplace_tree = QTreeWidget()
        self.marketplace_tree.setHeaderLabels([
            "Plugin", "Description", "Downloads", "Rating", "Install"
        ])
        self.marketplace_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.marketplace_tree)

        # Populate with sample plugins
        self.populate_marketplace()

        return widget

    def create_development_tab(self):
        """Create plugin development tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Development tools
        dev_tools_layout = QHBoxLayout()

        create_template_btn = QPushButton("📝 Create Template")
        create_template_btn.clicked.connect(self.create_plugin_template)
        dev_tools_layout.addWidget(create_template_btn)

        validate_btn = QPushButton("✅ Validate Plugin")
        validate_btn.clicked.connect(self.validate_plugin)
        dev_tools_layout.addWidget(validate_btn)

        package_btn = QPushButton("📦 Package Plugin")
        package_btn.clicked.connect(self.package_plugin)
        dev_tools_layout.addWidget(package_btn)

        dev_tools_layout.addStretch()

        layout.addLayout(dev_tools_layout)

        # Plugin API documentation
        api_label = QLabel("Plugin API Documentation")
        api_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffff;")
        layout.addWidget(api_label)

        self.api_docs_text = QTextEdit()
        self.api_docs_text.setReadOnly(True)
        self.api_docs_text.setHtml(self.get_api_documentation())
        layout.addWidget(self.api_docs_text)

        return widget

    def discover_and_load_plugins(self):
        """Discover and load plugins from plugins directory"""
        self.status_label.setText("Discovering plugins...")

        try:
            # Scan plugins directory
            for plugin_dir in self.plugins_dir.iterdir():
                if plugin_dir.is_dir() and not plugin_dir.name.startswith('.'):
                    self.load_plugin_from_directory(plugin_dir)

            self.refresh_plugins_display()
            self.status_label.setText(f"Loaded {len(self.loaded_plugins)} plugins")

        except Exception as e:
            logger.error(f"Error discovering plugins: {e}")
            self.status_label.setText("Error discovering plugins")

    def load_plugin_from_directory(self, plugin_dir: Path):
        """Load a plugin from a directory"""
        try:
            # Look for plugin manifest
            manifest_file = plugin_dir / "plugin.json"
            if not manifest_file.exists():
                logger.warning(f"No manifest found in {plugin_dir}")
                return

            # Load manifest
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)

            plugin_name = manifest.get('name')
            if not plugin_name:
                logger.warning(f"No plugin name in manifest: {manifest_file}")
                return

            # Load plugin module
            plugin_file = plugin_dir / f"{manifest.get('main', 'plugin')}.py"
            if not plugin_file.exists():
                logger.warning(f"Plugin file not found: {plugin_file}")
                return

            # Import plugin module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            plugin_module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = plugin_module
            spec.loader.exec_module(plugin_module)

            # Get plugin class
            plugin_class_name = manifest.get('class', 'Plugin')
            if not hasattr(plugin_module, plugin_class_name):
                logger.warning(f"Plugin class {plugin_class_name} not found in {plugin_file}")
                return

            plugin_class = getattr(plugin_module, plugin_class_name)

            # Create plugin instance
            plugin_instance = plugin_class(
                name=manifest.get('name'),
                version=manifest.get('version', '1.0.0'),
                description=manifest.get('description', '')
            )

            # Initialize plugin
            plugin_instance.initialize(self.ssh_client_app, self)

            # Store plugin
            self.loaded_plugins[plugin_name] = plugin_instance
            self.plugin_metadata[plugin_name] = manifest

            # Auto-enable if configured
            if self.plugin_configs.get(plugin_name, {}).get('enabled', False):
                self.activate_plugin(plugin_name)

            logger.info(f"Loaded plugin: {plugin_name}")
            self.plugin_loaded.emit(plugin_name)

        except Exception as e:
            logger.error(f"Error loading plugin from {plugin_dir}: {e}")

    def refresh_plugins_display(self):
        """Refresh the plugins display"""
        self.plugins_tree.clear()

        for plugin_name, plugin in self.loaded_plugins.items():
            metadata = self.plugin_metadata.get(plugin_name, {})
            status = "Enabled" if plugin.enabled else "Disabled"
            author = metadata.get('author', 'Unknown')

            item = QTreeWidgetItem([
                plugin_name,
                plugin.version,
                status,
                author,
                ""
            ])

            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            toggle_btn = QPushButton("Disable" if plugin.enabled else "Enable")
            toggle_btn.clicked.connect(lambda checked, name=plugin_name: self.toggle_plugin_by_name(name))
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336 if plugin.enabled else #4CAF50;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #da190b if plugin.enabled else #45a049;
                }
            """)
            actions_layout.addWidget(toggle_btn)

            self.plugins_tree.addTopLevelItem(item)
            self.plugins_tree.setItemWidget(item, 4, actions_widget)

    def on_plugin_selected(self):
        """Handle plugin selection"""
        current_item = self.plugins_tree.currentItem()
        if not current_item:
            return

        plugin_name = current_item.text(0)
        if plugin_name in self.loaded_plugins:
            plugin = self.loaded_plugins[plugin_name]
            self.display_plugin_details(plugin_name, plugin)

    def display_plugin_details(self, plugin_name: str, plugin: JETSSHPlugin):
        """Display plugin details"""
        metadata = self.plugin_metadata.get(plugin_name, {})

        details = []
        details.append(f"Plugin: {plugin.name}")
        details.append(f"Version: {plugin.version}")
        details.append(f"Description: {plugin.description}")
        details.append(f"Status: {'Enabled' if plugin.enabled else 'Disabled'}")
        details.append(f"Author: {metadata.get('author', 'Unknown')}")
        details.append(f"Website: {metadata.get('website', 'N/A')}")
        details.append(f"License: {metadata.get('license', 'Unknown')}")
        details.append("")
        details.append("Capabilities:")

        if hasattr(plugin, 'get_menu_items'):
            menu_items = plugin.get_menu_items()
            if menu_items:
                details.append(f"  • Adds {len(menu_items)} menu items")

        if hasattr(plugin, 'get_toolbar_items'):
            toolbar_items = plugin.get_toolbar_items()
            if toolbar_items:
                details.append(f"  • Adds {len(toolbar_items)} toolbar items")

        if hasattr(plugin, 'handle_connection_event'):
            details.append("  • Handles connection events")

        if hasattr(plugin, 'handle_terminal_output'):
            details.append("  • Processes terminal output")

        self.plugin_info_text.setText('\n'.join(details))

    def toggle_plugin(self):
        """Toggle selected plugin enabled/disabled state"""
        current_item = self.plugins_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No plugin selected")
            return

        plugin_name = current_item.text(0)
        self.toggle_plugin_by_name(plugin_name)

    def toggle_plugin_by_name(self, plugin_name: str):
        """Toggle plugin by name"""
        if plugin_name not in self.loaded_plugins:
            return

        plugin = self.loaded_plugins[plugin_name]

        try:
            if plugin.enabled:
                self.deactivate_plugin(plugin_name)
            else:
                self.activate_plugin(plugin_name)

            self.refresh_plugins_display()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle plugin: {str(e)}")
            logger.error(f"Plugin toggle error: {e}")

    def activate_plugin(self, plugin_name: str):
        """Activate a plugin"""
        if plugin_name not in self.loaded_plugins:
            return

        plugin = self.loaded_plugins[plugin_name]

        try:
            plugin.activate()
            plugin.enabled = True

            # Save configuration
            if plugin_name not in self.plugin_configs:
                self.plugin_configs[plugin_name] = {}
            self.plugin_configs[plugin_name]['enabled'] = True
            self.save_plugin_configs()

            self.plugin_activated.emit(plugin_name)
            logger.info(f"Activated plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Error activating plugin {plugin_name}: {e}")
            raise

    def deactivate_plugin(self, plugin_name: str):
        """Deactivate a plugin"""
        if plugin_name not in self.loaded_plugins:
            return

        plugin = self.loaded_plugins[plugin_name]

        try:
            plugin.deactivate()
            plugin.enabled = False

            # Save configuration
            if plugin_name not in self.plugin_configs:
                self.plugin_configs[plugin_name] = {}
            self.plugin_configs[plugin_name]['enabled'] = False
            self.save_plugin_configs()

            self.plugin_deactivated.emit(plugin_name)
            logger.info(f"Deactivated plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Error deactivating plugin {plugin_name}: {e}")
            raise

    def install_plugin(self):
        """Install a plugin from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Install Plugin",
            "", "Plugin Files (*.zip *.tar.gz *.jetssh);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Extract and install plugin
            self.extract_and_install_plugin(file_path)
            QMessageBox.information(self, "Success", "Plugin installed successfully")
            self.refresh_plugins()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to install plugin: {str(e)}")
            logger.error(f"Plugin installation error: {e}")

    def extract_and_install_plugin(self, file_path: str):
        """Extract and install plugin from archive"""
        import zipfile
        import tarfile

        plugin_file = Path(file_path)

        # Determine archive type and extract
        if plugin_file.suffix == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(self.plugins_dir)
        elif plugin_file.suffix in ['.tar', '.gz']:
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(self.plugins_dir)
        else:
            raise ValueError(f"Unsupported plugin file format: {plugin_file.suffix}")

    def uninstall_plugin(self):
        """Uninstall selected plugin"""
        current_item = self.plugins_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No plugin selected")
            return

        plugin_name = current_item.text(0)

        reply = QMessageBox.question(
            self, "Uninstall Plugin",
            f"Are you sure you want to uninstall '{plugin_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Deactivate plugin first
                if plugin_name in self.loaded_plugins:
                    plugin = self.loaded_plugins[plugin_name]
                    if plugin.enabled:
                        self.deactivate_plugin(plugin_name)

                    # Remove from loaded plugins
                    del self.loaded_plugins[plugin_name]

                # Remove plugin directory
                plugin_dir = self.plugins_dir / plugin_name
                if plugin_dir.exists():
                    import shutil
                    shutil.rmtree(plugin_dir)

                # Remove from metadata
                if plugin_name in self.plugin_metadata:
                    del self.plugin_metadata[plugin_name]

                # Remove from configs
                if plugin_name in self.plugin_configs:
                    del self.plugin_configs[plugin_name]
                    self.save_plugin_configs()

                self.refresh_plugins_display()
                QMessageBox.information(self, "Success", f"Plugin '{plugin_name}' uninstalled")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to uninstall plugin: {str(e)}")

    def configure_plugin(self):
        """Configure selected plugin"""
        current_item = self.plugins_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Error", "No plugin selected")
            return

        plugin_name = current_item.text(0)
        if plugin_name not in self.loaded_plugins:
            return

        plugin = self.loaded_plugins[plugin_name]

        try:
            settings_widget = plugin.get_settings_widget()
            if settings_widget:
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Configure {plugin_name}")
                dialog.resize(400, 300)

                layout = QVBoxLayout(dialog)
                layout.addWidget(settings_widget)

                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                dialog.exec_()
            else:
                QMessageBox.information(self, "Configuration", f"Plugin '{plugin_name}' has no configuration options")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to configure plugin: {str(e)}")

    def create_plugin_template(self):
        """Create a new plugin template"""
        dialog = PluginTemplateDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            template_data = dialog.get_template_data()
            try:
                self.generate_plugin_template(template_data)
                QMessageBox.information(self, "Success", "Plugin template created successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create template: {str(e)}")

    def generate_plugin_template(self, template_data: Dict[str, Any]):
        """Generate plugin template files"""
        plugin_name = template_data['name']
        plugin_dir = self.plugins_dir / plugin_name
        plugin_dir.mkdir(exist_ok=True)

        # Create manifest
        manifest = {
            'name': plugin_name,
            'version': template_data.get('version', '1.0.0'),
            'description': template_data.get('description', ''),
            'author': template_data.get('author', ''),
            'main': 'plugin',
            'class': 'Plugin'
        }

        with open(plugin_dir / 'plugin.json', 'w') as f:
            json.dump(manifest, f, indent=2)

        # Create plugin code
        plugin_code = f'''"""
{plugin_name} Plugin for JETSSH
{template_data.get('description', '')}
"""

from plugin_manager import JETSSHPlugin
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class Plugin(JETSSHPlugin):
    """Main plugin class"""

    def __init__(self, name, version, description):
        super().__init__(name, version, description)

    def activate(self):
        """Activate the plugin"""
        print(f"Activating {{self.name}} plugin")
        # Add your activation code here

    def deactivate(self):
        """Deactivate the plugin"""
        print(f"Deactivating {{self.name}} plugin")
        # Add your deactivation code here

    def get_menu_items(self):
        """Return menu items for this plugin"""
        return [
            {{
                'text': '{plugin_name} Action',
                'callback': self.plugin_action,
                'icon': None
            }}
        ]

    def plugin_action(self):
        """Example plugin action"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(
            None, self.name,
            f"Hello from {{self.name}} plugin!"
        )

    def handle_connection_event(self, event_type, host, data):
        """Handle SSH connection events"""
        print(f"{{self.name}}: Connection event {{event_type}} for {{host}}")

    def handle_terminal_output(self, host, output):
        """Handle terminal output"""
        # Process terminal output here
        pass

    def get_settings_widget(self):
        """Return settings widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel(f"Settings for {{self.name}}")
        layout.addWidget(label)

        return widget
'''

        with open(plugin_dir / 'plugin.py', 'w') as f:
            f.write(plugin_code)

        # Create README
        readme_content = f'''# {plugin_name} Plugin

{template_data.get('description', '')}

## Installation

1. Copy this plugin directory to the JETSSH plugins folder
2. Restart JETSSH or refresh plugins
3. Enable the plugin in the Plugin Manager

## Usage

Describe how to use your plugin here.

## Configuration

Describe any configuration options here.

## License

{template_data.get('license', 'MIT')}
'''

        with open(plugin_dir / 'README.md', 'w') as f:
            f.write(readme_content)

    def populate_marketplace(self):
        """Populate marketplace with sample plugins"""
        sample_plugins = [
            {
                'name': 'Git Integration',
                'description': 'Integrate Git commands and repository management',
                'downloads': '1.2K',
                'rating': '★★★★★'
            },
            {
                'name': 'Docker Manager',
                'description': 'Manage Docker containers and images',
                'downloads': '890',
                'rating': '★★★★☆'
            },
            {
                'name': 'Log Analyzer',
                'description': 'Advanced log parsing and analysis tools',
                'downloads': '654',
                'rating': '★★★★★'
            },
            {
                'name': 'Database Tools',
                'description': 'Connect to and manage databases',
                'downloads': '432',
                'rating': '★★★☆☆'
            }
        ]

        for plugin_data in sample_plugins:
            item = QTreeWidgetItem([
                plugin_data['name'],
                plugin_data['description'],
                plugin_data['downloads'],
                plugin_data['rating'],
                ""
            ])

            install_btn = QPushButton("Install")
            install_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)

            self.marketplace_tree.addTopLevelItem(item)
            self.marketplace_tree.setItemWidget(item, 4, install_btn)

    def filter_marketplace_plugins(self):
        """Filter marketplace plugins based on search and category"""
        # Implementation would filter the marketplace display
        pass

    def validate_plugin(self):
        """Validate a plugin"""
        QMessageBox.information(self, "Validate", "Plugin validation feature")

    def package_plugin(self):
        """Package a plugin for distribution"""
        QMessageBox.information(self, "Package", "Plugin packaging feature")

    def refresh_plugins(self):
        """Refresh plugin list"""
        self.discover_and_load_plugins()

    def save_plugin_configs(self):
        """Save plugin configurations"""
        config_file = Path("plugin_configs.json")
        try:
            with open(config_file, 'w') as f:
                json.dump(self.plugin_configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save plugin configs: {e}")

    def load_plugin_configs(self):
        """Load plugin configurations"""
        config_file = Path("plugin_configs.json")
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.plugin_configs = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load plugin configs: {e}")

    def get_api_documentation(self):
        """Get plugin API documentation"""
        return """
        <h2>JETSSH Plugin API Documentation</h2>

        <h3>Plugin Base Class</h3>
        <p>All plugins must inherit from <code>JETSSHPlugin</code> and implement the required methods:</p>

        <h4>Required Methods:</h4>
        <ul>
            <li><code>initialize(ssh_client_app, plugin_manager)</code> - Initialize plugin</li>
            <li><code>activate()</code> - Activate plugin functionality</li>
            <li><code>deactivate()</code> - Deactivate plugin functionality</li>
        </ul>

        <h4>Optional Methods:</h4>
        <ul>
            <li><code>get_menu_items()</code> - Return menu items to add</li>
            <li><code>get_toolbar_items()</code> - Return toolbar items to add</li>
            <li><code>get_context_menu_items(context)</code> - Return context menu items</li>
            <li><code>handle_connection_event(event_type, host, data)</code> - Handle SSH events</li>
            <li><code>handle_terminal_output(host, output)</code> - Process terminal output</li>
            <li><code>get_settings_widget()</code> - Return configuration widget</li>
        </ul>

        <h3>Plugin Manifest (plugin.json)</h3>
        <pre>
{
    "name": "Plugin Name",
    "version": "1.0.0",
    "description": "Plugin description",
    "author": "Author Name",
    "main": "plugin",
    "class": "Plugin"
}
        </pre>

        <h3>Examples</h3>
        <p>See the plugin template generator for complete examples.</p>
        """


class PluginTemplateDialog(QDialog):
    """Dialog for creating plugin templates"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Plugin Template")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Plugin Name:", self.name_edit)

        self.version_edit = QLineEdit("1.0.0")
        form_layout.addRow("Version:", self.version_edit)

        self.author_edit = QLineEdit()
        form_layout.addRow("Author:", self.author_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_edit)

        self.license_combo = QComboBox()
        self.license_combo.addItems(["MIT", "GPL-3.0", "Apache-2.0", "BSD-3-Clause", "Other"])
        form_layout.addRow("License:", self.license_combo)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_template_data(self):
        return {
            'name': self.name_edit.text(),
            'version': self.version_edit.text(),
            'author': self.author_edit.text(),
            'description': self.description_edit.toPlainText(),
            'license': self.license_combo.currentText()
        }