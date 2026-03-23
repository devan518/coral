from PySide6.QtWidgets import (
    QApplication, 
    QPlainTextEdit, 
    QPushButton, 
    QVBoxLayout, 
    QWidget, 
    QHBoxLayout, 
    QMenuBar,
    QMenu,
    QTreeView, 
    QFileSystemModel,
    QMessageBox,
    QInputDialog,
    QFileDialog
)

import pathlib

from PySide6.QtGui import (
    QSyntaxHighlighter, 
    QTextCharFormat, 
    QColor, 
    QFont,
    QAction,
)
from PySide6.QtCore import QRegularExpression, QDir
import sys
from subprocess import CREATE_NEW_CONSOLE
import subprocess
import os

# heya! this is a work in progress but if you want to make a commit
# i could use some help adding detailed descriptions to the classes/functions
# use docstrings on the top. describe what it does, what the parameters need, etc
# TODO:
# add intellisense via Qcompleter class
# fix highlighting in comments 
# undo/redo
# search and replace
# obviously call the crabby compiler
#dm me on discord @eelmo_

class Highlighter(QSyntaxHighlighter):
    def __init__(self, document, keywords):
        super().__init__(document)
        self.keywords = set(keywords)

        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569CD6"))
        self.keyword_format.setFontWeight(QFont.Bold)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#9E9E9E"))

    def highlightBlock(self, text):
        # --- comments ---
        if "#" in text:
            index = text.find("#")
            self.setFormat(index, len(text) - index, self.comment_format)

        # --- strings ---
        in_string = False
        start = 0
        for i, char in enumerate(text):
            if char in ['"', "'"]:
                if not in_string:
                    start = i
                    in_string = True
                else:
                    self.setFormat(start, i - start + 1, self.string_format)
                    in_string = False

        # --- keywords ---
        words = text.split()
        pos = 0

        for word in words:
            clean = word.strip("():,")  # basic cleanup

            if clean in self.keywords:
                index = text.find(word, pos)
                if index != -1:
                    self.setFormat(index, len(word), self.keyword_format)

            pos += len(word) + 1


class Main():
    def __init__(self):
        self.keywords = [
            "def","class","if","else","elif","while","for","in",
            "return","import","from","as","try","except","with","lambda"
        ]
        self.runningCode = False
        self.currentDir = None
        self.currentFile = None

    def runCode(self): 
        if self.currentFile is None:
            QMessageBox.warning(None, "Error", "No file selected")
            return

        # save before running
        self.saveFile()

        path = self.currentDir / self.currentFile

        process = subprocess.Popen(
            f'start "" cmd /k "cd /d {self.currentDir} && python {self.currentFile}"',
            shell=True,
            creationflags=CREATE_NEW_CONSOLE
        )

    def createNewfile(self):
        name = self.askUser("Create new file:", "New File")
        if not name:
            return

        path = pathlib.Path(self.model.rootPath()) / name
        with open(path, "w", encoding="utf-8") as f:
            f.write("")


    def createNewFolder(self):
        name = self.askUser("Create new folder:", "New Folder")
        if not name:
            return

        path = pathlib.Path(self.model.rootPath()) / name
        os.mkdir(path)

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

            except Exception as e:
                print("Error:", e)

    def saveFile(self):
        if self.currentFile is None or self.currentDir is None:
            QMessageBox.warning(None, "Error", "No file selected")
            return

        code = self.editor.toPlainText()

        with open(self.currentDir / self.currentFile, "w", encoding="utf-8") as f:
            f.write(code)

    def openFolder(self):
        ...
    def askUser(self, message, label):
        """
        ~--------------------~
        |new file       - O X|
        |--------------------|
        | create a new file: |
        |  ----------------  |
        | |name:          |  |
        | -----------------  |
        |   create  cancel   |
        ~--------------------~
        returns input
        """
        text, ok = QInputDialog.getText(None, label, message)
        if ok and text:
            return text
        return None
        ...

    def main(self):
        app = QApplication(sys.argv)

        # main window + layout
        window = QWidget()
        mainLayout = QVBoxLayout(window)

        # === TOPBAR ===
        topbar = QMenuBar()
        mainLayout.addWidget(topbar)

        # === MENUS ===
        file_menu = topbar.addMenu("File")
        run_menu = topbar.addMenu("Run")


        # === Run actions ===
        run_action = QAction("Run Code", window)
        run_action.triggered.connect(self.runCode)

        stop_action = QAction("Stop", window)
        stop_action.triggered.connect(self.stopCode)

        run_menu.addAction(run_action)
        run_menu.addAction(stop_action)

        # === file actions ===
        save_action = QAction("Save", window)
        save_action.triggered.connect(self.saveFile)

        new_file_action = QAction("New File", window)
        new_file_action.triggered.connect(self.createNewfile)

        new_folder_action = QAction("New Folder", window)
        new_folder_action.triggered.connect(self.createNewFolder)
        
        new_folder_action = QAction("Open Folder", window)
        new_folder_action.triggered.connect(self.openFolder)


        file_menu.addAction(save_action)
        file_menu.addAction(new_file_action)
        file_menu.addAction(new_folder_action)

        # === MAIN CONTENT (HORIZONTAL) ===
        Hlayout = QHBoxLayout()
        mainLayout.addLayout(Hlayout)

        # === FILE EXPLORER ===
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.currentPath()))
        self.tree.clicked.connect(self.openFile)

        for i in range(1, 4):
            self.tree.hideColumn(i)

        self.currentDir = pathlib.Path(self.model.rootPath())

        # === EDITOR ===
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet("background:#1e1e1e; color:white;")
        self.editor.setFont(QFont("Consolas", 12))

        self.highlighter = Highlighter(self.editor.document(), self.keywords)

        # === ADD TO LAYOUT ===
        Hlayout.addWidget(self.tree, 1)
        Hlayout.addWidget(self.editor, 3)

        # window setup
        window.resize(900, 600)
        window.show()

        app.exec()


if __name__ == "__main__":
    app = Main()
    app.main()