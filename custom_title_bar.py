# custom_title_bar.py

from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt, QPoint

class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.startPos = None
        self.moving = False

    def init_ui(self):
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: #2d2d2d;")

        self.title = QLabel("LAEFEX - Version 1.1.0")
        self.title.setStyleSheet("color: #ffffff; font-size: 12px;")

        # Minimize, Maximize, Close buttons
        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet("background-color: transparent; color: #ffffff;")
        self.minimize_button.clicked.connect(self.parent.showMinimized)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(30, 30)
        self.maximize_button.setStyleSheet("background-color: transparent; color: #ffffff;")
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("background-color: transparent; color: #ffffff;")
        self.close_button.clicked.connect(self.parent.close)

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def toggle_maximize_restore(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos = event.globalPosition().toPoint()
            self.moving = True

    def mouseMoveEvent(self, event):
        if self.moving:
            delta = event.globalPosition().toPoint() - self.startPos
            self.parent.move(self.parent.pos() + delta)
            self.startPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.moving = False
