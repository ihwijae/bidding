# ui_pyside/account_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QHeaderView, 
                               QPushButton, QMessageBox, QInputDialog, QLineEdit, QApplication, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from credentials_manager import credentials_manager
from .account_edit_popup import AccountEditPopup

class AccountViewPyside(QWidget):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.is_unlocked = False

        self.setup_ui()
        # __init__에서는 아무것도 자동으로 실행하지 않습니다.

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.table = QTableWidget()
        main_layout.addWidget(self.table)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def check_and_unlock(self):
        if self.is_unlocked:
            return

        password, ok = QInputDialog.getText(self, "마스터 비밀번호", "마스터 비밀번호를 입력하세요:", QLineEdit.Password)

        if ok and password:
            if credentials_manager.load_and_decrypt(password):
                self.is_unlocked = True
                self.populate_table()
            else:
                QMessageBox.critical(self, "오류", "비밀번호가 틀렸거나 데이터 파일이 손상되었습니다.")
                self.is_unlocked = False
                self.table.clear()
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
        else:
            self.is_unlocked = False

    def populate_table(self):
        if not self.is_unlocked:
            QMessageBox.warning(self, "잠김", "데이터가 잠겨있어 정보를 표시할 수 없습니다.")
            return

        data = credentials_manager.get_data()
        if not data: return
            
        sites = data.get("sites", [])
        corps = data.get("corporations", {})
        # [핵심] credentials_manager에서 생성된 법인 목록을 그대로 사용합니다.
        corp_names = list(corps.keys())
        
        self.table.clear()
        self.table.setRowCount(len(corp_names))
        self.table.setColumnCount(len(sites))
        
        self.table.setVerticalHeaderLabels(corp_names)
        self.table.setHorizontalHeaderLabels(sites)
        
        # [핵심 수정] 구분선 행을 처리하는 로직 추가
        for row, corp_name in enumerate(corp_names):
            if corp_name == "--- 구분선 ---":
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                line.setStyleSheet("background-color: #BDC3C7; border: 0px;") # 구분선 스타일
                
                self.table.setCellWidget(row, 0, line)
                self.table.setSpan(row, 0, 1, len(sites))
                # 구분선 행의 세로 헤더 텍스트를 비웁니다.
                self.table.verticalHeaderItem(row).setText("")
            else:
                # 일반 법인 행일 경우 기존 로직 수행
                for col, site_name in enumerate(sites):
                    cell_data = corps.get(corp_name, {}).get(site_name, {})
                    cell_widget = self.create_cell_widget(row, col, cell_data)
                    self.table.setCellWidget(row, col, cell_widget)
        
        self.table.resizeRowsToContents()

    def create_cell_widget(self, row, col, cell_data):
        widget = QWidget()
        layout = QVBoxLayout(widget); layout.setContentsMargins(5, 5, 5, 5); layout.setSpacing(5)

        id_val = cell_data.get("id", "")
        pw_val = cell_data.get("pw", "")
        site_name = self.table.horizontalHeaderItem(col).text()

        edit_button = QPushButton("수정")
        edit_button.clicked.connect(lambda _, r=row, c=col: self.open_edit_popup(r, c))

        if site_name == "공인인증서":
            if pw_val:
                pw_layout = QHBoxLayout(); pw_layout.addWidget(QLabel("암호:")); pw_layout.addStretch()
                copy_pw_btn = QPushButton("복사"); copy_pw_btn.clicked.connect(lambda _, text=pw_val: self.copy_to_clipboard(text))
                pw_layout.addWidget(copy_pw_btn); layout.addLayout(pw_layout)
        else:
            cert_pw_val = cell_data.get("cert_pw", "")
            if id_val:
                id_layout = QHBoxLayout(); id_layout.addWidget(QLabel("ID:")); id_layout.addStretch()
                copy_id_btn = QPushButton("복사"); copy_id_btn.clicked.connect(lambda _, text=id_val: self.copy_to_clipboard(text))
                id_layout.addWidget(copy_id_btn); layout.addLayout(id_layout)
            if pw_val:
                pw_layout = QHBoxLayout(); pw_layout.addWidget(QLabel("PW:")); pw_layout.addStretch()
                copy_pw_btn = QPushButton("복사"); copy_pw_btn.clicked.connect(lambda _, text=pw_val: self.copy_to_clipboard(text))
                pw_layout.addWidget(copy_pw_btn); layout.addLayout(pw_layout)
            if cert_pw_val:
                cert_layout = QHBoxLayout(); cert_layout.addWidget(QLabel("인증서:")); cert_layout.addStretch()
                copy_cert_btn = QPushButton("복사"); copy_cert_btn.clicked.connect(lambda _, text=cert_pw_val: self.copy_to_clipboard(text))
                cert_layout.addWidget(copy_cert_btn); layout.addLayout(cert_layout)

        layout.addWidget(edit_button)
        return widget

    def copy_to_clipboard(self, text):
        if not text:
            QMessageBox.warning(self, "복사 실패", "복사할 내용이 없습니다."); return
        QApplication.clipboard().setText(text)
        self.controller.statusBar().showMessage("클립보드에 복사되었습니다.", 2000)

    def open_edit_popup(self, row, column):
        corp_name = self.table.verticalHeaderItem(row).text()
        # [핵심] 구분선 행은 수정 팝업을 띄우지 않음
        if corp_name == "": # 구분선 행의 헤더는 비어있음
            return
            
        if not self.is_unlocked:
            QMessageBox.warning(self, "잠김", "먼저 마스터 비밀번호로 잠금을 해제하세요.")
            self.check_and_unlock(); return

        data = credentials_manager.get_data()
        site_name = self.table.horizontalHeaderItem(column).text()
        current_data = data.get("corporations", {}).get(corp_name, {}).get(site_name, {})
        popup = AccountEditPopup(corp_name, site_name, current_data, self)
        
        if popup.exec():
            new_data = popup.get_new_data()
            if credentials_manager.update_credential(corp_name, site_name, new_data):
                if credentials_manager.encrypt_and_save():
                    self.populate_table()
                else: QMessageBox.critical(self, "오류", "파일 저장 중 오류가 발생했습니다.")
            else: QMessageBox.warning(self, "업데이트 실패", "정보 업데이트에 실패했습니다.")