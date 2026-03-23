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
from pathlib import Path
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

# TODO: ADD INTELLISENSE

class Highlighter(QSyntaxHighlighter):
    """
    Provides syntax highlighting for the editor.
    
    This class parses the text in the QPlainTextEdit and applies 
    specific formatting (color/weight) to keywords, strings, and comments.
    """
    def __init__(self, document, keywords):
        """
        Initializes the highlighter.
        document: the editor
        keywords: a list of keywords to apply the highlight on
        """
        super().__init__(document)
        self.keywords = set(keywords)

        # Define styles
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#569CD6"))
        self.keyword_format.setFontWeight(QFont.Bold)

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#9E9E9E"))

    def highlightBlock(self, text):
        """
        Applies formatting to a block of text (usually a line).
        Automatically called by PySide when the editor's content changes.

        text: The raw string of the current block.
        """
        # === comments ===
        index = text.find("#")
        if index != -1:
            self.setFormat(index, len(text) - index, self.comment_format)
            text = text[:index]  # Ignore comment part for further parsing

        # === strings ===
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

        # === keywords ===
        words = text.split()
        pos = 0
        for word in words:
            clean = word.strip("():,")
            if clean in self.keywords:
                # Find index starting from the last position to handle multiple occurrences
                index = text.find(word, pos)
                if index != -1:
                    self.setFormat(index, len(word), self.keyword_format)
            pos += len(word) + 1


class Main():
    def downloadBinaries(self):
        """
        Checks for and installs required dependencies (Scoop, Rust, Git, Crabby).
        This ensures the user's environment is ready for compiling Crabby code.
        """
        scoopCheck = subprocess.run("scoop --version", shell=True, capture_output=True, text=True).stdout
        if "Scoop" not in scoopCheck:
            subprocess.run("irm get.scoop.sh | iex", shell=True)

        rustCheck = subprocess.run("rustc --version", shell=True, capture_output=True, text=True).stdout
        if "rustc" not in rustCheck:
            subprocess.run("scoop install rust", shell=True)

        gitCheck = subprocess.run("git --version", shell=True, capture_output=True, text=True).stdout
        if "git version" not in gitCheck:
            subprocess.run("scoop install git", shell=True)
        
        subprocess.run("git clone https://github.com/crabby-lang/crabby.git", shell=True)
        subprocess.run("cargo build", shell=True)
        
    def __init__(self):
        self.keywords = [
            "def","class","if","else","elif","while","for","in",
            "return","import","from","as","try","except","with","pub",
            "let", "const", "var"
        ]
        self.runningCode = False 
        self.currentDir =  None # Default to current working directory
        self.currentFile = None
        self.downloadBinaries()

    def runCode(self): 
        """
        Saves the current file and executes it using crabby in a new console window.
        """
        if self.currentFile is None:
            QMessageBox.warning(None, "Error", "No file selected")
            return

        self.saveFile()

        # Run in a new CMD window to keep the IDE and program execution separate
        process = subprocess.Popen(
            f'start "" cmd /k "cd /d {self.currentDir} && crabby {self.currentFile}"',
            shell=True,
            creationflags=CREATE_NEW_CONSOLE
        )

    def createNewfile(self):
        """
        Prompts the user for a filename and creates a new empty file in the current root directory.
        """
        name = self.askUser("Enter filename (with extension):", "Create New File")
        if not name:
            return

        path = pathlib.Path(self.model.rootPath()) / name
        with open(path, "w", encoding="utf-8") as f:
            f.write("")

    def createNewFolder(self):
        """
        Prompts the user for a folder name and creates a new directory in the current root.
        """
        name = self.askUser("Enter folder name:", "Create New Folder")
        if not name:
            return

        path = pathlib.Path(self.model.rootPath()) / name
        os.mkdir(path)

    def stopCode(self):
        """
        Placeholder for stopping external execution. 
        Note: Currently, since code runs in a separate 'cmd' process, 
        this has limited control unless tracking PIDs.
        """
        self.runningCode = False

    def openFile(self, index):
        """
        Opens and reads a file into the editor when its item is clicked in the File Explorer.

        index: The QModelIndex from the QTreeView. 
        """
        path = pathlib.Path(self.model.filePath(index))

        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())

                self.currentFile = path.name
                self.currentDir = path.parent

            except Exception as e:
                QMessageBox.critical(None, "Error", f"Could not open file: {e}")
    
    def saveFile(self):
        """
        Saves the text currently in the editor back to the current file on disk.
        """
        if self.currentFile is None or self.currentDir is None:
            QMessageBox.warning(None, "Error", "No file selected to save")
            return

        code = self.editor.toPlainText()
        try:
            with open(self.currentDir / self.currentFile, "w", encoding="utf-8") as f:
                f.write(code)
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Could not save file: {e}")

    def openFolder(self):
        """
        Opens a directory selection dialog and updates the File Explorer root.
        """
        dir_path = QFileDialog.getExistingDirectory(None, "Select Directory", str(self.currentDir))
        if dir_path:
            self.currentDir = Path(dir_path)
            if hasattr(self, 'model'): # Update tree if already initialized
                self.model.setRootPath(dir_path)
                self.tree.setRootIndex(self.model.index(dir_path))

    def askUser(self, message, label):
        """
        Opens a simple text input dialog.

        :param message: The prompt message shown inside the dialog.
        :param label: The title of the dialog window.
        :return: The string entered by the user, or None if cancelled.
        """
        text, ok = QInputDialog.getText(None, label, message)
        if ok and text:
            return text
        return None

    def main(self):
        """
        Sets up the UI components, layouts, and menus, then starts the application loop.
        """
        app = QApplication(sys.argv)

        # main window + layout
        window = QWidget()
        window.setWindowTitle("Coral")
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

        # === File actions ===
        save_action = QAction("Save", window)
        save_action.triggered.connect(self.saveFile)
        new_file_action = QAction("New File", window)
        new_file_action.triggered.connect(self.createNewfile)
        new_folder_action = QAction("New Folder", window)
        new_folder_action.triggered.connect(self.createNewFolder)
        open_folder_action = QAction("Open Folder", window)
        open_folder_action.triggered.connect(self.openFolder)

        file_menu.addAction(new_file_action)
        file_menu.addAction(new_folder_action)
        file_menu.addSeparator()
        file_menu.addAction(open_folder_action)
        file_menu.addAction(save_action)

        # === MAIN CONTENT (HORIZONTAL) ===
        Hlayout = QHBoxLayout()
        mainLayout.addLayout(Hlayout)

        # === FILE EXPLORER ===
        self.openFolder()
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.currentDir))

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(self.currentDir)))
        self.tree.clicked.connect(self.openFile)

        # Hide size, type, and date columns for a cleaner look
        for i in range(1, 4):
            self.tree.hideColumn(i)

        # === EDITOR ===
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet("background:#1e1e1e; color:white;")
        self.editor.setFont(QFont("Consolas", 12))

        self.highlighter = Highlighter(self.editor.document(), self.keywords)

        # === ADD TO LAYOUT ===
        Hlayout.addWidget(self.tree, 1)
        Hlayout.addWidget(self.editor, 3)

        window.resize(900, 600)
        window.show()

        sys.exit(app.exec())

if __name__ == "__main__":
    ide = Main()
    ide.main()