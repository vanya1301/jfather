"""JSON text editor with syntax highlighting."""

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit


def _fmt(color, bold=False):
    fmt = QTextCharFormat()
    fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(QFont.Bold)
    return fmt


class JsonHighlighter(QSyntaxHighlighter):
    """Minimal JSON syntax highlighter."""

    def __init__(self, document):
        super().__init__(document)
        self._key_format = _fmt("#7aa2f7", bold=True)
        self._rules = [
            (QRegularExpression(r'"(\\.|[^"\\])*"'), _fmt("#9ece6a")),
            (QRegularExpression(r"\b-?\d+(\.\d+)?([eE][+-]?\d+)?\b"), _fmt("#ff9e64")),
            (QRegularExpression(r"\b(true|false|null)\b"), _fmt("#bb9af7")),
        ]
        self._key_rule = QRegularExpression(r'"(\\.|[^"\\])*"(?=\s*:)')

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
        # Keys (quoted strings followed by a colon) override the string color.
        it = self._key_rule.globalMatch(text)
        while it.hasNext():
            match = it.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), self._key_format)


class JsonEditor(QPlainTextEdit):
    """Plain-text JSON editor with monospace font and highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font = QFont("Menlo")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(12)
        self.setFont(font)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.highlighter = JsonHighlighter(self.document())
        self._match_cursors = []
        self._find_index = -1
        self._match_format = QTextCharFormat()
        self._match_format.setBackground(QColor("#5f5f00"))

    def text(self):
        return self.toPlainText()

    def set_text(self, text):
        if text != self.toPlainText():
            self.setPlainText(text)

    def find_matches(self, term):
        self._match_cursors = []
        self._find_index = -1
        selections = []
        if term:
            document = self.document()
            cursor = QTextCursor(document)
            while True:
                cursor = document.find(term, cursor)
                if cursor.isNull():
                    break
                self._match_cursors.append(QTextCursor(cursor))
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = self._match_format
                selections.append(selection)
        self.setExtraSelections(selections)
        return len(self._match_cursors)

    def find_next(self, forward=True):
        if not self._match_cursors:
            return 0
        step = 1 if forward else -1
        self._find_index = (self._find_index + step) % len(self._match_cursors)
        self.setTextCursor(self._match_cursors[self._find_index])
        return self._find_index + 1

    def clear_find(self):
        self._match_cursors = []
        self._find_index = -1
        self.setExtraSelections([])
