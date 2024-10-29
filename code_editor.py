# code_editor.py

from PyQt6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem, QTextEdit,
    QMenu, QInputDialog, QMessageBox, QSplitter, QVBoxLayout, QPlainTextEdit
)
from PyQt6.QtGui import (
    QTextCursor, QColor, QPainter, QFont, QTextFormat,
    QTextBlockUserData, QTextCharFormat, QAction, QSyntaxHighlighter
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QRegularExpression

import keyword
import re
import ast

# --- Syntax Highlighter ---
from syntax_highlighter import PythonHighlighter

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

# --- Folding Data ---
class FoldScopeData(QTextBlockUserData):
    def __init__(self):
        super().__init__()
        self.folded = False
        self.foldable = False

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
class CodeEditor(QWidget):
    breakpoint_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        # Layout for code editor and mini-map
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter to hold editor and mini-map
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Code Editor Area
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("# Write your Python code here")
        self.highlighter = PythonHighlighter(self.editor.document())
        self.error_highlighter = ErrorHighlighter(self.editor.document())
        self.editor.blockCountChanged.connect(self.update_folds)
        self.editor.cursorPositionChanged.connect(self.highlight_current_line)
        self.editor.textChanged.connect(self.parse_code)
        self.editor.installEventFilter(self)

        # Line Number Area
        self.line_number_area = LineNumberArea(self)
        self.editor.updateRequest.connect(self.update_line_number_area)
        self.editor.viewport().installEventFilter(self)

        # Mini-map Area
        self.mini_map = QPlainTextEdit()
        self.mini_map.setReadOnly(True)
        self.mini_map.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mini_map.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mini_map.setStyleSheet("background-color: #1e1e1e; color: #555555;")
        self.mini_map.setFont(QFont("Courier", 2))

        # Add widgets to splitter
        splitter.addWidget(self.line_number_area)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.mini_map)
        splitter.setSizes([30, 800, 100])

        # Variables for code analysis
        self.variables = set()
        self.functions = set()

        # Autocomplete
        self.completer = QListWidget()
        self.completer.hide()
        self.completer.itemClicked.connect(self.insert_completion)
        self.keywords = sorted(keyword.kwlist + [
            'print', 'len', 'range', 'int', 'float', 'str', 'list', 'dict',
            'set', 'tuple', 'input', 'open', 'close', 'exit', 'help', 'type'
        ])

        # Bracket Matching
        self.bracket_positions = []

        # Update folds
        self.update_folds()

    # --- Event Filter ---
    def eventFilter(self, source, event):
        if event.type() == event.Type.Paint and source is self.editor.viewport():
            self.line_number_area.update()
        return super().eventFilter(source, event)

    # --- Line Numbers and Folding ---
    def line_number_area_width(self):
        digits = len(str(max(1, self.editor.blockCount())))
        space = 12 + 3 + self.editor.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.editor.viewport().rect()):
            self.update_line_number_area_width(0)

    def update_line_number_area_width(self, _):
        self.editor.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.editor.contentsRect()
        self.line_number_area.setGeometry(
            QRect(self.editor.viewport().geometry().left(), cr.top(), self.line_number_area_width(), cr.height()))
        self.update_mini_map()

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor('#1e1e1e'))

        block = self.editor.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        bottom = top + int(self.editor.blockBoundingRect(block).height())

        font = QFont()
        font.setBold(True)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                # Draw line number
                painter.setPen(QColor('#757575'))
                painter.drawText(0, top, self.line_number_area.width() - 5,
                                 self.editor.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.editor.blockBoundingRect(block).height())
            block_number += 1

    # --- Events ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().x() < self.line_number_area.width():
                x = event.pos().x()
                if x < self.line_number_area.width():
                    # Line number area clicked
                    cursor = self.editor.cursorForPosition(event.pos())
                    line = cursor.blockNumber() + 1
                    # Implement breakpoint logic if needed
                    return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        # Handle autocomplete navigation
        if self.completer.isVisible():
            if event.key() == Qt.Key.Key_Down:
                current_row = self.completer.currentRow()
                if current_row < self.completer.count() - 1:
                    self.completer.setCurrentRow(current_row + 1)
                return
            elif event.key() == Qt.Key.Key_Up:
                current_row = self.completer.currentRow()
                if current_row > 0:
                    self.completer.setCurrentRow(current_row - 1)
                return
            elif event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                current_item = self.completer.currentItem()
                if current_item:
                    self.insert_completion(current_item)
                return

        if event.key() == Qt.Key.Key_Tab:
            cursor = self.editor.textCursor()
            if cursor.hasSelection():
                # Indent selected lines
                self.indent_selection()
            else:
                # Insert spaces equivalent to a tab
                cursor.insertText(' ' * 4)
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Backtab:
            cursor = self.editor.textCursor()
            if cursor.hasSelection():
                # Unindent selected lines
                self.unindent_selection()
            else:
                # Remove indentation from the current line
                self.unindent_line()
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Backspace:
            # Handle backspace properly to remove spaces
            cursor = self.editor.textCursor()
            if cursor.selectionStart() == cursor.selectionEnd():
                # No selection, delete spaces equivalent to a tab if at indentation
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 4)
                if cursor.selectedText() == ' ' * 4:
                    cursor.removeSelectedText()
                else:
                    # Move back to original position and delete one character
                    cursor.clearSelection()
                    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor, 4)
                    super(QPlainTextEdit, self.editor).keyPressEvent(event)
            else:
                # If text is selected, delete as usual
                super(QPlainTextEdit, self.editor).keyPressEvent(event)
            event.accept()
            return

        # Call the base class implementation
        super(QPlainTextEdit, self.editor).keyPressEvent(event)

        # Only trigger autocomplete on character keys
        if event.text().isalpha() or event.text() == '_':
            cursor = self.editor.textCursor()
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            word = cursor.selectedText()
            if word:
                self.all_completions = sorted(set(
                    self.keywords + list(self.variables) + list(self.functions)))
                matches = [kw for kw in self.all_completions if kw.startswith(word)]
                if matches:
                    self.show_completer(matches)
        else:
            self.completer.hide()

        self.parse_code()
        self.error_highlighter.rehighlight()
        self.update_folds()
        self.highlight_matching_brackets()

    # Additional methods for indentation handling
    def indent_selection(self):
        cursor = self.editor.textCursor()
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
        cursor = self.editor.textCursor()
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
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 4)
        if cursor.selectedText() == ' ' * 4:
            cursor.removeSelectedText()

    # --- Code Folding ---
    def update_folds(self, _=None):
        # Implement folding logic if needed
        pass

    # --- Highlight Current Line ---
    def highlight_current_line(self):
        extra_selections = []
        if not self.editor.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor('#292929')
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.editor.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.editor.setExtraSelections(extra_selections)

    # --- Autocomplete ---
    def parse_code(self):
        code = self.editor.toPlainText()
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
        self.update_mini_map()

    def show_completer(self, completions):
        self.completer.clear()
        for c in completions:
            item = QListWidgetItem(c)
            self.completer.addItem(item)
        self.completer.setCurrentRow(0)
        cursor_rect = self.editor.cursorRect()
        point = self.editor.mapToGlobal(cursor_rect.bottomRight())
        self.completer.move(point)
        self.completer.resize(200, self.completer.sizeHintForRow(0) * min(6, len(completions)))
        self.completer.show()

    def insert_completion(self, item):
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        cursor.insertText(item.text()[len(word):])
        self.completer.hide()

    # --- Bracket Matching ---
    def highlight_matching_brackets(self):
        extra_selections = []
        cursor = self.editor.textCursor()
        block = cursor.block()
        text = block.text()
        pos = cursor.positionInBlock()

        brackets = {'(': ')', '[': ']', '{': '}'}
        rev_brackets = {v: k for k, v in brackets.items()}

        if pos > 0 and text[pos - 1] in brackets:
            char = text[pos - 1]
            match_char = brackets[char]
            direction = 1
            start_pos = pos - 1
        elif pos < len(text) and text[pos] in rev_brackets:
            char = text[pos]
            match_char = rev_brackets[char]
            direction = -1
            start_pos = pos
        else:
            return

        match_pos = self.find_matching_bracket(block, start_pos, char, match_char, direction)
        if match_pos:
            format = QTextCharFormat()
            format.setBackground(QColor('#49483E'))
            positions = [cursor.position()]
            positions.append(match_pos)
            for position in positions:
                selection = QTextEdit.ExtraSelection()
                temp_cursor = self.editor.textCursor()
                temp_cursor.setPosition(position)
                temp_cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
                selection.cursor = temp_cursor
                selection.format = format
                extra_selections.append(selection)
            self.editor.setExtraSelections(extra_selections)

    def find_matching_bracket(self, block, pos, char, match_char, direction):
        text = block.text()
        stack = 1
        while True:
            pos += direction
            if pos < 0 or pos >= len(text):
                block = block.next() if direction > 0 else block.previous()
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
    
    # --- Mini-map ---
    def update_mini_map(self):
        self.mini_map.setPlainText(self.editor.toPlainText())

    # --- Context Menu ---
    def contextMenuEvent(self, event):
        menu = self.editor.createStandardContextMenu()

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
            'If Statement': 'if condition:\n    pass',
            'For Loop': 'for item in iterable:\n    pass',
            'While Loop': 'while condition:\n    pass',
            'Function': 'def function_name(parameters):\n    pass',
            'Class': 'class ClassName:\n    def __init__(self):\n        pass'
        }
        for name, code in snippet_actions.items():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, c=code: self.editor.insertPlainText(c))
            snippets_menu.addAction(action)
        menu.addMenu(snippets_menu)

        menu.exec(event.globalPos())

    # --- Find and Replace ---
    def show_find_dialog(self):
        text, ok = QInputDialog.getText(self, 'Find', 'Find:')
        if ok and text:
            self.find_text(text)

    def find_text(self, text):
        if self.editor.find(text):
            pass
        else:
            cursor = self.editor.textCursor()
            cursor.setPosition(0)
            self.editor.setTextCursor(cursor)
            if self.editor.find(text):
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
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        while self.editor.find(find_text):
            cursor = self.editor.textCursor()
            cursor.insertText(replace_text)
        cursor.endEditBlock()
        self.editor.setTextCursor(cursor)
