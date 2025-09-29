"""
Modern UI Theme System for JETSSH Enhanced
Provides a comprehensive modern design system with themes, components, and styling
"""

from PyQt5.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect
from PyQt5.QtGui import QColor, QPalette, QFont, QFontDatabase, QPainter, QPen, QBrush, QLinearGradient


class ModernColors:
    """Modern color palette for JETSSH Enhanced"""

    # Primary Theme Colors
    PRIMARY = "#0078d4"
    PRIMARY_LIGHT = "#106ebe"
    PRIMARY_DARK = "#005a9e"
    PRIMARY_HOVER = "#1084d8"

    # Secondary Colors
    SECONDARY = "#6c757d"
    SECONDARY_LIGHT = "#858a8e"
    SECONDARY_DARK = "#545b62"

    # Accent Colors
    ACCENT = "#00d4aa"
    ACCENT_LIGHT = "#1ae0b5"
    ACCENT_DARK = "#00b894"

    # Status Colors
    SUCCESS = "#28a745"
    SUCCESS_LIGHT = "#34ce57"
    SUCCESS_DARK = "#1e7e34"

    WARNING = "#ffc107"
    WARNING_LIGHT = "#ffcd39"
    WARNING_DARK = "#e0a800"

    ERROR = "#dc3545"
    ERROR_LIGHT = "#e15564"
    ERROR_DARK = "#c82333"

    INFO = "#17a2b8"
    INFO_LIGHT = "#3db5c9"
    INFO_DARK = "#138496"

    # Background Colors
    BG_PRIMARY = "#0d1117"
    BG_SECONDARY = "#161b22"
    BG_TERTIARY = "#21262d"
    BG_QUATERNARY = "#30363d"

    # Surface Colors
    SURFACE = "#1c2128"
    SURFACE_HOVER = "#262c36"
    SURFACE_ACTIVE = "#2d3748"

    # Border Colors
    BORDER = "#30363d"
    BORDER_LIGHT = "#484f58"
    BORDER_FOCUS = "#0078d4"

    # Text Colors
    TEXT_PRIMARY = "#f0f6fc"
    TEXT_SECONDARY = "#8b949e"
    TEXT_TERTIARY = "#6e7681"
    TEXT_DISABLED = "#484f58"
    TEXT_INVERSE = "#24292f"

    # Glass/Transparent Effects
    GLASS_LIGHT = "rgba(255, 255, 255, 0.1)"
    GLASS_MEDIUM = "rgba(255, 255, 255, 0.05)"
    GLASS_DARK = "rgba(0, 0, 0, 0.3)"

    # Gradient Presets
    GRADIENT_PRIMARY = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PRIMARY}, stop:1 {PRIMARY_DARK})"
    GRADIENT_SURFACE = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {SURFACE}, stop:1 {BG_TERTIARY})"
    GRADIENT_BUTTON = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {BG_QUATERNARY}, stop:1 {BG_TERTIARY})"


class ModernTypography:
    """Modern typography system"""

    # Font Families
    PRIMARY_FONT = "Segoe UI"
    MONO_FONT = "Consolas"

    # Font Sizes
    H1 = 32
    H2 = 28
    H3 = 24
    H4 = 20
    H5 = 18
    H6 = 16
    BODY = 14
    CAPTION = 12
    SMALL = 10

    # Font Weights
    THIN = 100
    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700
    BLACK = 900

    @staticmethod
    def get_font(size=BODY, weight=REGULAR, family=PRIMARY_FONT):
        """Get a font with specified properties"""
        font = QFont(family, size)
        font.setWeight(weight)
        return font


class ModernSpacing:
    """Modern spacing system"""

    # Base unit (4px)
    UNIT = 4

    # Spacing scale
    XS = UNIT * 1      # 4px
    SM = UNIT * 2      # 8px
    MD = UNIT * 3      # 12px
    LG = UNIT * 4      # 16px
    XL = UNIT * 5      # 20px
    XXL = UNIT * 6     # 24px
    XXXL = UNIT * 8    # 32px

    # Component-specific spacing
    BUTTON_PADDING = f"{MD}px {LG}px"
    INPUT_PADDING = f"{SM}px {MD}px"
    CARD_PADDING = f"{LG}px"
    DIALOG_PADDING = f"{XXL}px"

    # Border radius
    RADIUS_SM = 4
    RADIUS_MD = 6
    RADIUS_LG = 8
    RADIUS_XL = 12
    RADIUS_ROUND = 50


