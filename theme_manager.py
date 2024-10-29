# theme_manager.py

import os
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject

class ThemeManager(QObject):
    def __init__(self, bin_folder):
        super().__init__()
        self.themes_dir = os.path.join(bin_folder, 'themes')
        if not os.path.exists(self.themes_dir):
            os.makedirs(self.themes_dir)

    def get_available_themes(self):
        return [os.path.splitext(f)[0] for f in os.listdir(self.themes_dir) if f.endswith('.qss')]

    def apply_theme(self, theme_name, app):
        theme_path = os.path.join(self.themes_dir, f'{theme_name}.qss')
        if os.path.exists(theme_path):
            with open(theme_path, 'r') as stylesheet:
                app.setStyleSheet(stylesheet.read())
        else:
            QMessageBox.warning(None, "Theme Error", f"Theme '{theme_name}' not found.")
