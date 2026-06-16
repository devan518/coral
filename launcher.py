import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QFileDialog,
    QLineEdit,
    QMessageBox,
)

from PySide6.QtCore import Qt

from crabby_ide import Main as CrabbyMain
from esolang_ide import Main as EsolangMain


class IDELauncher(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Coral IDE Launcher")
        self.resize(900, 550)

        self.open_project_window = None
        self.new_project_window = None

        # Store IDE windows so Python does not delete them
        self.ide_windows = []

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("sidebar")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 20)
        sidebar_layout.setSpacing(15)
        sidebar_layout.setAlignment(Qt.AlignTop)

        open_project_btn = QPushButton("Open Project")
        new_project_btn = QPushButton("New Project")

        open_project_btn.setFixedHeight(42)
        new_project_btn.setFixedHeight(42)

        open_project_btn.clicked.connect(self.open_project)
        new_project_btn.clicked.connect(self.new_project)

        sidebar_layout.addWidget(open_project_btn)
        sidebar_layout.addWidget(new_project_btn)

        content = QFrame()
        content.setObjectName("content")

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.setCentralWidget(main_widget)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }

            #sidebar {
                background-color: #252526;
                border-right: 1px solid #333333;
            }

            #content {
                background-color: #1e1e1e;
            }

            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                text-align: left;
                padding-left: 14px;
            }

            QPushButton:hover {
                background-color: #3f3f46;
            }

            QPushButton:pressed {
                background-color: #007acc;
            }
        """)

    def launch_ide(self, path, ide_type="crabby"):
        try:
            if ide_type == "esolang":
                ide = EsolangMain(path)
            else:
                ide = CrabbyMain(path)

            ide.show()
            self.ide_windows.append(ide)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open project:\n{e}")

    def open_project(self):
        self.open_project_window = QWidget()
        self.open_project_window.setWindowTitle("Open Project")
        self.open_project_window.resize(620, 360)

        layout = QVBoxLayout(self.open_project_window)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(14)

        title = QLabel("Open Project")
        title.setObjectName("title")

        subtitle = QLabel("Choose which IDE to open this project with.")
        subtitle.setObjectName("subtitle")

        # ================= IDE TYPE =================

        ide_type_label = QLabel("IDE Type")
        ide_type_label.setObjectName("pathLabel")

        ide_type_row = QHBoxLayout()
        ide_type_row.setSpacing(10)

        crabby_btn = QPushButton("Crabby")
        yurilang_btn = QPushButton("Yurilang")

        crabby_btn.setFixedHeight(36)
        yurilang_btn.setFixedHeight(36)

        selected_type = {"type": "crabby"}

        def set_type_button_styles():
            if selected_type["type"] == "crabby":
                crabby_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D52D00;
                        color: white;
                        border: none;
                        border-radius: 7px;
                        padding: 8px 12px;
                        font-weight: bold;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #EF7627;
                    }
                """)

                yurilang_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #333333;
                        color: white;
                        border: 1px solid #444444;
                        border-radius: 7px;
                        padding: 8px 12px;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #3f3f46;
                    }
                """)

            else:
                yurilang_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D162A4;
                        color: white;
                        border: none;
                        border-radius: 7px;
                        padding: 8px 12px;
                        font-weight: bold;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #FF1493;
                    }
                """)

                crabby_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #333333;
                        color: white;
                        border: 1px solid #444444;
                        border-radius: 7px;
                        padding: 8px 12px;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #3f3f46;
                    }
                """)

        def select_crabby():
            selected_type["type"] = "crabby"
            set_type_button_styles()

        def select_yurilang():
            selected_type["type"] = "esolang"
            set_type_button_styles()

        crabby_btn.clicked.connect(select_crabby)
        yurilang_btn.clicked.connect(select_yurilang)

        ide_type_row.addWidget(crabby_btn)
        ide_type_row.addWidget(yurilang_btn)

        select_crabby()

        # ================= PROJECT PATH =================

        path_label = QLabel("Project Folder")
        path_label.setObjectName("pathLabel")

        path_row = QHBoxLayout()
        path_row.setSpacing(10)

        path_input = QLineEdit()
        path_input.setPlaceholderText("Type or select the project folder...")

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(100)

        path_row.addWidget(path_input)
        path_row.addWidget(browse_btn)

        def select_path():
            folder = QFileDialog.getExistingDirectory(
                self.open_project_window,
                "Open Project Folder"
            )

            if folder:
                path_input.setText(folder.replace("\\", "/"))

        browse_btn.clicked.connect(select_path)

        # ================= OPEN PROJECT =================

        def open_selected_project():
            project_path_text = path_input.text().strip()

            if not project_path_text:
                QMessageBox.warning(
                    self.open_project_window,
                    "Missing Project Folder",
                    "Please enter or select a project folder."
                )
                return

            project_path = Path(project_path_text).expanduser()

            if not project_path.exists():
                QMessageBox.warning(
                    self.open_project_window,
                    "Folder Not Found",
                    "That project folder does not exist."
                )
                return

            if not project_path.is_dir():
                QMessageBox.warning(
                    self.open_project_window,
                    "Invalid Project Folder",
                    "The selected path is not a folder."
                )
                return

            self.launch_ide(str(project_path), selected_type["type"])
            self.open_project_window.close()

        open_btn = QPushButton("Open Project")
        open_btn.setObjectName("primaryButton")
        open_btn.setFixedHeight(40)
        open_btn.clicked.connect(open_selected_project)

        # ================= ADD WIDGETS =================

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        layout.addWidget(ide_type_label)
        layout.addLayout(ide_type_row)

        layout.addSpacing(10)

        layout.addWidget(path_label)
        layout.addLayout(path_row)

        layout.addStretch()
        layout.addWidget(open_btn)

        self.open_project_window.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
                font-family: Segoe UI;
                font-size: 14px;
            }

            QLabel#title {
                font-size: 22px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #a0a0a0;
                font-size: 13px;
            }

            QLabel#pathLabel {
                color: #d4d4d4;
                font-weight: bold;
            }

            QLineEdit {
                background-color: #2d2d30;
                color: white;
                border: 1px solid #3f3f46;
                border-radius: 7px;
                padding: 8px 10px;
                selection-background-color: #007acc;
            }

            QLineEdit:focus {
                border: 1px solid #007acc;
            }

            QPushButton {
                background-color: #333333;
                color: white;
                border: 1px solid #444444;
                border-radius: 7px;
                padding: 8px 12px;
                text-align: center;
            }

            QPushButton:hover {
                background-color: #3f3f46;
            }

            QPushButton:pressed {
                background-color: #007acc;
            }

            QPushButton#primaryButton {
                background-color: #007acc;
                border: none;
                font-weight: bold;
            }

            QPushButton#primaryButton:hover {
                background-color: #1688d9;
            }
        """)

        self.open_project_path_input = path_input
        self.open_project_window.show()

    def new_project(self):
        self.new_project_window = QWidget()
        self.new_project_window.setWindowTitle("New Project")
        self.new_project_window.resize(620, 460)

        layout = QVBoxLayout(self.new_project_window)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(14)

        title = QLabel("Create New Project")
        title.setObjectName("title")

        subtitle = QLabel("Choose a project type, project name, and parent folder.")
        subtitle.setObjectName("subtitle")

        # ================= PROJECT TYPE =================

        project_type_label = QLabel("Project Type")
        project_type_label.setObjectName("pathLabel")

        project_type_row = QHBoxLayout()
        project_type_row.setSpacing(10)

        crabby_btn = QPushButton("Crabby")
        yurilang_btn = QPushButton("Yurilang")

        crabby_btn.setFixedHeight(36)
        yurilang_btn.setFixedHeight(36)

        selected_type = {"type": "crabby"}

        def set_type_button_styles():
            if selected_type["type"] == "crabby":
                crabby_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D52D00;
                        color: white;
                        border: none;
                        border-radius: 7px;
                        padding: 8px 12px;
                        font-weight: bold;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #EF7627;
                    }
                """)

                yurilang_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #333333;
                        color: white;
                        border: 1px solid #444444;
                        border-radius: 7px;
                        padding: 8px 12px;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #3f3f46;
                    }
                """)

            else:
                yurilang_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #D162A4;
                        color: white;
                        border: none;
                        border-radius: 7px;
                        padding: 8px 12px;
                        font-weight: bold;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #FF1493;
                    }
                """)

                crabby_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #333333;
                        color: white;
                        border: 1px solid #444444;
                        border-radius: 7px;
                        padding: 8px 12px;
                        text-align: center;
                    }

                    QPushButton:hover {
                        background-color: #3f3f46;
                    }
                """)

        def select_crabby():
            selected_type["type"] = "crabby"
            set_type_button_styles()

        def select_yurilang():
            selected_type["type"] = "esolang"
            set_type_button_styles()

        crabby_btn.clicked.connect(select_crabby)
        yurilang_btn.clicked.connect(select_yurilang)

        project_type_row.addWidget(crabby_btn)
        project_type_row.addWidget(yurilang_btn)

        select_crabby()

        # ================= PROJECT NAME =================

        name_label = QLabel("Project Name")
        name_label.setObjectName("pathLabel")

        name_input = QLineEdit()
        name_input.setPlaceholderText("Example: my_project")

        # ================= PROJECT PATH =================

        path_label = QLabel("Parent Folder")
        path_label.setObjectName("pathLabel")

        path_row = QHBoxLayout()
        path_row.setSpacing(10)

        path_input = QLineEdit()
        path_input.setPlaceholderText("Type or select the parent folder...")

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(100)

        path_row.addWidget(path_input)
        path_row.addWidget(browse_btn)

        # ================= PREVIEW =================

        preview_label_title = QLabel("Final Project Path")
        preview_label_title.setObjectName("pathLabel")

        preview_label = QLabel("No project path selected yet.")
        preview_label.setObjectName("previewLabel")
        preview_label.setWordWrap(True)

        def update_preview():
            parent_path = path_input.text().strip()
            project_name = name_input.text().strip()

            if parent_path and project_name:
                final_path = Path(parent_path).expanduser() / project_name
                preview_label.setText(str(final_path).replace("\\", "/"))

            elif parent_path:
                preview_label.setText(
                    str(Path(parent_path).expanduser()).replace("\\", "/") + "/..."
                )

            elif project_name:
                preview_label.setText(f".../{project_name}")

            else:
                preview_label.setText("No project path selected yet.")

        def select_path():
            folder = QFileDialog.getExistingDirectory(
                self.new_project_window,
                "Select Parent Folder"
            )

            if folder:
                path_input.setText(folder.replace("\\", "/"))
                update_preview()

        browse_btn.clicked.connect(select_path)
        name_input.textChanged.connect(update_preview)
        path_input.textChanged.connect(update_preview)

        # ================= CREATE PROJECT =================

        def create_project():
            parent_path_text = path_input.text().strip()
            project_name_text = name_input.text().strip()

            if not project_name_text:
                QMessageBox.warning(
                    self.new_project_window,
                    "Missing Project Name",
                    "Please enter a project name."
                )
                return

            if not parent_path_text:
                QMessageBox.warning(
                    self.new_project_window,
                    "Missing Parent Folder",
                    "Please enter or select a parent folder."
                )
                return

            invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

            if any(char in project_name_text for char in invalid_chars):
                QMessageBox.warning(
                    self.new_project_window,
                    "Invalid Project Name",
                    "Project name cannot contain: < > : \" / \\ | ? *"
                )
                return

            project_path = Path(parent_path_text).expanduser() / project_name_text

            try:
                project_path.mkdir(parents=True, exist_ok=True)

            except Exception as e:
                QMessageBox.critical(
                    self.new_project_window,
                    "Error",
                    f"Could not create project folder:\n{e}"
                )
                return

            self.launch_ide(str(project_path), selected_type["type"])
            self.new_project_window.close()

        create_btn = QPushButton("Create Project")
        create_btn.setObjectName("primaryButton")
        create_btn.setFixedHeight(40)
        create_btn.clicked.connect(create_project)

        # ================= ADD WIDGETS =================

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        layout.addWidget(project_type_label)
        layout.addLayout(project_type_row)

        layout.addSpacing(10)

        layout.addWidget(name_label)
        layout.addWidget(name_input)

        layout.addWidget(path_label)
        layout.addLayout(path_row)

        layout.addWidget(preview_label_title)
        layout.addWidget(preview_label)

        layout.addStretch()
        layout.addWidget(create_btn)

        self.new_project_window.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
                font-family: Segoe UI;
                font-size: 14px;
            }

            QLabel#title {
                font-size: 22px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #a0a0a0;
                font-size: 13px;
            }

            QLabel#pathLabel {
                color: #d4d4d4;
                font-weight: bold;
            }

            QLabel#previewLabel {
                background-color: #252526;
                color: #cfcfcf;
                border: 1px solid #3f3f46;
                border-radius: 7px;
                padding: 8px 10px;
                font-family: Consolas;
                font-size: 12px;
            }

            QLineEdit {
                background-color: #2d2d30;
                color: white;
                border: 1px solid #3f3f46;
                border-radius: 7px;
                padding: 8px 10px;
                selection-background-color: #007acc;
            }

            QLineEdit:focus {
                border: 1px solid #007acc;
            }

            QPushButton {
                background-color: #333333;
                color: white;
                border: 1px solid #444444;
                border-radius: 7px;
                padding: 8px 12px;
                text-align: center;
            }

            QPushButton:hover {
                background-color: #3f3f46;
            }

            QPushButton:pressed {
                background-color: #007acc;
            }

            QPushButton#primaryButton {
                background-color: #007acc;
                border: none;
                font-weight: bold;
            }

            QPushButton#primaryButton:hover {
                background-color: #1688d9;
            }
        """)

        self.new_project_name_input = name_input
        self.new_project_path_input = path_input
        self.new_project_window.show()


app = QApplication(sys.argv)

window = IDELauncher()
window.show()

sys.exit(app.exec())