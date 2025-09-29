"""
Modern UI Demo for JETSSH Enhanced
Demonstrates the new modern UI components and styling
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer

from modern_ui_theme import ModernTheme, ModernColors, ModernTypography, ModernSpacing
from modern_ui_components import (ModernCard, ModernButton, ModernInput, ModernComboBox,
                                 ModernSeparator, ModernStatusIndicator, ModernNotification,
                                 ModernSearchBox, ModernBadge, ModernProgressBar, ModernLoadingSpinner)


class ModernUIDemo(QMainWindow):
    """Demo window showcasing modern UI components"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JETSSH Enhanced - Modern UI Demo")
        self.resize(800, 600)
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Setup the demo UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(ModernSpacing.LG)
        layout.setContentsMargins(ModernSpacing.XXL, ModernSpacing.XXL,
                                 ModernSpacing.XXL, ModernSpacing.XXL)

        # Title
        title_label = QLabel("Modern UI Components Demo")
        title_label.setProperty("labelType", "title")
        layout.addWidget(title_label)

        subtitle_label = QLabel("Showcasing the new modern design system for JETSSH Enhanced")
        subtitle_label.setProperty("labelType", "subtitle")
        layout.addWidget(subtitle_label)

        layout.addWidget(ModernSeparator())

        # Demo content in cards
        self.create_buttons_demo(layout)
        self.create_inputs_demo(layout)
        self.create_status_demo(layout)

    def create_buttons_demo(self, parent_layout):
        """Create buttons demonstration"""
        buttons_content = QWidget()
        buttons_layout = QVBoxLayout(buttons_content)

        # Different button types
        button_types_layout = QHBoxLayout()

        default_btn = ModernButton("Default", "default", "🔧")
        primary_btn = ModernButton("Primary", "primary", "🚀")
        success_btn = ModernButton("Success", "success", "✓")
        warning_btn = ModernButton("Warning", "warning", "⚠")
        error_btn = ModernButton("Error", "error", "✗")

        for btn in [default_btn, primary_btn, success_btn, warning_btn, error_btn]:
            btn.clicked.connect(lambda checked, b=btn: self.show_demo_notification(f"{b.text()} button clicked!"))
            button_types_layout.addWidget(btn)

        buttons_layout.addLayout(button_types_layout)

        # Create buttons card
        buttons_card = ModernCard(title="Modern Buttons", content_widget=buttons_content)
        parent_layout.addWidget(buttons_card)

    def create_inputs_demo(self, parent_layout):
        """Create inputs demonstration"""
        inputs_content = QWidget()
        inputs_layout = QVBoxLayout(inputs_content)

        # Input fields
        inputs_row1 = QHBoxLayout()

        host_input = ModernInput("Enter hostname...", "Host")
        user_input = ModernInput("Enter username...", "Username")

        inputs_row1.addWidget(host_input)
        inputs_row1.addWidget(user_input)
        inputs_layout.addLayout(inputs_row1)

        # Search and combo
        inputs_row2 = QHBoxLayout()

        search_box = ModernSearchBox("Search connections...")
        combo_box = ModernComboBox()
        combo_box.addItems(["SSH", "SFTP", "SCP"])

        inputs_row2.addWidget(search_box)
        inputs_row2.addWidget(combo_box)
        inputs_layout.addLayout(inputs_row2)

        # Progress bar
        progress_bar = ModernProgressBar()
        progress_bar.setValue(65)
        inputs_layout.addWidget(progress_bar)

        # Create inputs card
        inputs_card = ModernCard(title="Modern Input Components", content_widget=inputs_content)
        parent_layout.addWidget(inputs_card)

    def create_status_demo(self, parent_layout):
        """Create status indicators demonstration"""
        status_content = QWidget()
        status_layout = QVBoxLayout(status_content)

        # Status indicators row
        status_row1 = QHBoxLayout()

        # Status indicators
        active_status = ModernStatusIndicator("active")
        inactive_status = ModernStatusIndicator("inactive")
        warning_status = ModernStatusIndicator("warning")
        error_status = ModernStatusIndicator("error")
        connecting_status = ModernStatusIndicator("connecting")

        status_indicators = [
            (active_status, "Active"),
            (inactive_status, "Inactive"),
            (warning_status, "Warning"),
            (error_status, "Error"),
            (connecting_status, "Connecting")
        ]

        for indicator, label_text in status_indicators:
            indicator_layout = QVBoxLayout()
            indicator_layout.addWidget(indicator)
            indicator_layout.addWidget(QLabel(label_text))
            indicator_layout.setAlignment(Qt.AlignCenter)
            status_row1.addLayout(indicator_layout)

        status_layout.addLayout(status_row1)

        # Badges row
        badges_row = QHBoxLayout()

        default_badge = ModernBadge("Default", "default")
        primary_badge = ModernBadge("Primary", "primary")
        success_badge = ModernBadge("Success", "success")
        warning_badge = ModernBadge("Warning", "warning")
        error_badge = ModernBadge("Error", "error")

        for badge in [default_badge, primary_badge, success_badge, warning_badge, error_badge]:
            badges_row.addWidget(badge)

        badges_row.addStretch()
        status_layout.addLayout(badges_row)

        # Loading spinner
        spinner_layout = QHBoxLayout()
        self.loading_spinner = ModernLoadingSpinner(32)
        spinner_layout.addWidget(QLabel("Loading Spinner:"))
        spinner_layout.addWidget(self.loading_spinner)
        spinner_layout.addStretch()
        status_layout.addLayout(spinner_layout)

        # Start spinner
        self.loading_spinner.start()

        # Create status card
        status_card = ModernCard(title="Status Indicators & Badges", content_widget=status_content)
        parent_layout.addWidget(status_card)

    def show_demo_notification(self, message):
        """Show a demo notification"""
        notification = ModernNotification(message, "info", self)
        notification.move(self.width() - notification.width() - 20, 50)
        notification.show_notification()

    def apply_theme(self):
        """Apply the modern theme"""
        self.setStyleSheet(ModernTheme.get_application_style())

        # Set application font
        app_font = ModernTypography.get_font()
        QApplication.instance().setFont(app_font)


def main():
    """Main demo entry point"""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("JETSSH Enhanced - UI Demo")
    app.setApplicationVersion("2.0")

    # Create and show demo window
    demo = ModernUIDemo()
    demo.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()