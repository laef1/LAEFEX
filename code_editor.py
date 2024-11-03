# code_editor.py

from PyQt6.QtWidgets import (
    QPlainTextEdit, QWidget, QTextEdit, QMenu, QInputDialog, QMessageBox, QVBoxLayout, QCompleter
)
from PyQt6.QtGui import (
    QTextCursor, QColor, QPainter, QFont, QTextFormat,
    QTextCharFormat, QAction, QSyntaxHighlighter
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QRegularExpression, QStringListModel

import keyword
import re
import ast
import jedi  # Import jedi for advanced autocompletion

# --- Syntax Highlighter ---
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        # Define color scheme similar to VSCode's Python syntax highlighting
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor(86, 156, 214))  # Blue

        self.operator_format = QTextCharFormat()
        self.operator_format.setForeground(QColor(212, 212, 212))  # Light gray

        self.brace_format = QTextCharFormat()
        self.brace_format.setForeground(QColor(212, 212, 212))  # Light gray

        self.def_class_format = QTextCharFormat()
        self.def_class_format.setForeground(QColor(78, 201, 176))  # Teal

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(214, 157, 133))  # Orange

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor(87, 166, 74))  # Green
        self.comment_format.setFontItalic(True)

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(181, 206, 168))  # Light green

        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(QColor(220, 220, 170))  # Light yellow

        self.decorator_format = QTextCharFormat()
        self.decorator_format.setForeground(QColor(155, 155, 255))  # Purple

        # Regular expressions for syntax highlighting
        self.rules = []

        # Keywords
        keywords = keyword.kwlist
        keyword_patterns = [r'\b' + kw + r'\b' for kw in keywords]
        self.rules += [(QRegularExpression(pattern), self.keyword_format) for pattern in keyword_patterns]

        # Built-in functions
        builtins = dir(__builtins__)
        builtin_patterns = [r'\b' + fn + r'\b' for fn in builtins]
        self.rules += [(QRegularExpression(pattern), self.builtin_format) for pattern in builtin_patterns]

        # Operators
        operator_patterns = [
            r'\+', r'-', r'\*', r'/', r'//', r'%', r'\*\*',
            r'==', r'!=', r'<', r'<=', r'>', r'>=', r'=', r'\+=', r'-=',
            r'\*=', r'/=', r'%=', r'\^', r'\|', r'&', r'~', r'>>', r'<<'
        ]
        self.rules += [(QRegularExpression(pattern), self.operator_format) for pattern in operator_patterns]

        # Braces
        brace_patterns = [r'\{', r'\}', r'\(', r'\)', r'\[', r'\]']
        self.rules += [(QRegularExpression(pattern), self.brace_format) for pattern in brace_patterns]

        # Strings
        string_patterns = [
            QRegularExpression(r'".*?"'),  # Double quotes
            QRegularExpression(r"'.*?'"),  # Single quotes
            QRegularExpression(r'""".*?"""', QRegularExpression.PatternOption.DotMatchesEverythingOption),
            QRegularExpression(r"'''.*?'''", QRegularExpression.PatternOption.DotMatchesEverythingOption)
        ]
        self.rules += [(pattern, self.string_format) for pattern in string_patterns]

        # Comments
        self.rules.append((QRegularExpression(r'#.*'), self.comment_format))

        # Numbers
        self.rules.append((QRegularExpression(r'\b[0-9]+(\.[0-9]+)?\b'), self.number_format))

        # Decorators
        self.rules.append((QRegularExpression(r'@\w+'), self.decorator_format))

        # Function and class definitions
        def_class_patterns = [
            (QRegularExpression(r'\bdef\b\s+(\w+)'), self.def_class_format),
            (QRegularExpression(r'\bclass\b\s+(\w+)'), self.def_class_format)
        ]
        self.rules += def_class_patterns

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)
        self.setCurrentBlockState(0)

# --- Error Highlighter ---
class ErrorHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineColor(QColor('red'))
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)

    def highlightBlock(self, text):
        try:
            ast.parse(text)
        except SyntaxError as e:
            if e.lineno == self.currentBlock().blockNumber() + 1:
                col_offset = e.offset - 1 if e.offset else 0
                length = len(text) - col_offset
                self.setFormat(col_offset, length, self.error_format)

# --- Line Number Area ---
class LineNumberArea(QWidget):
    def __init__(self, code_editor):
        super().__init__(code_editor)
        self.code_editor = code_editor
        self.setObjectName("LineNumberArea")

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

