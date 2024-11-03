# syntax_highlighter.py

from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#CC7832'))  # Orange color
        keyword_patterns = [
            r'\bdef\b', r'\bclass\b', r'\breturn\b', r'\bif\b', r'\belse\b',
            r'\belif\b', r'\bwhile\b', r'\bfor\b', r'\bin\b', r'\bimport\b',
            r'\bfrom\b', r'\bas\b', r'\bpass\b', r'\bbreak\b', r'\bcontinue\b',
            r'\bTrue\b', r'\bFalse\b', r'\bNone\b', r'\band\b', r'\bor\b', r'\bnot\b',
            r'\bprint\b', r'\blen\b', r'\braise\b', r'\bexcept\b', r'\btry\b', r'\bfinally\b'
        ]
        for pattern in keyword_patterns:
            expression = QRegularExpression(pattern)
            self.highlighting_rules.append((expression, keyword_format))

        # Built-in functions
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor('#A9B7C6'))  # Light blue
        builtin_patterns = [
            r'\babs\b', r'\bdict\b', r'\bhelp\b', r'\bmin\b', r'\bsetattr\b',
            r'\ball\b', r'\bdir\b', r'\bhex\b', r'\bnext\b', r'\bslice\b',
            r'\bany\b', r'\bdivmod\b', r'\bid\b', r'\bobject\b', r'\bsorted\b',
            r'\bascii\b', r'\benumerate\b', r'\binput\b', r'\boct\b', r'\bstaticmethod\b',
            # Add more built-in functions as needed
        ]
        for pattern in builtin_patterns:
            expression = QRegularExpression(pattern)
            self.highlighting_rules.append((expression, builtin_format))

        # Single-line comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#808080'))  # Gray color
        comment_pattern = QRegularExpression(r'#.*')
        self.highlighting_rules.append((comment_pattern, comment_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#6A8759'))  # Green color
        string_patterns = [
            QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'),
            QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'")
        ]
        for pattern in string_patterns:
            self.highlighting_rules.append((pattern, string_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor('#6897BB'))  # Blue color
        number_pattern = QRegularExpression(r'\b[0-9]+\b')
        self.highlighting_rules.append((number_pattern, number_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)
        self.setCurrentBlockState(0)
