# utils.py

from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

def fade_in_widget(widget, duration=1000):
    effect = QGraphicsOpacityEffect()
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0)
    animation.setEndValue(1)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start()
    widget.animation = animation  # Keep a reference to prevent garbage collection
