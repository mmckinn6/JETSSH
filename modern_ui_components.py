"""
Modern UI Components for JETSSH Enhanced
Provides reusable modern UI components with consistent styling and behavior
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QLineEdit, QFrame, QGraphicsOpacityEffect, QSizePolicy,
                             QTextEdit, QScrollArea, QGridLayout, QSpacerItem,
                             QListWidget, QListWidgetItem, QProgressBar, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QPen, QFontMetrics

from modern_ui_theme import ModernColors, ModernTypography, ModernSpacing, ModernTheme


class ModernCard(QFrame):
    """Modern card component with shadow and hover effects"""

    def __init__(self, parent=None, title="", content_widget=None):
        super().__init__(parent)
        self.setup_ui(title, content_widget)

    def setup_ui(self, title, content_widget):
        """Setup the card UI"""
        self.setFrameStyle(QFrame.Box)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.setStyleSheet(f"""
            ModernCard {{
                background: {ModernColors.GRADIENT_SURFACE};
                border: 1px solid {ModernColors.BORDER};
                border-radius: {ModernSpacing.RADIUS_LG}px;
                margin: {ModernSpacing.XS}px;
            }}
            ModernCard:hover {{
                border-color: {ModernColors.BORDER_LIGHT};
                background-color: {ModernColors.SURFACE_HOVER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(ModernSpacing.MD, ModernSpacing.MD,
                                 ModernSpacing.MD, ModernSpacing.MD)
        layout.setSpacing(ModernSpacing.SM)

        if title:
            title_label = QLabel(title)
            title_label.setProperty("labelType", "title")
            layout.addWidget(title_label)

            # Add separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setStyleSheet(f"""
                QFrame {{
                    color: {ModernColors.BORDER};
                    background-color: {ModernColors.BORDER};
                    border: none;
                    height: 1px;
                    margin: {ModernSpacing.MD}px 0px;
                }}
            """)
            layout.addWidget(separator)

        if content_widget:
            layout.addWidget(content_widget)

        # Apply shadow effect
        ModernTheme.apply_shadow(self)


class ModernButton(QPushButton):
    """Modern button with enhanced styling and animations"""

    def __init__(self, text="", button_type="default", icon=None, parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self.icon_text = icon
        self.setup_button()

    def setup_button(self):
        """Setup button styling and behavior"""
        self.setProperty("buttonType", self.button_type)

        # Set minimum size for better touch targets
        self.setMinimumHeight(36)
        self.setMinimumWidth(80)

        # Add icon if provided
        if self.icon_text:
            current_text = self.text()
            self.setText(f"{self.icon_text} {current_text}")

        # Apply hover animation
        self.setCursor(Qt.PointingHandCursor)

    def enterEvent(self, event):
        """Animate on hover"""
        self.animate_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Animate on leave"""
        self.animate_hover(False)
        super().leaveEvent(event)

    def animate_hover(self, hovered):
        """Create hover animation"""
        # This would typically use QPropertyAnimation for transform effects
        # For now, we rely on CSS transitions
        pass


class ModernInput(QLineEdit):
    """Modern input field with floating label and validation"""

    def __init__(self, placeholder="", label="", parent=None):
        super().__init__(parent)
        self.label_text = label
        self.placeholder_text = placeholder
        self.setup_input()

    def setup_input(self):
        """Setup input styling"""
        self.setPlaceholderText(self.placeholder_text)
        self.setMinimumHeight(40)

        # Set focus policy
        self.setFocusPolicy(Qt.StrongFocus)

    def set_error_state(self, error=True, message=""):
        """Set error state for validation"""
        if error:
            self.setStyleSheet(f"""
                QLineEdit {{
                    border-color: {ModernColors.ERROR};
                    background-color: rgba(220, 53, 69, 0.1);
                }}
            """)
            if message:
                self.setToolTip(message)
        else:
            self.setStyleSheet("")
            self.setToolTip("")

    def set_success_state(self):
        """Set success state for validation"""
        self.setStyleSheet(f"""
            QLineEdit {{
                border-color: {ModernColors.SUCCESS};
                background-color: rgba(40, 167, 69, 0.1);
            }}
        """)


class ModernTextArea(QTextEdit):
    """Modern text area with enhanced styling"""

    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(100)

        # Set font for better readability
        font = ModernTypography.get_font(
            size=ModernTypography.BODY,
            family=ModernTypography.MONO_FONT
        )
        self.setFont(font)


class ModernProgressBar(QProgressBar):
    """Modern progress bar with enhanced animations"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(8)
        self.setTextVisible(False)

    def set_animated(self, animated=True):
        """Enable smooth animations"""
        if animated:
            self.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background: {ModernColors.GRADIENT_PRIMARY};
                    border-radius: {ModernSpacing.RADIUS_SM}px;
                    margin: 1px;
                    animation: progress-animation 2s ease-in-out infinite;
                }}
                @keyframes progress-animation {{
                    0% {{ background-position: 0% 50%; }}
                    50% {{ background-position: 100% 50%; }}
                    100% {{ background-position: 0% 50%; }}
                }}
            """)


class ModernComboBox(QComboBox):
    """Modern combo box with enhanced styling"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)

    def add_items_with_data(self, items_data):
        """Add items with associated data"""
        for text, data in items_data:
            self.addItem(text, data)


class ModernSeparator(QFrame):
    """Modern separator line"""

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(parent)
        if orientation == Qt.Horizontal:
            self.setFrameShape(QFrame.HLine)
            self.setFixedHeight(1)
        else:
            self.setFrameShape(QFrame.VLine)
            self.setFixedWidth(1)

        self.setStyleSheet(f"""
            QFrame {{
                color: {ModernColors.BORDER};
                background-color: {ModernColors.BORDER};
                border: none;
            }}
        """)


class ModernToggleButton(QPushButton):
    """Modern toggle button with on/off states"""

    toggled = pyqtSignal(bool)

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.is_toggled = False
        self.setCheckable(True)
        self.clicked.connect(self.on_toggle)
        self.setup_toggle()

    def setup_toggle(self):
        """Setup toggle button styling"""
        self.setMinimumHeight(32)
        self.update_style()

    def on_toggle(self):
        """Handle toggle event"""
        self.is_toggled = not self.is_toggled
        self.update_style()
        self.toggled.emit(self.is_toggled)

    def update_style(self):
        """Update button style based on state"""
        if self.is_toggled:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {ModernColors.GRADIENT_PRIMARY};
                    border: 2px solid {ModernColors.PRIMARY};
                    color: {ModernColors.TEXT_PRIMARY};
                    font-weight: {ModernTypography.SEMIBOLD};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {ModernColors.BG_TERTIARY};
                    border: 2px solid {ModernColors.BORDER};
                    color: {ModernColors.TEXT_SECONDARY};
                }}
            """)


class ModernStatusIndicator(QLabel):
    """Modern status indicator with colored dots"""

    def __init__(self, status="inactive", parent=None):
        super().__init__(parent)
        self.current_status = status
        self.setFixedSize(12, 12)
        self.update_status(status)

    def update_status(self, status):
        """Update status indicator"""
        self.current_status = status

        colors = {
            "active": ModernColors.SUCCESS,
            "inactive": ModernColors.TEXT_DISABLED,
            "warning": ModernColors.WARNING,
            "error": ModernColors.ERROR,
            "connecting": ModernColors.INFO
        }

        color = colors.get(status, ModernColors.TEXT_DISABLED)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                border: 2px solid {ModernColors.BG_PRIMARY};
            }}
        """)

        # Add pulsing animation for connecting state
        if status == "connecting":
            self.start_pulse_animation()

    def start_pulse_animation(self):
        """Start pulsing animation"""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0.3)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutSine)
        self.animation.setLoopCount(-1)
        self.animation.start()


class ModernTooltip(QLabel):
    """Modern tooltip with enhanced styling"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWindowFlags(Qt.ToolTip)
        self.setup_tooltip()

    def setup_tooltip(self):
        """Setup tooltip styling"""
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {ModernColors.BG_SECONDARY};
                color: {ModernColors.TEXT_PRIMARY};
                border: 1px solid {ModernColors.BORDER};
                border-radius: {ModernSpacing.RADIUS_MD}px;
                padding: {ModernSpacing.SM}px {ModernSpacing.MD}px;
                font-size: {ModernTypography.CAPTION}px;
            }}
        """)

        # Apply shadow
        ModernTheme.apply_shadow(self, blur=8, offset=(0, 4))


class ModernNotification(QFrame):
    """Modern notification component"""

    def __init__(self, message="", notification_type="info", parent=None):
        super().__init__(parent)
        self.message = message
        self.notification_type = notification_type
        self.setup_notification()

    def setup_notification(self):
        """Setup notification UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(ModernSpacing.LG, ModernSpacing.MD,
                                 ModernSpacing.LG, ModernSpacing.MD)

        # Icon based on type
        icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗"
        }

        colors = {
            "info": ModernColors.INFO,
            "success": ModernColors.SUCCESS,
            "warning": ModernColors.WARNING,
            "error": ModernColors.ERROR
        }

        icon_label = QLabel(icons.get(self.notification_type, "ℹ"))
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: {colors.get(self.notification_type, ModernColors.INFO)};
                font-size: 18px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(icon_label)

        # Message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {ModernColors.TEXT_SECONDARY};
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {ModernColors.TEXT_PRIMARY};
                background-color: {ModernColors.SURFACE_HOVER};
                border-radius: 12px;
            }}
        """)
        close_btn.clicked.connect(self.hide_notification)
        layout.addWidget(close_btn)

        # Set notification style
        border_color = colors.get(self.notification_type, ModernColors.INFO)
        self.setStyleSheet(f"""
            ModernNotification {{
                background-color: {ModernColors.BG_SECONDARY};
                border: 1px solid {border_color};
                border-left: 4px solid {border_color};
                border-radius: {ModernSpacing.RADIUS_MD}px;
                margin: {ModernSpacing.SM}px;
            }}
        """)

        # Apply shadow
        ModernTheme.apply_shadow(self)

        # Auto-hide timer for non-error notifications
        if self.notification_type != "error":
            QTimer.singleShot(5000, self.hide_notification)

    def hide_notification(self):
        """Hide notification with animation"""
        self.hide()

    def show_notification(self):
        """Show notification with animation"""
        self.show()


class ModernLoadingSpinner(QLabel):
    """Modern loading spinner component"""

    def __init__(self, size=32, parent=None):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.setFixedSize(size, size)

        # Setup timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)

        self.setup_spinner()

    def setup_spinner(self):
        """Setup spinner appearance"""
        self.setStyleSheet(f"""
            QLabel {{
                color: {ModernColors.PRIMARY};
                font-size: {self.size - 8}px;
                background: transparent;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setText("◐")

    def start(self):
        """Start spinner animation"""
        self.timer.start(100)  # Update every 100ms
        self.show()

    def stop(self):
        """Stop spinner animation"""
        self.timer.stop()
        self.hide()

    def rotate(self):
        """Rotate spinner"""
        self.angle = (self.angle + 45) % 360

        # Simple text rotation effect
        spinner_chars = ["◐", "◓", "◑", "◒"]
        char_index = (self.angle // 45) % len(spinner_chars)
        self.setText(spinner_chars[char_index])


class ModernBadge(QLabel):
    """Modern badge component for status indicators"""

    def __init__(self, text="", badge_type="default", parent=None):
        super().__init__(text, parent)
        self.badge_type = badge_type
        self.setup_badge()

    def setup_badge(self):
        """Setup badge styling"""
        self.setAlignment(Qt.AlignCenter)

        colors = {
            "default": (ModernColors.BG_QUATERNARY, ModernColors.TEXT_PRIMARY),
            "primary": (ModernColors.PRIMARY, ModernColors.TEXT_PRIMARY),
            "success": (ModernColors.SUCCESS, ModernColors.TEXT_PRIMARY),
            "warning": (ModernColors.WARNING, ModernColors.TEXT_INVERSE),
            "error": (ModernColors.ERROR, ModernColors.TEXT_PRIMARY),
            "info": (ModernColors.INFO, ModernColors.TEXT_PRIMARY)
        }

        bg_color, text_color = colors.get(self.badge_type, colors["default"])

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: {ModernSpacing.RADIUS_ROUND}px;
                padding: {ModernSpacing.XS}px {ModernSpacing.SM}px;
                font-size: {ModernTypography.SMALL}px;
                font-weight: {ModernTypography.SEMIBOLD};
                min-width: 20px;
            }}
        """)

        # Calculate size based on content
        font_metrics = QFontMetrics(self.font())
        text_width = font_metrics.horizontalAdvance(self.text())
        self.setFixedSize(max(24, text_width + 16), 20)


class ModernSearchBox(QLineEdit):
    """Modern search box with search icon and clear button"""

    def __init__(self, placeholder="Search...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setup_search_box()

    def setup_search_box(self):
        """Setup search box with icons"""
        self.setStyleSheet(f"""
            QLineEdit {{
                padding-left: {ModernSpacing.XXL}px;
                padding-right: {ModernSpacing.XXL}px;
                background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{ModernColors.TEXT_SECONDARY}"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>');
                background-repeat: no-repeat;
                background-position: {ModernSpacing.MD}px center;
                background-size: 16px 16px;
            }}
        """)

        # Add clear button functionality
        self.textChanged.connect(self.toggle_clear_button)

    def toggle_clear_button(self):
        """Show/hide clear button based on content"""
        # This would typically add a clear button widget
        # For now, we can implement Esc key clearing
        pass

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            self.clear()
        super().keyPressEvent(event)