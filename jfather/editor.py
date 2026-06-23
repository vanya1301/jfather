"""JSON text editor with syntax highlighting."""

from PySide6.QtCore import QRect, QRegularExpression, QSize, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


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


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self._editor.paint_line_numbers(event)


class JsonEditor(QPlainTextEdit):
    """Plain-text JSON editor with monospace font and highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        font = QFont("Menlo")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(12)
        self.setFont(font)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width(0)
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

    def line_number_area_width(self):
        digits = max(2, len(str(max(1, self.blockCount()))))
        return 14 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area_width(self, _count):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def paint_line_numbers(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#161514"))
        painter.setPen(QColor("#5b554d"))
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        width = self.line_number_area.width() - 6
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(
                    0, int(top), width, self.fontMetrics().height(),
                    Qt.AlignRight, str(number + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            number += 1
