import sys
import os
import pathlib
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QMenuBar,
    QTreeView,
    QFileSystemModel,
    QMessageBox,
    QInputDialog,
    QFileDialog,
    QCompleter,
)
from PySide6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QAction,
    QTextCursor,
)
from PySide6.QtCore import Qt, QStringListModel
from subprocess import CREATE_NEW_CONSOLE

class Highlighter(QSyntaxHighlighter):
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


class Main(QWidget):
    def __init__(self, startup_path):
        super().__init__()

        self.keywords = [
            "def", "class", "if", "else", "elif", "while", "for", "in",
            "return", "import", "from", "as", "try", "except", "with", "pub",
            "let", "const", "var",
        ]

        self.runningCode = False
        self.currentDir = None
        self.currentFile = None

        self.startupPath = Path(startup_path).expanduser().resolve()

        self.downloadBinaries()
        self.loadStartupPath()
        self.buildUI()

    def repairBinaries(self):
        ...

    def downloadBinaries(self):
        """
        Checks for and installs required dependencies.
        Currently disabled.
        """
        ...

    def runCode(self):
        if self.currentFile is None:
            QMessageBox.warning(self, "Error", "No file selected")
            return

        self.saveFile()

        command = f'cd /d "{self.currentDir}" && crabby "{self.currentFile}"'

        subprocess.Popen(
            ["cmd", "/k", command],
            creationflags=CREATE_NEW_CONSOLE,
        )

    def createNewfile(self):
        name = self.askUser("Enter filename with extension:", "Create New File")

        if not name:
            return

        path = pathlib.Path(self.model.rootPath()) / name

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create file: {e}")

    def createNewFolder(self):
        name = self.askUser("Enter folder name:", "Create New Folder")

        if not name:
            return

        path = pathlib.Path(self.model.rootPath()) / name

        try:
            os.mkdir(path)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not create folder: {e}")

    def stopCode(self):
        self.runningCode = False

    def openFile(self, index):
        path = pathlib.Path(self.model.filePath(index))

        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())

                self.currentFile = path.name
                self.currentDir = path.parent
                self.setWindowTitle(f"Coral - {path.name}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def saveFile(self):
        if self.currentFile is None or self.currentDir is None:
            QMessageBox.warning(self, "Error", "No file selected to save")
            return

        code = self.editor.toPlainText()

        try:
            with open(self.currentDir / self.currentFile, "w", encoding="utf-8") as f:
                f.write(code)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    def openFolder(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            str(self.currentDir or Path.home()),
        )

        if dir_path:
            self.currentDir = Path(dir_path)
            self.currentFile = None

            self.model.setRootPath(dir_path)
            self.tree.setRootIndex(self.model.index(dir_path))
            self.editor.clear()
            self.setWindowTitle(f"Coral - {self.currentDir.name}")

    def askUser(self, message, label):
        text, ok = QInputDialog.getText(self, label, message)

        if ok and text:
            return text.strip()

        return None

    def loadStartupPath(self):
        if not self.startupPath.exists():
            raise FileNotFoundError(f"Path does not exist: {self.startupPath}")

        if self.startupPath.is_file():
            self.currentDir = self.startupPath.parent
            self.currentFile = self.startupPath.name

        elif self.startupPath.is_dir():
            self.currentDir = self.startupPath
            self.currentFile = None

        else:
            raise ValueError(f"Invalid path: {self.startupPath}")

    def buildUI(self):
        self.setWindowTitle("Coral")

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # === TOPBAR ===
        topbar = QMenuBar()
        mainLayout.addWidget(topbar)

        # === MENUS ===
        file_menu = topbar.addMenu("File")
        run_menu = topbar.addMenu("Run")

        # === RUN MENU ACTIONS ===
        run_action = QAction("Run Code", self)
        run_action.triggered.connect(self.runCode)

        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stopCode)

        run_menu.addAction(run_action)
        run_menu.addAction(stop_action)

        # === FILE MENU ACTIONS ===
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.saveFile)

        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(self.createNewfile)

        new_folder_action = QAction("New Folder", self)
        new_folder_action.triggered.connect(self.createNewFolder)

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.triggered.connect(self.openFolder)

        file_menu.addAction(new_file_action)
        file_menu.addAction(new_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(open_folder_action)
        file_menu.addAction(save_action)

        # === MAIN CONTENT LAYOUT ===
        Hlayout = QHBoxLayout()
        Hlayout.setContentsMargins(0, 0, 0, 0)
        Hlayout.setSpacing(0)
        mainLayout.addLayout(Hlayout)

        # === FILE EXPLORER ===
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.currentDir))

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(self.currentDir)))
        self.tree.clicked.connect(self.openFile)

        for i in range(1, 4):
            self.tree.hideColumn(i)

        # === EDITOR ===
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet("background:#1e1e1e; color:white;")
        self.editor.setFont(QFont("Consolas", 12))

        self.highlighter = Highlighter(self.editor.document(), self.keywords)
        self.codehinter = CodeHinter(self.editor, self.keywords)

        # === OPEN FILE IF STARTUP PATH WAS A FILE ===
        if self.currentFile is not None:
            try:
                with open(self.currentDir / self.currentFile, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())

                self.setWindowTitle(f"Coral - {self.currentFile}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")

        else:
            self.setWindowTitle(f"Coral - {self.currentDir.name}")

        # === ADD WIDGETS ===
        Hlayout.addWidget(self.tree, 1)
        Hlayout.addWidget(self.editor, 3)

        self.resize(900, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = Main(Path.cwd())
    ide.show()
    sys.exit(app.exec())