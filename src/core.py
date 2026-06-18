from PySide6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QTextCursor,
)

from PySide6.QtWidgets import QCompleter
from PySide6.QtCore import Qt, QStringListModel, QUrl

class Highlighter(QSyntaxHighlighter):
    def __init__(self, document, keywords):
        super().__init__(document)

        self.keywords = set(keywords)

        # Lesbian flag inspired syntax palette
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#D162A4"))
        self.keyword_format.setFontWeight(QFont.Bold)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#FF9A56"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#B55690"))

        self.bracket_format = QTextCharFormat()
        self.bracket_format.setForeground(QColor("#EF7627"))

        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor("#D52D00"))

        self.variable_format = QTextCharFormat()
        self.variable_format.setForeground(QColor("#FFD3E6"))

        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#EF7627"))
        self.function_format.setFontWeight(QFont.Bold)

    def highlightBlock(self, text):
        # Comments
        index = text.find("//")

        if index != -1:
            self.setFormat(index, len(text) - index, self.comment_format)
            text = text[:index]

        # Strings
        in_string = False
        start = 0

        for i, char in enumerate(text):
            if char == '"':
                if not in_string:
                    start = i
                    in_string = True
                else:
                    self.setFormat(start, i - start + 1, self.string_format)
                    in_string = False

        # Keywords
        words = text.split()
        pos = 0

        for word in words:
            clean = word.strip("():,;")

            if clean in self.keywords:
                index = text.find(word, pos)

                if index != -1:
                    self.setFormat(index, len(word), self.keyword_format)

            pos += len(word) + 1


class CodeHinter(QCompleter):
    def __init__(self, editor, keywords):
        super().__init__()

        self.editor = editor
        self.keywords = keywords

        self.setModel(QStringListModel(keywords))
        self.setWidget(editor)

        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        self.activated.connect(self.insertCompletion)
        self.editor.textChanged.connect(self.showCompletion)

    def getCurrentWord(self):
        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        pos = cursor.position()

        def is_word_char(char):
            return char.isalnum() or char == "_" or char == "@"

        start = pos
        while start > 0 and is_word_char(text[start - 1]):
            start -= 1

        end = pos
        while end < len(text) and is_word_char(text[end]):
            end += 1

        return text[start:end], start, end

    def showCompletion(self):
        word, start, end = self.getCurrentWord()

        if not word:
            self.popup().hide()
            return

        matches = [k for k in self.keywords if word.lower() in k.lower()]

        if not matches:
            self.popup().hide()
            return

        self.model().setStringList(matches)

        rect = self.editor.cursorRect()
        rect.setWidth(
            self.popup().sizeHintForColumn(0)
            + self.popup().verticalScrollBar().sizeHint().width()
        )

        self.complete(rect)

    def insertCompletion(self, completion):
        word, start, end = self.getCurrentWord()

        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(completion)

        self.editor.setTextCursor(cursor)


class CrabHighlighter(QSyntaxHighlighter):
    """
    Provides syntax highlighting for the editor.
    """

    def __init__(self, document, keywords):
        super().__init__(document)

        self.keywords = set(keywords)

        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#C695E8"))
        self.keyword_format.setFontWeight(QFont.Bold)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#9E9E9E"))

        self.bracket_format = QTextCharFormat()
        self.bracket_format.setForeground(QColor("#FFD326"))

        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor("#D1071B"))

        self.variable_format = QTextCharFormat()
        self.variable_format.setForeground(QColor("#9CDEFD"))

    def highlightBlock(self, text):
        #comments
        index = text.find("//")

        if index != -1:
            self.setFormat(index, len(text) - index, self.comment_format)
            text = text[:index]

        #strings
        in_string = False
        start = 0

        for i, char in enumerate(text):
            if char == '"':
                if not in_string:
                    start = i
                    in_string = True
                else:
                    self.setFormat(start, i - start + 1, self.string_format)
                    in_string = False

        #keywords
        words = text.split()
        pos = 0

        for word in words:
            clean = word.strip("():,")

            if clean in self.keywords:
                index = text.find(word, pos)

                if index != -1:
                    self.setFormat(index, len(word), self.keyword_format)

            pos += len(word) + 1


class CrabCodeHinter(QCompleter):
    def __init__(self, editor, keywords):
        super().__init__()

        self.editor = editor
        self.keywords = keywords

        self.setModel(QStringListModel(keywords))
        self.setWidget(editor)

        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        self.activated.connect(self.insertCompletion)
        self.editor.textChanged.connect(self.showCompletion)

    def getCurrentWord(self):
        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        pos = cursor.position()

        start = pos
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
            start -= 1

        end = pos
        while end < len(text) and (text[end].isalnum() or text[end] == "_"):
            end += 1

        return text[start:end], start, end

    def showCompletion(self):
        word, start, end = self.getCurrentWord()

        if not word:
            self.popup().hide()
            return

        matches = [k for k in self.keywords if word.lower() in k.lower()]

        if not matches:
            self.popup().hide()
            return

        self.model().setStringList(matches)

        rect = self.editor.cursorRect()
        rect.setWidth(
            self.popup().sizeHintForColumn(0)
            + self.popup().verticalScrollBar().sizeHint().width()
        )

        self.complete(rect)

    def insertCompletion(self, completion):
        word, start, end = self.getCurrentWord()

        cursor = self.editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(completion)

        self.editor.setTextCursor(cursor)