class ModernTheme:
    """Main theme class that provides complete styling"""

    @staticmethod
    def get_application_style():
        """Get the main application stylesheet"""
        return f"""
        /* Global Application Styles */
        QMainWindow {{
            background-color: {ModernColors.BG_PRIMARY};
            color: {ModernColors.TEXT_PRIMARY};
            font-family: '{ModernTypography.PRIMARY_FONT}';
            font-size: {ModernTypography.BODY}px;
        }}

        QWidget {{
            background-color: transparent;
            color: {ModernColors.TEXT_PRIMARY};
            font-family: '{ModernTypography.PRIMARY_FONT}';
            selection-background-color: {ModernColors.PRIMARY};
            selection-color: {ModernColors.TEXT_PRIMARY};
        }}

        /* Modern Buttons */
        QPushButton {{
            background: {ModernColors.GRADIENT_BUTTON};
            border: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_PRIMARY};
            font-weight: {ModernTypography.MEDIUM};
            padding: {ModernSpacing.BUTTON_PADDING};
            min-height: 20px;
            transition: all 0.2s ease;
        }}

        QPushButton:hover {{
            background: {ModernColors.SURFACE_HOVER};
            border-color: {ModernColors.BORDER_LIGHT};
            transform: translateY(-1px);
        }}

        QPushButton:pressed {{
            background: {ModernColors.SURFACE_ACTIVE};
            transform: translateY(0px);
        }}

        QPushButton:disabled {{
            background: {ModernColors.BG_TERTIARY};
            color: {ModernColors.TEXT_DISABLED};
            border-color: {ModernColors.BORDER};
        }}

        /* Primary Button Variant */
        QPushButton[buttonType="primary"] {{
            background: {ModernColors.GRADIENT_PRIMARY};
            border: 1px solid {ModernColors.PRIMARY_DARK};
            color: {ModernColors.TEXT_PRIMARY};
            font-weight: {ModernTypography.SEMIBOLD};
        }}

        QPushButton[buttonType="primary"]:hover {{
            background: {ModernColors.PRIMARY_HOVER};
            border-color: {ModernColors.PRIMARY_LIGHT};
        }}

        QPushButton[buttonType="primary"]:pressed {{
            background: {ModernColors.PRIMARY_DARK};
        }}

        /* Success Button Variant */
        QPushButton[buttonType="success"] {{
            background: {ModernColors.SUCCESS};
            border: 1px solid {ModernColors.SUCCESS_DARK};
            color: white;
        }}

        QPushButton[buttonType="success"]:hover {{
            background: {ModernColors.SUCCESS_LIGHT};
        }}

        /* Warning Button Variant */
        QPushButton[buttonType="warning"] {{
            background: {ModernColors.WARNING};
            border: 1px solid {ModernColors.WARNING_DARK};
            color: {ModernColors.TEXT_INVERSE};
        }}

        QPushButton[buttonType="warning"]:hover {{
            background: {ModernColors.WARNING_LIGHT};
        }}

        /* Error Button Variant */
        QPushButton[buttonType="error"] {{
            background: {ModernColors.ERROR};
            border: 1px solid {ModernColors.ERROR_DARK};
            color: white;
        }}

        QPushButton[buttonType="error"]:hover {{
            background: {ModernColors.ERROR_LIGHT};
        }}

        /* Modern Input Fields */
        QLineEdit {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 2px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_PRIMARY};
            padding: {ModernSpacing.INPUT_PADDING};
            font-size: {ModernTypography.BODY}px;
            selection-background-color: {ModernColors.PRIMARY};
        }}

        QLineEdit:focus {{
            border-color: {ModernColors.BORDER_FOCUS};
            background-color: {ModernColors.BG_TERTIARY};
        }}

        QLineEdit:disabled {{
            background-color: {ModernColors.BG_TERTIARY};
            color: {ModernColors.TEXT_DISABLED};
            border-color: {ModernColors.BORDER};
        }}

        /* Modern ComboBox */
        QComboBox {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 2px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_PRIMARY};
            padding: {ModernSpacing.INPUT_PADDING};
            min-width: 100px;
        }}

        QComboBox:hover {{
            border-color: {ModernColors.BORDER_LIGHT};
        }}

        QComboBox:focus {{
            border-color: {ModernColors.BORDER_FOCUS};
        }}

        QComboBox::drop-down {{
            border: none;
            background: transparent;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {ModernColors.TEXT_SECONDARY};
            margin-right: 10px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_PRIMARY};
            selection-background-color: {ModernColors.PRIMARY};
            padding: {ModernSpacing.SM}px;
        }}

        /* Modern List Widgets */
        QListWidget {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_PRIMARY};
            alternate-background-color: {ModernColors.BG_TERTIARY};
            outline: none;
        }}

        QListWidget::item {{
            padding: {ModernSpacing.MD}px;
            border-bottom: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_SM}px;
            margin: 2px;
        }}

        QListWidget::item:selected {{
            background: {ModernColors.GRADIENT_PRIMARY};
            color: {ModernColors.TEXT_PRIMARY};
        }}

        QListWidget::item:hover {{
            background-color: {ModernColors.SURFACE_HOVER};
        }}

        /* Modern Tree Widgets */
        QTreeWidget {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_PRIMARY};
            alternate-background-color: {ModernColors.BG_TERTIARY};
            outline: none;
        }}

        QTreeWidget::item {{
            padding: {ModernSpacing.SM}px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        QTreeWidget::item:selected {{
            background: {ModernColors.GRADIENT_PRIMARY};
        }}

        QTreeWidget::item:hover {{
            background-color: {ModernColors.SURFACE_HOVER};
        }}

        QHeaderView::section {{
            background: {ModernColors.GRADIENT_SURFACE};
            border: 1px solid {ModernColors.BORDER};
            color: {ModernColors.TEXT_PRIMARY};
            padding: {ModernSpacing.SM}px;
            font-weight: {ModernTypography.SEMIBOLD};
        }}

        /* Modern Text Areas */
        QTextEdit {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 2px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_PRIMARY};
            selection-background-color: {ModernColors.PRIMARY};
            font-family: '{ModernTypography.MONO_FONT}';
            font-size: {ModernTypography.BODY}px;
            padding: {ModernSpacing.MD}px;
        }}

        QTextEdit:focus {{
            border-color: {ModernColors.BORDER_FOCUS};
        }}

        /* Modern Tabs */
        QTabWidget::pane {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            margin-top: 2px;
        }}

        QTabWidget::tab-bar {{
            alignment: left;
        }}

        QTabBar::tab {{
            background: {ModernColors.BG_TERTIARY};
            border: 1px solid {ModernColors.BORDER};
            border-bottom: none;
            border-top-left-radius: {ModernSpacing.RADIUS_MD}px;
            border-top-right-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_SECONDARY};
            padding: {ModernSpacing.MD}px {ModernSpacing.LG}px;
            margin-right: 2px;
            min-width: 100px;
            font-weight: {ModernTypography.MEDIUM};
        }}

        QTabBar::tab:selected {{
            background: {ModernColors.GRADIENT_PRIMARY};
            color: {ModernColors.TEXT_PRIMARY};
            border-color: {ModernColors.PRIMARY};
        }}

        QTabBar::tab:hover {{
            background-color: {ModernColors.SURFACE_HOVER};
            color: {ModernColors.TEXT_PRIMARY};
        }}

        QTabBar::close-button {{
            image: none;
            background: {ModernColors.ERROR};
            border-radius: 8px;
            width: 16px;
            height: 16px;
            margin: 2px;
        }}

        QTabBar::close-button:hover {{
            background: {ModernColors.ERROR_LIGHT};
        }}

        /* Modern Menu System */
        QMenuBar {{
            background: {ModernColors.GRADIENT_SURFACE};
            border-bottom: 1px solid {ModernColors.BORDER};
            color: {ModernColors.TEXT_PRIMARY};
            padding: {ModernSpacing.SM}px;
        }}

        QMenuBar::item {{
            background: transparent;
            padding: {ModernSpacing.SM}px {ModernSpacing.MD}px;
            border-radius: {ModernSpacing.RADIUS_SM}px;
        }}

        QMenuBar::item:selected {{
            background-color: {ModernColors.SURFACE_HOVER};
        }}

        QMenu {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            color: {ModernColors.TEXT_PRIMARY};
            padding: {ModernSpacing.SM}px;
        }}

        QMenu::item {{
            padding: {ModernSpacing.SM}px {ModernSpacing.LG}px;
            border-radius: {ModernSpacing.RADIUS_SM}px;
            margin: 2px;
        }}

        QMenu::item:selected {{
            background: {ModernColors.GRADIENT_PRIMARY};
        }}

        QMenu::separator {{
            height: 1px;
            background: {ModernColors.BORDER};
            margin: {ModernSpacing.SM}px;
        }}

        /* Modern Toolbar */
        QToolBar {{
            background: {ModernColors.GRADIENT_SURFACE};
            border: none;
            padding: {ModernSpacing.SM}px;
            spacing: {ModernSpacing.SM}px;
        }}

        QToolBar::separator {{
            background: {ModernColors.BORDER};
            width: 1px;
            margin: {ModernSpacing.SM}px;
        }}

        QToolButton {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: {ModernSpacing.RADIUS_MD}px;
            padding: {ModernSpacing.SM}px;
            margin: 2px;
        }}

        QToolButton:hover {{
            background-color: {ModernColors.SURFACE_HOVER};
            border-color: {ModernColors.BORDER_LIGHT};
        }}

        QToolButton:pressed {{
            background-color: {ModernColors.SURFACE_ACTIVE};
        }}

        /* Modern Status Bar */
        QStatusBar {{
            background: {ModernColors.GRADIENT_SURFACE};
            border-top: 1px solid {ModernColors.BORDER};
            color: {ModernColors.TEXT_SECONDARY};
            padding: {ModernSpacing.SM}px;
        }}

        QStatusBar::item {{
            border: none;
        }}

        /* Modern Splitter */
        QSplitter::handle {{
            background: {ModernColors.BORDER_LIGHT};
            border-radius: 2px;
        }}

        QSplitter::handle:horizontal {{
            width: 3px;
            margin: 2px 0px;
        }}

        QSplitter::handle:vertical {{
            height: 3px;
            margin: 0px 2px;
        }}

        QSplitter::handle:hover {{
            background: {ModernColors.PRIMARY};
        }}

        /* Modern Scrollbars */
        QScrollBar:vertical {{
            background: {ModernColors.BG_TERTIARY};
            width: 12px;
            border-radius: 6px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {ModernColors.BORDER_LIGHT};
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background: {ModernColors.TEXT_SECONDARY};
        }}

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            border: none;
            background: none;
        }}

        QScrollBar:horizontal {{
            background: {ModernColors.BG_TERTIARY};
            height: 12px;
            border-radius: 6px;
            margin: 0px;
        }}

        QScrollBar::handle:horizontal {{
            background: {ModernColors.BORDER_LIGHT};
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {ModernColors.TEXT_SECONDARY};
        }}

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
        }}

        /* Modern Progress Bars */
        QProgressBar {{
            background-color: {ModernColors.BG_TERTIARY};
            border: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_MD}px;
            text-align: center;
            color: {ModernColors.TEXT_PRIMARY};
            font-weight: {ModernTypography.MEDIUM};
            padding: 2px;
        }}

        QProgressBar::chunk {{
            background: {ModernColors.GRADIENT_PRIMARY};
            border-radius: {ModernSpacing.RADIUS_SM}px;
            margin: 1px;
        }}

        /* Modern Dialog Boxes */
        QDialog {{
            background-color: {ModernColors.BG_SECONDARY};
            border: 1px solid {ModernColors.BORDER};
            border-radius: {ModernSpacing.RADIUS_LG}px;
        }}

        /* Modern Message Boxes */
        QMessageBox {{
            background-color: {ModernColors.BG_SECONDARY};
            color: {ModernColors.TEXT_PRIMARY};
        }}

        QMessageBox QPushButton {{
            min-width: 80px;
            margin: {ModernSpacing.SM}px;
        }}

        /* Modern Labels */
        QLabel {{
            color: {ModernColors.TEXT_PRIMARY};
            background: transparent;
        }}

        QLabel[labelType="title"] {{
            font-size: {ModernTypography.H4}px;
            font-weight: {ModernTypography.SEMIBOLD};
            color: {ModernColors.TEXT_PRIMARY};
        }}

        QLabel[labelType="subtitle"] {{
            font-size: {ModernTypography.H6}px;
            font-weight: {ModernTypography.MEDIUM};
            color: {ModernColors.TEXT_SECONDARY};
        }}

        QLabel[labelType="caption"] {{
            font-size: {ModernTypography.CAPTION}px;
            color: {ModernColors.TEXT_TERTIARY};
        }}

        QLabel[labelType="accent"] {{
            color: {ModernColors.ACCENT};
            font-weight: {ModernTypography.SEMIBOLD};
        }}
        """

    @staticmethod
    def apply_shadow(widget, blur=10, offset=(0, 2), color=ModernColors.GLASS_DARK):
        """Apply modern drop shadow to widget"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setXOffset(offset[0])
        shadow.setYOffset(offset[1])
        shadow.setColor(QColor(color))
        widget.setGraphicsEffect(shadow)

    @staticmethod
    def create_gradient(start_color, end_color, direction=Qt.Vertical):
        """Create a linear gradient"""
        gradient = QLinearGradient()
        if direction == Qt.Vertical:
            gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
            gradient.setStart(0, 0)
            gradient.setFinalStop(0, 1)
        else:
            gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
            gradient.setStart(0, 0)
            gradient.setFinalStop(1, 0)

        gradient.setColorAt(0, QColor(start_color))
        gradient.setColorAt(1, QColor(end_color))
        return gradient


class ModernAnimations:
    """Animation utilities for modern UI effects"""

    @staticmethod
    def fade_in(widget, duration=300):
        """Fade in animation"""
        widget.setWindowOpacity(0)
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        return animation

    @staticmethod
    def slide_in(widget, direction="bottom", duration=300):
        """Slide in animation"""
        geometry = widget.geometry()
        if direction == "bottom":
            start_geometry = QRect(geometry.x(), geometry.y() + geometry.height(),
                                 geometry.width(), geometry.height())
        elif direction == "top":
            start_geometry = QRect(geometry.x(), geometry.y() - geometry.height(),
                                 geometry.width(), geometry.height())
        elif direction == "left":
            start_geometry = QRect(geometry.x() - geometry.width(), geometry.y(),
                                 geometry.width(), geometry.height())
        else:  # right
            start_geometry = QRect(geometry.x() + geometry.width(), geometry.y(),
                                 geometry.width(), geometry.height())

        widget.setGeometry(start_geometry)

        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setStartValue(start_geometry)
        animation.setEndValue(geometry)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        return animation


class ModernIconSystem:
    """Modern icon system using Unicode symbols and custom styling"""

    # Navigation Icons
    HOME = "🏠"
    BACK = "←"
    FORWARD = "→"
    UP = "↑"
    DOWN = "↓"
    REFRESH = "↻"

    # Action Icons
    ADD = "+"
    REMOVE = "−"
    EDIT = "✎"
    DELETE = "🗑"
    SAVE = "💾"
    COPY = "📋"
    CUT = "✂"
    PASTE = "📄"

    # Connection Icons
    CONNECT = "🔗"
    DISCONNECT = "🔌"
    NETWORK = "🌐"
    SERVER = "🖥"

    # File Icons
    FILE = "📄"
    FOLDER = "📁"
    UPLOAD = "⬆"
    DOWNLOAD = "⬇"

    # Tool Icons
    SETTINGS = "⚙"
    TERMINAL = "💻"
    TUNNEL = "🚇"
    KEY = "🔑"

    # Status Icons
    SUCCESS = "✓"
    ERROR = "✗"
    WARNING = "⚠"
    INFO = "ℹ"

    @staticmethod
    def get_styled_icon(icon, size=16, color=ModernColors.TEXT_PRIMARY):
        """Get a styled icon label"""
        from PyQt5.QtWidgets import QLabel
        label = QLabel(icon)
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: {size}px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(size + 4, size + 4)
        return label