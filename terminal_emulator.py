"""
Advanced Terminal Emulator Module for JETSSH
Provides VT100/ANSI terminal emulation with full escape sequence support
"""

import re
import logging
from collections import deque
from PyQt5.QtWidgets import QTextEdit, QAction, QMenu
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont, QTextDocument

logger = logging.getLogger(__name__)


class TerminalEmulator(QTextEdit):
    """Advanced terminal emulator with VT100/ANSI support"""

    command_executed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # Terminal state
        self.cursor_row = 0
        self.cursor_col = 0
        self.saved_cursor_row = 0
        self.saved_cursor_col = 0
        self.scroll_region_top = 0
        self.scroll_region_bottom = 24
        self.terminal_width = 80
        self.terminal_height = 24

        # Terminal attributes
        self.current_bg_color = QColor(30, 30, 30)  # Dark background
        self.current_fg_color = QColor(220, 220, 220)  # Light foreground
        self.bold = False
        self.underline = False
        self.reverse = False
        self.blink = False

        # Scrollback buffer
        self.scrollback_buffer = deque(maxlen=10000)
        self.max_scrollback = 10000

        # Search functionality
        self.search_term = ""
        self.search_matches = []
        self.current_search_index = 0

        # Setup terminal
        self.setup_terminal()
        self.setup_context_menu()

        # Color palette (standard 16 colors + 256 color support)
        self.color_palette = self._init_color_palette()

        # Terminal modes
        self.application_mode = False
        self.origin_mode = False
        self.auto_wrap_mode = True
        self.insert_mode = False

    def setup_terminal(self):
        """Initialize terminal settings"""
        self.setReadOnly(True)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Set monospace font
        font = QFont("Consolas", 10)
        font.setFixedPitch(True)
        self.setFont(font)

        # Set dark theme
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #dcdcdc;
                border: 1px solid #3a3a3a;
                selection-background-color: #3a3a3a;
            }
        """)

    def setup_context_menu(self):
        """Setup right-click context menu"""
        self.context_menu = QMenu(self)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy)
        copy_action.setShortcut("Ctrl+C")

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(self.request_paste)
        paste_action.setShortcut("Ctrl+V")

        select_all_action = QAction("Select All", self)
        select_all_action.triggered.connect(self.selectAll)
        select_all_action.setShortcut("Ctrl+A")

        clear_action = QAction("Clear Screen", self)
        clear_action.triggered.connect(self.clear_screen)

        find_action = QAction("Find...", self)
        find_action.triggered.connect(self.show_find_dialog)
        find_action.setShortcut("Ctrl+F")

        self.context_menu.addAction(copy_action)
        self.context_menu.addAction(paste_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(select_all_action)
        self.context_menu.addAction(clear_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(find_action)

    def show_context_menu(self, position):
        """Show context menu at position"""
        self.context_menu.exec_(self.mapToGlobal(position))

    def request_paste(self):
        """Request paste from parent"""
        if hasattr(self.parent, 'paste_to_terminal'):
            self.parent.paste_to_terminal()

    def clear_screen(self):
        """Clear the terminal screen"""
        self.clear()
        self.cursor_row = 0
        self.cursor_col = 0

    def show_find_dialog(self):
        """Show find dialog"""
        from PyQt5.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Find", "Search for:")
        if ok and text:
            self.search_term = text
            self.find_text(text)

    def find_text(self, search_term):
        """Find text in terminal"""
        if not search_term:
            return

        document = self.document()
        self.search_matches = []

        cursor = QTextCursor(document)
        while not cursor.isNull() and not cursor.atEnd():
            cursor = document.find(search_term, cursor)
            if not cursor.isNull():
                self.search_matches.append(cursor)

        if self.search_matches:
            self.current_search_index = 0
            self.highlight_search_match()

    def highlight_search_match(self):
        """Highlight current search match"""
        if self.search_matches and 0 <= self.current_search_index < len(self.search_matches):
            cursor = self.search_matches[self.current_search_index]
            self.setTextCursor(cursor)

    def _init_color_palette(self):
        """Initialize 256-color palette"""
        colors = {}

        # Standard 16 colors
        standard_colors = [
            QColor(0, 0, 0),        # Black
            QColor(128, 0, 0),      # Dark Red
            QColor(0, 128, 0),      # Dark Green
            QColor(128, 128, 0),    # Dark Yellow
            QColor(0, 0, 128),      # Dark Blue
            QColor(128, 0, 128),    # Dark Magenta
            QColor(0, 128, 128),    # Dark Cyan
            QColor(192, 192, 192),  # Light Gray
            QColor(128, 128, 128),  # Dark Gray
            QColor(255, 0, 0),      # Red
            QColor(0, 255, 0),      # Green
            QColor(255, 255, 0),    # Yellow
            QColor(0, 0, 255),      # Blue
            QColor(255, 0, 255),    # Magenta
            QColor(0, 255, 255),    # Cyan
            QColor(255, 255, 255),  # White
        ]

        for i, color in enumerate(standard_colors):
            colors[i] = color

        # 216 color cube (6x6x6)
        for i in range(216):
            r = (i // 36) * 51
            g = ((i % 36) // 6) * 51
            b = (i % 6) * 51
            colors[16 + i] = QColor(r, g, b)

        # 24 grayscale colors
        for i in range(24):
            gray = 8 + i * 10
            colors[232 + i] = QColor(gray, gray, gray)

        return colors

    def process_ansi_escape(self, text):
        """Process ANSI escape sequences and display text"""
        # ANSI escape sequence pattern
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

        parts = ansi_pattern.split(text)
        sequences = ansi_pattern.findall(text)

        cursor = self.textCursor()

        for i, part in enumerate(parts):
            if part:  # Display regular text
                self._insert_text_with_formatting(part, cursor)

            if i < len(sequences):  # Process escape sequence
                self._process_escape_sequence(sequences[i])

        self.setTextCursor(cursor)

    def _insert_text_with_formatting(self, text, cursor):
        """Insert text with current formatting"""
        char_format = QTextCharFormat()

        # Set colors
        char_format.setForeground(self.current_fg_color)
        char_format.setBackground(self.current_bg_color)

        # Set text attributes
        if self.bold:
            char_format.setFontWeight(QFont.Bold)
        if self.underline:
            char_format.setFontUnderline(True)

        cursor.insertText(text, char_format)

    def _process_escape_sequence(self, sequence):
        """Process individual ANSI escape sequence"""
        if not sequence.startswith('\x1b['):
            return

        # Remove escape prefix and get command
        command = sequence[2:]
        if not command:
            return

        command_char = command[-1]
        params = command[:-1].split(';') if command[:-1] else ['']

        # Convert parameters to integers, default to 0
        int_params = []
        for param in params:
            try:
                int_params.append(int(param) if param else 0)
            except ValueError:
                int_params.append(0)

        # Process commands
        if command_char == 'A':  # Cursor Up
            self._cursor_up(int_params[0] if int_params else 1)
        elif command_char == 'B':  # Cursor Down
            self._cursor_down(int_params[0] if int_params else 1)
        elif command_char == 'C':  # Cursor Forward
            self._cursor_forward(int_params[0] if int_params else 1)
        elif command_char == 'D':  # Cursor Backward
            self._cursor_backward(int_params[0] if int_params else 1)
        elif command_char == 'H':  # Cursor Position
            row = int_params[0] - 1 if int_params else 0
            col = int_params[1] - 1 if len(int_params) > 1 else 0
            self._set_cursor_position(row, col)
        elif command_char == 'J':  # Erase Display
            self._erase_display(int_params[0] if int_params else 0)
        elif command_char == 'K':  # Erase Line
            self._erase_line(int_params[0] if int_params else 0)
        elif command_char == 'm':  # Set Graphics Mode
            self._set_graphics_mode(int_params)
        elif command_char == 's':  # Save Cursor Position
            self._save_cursor()
        elif command_char == 'u':  # Restore Cursor Position
            self._restore_cursor()
        elif command_char == 'r':  # Set Scroll Region
            if len(int_params) >= 2:
                self._set_scroll_region(int_params[0] - 1, int_params[1] - 1)

    def _cursor_up(self, count):
        """Move cursor up"""
        cursor = self.textCursor()
        for _ in range(count):
            cursor.movePosition(QTextCursor.Up)
        self.setTextCursor(cursor)

    def _cursor_down(self, count):
        """Move cursor down"""
        cursor = self.textCursor()
        for _ in range(count):
            cursor.movePosition(QTextCursor.Down)
        self.setTextCursor(cursor)

    def _cursor_forward(self, count):
        """Move cursor forward"""
        cursor = self.textCursor()
        for _ in range(count):
            cursor.movePosition(QTextCursor.Right)
        self.setTextCursor(cursor)

    def _cursor_backward(self, count):
        """Move cursor backward"""
        cursor = self.textCursor()
        for _ in range(count):
            cursor.movePosition(QTextCursor.Left)
        self.setTextCursor(cursor)

    def _set_cursor_position(self, row, col):
        """Set absolute cursor position"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start)

        # Move to specified row
        for _ in range(row):
            cursor.movePosition(QTextCursor.Down)

        # Move to specified column
        for _ in range(col):
            cursor.movePosition(QTextCursor.Right)

        self.setTextCursor(cursor)

    def _erase_display(self, mode):
        """Erase display based on mode"""
        cursor = self.textCursor()

        if mode == 0:  # Erase from cursor to end of screen
            cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
        elif mode == 1:  # Erase from start of screen to cursor
            pos = cursor.position()
            cursor.movePosition(QTextCursor.Start, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
        elif mode == 2:  # Erase entire screen
            self.clear()

        self.setTextCursor(cursor)

    def _erase_line(self, mode):
        """Erase line based on mode"""
        cursor = self.textCursor()

        if mode == 0:  # Erase from cursor to end of line
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
        elif mode == 1:  # Erase from start of line to cursor
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
        elif mode == 2:  # Erase entire line
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()

        self.setTextCursor(cursor)

    def _set_graphics_mode(self, params):
        """Set graphics/color mode"""
        if not params:
            params = [0]

        for param in params:
            if param == 0:  # Reset all attributes
                self.current_fg_color = QColor(220, 220, 220)
                self.current_bg_color = QColor(30, 30, 30)
                self.bold = False
                self.underline = False
                self.reverse = False
                self.blink = False
            elif param == 1:  # Bold
                self.bold = True
            elif param == 4:  # Underline
                self.underline = True
            elif param == 7:  # Reverse
                self.reverse = True
            elif param == 5:  # Blink
                self.blink = True
            elif param == 22:  # Normal intensity
                self.bold = False
            elif param == 24:  # No underline
                self.underline = False
            elif param == 27:  # No reverse
                self.reverse = False
            elif param == 25:  # No blink
                self.blink = False
            elif 30 <= param <= 37:  # Foreground colors
                self.current_fg_color = self.color_palette.get(param - 30, QColor(220, 220, 220))
            elif 40 <= param <= 47:  # Background colors
                self.current_bg_color = self.color_palette.get(param - 40, QColor(30, 30, 30))
            elif 90 <= param <= 97:  # Bright foreground colors
                self.current_fg_color = self.color_palette.get(param - 90 + 8, QColor(220, 220, 220))
            elif 100 <= param <= 107:  # Bright background colors
                self.current_bg_color = self.color_palette.get(param - 100 + 8, QColor(30, 30, 30))

    def _save_cursor(self):
        """Save current cursor position"""
        cursor = self.textCursor()
        self.saved_cursor_row = cursor.blockNumber()
        self.saved_cursor_col = cursor.columnNumber()

    def _restore_cursor(self):
        """Restore saved cursor position"""
        self._set_cursor_position(self.saved_cursor_row, self.saved_cursor_col)

    def _set_scroll_region(self, top, bottom):
        """Set scrolling region"""
        self.scroll_region_top = top
        self.scroll_region_bottom = bottom

    def append_output(self, text):
        """Append output to terminal with ANSI processing"""
        # Save current scrollbar position
        scrollbar = self.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()

        # Process ANSI sequences
        self.process_ansi_escape(text)

        # Auto-scroll if we were at the bottom
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

        # Add to scrollback buffer
        lines = text.split('\n')
        for line in lines:
            if line.strip():  # Only add non-empty lines
                self.scrollback_buffer.append(line)

    def keyPressEvent(self, event):
        """Handle key press events"""
        # Don't allow editing in read-only mode
        if event.key() in [Qt.Key_Backspace, Qt.Key_Delete]:
            return

        # Handle copy shortcut
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            if self.textCursor().hasSelection():
                self.copy()
            return

        # Handle find shortcut
        if event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.show_find_dialog()
            return

        # Handle find next/previous
        if event.key() == Qt.Key_F3:
            if self.search_matches:
                if event.modifiers() == Qt.ShiftModifier:
                    self.current_search_index = (self.current_search_index - 1) % len(self.search_matches)
                else:
                    self.current_search_index = (self.current_search_index + 1) % len(self.search_matches)
                self.highlight_search_match()
            return

        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop events for file operations"""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if hasattr(self.parent, 'handle_file_drop'):
                self.parent.handle_file_drop(file_path)

    def get_scrollback_content(self):
        """Get content from scrollback buffer"""
        return '\n'.join(self.scrollback_buffer)

    def export_session(self, file_path):
        """Export session content to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())
            return True
        except Exception as e:
            logger.error(f"Failed to export session: {e}")
            return False