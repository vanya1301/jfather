# jfather/update_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTextEdit, QDialogButtonBox)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

class UpdateDialog(QDialog):
    def __init__(self, current_version: str, release_info: dict, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.setup_ui(current_version, release_info)
        
    def setup_ui(self, current_version: str, release_info: dict):
        self.setWindowTitle("Update Available")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        if release_info:
            # Update available
            latest_version = release_info.get('tag_name', 'Unknown').lstrip('v')
            
            title = QLabel(f"Version {latest_version} is available!")
            title.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(title)
            
            current = QLabel(f"Current version: {current_version}")
            layout.addWidget(current)
            
            changelog_label = QLabel("Changelog:")
            layout.addWidget(changelog_label)
            
            changelog = QTextEdit()
            changelog.setReadOnly(True)
            changelog.setPlainText(release_info.get('body', 'No changelog available'))
            layout.addWidget(changelog)
            
            button_box = QDialogButtonBox()
            download_btn = QPushButton("Download")
            download_btn.clicked.connect(self.open_download)
            button_box.addButton(download_btn, QDialogButtonBox.ActionRole)
            
            later_btn = QPushButton("Later")
            later_btn.clicked.connect(self.reject)
            button_box.addButton(later_btn, QDialogButtonBox.RejectRole)
            
            layout.addWidget(button_box)
        else:
            # No update available
            title = QLabel("You're up to date!")
            title.setStyleSheet("font-size: 14px; font-weight: bold;")
            layout.addWidget(title)
            
            current = QLabel(f"Current version: {current_version}")
            layout.addWidget(current)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(self.accept)
            layout.addWidget(button_box)
    
    def open_download(self):
        if self.release_info:
            url = QUrl(self.release_info.get('html_url'))
            QDesktopServices.openUrl(url)
        self.accept()
