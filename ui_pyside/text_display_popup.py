# ui_pyside/text_display_popup.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, 
                               QHBoxLayout, QApplication, QMessageBox)

class TextDisplayPopup(QDialog):
    def __init__(self, title, text_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 600)
        
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text_content)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        copy_button = QPushButton("전체 복사")
        copy_button.clicked.connect(self.copy_all)
        button_layout.addWidget(copy_button)
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)

    def copy_all(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "복사 완료", "모든 내용이 클립보드에 복사되었습니다.")