# --- Code Editor ---
class CodeEditor(QPlainTextEdit):
    breakpoint_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.setPlaceholderText("# Write your Python code here")
        self.highlighter = PythonHighlighter(self.document())
        self.error_highlighter = ErrorHighlighter(self.document())

        # Line Number Area
        self.line_number_area = LineNumberArea(self)

        # Set tab width
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        # Variables for code analysis
        self.variables = set()
        self.functions = set()

        # Autocomplete
        self.keywords = sorted(keyword.kwlist + [
            'print', 'len', 'range', 'int', 'float', 'str', 'list', 'dict',
            'set', 'tuple', 'input', 'open', 'close', 'exit', 'help', 'type'
        ])
        self.completer = QCompleter()
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)

        # Bracket Matching
        self.bracket_positions = []

        # Update line number area width
        self.update_line_number_area_width(0)

        # Connect signals after initializing line_number_area
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self.parse_code)

    # --- Event Filter ---
    def eventFilter(self, source, event):
        if event.type() == event.Type.Paint and source is self.viewport():
            self.line_number_area.update()
        return super().eventFilter(source, event)

    # --- Line Numbers ---
    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 12 + 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor('#1e1e1e'))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        font = QFont()
        font.setBold(True)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                # Draw line number
                painter.setPen(QColor('#757575'))
                painter.drawText(0, top, self.line_number_area.width() - 5,
                                 self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

        painter.end()  # Explicitly end the painter

    # --- Key Press Event ---
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            cursor = self.textCursor()
            cursor.insertText('\n')
            self.auto_indent(cursor)
            event.accept()
            return
        elif key == Qt.Key.Key_Tab and not modifiers & Qt.KeyboardModifier.ShiftModifier:
            # Indent
            cursor = self.textCursor()
            if cursor.hasSelection():
                self.indent_selection()
            else:
                cursor.insertText(' ' * 4)
            event.accept()
            return
        elif key == Qt.Key.Key_Backtab or (key == Qt.Key.Key_Tab and modifiers & Qt.KeyboardModifier.ShiftModifier):
            # Unindent
            cursor = self.textCursor()
            if cursor.hasSelection():
                self.unindent_selection()
            else:
                self.unindent_line()
            event.accept()
            return

        # Call the base class implementation
        super().keyPressEvent(event)

        # Start autocompletion after certain keys
        completion_prefix = self.text_under_cursor()
        if completion_prefix != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completion_prefix)
            self.completer.popup().setCurrentIndex(
                self.completer.completionModel().index(0, 0))

        if len(event.text()) > 0 and completion_prefix:
            cr = self.cursorRect()
            cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                        + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
        else:
            self.completer.popup().hide()

        self.error_highlighter.rehighlight()
        self.highlight_matching_brackets()

    def text_under_cursor(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def insert_completion(self, completion):
        tc = self.textCursor()
        extra = completion[len(self.completer.completionPrefix()):]
        tc.insertText(extra)
        self.setTextCursor(tc)

    # --- Auto Indentation ---
    def auto_indent(self, cursor):
        block_text = cursor.block().previous().text()
        indentation = re.match(r'^\s*', block_text).group()
        cursor.insertText(indentation)

        # Increase indentation after a colon
        if re.search(r':\s*$', block_text):
            cursor.insertText(' ' * 4)

        self.setTextCursor(cursor)

    def indent_selection(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        while cursor.position() <= end:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.insertText(' ' * 4)
            if not cursor.movePosition(QTextCursor.MoveOperation.Down):
                break
            end += 4  # Adjust end position due to added spaces

    def unindent_selection(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        while cursor.position() <= end:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 4)
            if cursor.selectedText() == ' ' * 4:
                cursor.removeSelectedText()
                end -= 4  # Adjust end position due to removed spaces
            if not cursor.movePosition(QTextCursor.MoveOperation.Down):
                break

    def unindent_line(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 4)
        if cursor.selectedText() == ' ' * 4:
            cursor.removeSelectedText()

    # --- Highlight Current Line ---
    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor('#292929')
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    # --- Parse Code ---
    def parse_code(self):
        code = self.toPlainText()
        try:
            tree = ast.parse(code)
            self.variables = set()
            self.functions = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    self.functions.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.variables.add(target.id)
        except:
            pass  # Ignore parsing errors

        # Update the completer model using jedi
        self.update_completions()

    def update_completions(self):
        code = self.toPlainText()
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber()
        try:
            script = jedi.Script(code, path='')
            completions = script.complete(line, column)
            completion_list = [c.name for c in completions]
            if completion_list:
                self.completer.setModel(QStringListModel(completion_list))
            else:
                # Fallback to keywords
                self.completer.setModel(QStringListModel(self.keywords))
        except Exception as e:
            # Fallback to keywords if jedi fails
            self.completer.setModel(QStringListModel(self.keywords))

    # --- Bracket Matching ---
    def highlight_matching_brackets(self):
        extra_selections = []
        cursor = self.textCursor()
        block = cursor.block()
        text = block.text()
        pos = cursor.positionInBlock() - 1

        brackets = {'(': ')', '[': ']', '{': '}'}
        rev_brackets = {v: k for k, v in brackets.items()}

        if pos >= 0 and text[pos] in brackets:
            char = text[pos]
            match_char = brackets[char]
            direction = 1
            start_pos = pos
        elif pos + 1 < len(text) and text[pos + 1] in rev_brackets:
            char = text[pos + 1]
            match_char = rev_brackets[char]
            direction = -1
            start_pos = pos + 1
        else:
            self.setExtraSelections(extra_selections)
            return

        match_pos = self.find_matching_bracket(block, start_pos, char, match_char, direction)
        if match_pos:
            fmt = QTextCharFormat()
            fmt.setBackground(QColor('#49483E'))
            # Highlight the brackets
            for position in [cursor.position(), match_pos]:
                selection = QTextEdit.ExtraSelection()
                temp_cursor = self.textCursor()
                temp_cursor.setPosition(position)
                temp_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
                selection.cursor = temp_cursor
                selection.format = fmt
                extra_selections.append(selection)
            self.setExtraSelections(extra_selections)
        else:
            self.setExtraSelections(extra_selections)

    def find_matching_bracket(self, block, pos, char, match_char, direction):
        text = block.text()
        stack = 1
        block_number = block.blockNumber()
        while True:
            pos += direction
            if pos < 0 or pos >= len(text):
                block_number += direction
                block = self.document().findBlockByNumber(block_number)
                if not block.isValid():
                    return None
                text = block.text()
                pos = 0 if direction > 0 else len(text) - 1
            c = text[pos]
            if c == char:
                stack += 1
            elif c == match_char:
                stack -= 1
            if stack == 0:
                cursor = QTextCursor(block)
                cursor.setPosition(block.position() + pos)
                return cursor.position()
        return None

    # --- Context Menu ---
    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()

        # Find and Replace
        find_action = QAction('Find', self)
        find_action.triggered.connect(self.show_find_dialog)
        menu.addAction(find_action)

        replace_action = QAction('Replace', self)
        replace_action.triggered.connect(self.show_replace_dialog)
        menu.addAction(replace_action)

        # Code Snippets
        snippets_menu = QMenu("Insert Snippet", self)
        snippet_actions = {
            'If Statement': 'if condition:\n    ',
            'For Loop': 'for item in iterable:\n    ',
            'While Loop': 'while condition:\n    ',
            'Function': 'def function_name(parameters):\n    ',
            'Class': 'class ClassName:\n    def __init__(self):\n        '
        }
        for name, code in snippet_actions.items():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, c=code: self.insertPlainText(c))
            snippets_menu.addAction(action)
        menu.addMenu(snippets_menu)

        menu.exec(event.globalPos())

    # --- Find and Replace ---
    def show_find_dialog(self):
        text, ok = QInputDialog.getText(self, 'Find', 'Find:')
        if ok and text:
            self.find_text(text)

    def find_text(self, text):
        if self.find(text):
            pass
        else:
            cursor = self.textCursor()
            cursor.setPosition(0)
            self.setTextCursor(cursor)
            if self.find(text):
                pass
            else:
                QMessageBox.information(self, 'Find', 'Text not found.')

    def show_replace_dialog(self):
        find_text, ok = QInputDialog.getText(self, 'Replace', 'Find:')
        if ok and find_text:
            replace_text, ok = QInputDialog.getText(self, 'Replace', 'Replace with:')
            if ok:
                self.replace_text(find_text, replace_text)

    def replace_text(self, find_text, replace_text):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        while self.find(find_text):
            cursor = self.textCursor()
            cursor.insertText(replace_text)
        cursor.endEditBlock()
        self.setTextCursor(cursor)
