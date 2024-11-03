# main.py

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPlainTextEdit,
    QTreeWidget, QTreeWidgetItem, QDockWidget, QStatusBar, QFileDialog,
    QMessageBox, QInputDialog, QFontDialog, QTabWidget, QHBoxLayout, QPushButton,
    QMenu, QSizePolicy
)
from PyQt6.QtGui import QKeySequence, QFontDatabase, QShortcut, QAction, QColor, QIcon
from PyQt6.QtCore import Qt, QPoint, QTimer

from code_editor import CodeEditor
from dashboard import Dashboard
from custom_title_bar import TitleBar
from utils import fade_in_widget
from theme_manager import ThemeManager
import qtawesome as qta

class LAEFEXExecutor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LAEFEX - Version 1.1.0")
        self.setGeometry(100, 100, 1000, 700)
        self.bin_folder = os.path.join(os.path.dirname(__file__), 'bin')
        if not os.path.exists(self.bin_folder):
            os.makedirs(self.bin_folder)
        self.load_fonts()
        self.theme_manager = ThemeManager(self.bin_folder)
        self.setup_ui()
        self.fade_in_main_window()

    def load_fonts(self):
        # Load fonts from bin/fonts
        fonts_dir = os.path.join(self.bin_folder, 'fonts')
        if os.path.exists(fonts_dir):
            for font_file in os.listdir(fonts_dir):
                if font_file.endswith('.ttf') or font_file.endswith('.otf'):
                    QFontDatabase.addApplicationFont(os.path.join(fonts_dir, font_file))
        else:
            os.makedirs(fonts_dir)

    def setup_ui(self):
        # Remove window frame
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Set window icon
        self.setWindowIcon(QIcon('path_to_icon.png'))  # Replace with your icon path

        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)  # Ensure no spacing between widgets

        # Custom Title Bar
        self.title_bar = TitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Tool Bar
        self.create_tool_bar()
        main_layout.addWidget(self.tool_bar)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                background: #2d2d2d;
                color: #ffffff;
                padding: 10px;
            }
            QTabBar::tab:selected {
                background: #3d3d3d;
            }
            QTabWidget::pane {
                border: none;
            }
        """)

        # Add Dashboard Tab
        dashboard = Dashboard()
        index = self.tab_widget.addTab(dashboard, "Dashboard")
        self.tab_widget.setCurrentIndex(index)

        self.new_tab()

        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)

        self.setCentralWidget(central_widget)

        # Variable Explorer Dock
        self.variable_explorer = QTreeWidget()
        self.variable_explorer.setHeaderLabels(['Variable', 'Type', 'Value'])
        variable_dock = QDockWidget("Variable Explorer", self)
        variable_dock.setWidget(self.variable_explorer)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, variable_dock)

        # Integrated Terminal
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.terminal.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        terminal_dock = QDockWidget("Terminal", self)
        terminal_dock.setWidget(self.terminal)
        terminal_dock.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        terminal_dock.hide()  # Start minimized
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, terminal_dock)
        self.terminal_dock = terminal_dock  # Keep a reference

        # Apply default theme
        self.apply_theme('dark')  # Set your default theme here

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Shortcuts
        new_tab_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_tab_shortcut.activated.connect(self.new_tab)
        close_tab_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        close_tab_shortcut.activated.connect(self.close_current_tab)

    def fade_in_main_window(self):
        fade_in_widget(self, duration=1500)

    def create_tool_bar(self):
        # Create custom toolbar
        self.tool_bar = QWidget()
        tool_bar_layout = QHBoxLayout(self.tool_bar)
        tool_bar_layout.setContentsMargins(5, 5, 5, 5)
        tool_bar_layout.setSpacing(10)

        self.tool_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.tool_bar.setStyleSheet("background-color: #252525;")

        # Run Button
        run_icon = qta.icon('fa.play', color='green')
        run_button = QPushButton(run_icon, "")
        run_button.setFixedSize(40, 40)
        run_button.setToolTip("Run Code")
        run_button.setStyleSheet(self.button_style())
        run_button.clicked.connect(self.run_code)
        tool_bar_layout.addWidget(run_button)

        # Debug Button
        debug_icon = qta.icon('fa.bug', color='orange')
        debug_button = QPushButton(debug_icon, "")
        debug_button.setFixedSize(40, 40)
        debug_button.setToolTip("Debug Code")
        debug_button.setStyleSheet(self.button_style())
        debug_button.clicked.connect(self.debug_code)
        tool_bar_layout.addWidget(debug_button)

        # Stop Button
        stop_icon = qta.icon('fa.stop', color='red')
        stop_button = QPushButton(stop_icon, "")
        stop_button.setFixedSize(40, 40)
        stop_button.setToolTip("Stop Execution")
        stop_button.setStyleSheet(self.button_style())
        stop_button.clicked.connect(self.stop_code)
        tool_bar_layout.addWidget(stop_button)

        # Settings Button
        settings_icon = qta.icon('fa.cog', color='white')
        settings_button = QPushButton(settings_icon, "")
        settings_button.setFixedSize(40, 40)
        settings_button.setToolTip("Settings")
        settings_button.setStyleSheet(self.button_style())
        settings_button.clicked.connect(self.open_settings_menu)
        tool_bar_layout.addWidget(settings_button)

        # Toggle Terminal Button
        terminal_icon = qta.icon('fa.terminal', color='white')
        terminal_button = QPushButton(terminal_icon, "")
        terminal_button.setFixedSize(40, 40)
        terminal_button.setToolTip("Toggle Terminal")
        terminal_button.setStyleSheet(self.button_style())
        terminal_button.clicked.connect(self.toggle_terminal_visibility)
        tool_bar_layout.addWidget(terminal_button)

        # Spacer
        tool_bar_layout.addStretch()

    def button_style(self):
        return """
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """

    def open_settings_menu(self):
        # Create a simple settings menu
        menu = QMenu()
        change_theme_action = QAction("Change Theme", self)
        change_theme_action.triggered.connect(self.change_theme)
        menu.addAction(change_theme_action)

        change_font_action = QAction("Change Font", self)
        change_font_action.triggered.connect(self.change_font)
        menu.addAction(change_font_action)

        # Position the menu under the settings button
        sender = self.sender()
        if sender:
            menu.exec(sender.mapToGlobal(QPoint(0, sender.height())))

    def apply_theme(self, theme_name):
        self.theme_manager.apply_theme(theme_name, self)

    def new_tab(self):
        # Create a new code editor
        code_editor = CodeEditor()
        fade_in_widget(code_editor, duration=800)

        # Add to tab widget
        index = self.tab_widget.addTab(code_editor, "Untitled")
        self.tab_widget.setCurrentIndex(index)

    def close_tab(self, index):
        widget = self.tab_widget.widget(index)
        from dashboard import Dashboard
        if isinstance(widget, Dashboard):
            QMessageBox.warning(self, "Action Denied", "Cannot close the Dashboard tab.")
        else:
            self.tab_widget.removeTab(index)

    def close_current_tab(self):
        index = self.tab_widget.currentIndex()
        if index >= 0:
            self.close_tab(index)

    def get_current_code_editor(self):
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, CodeEditor):
            return current_widget
        return None

    def run_code(self):
        code_editor = self.get_current_code_editor()
        if code_editor:
            code = code_editor.editor.toPlainText()
            self.terminal.clear()

            # Write the code to a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
                tmp_file.write(code)
                tmp_file_path = tmp_file.name

            # Execute the code in a subprocess
            import subprocess
            try:
                result = subprocess.run(
                    [sys.executable, tmp_file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                output = result.stdout
                errors = result.stderr

                if output:
                    self.terminal.appendPlainText(output)
                if errors:
                    self.terminal.appendPlainText(errors)
                # Show terminal if there is output
                if output or errors:
                    self.terminal_dock.show()
                # Since subprocess runs in a separate process, we cannot update the variable explorer
                self.variable_explorer.clear()
            except Exception as e:
                self.terminal.appendPlainText(str(e))
                self.terminal_dock.show()
            finally:
                os.remove(tmp_file_path)  # Clean up the temporary file

    def debug_code(self):
        QMessageBox.information(self, "Debug", "Debugging not implemented yet.")

    def stop_code(self):
        QMessageBox.information(self, "Stop", "Stopping code not implemented yet.")

    def toggle_terminal_visibility(self):
        if self.terminal_dock.isVisible():
            self.terminal_dock.hide()
        else:
            self.terminal_dock.show()

    # --- Settings Actions ---
    def change_theme(self):
        themes = self.theme_manager.get_available_themes()
        theme, ok = QInputDialog.getItem(self, "Select Theme", "Theme:", themes, 0, False)
        if ok and theme:
            self.apply_theme(theme)

    def change_font(self):
        font, ok = QFontDialog.getFont()
        if ok:
            self.setFont(font)

    # --- Help Actions ---
    def show_about(self):
        QMessageBox.information(self, "About LAEFEX",
                                "LAEFEX Version 1.1.0\n\nA powerful Python code editor and executor.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LAEFEXExecutor()
    window.show()
    sys.exit(app.exec())
