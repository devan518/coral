# since im a beginner at the qt framework i just keep the vibecoded stuff here to test out the
# classes, functions of qt etc
# the actual code is hand written like a psycho

import sys
import os
import pathlib
from pathlib import Path
import subprocess

from PySide6.QtWidgets import (
    QApplication, QPlainTextEdit, QVBoxLayout, QWidget, 
    QHBoxLayout, QMenuBar, QTreeView, QFileSystemModel,
    QMessageBox, QInputDialog, QFileDialog, QCompleter,
    QMainWindow
)
from PySide6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont,
    QAction, QTextCursor
)
from PySide6.QtCore import QRegularExpression, Qt

class Highlighter(QSyntaxHighlighter):
    def __init__(self, document, keywords):
        super().__init__(document)
        self.highlighting_rules = []

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Bold)
        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, keyword_format))

        # String format
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))
        self.highlighting_rules.append((QRegularExpression("\".*\""), self.string_format))
        self.highlighting_rules.append((QRegularExpression("'.*'"), self.string_format))

        # Comment format
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#9E9E9E"))
        self.highlighting_rules.append((QRegularExpression("#.*"), self.comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class CodeHinter(QCompleter):
    def __init__(self, keywords, parent=None):
        super().__init__(keywords, parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)

class CoralIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Coral IDE")
        self.resize(1000, 700)

        self.keywords = [
            "def","class","if","else","elif","while","for","in",
            "return","import","from","as","try","except","with","pub",
            "let", "const", "var"
        ]
        
        self.current_file = None
        self.current_dir = Path.cwd()

        self.init_ui()

    def init_ui(self):
        # Central Widget and Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Menu Bar
        self.setup_menus()

        # Layout for Explorer and Editor
        h_layout = QHBoxLayout()
        self.main_layout.addLayout(h_layout)

        # File Explorer
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.current_dir))
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(self.current_dir)))
        self.tree.clicked.connect(self.open_file)
        for i in range(1, 4): self.tree.hideColumn(i) # Hide size, date, type

        # Editor
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet("background:#1e1e1e; color:white; border: none;")
        self.editor.setFont(QFont("Consolas", 12))
        
        # Highlighter and Completer
        self.highlighter = Highlighter(self.editor.document(), self.keywords)
        self.completer = CodeHinter(self.keywords, self.editor)
        self.completer.setWidget(self.editor)
        
        # Connect signals
        self.editor.textChanged.connect(self.handle_autocomplete)
        self.completer.activated.connect(self.insert_completion)

        h_layout.addWidget(self.tree, 1)
        h_layout.addWidget(self.editor, 3)

    def setup_menus(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("&File")
        new_file_act = QAction("New File", self)
        new_file_act.triggered.connect(self.create_new_file)
        open_folder_act = QAction("Open Folder", self)
        open_folder_act.triggered.connect(self.open_folder)
        save_act = QAction("Save", self)
        save_act.triggered.connect(self.save_file)
        
        file_menu.addActions([new_file_act, open_folder_act, save_act])

        run_menu = menubar.addMenu("&Run")
        run_act = QAction("Run Code", self)
        run_act.triggered.connect(self.run_code)
        run_menu.addAction(run_act)

    # --- Logic Methods ---

    def handle_autocomplete(self):
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText()

        if not word or len(word) < 1:
            self.completer.popup().hide()
            return

        self.completer.setCompletionPrefix(word)
        rect = self.editor.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0))
        self.completer.complete(rect)

    def insert_completion(self, completion):
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        cursor.insertText(completion)

    def open_file(self, index):
        path = Path(self.model.filePath(index))
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.current_file = path
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def save_file(self):
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(self, "Save File", str(self.current_dir))
            if path: self.current_file = Path(path)
            else: return

        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.editor.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")

    def open_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.current_dir = Path(dir_path)
            self.model.setRootPath(dir_path)
            self.tree.setRootIndex(self.model.index(dir_path))

    def create_new_file(self):
        name, ok = QInputDialog.getText(self, "New File", "Filename:")
        if ok and name:
            path = self.current_dir / name
            path.touch()
            self.open_file(self.model.index(str(path)))

    def run_code(self):
        if not self.current_file:
            return QMessageBox.warning(self, "Error", "Save the file first!")
        
        self.save_file()
        # Note: Using 'start' is Windows specific
        cmd = f'start cmd /k "crabby {self.current_file.name}"'
        subprocess.Popen(cmd, shell=True, cwd=str(self.current_file.parent))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = CoralIDE()
    ide.show()
    sys.exit(app.exec())