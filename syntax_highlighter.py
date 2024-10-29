# syntax_highlighter.py

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression

import keyword

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#C586C0'))
        keywords = keyword.kwlist
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlighting_rules.append((pattern, keyword_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#CE9178'))
        self.highlighting_rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#6A9955'))
        self.highlighting_rules.append((QRegularExpression(r'#.*'), comment_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor('#DCDCAA'))
        self.highlighting_rules.append((QRegularExpression(r'\bdef\b\s*(\w+)'), function_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, format)
