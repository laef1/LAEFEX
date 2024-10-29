# dashboard.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from utils import fade_in_widget

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        fade_in_widget(self, duration=1000)

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        title = QLabel("Welcome to LAEFEX")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        news = QLabel(self.get_news())
        news.setWordWrap(True)
        news.setStyleSheet("font-size: 14px;")

        layout.addWidget(title)
        layout.addWidget(news)

    def get_news(self):
        # Placeholder for fetching news/hotfixes
        return "Latest Updates:\n\n- Version 1.1 released.\n- Added multiple themes.\n- Enhanced GUI with animations."
