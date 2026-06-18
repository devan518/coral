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
    QLineEdit
)
from PySide6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QColor,
    QFont,
    QAction,
    QTextCursor,
)
from PySide6.QtCore import Qt, QStringListModel, QEvent
from subprocess import CREATE_NEW_CONSOLE
import shutil
from src.core import CrabHighlighter, CrabCodeHinter


class Main(QWidget):
    def __init__(self, startup_path):
        super().__init__()
        self.setObjectName("mainWindow")

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
        QApplication.instance().installEventFilter(self)

    def repairBinaries(self):
        ...

    def downloadBinaries(self):
        """
        Checks for and installs required dependencies.
        Currently disabled.
        """
        ...

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ContextMenu:
            widget = QApplication.widgetAt(event.globalPos())

            # Ignore right-clicks outside this window
            if widget is None:
                return False

            if widget != self and not self.isAncestorOf(widget):
                return False

            self.showContextMenuForPosition(event.globalPos())
            return True

        return super().eventFilter(obj, event)
    
    def copyQtObjectName(self, widget):
        object_name = widget.objectName()

        if not object_name:
            object_name = f"<no objectName> {widget.metaObject().className()}"

        QApplication.clipboard().setText(object_name)

    def showContextMenuForPosition(self, global_pos):
        menu = QMenu(self)

        clicked_widget = QApplication.widgetAt(global_pos)
        object_name_widget = clicked_widget

        # Check if right-click was inside the file tree
        tree_pos = self.tree.viewport().mapFromGlobal(global_pos)
        inside_tree = self.tree.viewport().rect().contains(tree_pos)

        if inside_tree:
            object_name_widget = self.tree
            index = self.tree.indexAt(tree_pos)

            if index.isValid():
                path = Path(self.model.filePath(index))

                open_action = QAction("Open", self)
                open_action.triggered.connect(lambda checked=False, p=path: self.openPath(p))

                rename_action = QAction("Rename", self)
                rename_action.triggered.connect(lambda checked=False, p=path: self.renamePath(p))

                delete_action = QAction("Delete", self)
                delete_action.triggered.connect(lambda checked=False, p=path: self.deletePath(p))

                menu.addAction(open_action)
                menu.addAction(rename_action)
                menu.addAction(delete_action)

            else:
                new_file_action = QAction("New File", self)
                new_file_action.triggered.connect(self.createNewfile)

                new_folder_action = QAction("New Folder", self)
                new_folder_action.triggered.connect(self.createNewFolder)

                menu.addAction(new_file_action)
                menu.addAction(new_folder_action)

        # Check if right-click was inside the editor
        editor_pos = self.editor.viewport().mapFromGlobal(global_pos)
        inside_editor = self.editor.viewport().rect().contains(editor_pos)

        if inside_editor:
            object_name_widget = self.editor

            if not menu.isEmpty():
                menu.addSeparator()

            cut_action = QAction("Cut", self)
            cut_action.triggered.connect(self.editor.cut)

            copy_action = QAction("Copy", self)
            copy_action.triggered.connect(self.editor.copy)

            paste_action = QAction("Paste", self)
            paste_action.triggered.connect(self.editor.paste)

            save_action = QAction("Save", self)
            save_action.triggered.connect(self.saveFile)

            run_action = QAction("Run Code", self)
            run_action.triggered.connect(self.runCode)

            menu.addAction(cut_action)
            menu.addAction(copy_action)
            menu.addAction(paste_action)
            menu.addSeparator()
            menu.addAction(save_action)
            menu.addAction(run_action)

        # If right-click was somewhere else in the window
        if menu.isEmpty():
            new_file_action = QAction("New File", self)
            new_file_action.triggered.connect(self.createNewfile)

            open_folder_action = QAction("Open Folder", self)
            open_folder_action.triggered.connect(self.openFolder)

            menu.addAction(new_file_action)
            menu.addAction(open_folder_action)

        # Always add this debug/helper action at the bottom
        if object_name_widget is not None:
            if not menu.isEmpty():
                menu.addSeparator()

            copy_object_name_action = QAction("Copy Qt Object Name", self)
            copy_object_name_action.triggered.connect(
                lambda checked=False, w=object_name_widget: self.copyQtObjectName(w)
            )

            menu.addAction(copy_object_name_action)

        menu.exec(global_pos)


    def openPath(self, path):
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())

                self.currentFile = path.name
                self.currentDir = path.parent
                self.setWindowTitle(f"Coral - {path.name}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")

        elif path.is_dir():
            self.currentDir = path
            self.currentFile = None

            self.model.setRootPath(str(path))
            self.tree.setRootIndex(self.model.index(str(path)))
            self.editor.clear()
            self.setWindowTitle(f"Coral - {path.name}")

    def deletePath(self, path):
        if not path.exists():
            QMessageBox.warning(self, "Error", "Path does not exist")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{path.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            if path.is_file():
                path.unlink()

            elif path.is_dir():
                shutil.rmtree(path)

            opened_path = None

            if self.currentFile is not None and self.currentDir is not None:
                opened_path = self.currentDir / self.currentFile

            if opened_path == path:
                self.editor.clear()
                self.currentFile = None
                self.setWindowTitle(f"Coral - {self.currentDir.name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not delete: {e}")
    
    def renamePath(self, path):
        new_name = self.askUser("Enter new name:", "Rename", str(path.name))

        if not new_name:
            return

        new_path = path.parent / new_name

        try:
            path.rename(new_path)

            if self.currentFile == path.name and self.currentDir == path.parent:
                self.currentFile = new_path.name
                self.currentDir = new_path.parent
                self.setWindowTitle(f"Coral - {new_path.name}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not rename: {e}")
            
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

    def askUser(self, message, label, placeholder=""):
        dialog = QInputDialog(self)
        dialog.setWindowTitle(label)
        dialog.setLabelText(message)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setTextValue(placeholder)

        if dialog.exec():
            text = dialog.textValue().strip()

            if text:
                return text

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
        topbar.setObjectName("topMenuBar")
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
        self.tree.setObjectName("fileTree")
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(self.currentDir)))
        self.tree.clicked.connect(self.openFile)

        for i in range(1, 4):
            self.tree.hideColumn(i)

        # === EDITOR ===
        self.editor = QPlainTextEdit()
        self.editor.setObjectName("codeEditor")
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
    