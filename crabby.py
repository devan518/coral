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
    QMenu,
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
import shutil
from src.core import CrabHighlighter, CrabCodeHinter


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

    def deleteFile(self):
        if self.currentFile is None or self.currentDir is None:
            QMessageBox.warning(self, "Error", "No file selected to delete")
            return

        file_path = self.currentDir / self.currentFile
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{self.currentFile}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if file_path.is_file():
                    file_path.unlink()
                    self.editor.clear()
                    self.currentFile = None
                    self.setWindowTitle(f"Coral - {self.currentDir.name}")
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                    self.editor.clear()
                    self.currentFile = None
                    self.setWindowTitle(f"Coral - {self.currentDir.name}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete file: {e}")

    def onTreeContextMenu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            return

        file_path = self.model.filePath(index)
        self.currentFile = Path(file_path).name
        self.currentDir = Path(file_path).parent

        menu = QMenu()
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.deleteFile)
        menu.addAction(delete_action)
        menu.exec(self.tree.mapToGlobal(position))

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
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.onTreeContextMenu)

        for i in range(1, 4):
            self.tree.hideColumn(i)

        # === EDITOR ===
        self.editor = QPlainTextEdit()
        self.editor.setStyleSheet("background:#1e1e1e; color:white;")
        self.editor.setFont(QFont("Consolas", 12))

        self.highlighter = CrabHighlighter(self.editor.document(), self.keywords)
        self.codehinter = CrabCodeHinter(self.editor, self.keywords)

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

        qss_path = Path(__file__).parent / "assets" / "crabby.styling.qss"
        self.setStyleSheet(qss_path.read_text())
        self.showMaximized()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = Main(Path.cwd())
    ide.show()
    sys.exit(app.exec())
    