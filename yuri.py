import sys
import os
import pathlib
import subprocess
from pathlib import Path
from subprocess import CREATE_NEW_CONSOLE

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
    QFileDialog
)

from PySide6.QtGui import (
    QFont,
    QAction,
    QDesktopServices
)

from PySide6.QtCore import QUrl

from src.core import Highlighter, CodeHinter

class Main(QWidget):
    def __init__(self, startup_path):
        super().__init__()

        self.keywords = [
            "@wlw",
            "@yuri",
            "@bond",
            "@awakening",
            "@confess",
            "@ship",
            "@promise",
            "@jealous",
            "@forgive",
            "@fate",
            "@cling",
            "@sappho",
            "@poet",
            "@spectrum",
            "@persona",
            "@rebond",
            "plus",
            "minus",
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

        command = f'cd /d "{self.currentDir}" && yurilang "{self.currentFile}"'

        subprocess.Popen(
            ["cmd", "/k", command],
            creationflags=CREATE_NEW_CONSOLE,
        )

    def createNewfile(self):
        name = self.askUser("Enter filename with extension (.yuri):", "Create New File")

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
                self.setWindowTitle(f"Yurilang IDE - {path.name}")

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
            self.setWindowTitle(f"Yurilang IDE - {self.currentDir.name}")

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
        self.setWindowTitle("Yurilang IDE")

        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # === TOPBAR ===
        topbar = QMenuBar()
        topbar.setObjectName("topbar")
        mainLayout.addWidget(topbar)

        # === MENUS ===
        file_menu = topbar.addMenu("File")
        run_menu = topbar.addMenu("Run")
        doc_menu = topbar.addMenu("Docs")
        cberg_menu = topbar.addMenu("Yuri")
        coral_menu = topbar.addMenu("Repo")

        doc_action = QAction("Documentation", self)
        doc_action.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://kazooki123.github.io/yurilang-docs/")
            )
        )
        
        cberg_action = QAction("Codeberg",self)
        coral_repo   = QAction("Coral", self)
        cberg_action.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://codeberg.org/Kazooki123/yurilang")
            ),
        )
        coral_repo.triggered.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/devan518/coral")
            )
        )
        
        doc_menu.addAction(doc_action)  
        cberg_menu.addAction(cberg_action)
        coral_menu.addAction(coral_repo)
        
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
        self.tree.setObjectName("fileTree")
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(self.currentDir)))
        self.tree.clicked.connect(self.openFile)

        for i in range(1, 4):
            self.tree.hideColumn(i)

        # === EDITOR ===
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("editor")
        self.editor.setFont(QFont("Consolas", 12))

        self.highlighter = Highlighter(self.editor.document(), self.keywords)
        self.codehinter = CodeHinter(self.editor, self.keywords)

        self.codehinter.popup().setStyleSheet("""
            QListView {
                background-color: #3A102B;
                color: #FFF4FA;
                border: 1px solid #D162A4;
                selection-background-color: #A30262;
                selection-color: white;
                padding: 4px;
                font-family: Consolas;
                font-size: 13px;
            }
        """)

        # === OPEN FILE IF STARTUP PATH WAS A FILE ===
        if self.currentFile is not None:
            try:
                with open(self.currentDir / self.currentFile, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())

                self.setWindowTitle(f"Yurilang IDE - {self.currentFile}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")

        else:
            self.setWindowTitle(f"Yurilang IDE - {self.currentDir.name}")

        # === ADD WIDGETS ===
        Hlayout.addWidget(self.tree, 1)
        Hlayout.addWidget(self.editor, 3)

        self.setStyleSheet("""
            QWidget {
                background-color: #240B1B;
                color: #FFF4FA;
                font-family: Segoe UI;
                font-size: 13px;
            }

            QMenuBar#topbar {
                background-color: #3A102B;
                color: #FFF4FA;
                border-bottom: 2px solid #A30262;
                padding: 3px;
            }

            QMenuBar#topbar::item {
                background: transparent;
                color: #FFF4FA;
                padding: 6px 12px;
                border-radius: 5px;
            }

            QMenuBar#topbar::item:selected {
                background-color: #A30262;
                color: white;
            }

            QMenu {
                background-color: #3A102B;
                color: #FFF4FA;
                border: 1px solid #D162A4;
                padding: 5px;
            }

            QMenu::item {
                padding: 7px 26px 7px 20px;
                border-radius: 4px;
            }

            QMenu::item:selected {
                background-color: #A30262;
                color: white;
            }

            QMenu::separator {
                height: 1px;
                background-color: #B55690;
                margin: 5px 8px;
            }

            QTreeView#fileTree {
                background-color: #2D0C22;
                color: #FFF4FA;
                border: none;
                border-right: 2px solid #A30262;
                alternate-background-color: #3A102B;
                selection-background-color: #D162A4;
                selection-color: white;
                outline: none;
                padding: 6px;
            }

            QTreeView#fileTree::item {
                padding: 5px;
                border-radius: 5px;
            }

            QTreeView#fileTree::item:hover {
                background-color: #54213F;
            }

            QTreeView#fileTree::item:selected {
                background-color: #A30262;
                color: white;
            }

            QHeaderView::section {
                background-color: #3A102B;
                color: #FFF4FA;
                border: none;
                border-bottom: 1px solid #B55690;
                padding: 5px;
            }

            QPlainTextEdit#editor {
                background-color: #180711;
                color: #FFF4FA;
                border: none;
                selection-background-color: #D162A4;
                selection-color: white;
                padding: 12px;
            }

            QScrollBar:vertical {
                background-color: #240B1B;
                width: 12px;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background-color: #B55690;
                border-radius: 6px;
                min-height: 25px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #D162A4;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar:horizontal {
                background-color: #240B1B;
                height: 12px;
                margin: 0px;
            }

            QScrollBar::handle:horizontal {
                background-color: #B55690;
                border-radius: 6px;
                min-width: 25px;
            }

            QScrollBar::handle:horizontal:hover {
                background-color: #D162A4;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }

            QMessageBox {
                background-color: #240B1B;
                color: #FFF4FA;
            }

            QInputDialog {
                background-color: #240B1B;
                color: #FFF4FA;
            }

            QLineEdit {
                background-color: #180711;
                color: #FFF4FA;
                border: 1px solid #D162A4;
                border-radius: 6px;
                padding: 7px;
                selection-background-color: #A30262;
            }

            QPushButton {
                background-color: #A30262;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 7px 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #D162A4;
            }

            QPushButton:pressed {
                background-color: #EF7627;
            }
        """)

        self.resize(900, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    ide = Main(Path.cwd())
    ide.show()

    sys.exit(app.exec())