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
    QTabWidget,
    QTextEdit,
    QFileDialog,
    QSplitter
)

import pathlib
import shutil

from PySide6.QtGui import (
    QSyntaxHighlighter, 
    QTextCharFormat, 
    QColor, 
    QFont,
    QAction,
)
from PySide6.QtCore import QRegularExpression, QDir, Qt, QProcess
import sys
import subprocess
import os

#heya! this is a work in progress but if you want to make a commit
#i could use some help adding detailed descriptions to the classes/functions
#use docstrings on the top. describe what it does, what the parameters need, etc
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
        self.currentDir = pathlib.Path(QDir.currentPath())
        self.currentFile = None
        self.process = None
        self.tabPaths = {}
        self.highlighters = {}

    def getCurrentEditor(self):
        return self.tabs.currentWidget()

    def getCurrentPath(self):
        editor = self.getCurrentEditor()
        if editor in self.tabPaths:
            return self.tabPaths[editor]
        return None

    def setCurrentFileStuff(self):
        path = self.getCurrentPath()
        if path is not None:
            self.currentFile = path.name
            self.currentDir = path.parent
        else:
            self.currentFile = None

    def createEditorTab(self, path=None, content=""):
        editor = QPlainTextEdit()
        editor.setStyleSheet("background:#1e1e1e; color:white;")
        editor.setFont(QFont("Consolas", 12))
        editor.setPlainText(content)

        self.highlighters[editor] = Highlighter(editor.document(), self.keywords)

        if path is not None:
            self.tabPaths[editor] = pathlib.Path(path)
            name = pathlib.Path(path).name
        else:
            name = "untitled"

        self.tabs.addTab(editor, name)
        self.tabs.setCurrentWidget(editor)
        self.setCurrentFileStuff()
        return editor

    def appendConsole(self, text):
        self.console.moveCursor(self.console.textCursor().End)
        self.console.insertPlainText(text)
        self.console.moveCursor(self.console.textCursor().End)

    def clearConsole(self):
        self.console.clear()

    def handleReadyRead(self):
        if self.process is None:
            return

        data = self.process.readAllStandardOutput().data().decode(errors="ignore")
        if data:
            self.appendConsole(data)

    def handleFinished(self):
        self.runningCode = False
        self.appendConsole("\n[process finished]\n")

    def runCode(self): 
        path = self.getCurrentPath()

        if path is None:
            QMessageBox.warning(self.window, "Error", "No file selected")
            return

        self.saveFile()

        if self.process is not None and self.process.state() != QProcess.NotRunning:
            self.process.kill()

        self.clearConsole()
        self.appendConsole(f"[running] {path}\n\n")

        self.process = QProcess()
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handleReadyRead)
        self.process.finished.connect(self.handleFinished)

        self.runningCode = True
        self.process.setWorkingDirectory(str(path.parent))
        self.process.start("python", [str(path.name)])

    def createNewfile(self):
        name = self.askUser("Create new file:", "New File")
        if not name:
            return

        baseDir = self.getSelectedDir()
        path = baseDir / name

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("")
            self.createEditorTab(path, "")
        except Exception as e:
            QMessageBox.warning(self.window, "Error", str(e))

    def createNewFolder(self):
        name = self.askUser("Create new folder:", "New Folder")
        if not name:
            return

        baseDir = self.getSelectedDir()
        path = baseDir / name

        try:
            os.mkdir(path)
        except Exception as e:
            QMessageBox.warning(self.window, "Error", str(e))

    def renameItem(self):
        index = self.tree.currentIndex()
        if not index.isValid():
            return

        oldPath = pathlib.Path(self.model.filePath(index))
        newName = self.askUser(f"Rename '{oldPath.name}' to:", "Rename")
        if not newName:
            return

        newPath = oldPath.parent / newName

        try:
            oldPath.rename(newPath)

            for editor, path in list(self.tabPaths.items()):
                if path == oldPath:
                    self.tabPaths[editor] = newPath
                    i = self.tabs.indexOf(editor)
                    if i != -1:
                        self.tabs.setTabText(i, newPath.name)

            self.setCurrentFileStuff()

        except Exception as e:
            QMessageBox.warning(self.window, "Error", str(e))

    def deleteItem(self):
        index = self.tree.currentIndex()
        if not index.isValid():
            return

        path = pathlib.Path(self.model.filePath(index))

        confirm = QMessageBox.question(
            self.window,
            "Delete",
            f"Delete '{path.name}'?"
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

            for editor, editorPath in list(self.tabPaths.items()):
                if editorPath == path:
                    i = self.tabs.indexOf(editor)
                    if i != -1:
                        self.tabs.removeTab(i)
                    del self.tabPaths[editor]
                    if editor in self.highlighters:
                        del self.highlighters[editor]

            self.setCurrentFileStuff()

        except Exception as e:
            QMessageBox.warning(self.window, "Error", str(e))

    def stopCode(self):
        self.runningCode = False
        if self.process is not None and self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.appendConsole("\n[process stopped]\n")

    def openFile(self, index):
        path = pathlib.Path(self.model.filePath(index))

        if path.is_file():
            for editor, editorPath in self.tabPaths.items():
                if editorPath == path:
                    self.tabs.setCurrentWidget(editor)
                    self.setCurrentFileStuff()
                    return

            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.createEditorTab(path, f.read())

                self.currentFile = path.name
                self.currentDir = path.parent

            except Exception as e:
                print("Error:", e)

    def saveFile(self):
        editor = self.getCurrentEditor()
        path = self.getCurrentPath()

        if editor is None or path is None:
            QMessageBox.warning(self.window, "Error", "No file selected")
            return

        code = editor.toPlainText()

        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

    def saveCurrentTabAs(self):
        editor = self.getCurrentEditor()
        if editor is None:
            return

        filePath, _ = QFileDialog.getSaveFileName(self.window, "Save File As", str(self.currentDir))
        if not filePath:
            return

        path = pathlib.Path(filePath)

        with open(path, "w", encoding="utf-8") as f:
            f.write(editor.toPlainText())

        self.tabPaths[editor] = path
        i = self.tabs.indexOf(editor)
        if i != -1:
            self.tabs.setTabText(i, path.name)

        self.currentFile = path.name
        self.currentDir = path.parent

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
        text, ok = QInputDialog.getText(self.window, label, message)
        if ok and text:
            return text
        return None

    def getSelectedDir(self):
        index = self.tree.currentIndex()

        if index.isValid():
            path = pathlib.Path(self.model.filePath(index))
            if path.is_dir():
                return path
            return path.parent

        return pathlib.Path(self.model.rootPath())

    def openFolder(self):
        folder = QFileDialog.getExistingDirectory(self.window, "Open Folder", str(self.currentDir))
        if not folder:
            return

        self.currentDir = pathlib.Path(folder)
        self.model.setRootPath(folder)
        self.tree.setRootIndex(self.model.index(folder))

    def closeTab(self, index):
        editor = self.tabs.widget(index)
        if editor is None:
            return

        if editor in self.tabPaths:
            del self.tabPaths[editor]

        if editor in self.highlighters:
            del self.highlighters[editor]

        self.tabs.removeTab(index)
        self.setCurrentFileStuff()

    def changeTab(self):
        self.setCurrentFileStuff()

    def showExplorerMenu(self, pos):
        menu = QMenu(self.tree)

        new_file_action = QAction("New File", self.window)
        new_file_action.triggered.connect(self.createNewfile)

        new_folder_action = QAction("New Folder", self.window)
        new_folder_action.triggered.connect(self.createNewFolder)

        rename_action = QAction("Rename", self.window)
        rename_action.triggered.connect(self.renameItem)

        delete_action = QAction("Delete", self.window)
        delete_action.triggered.connect(self.deleteItem)

        menu.addAction(new_file_action)
        menu.addAction(new_folder_action)
        menu.addSeparator()
        menu.addAction(rename_action)
        menu.addAction(delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def main(self):
        app = QApplication(sys.argv)

        # main window + layout
        window = QWidget()
        self.window = window
        mainLayout = QVBoxLayout(window)

        # === TOPBAR ===
        topbar = QMenuBar()
        mainLayout.addWidget(topbar)

        # === MENUS ===
        run_menu = topbar.addMenu("Run")
        file_menu = topbar.addMenu("File")

        # --- Run actions ---
        run_action = QAction("Run Code", window)
        run_action.triggered.connect(self.runCode)

        stop_action = QAction("Stop", window)
        stop_action.triggered.connect(self.stopCode)

        run_menu.addAction(run_action)
        run_menu.addAction(stop_action)

        # --- File actions ---
        open_folder_action = QAction("Open Folder", window)
        open_folder_action.triggered.connect(self.openFolder)

        save_action = QAction("Save", window)
        save_action.triggered.connect(self.saveFile)

        save_as_action = QAction("Save As", window)
        save_as_action.triggered.connect(self.saveCurrentTabAs)

        new_file_action = QAction("New File", window)
        new_file_action.triggered.connect(self.createNewfile)

        new_folder_action = QAction("New Folder", window)
        new_folder_action.triggered.connect(self.createNewFolder)

        file_menu.addAction(open_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(new_file_action)
        file_menu.addAction(new_folder_action)

        topbar.setStyleSheet("""
            QMenuBar {
                background-color: #2b2b2b;
                color: white;
            }

            QMenuBar::item {
                background: transparent;
                padding: 6px 12px;
            }

            QMenuBar::item:selected {
                background: #3c3c3c;
            }

            QMenu {
                background-color: #2b2b2b;
                color: white;
            }

            QMenu::item:selected {
                background-color: #3c3c3c;
            }
        """)

        # === MAIN CONTENT ===
        splitter = QSplitter(Qt.Horizontal)
        mainLayout.addWidget(splitter)

        # === FILE EXPLORER ===
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.currentPath())

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.currentPath()))
        self.tree.clicked.connect(self.openFile)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.showExplorerMenu)

        for i in range(1, 4):
            self.tree.hideColumn(i)

        self.tree.setStyleSheet("""
            QTreeView {
                background:#1e1e1e;
                color:white;
                border:none;
            }
            QTreeView::item:selected {
                background:#3c3c3c;
            }
        """)

        # === RIGHT SIDE ===
        rightWidget = QWidget()
        rightLayout = QVBoxLayout(rightWidget)
        rightLayout.setContentsMargins(0, 0, 0, 0)

        # === TABS ===
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.closeTab)
        self.tabs.currentChanged.connect(self.changeTab)

        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border:none;
            }
            QTabBar::tab {
                background:#2b2b2b;
                color:white;
                padding:8px 12px;
            }
            QTabBar::tab:selected {
                background:#3c3c3c;
            }
        """)

        # === CONSOLE ===
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 10))
        self.console.setStyleSheet("""
            background:#111111;
            color:#d4d4d4;
            border:none;
        """)
        self.console.setFixedHeight(180)

        rightLayout.addWidget(self.tabs, 3)
        rightLayout.addWidget(self.console, 1)

        splitter.addWidget(self.tree)
        splitter.addWidget(rightWidget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        # starter tab
        self.createEditorTab()

        # window setup
        window.resize(1100, 700)
        window.show()

        app.exec()


if __name__ == "__main__":
    app = Main()
    app.main()