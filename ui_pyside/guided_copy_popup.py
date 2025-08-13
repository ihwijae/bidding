# ui_pyside/guided_copy_popup.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QApplication, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class GuidedCopyPopup(QDialog):
    def __init__(self, copy_chunks, parent=None):
        super().__init__(parent)
        self.copy_chunks = copy_chunks
        self.current_step = 0
        self.setWindowTitle("단계별 안전 복사"); self.setMinimumWidth(450)
        main_layout = QVBoxLayout(self)
        self.step_label = QLabel(); self.step_label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        self.instruction_label = QLabel(); self.instruction_label.setFont(QFont("맑은 고딕", 10))
        self.instruction_label.setStyleSheet("color: blue; padding: 10px; background-color: #F0F0F0; border-radius: 5px;")
        main_layout.addWidget(self.step_label); main_layout.addWidget(self.instruction_label)
        button_layout = QHBoxLayout(); button_layout.addStretch(1)
        self.copy_button = QPushButton("📋 클립보드로 복사"); self.next_button = QPushButton("다음 ▶"); self.cancel_button = QPushButton("취소")
        button_layout.addWidget(self.copy_button); button_layout.addWidget(self.next_button); button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)
        self.copy_button.clicked.connect(self.copy_current_chunk)
        self.next_button.clicked.connect(self.go_to_next_step); self.cancel_button.clicked.connect(self.reject)
        self.update_step_ui()

    def update_step_ui(self):
        chunk = self.copy_chunks[self.current_step]
        self.step_label.setText(f"<b>[ {self.current_step + 1} / {len(self.copy_chunks)} 단계 ]</b>")
        self.instruction_label.setText(chunk["instruction"])
        if self.current_step == len(self.copy_chunks) - 1: self.next_button.setText("완료 ✔")
        else: self.next_button.setText("다음 ▶")

    def copy_current_chunk(self):
        data_to_copy = self.copy_chunks[self.current_step]["data"]
        QApplication.clipboard().setText(data_to_copy)
        QMessageBox.information(self, "복사 완료", "데이터가 클립보드에 복사되었습니다.\n안내에 따라 엑셀에 붙여넣어 주세요.")

    def go_to_next_step(self):
        if self.current_step < len(self.copy_chunks) - 1:
            self.current_step += 1; self.update_step_ui()
        else: self.accept()