# ui_pyside/account_edit_popup.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QPushButton, QHBoxLayout, QMessageBox, QLabel)
from PySide6.QtCore import Qt

class AccountEditPopup(QDialog):
    def __init__(self, corp_name, site_name, current_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"'{corp_name} - {site_name}' 정보 수정")
        
        self.new_data = None # 사용자가 저장하면 여기에 데이터가 담김
        
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.id_edit = QLineEdit()
        self.pw_edit = QLineEdit()
        self.cert_pw_edit = QLineEdit()

        # "공인인증서"의 경우 ID 입력란을 비활성화하고 숨깁니다.
        if site_name == "공인인증서":
            form_layout.addRow("암호:", self.pw_edit)
            # pw_edit이 인증서 암호를 의미하도록 라벨 변경 (cert_pw_edit은 사용 안함)
            self.pw_edit.setText(current_data.get("pw", ""))
        else:
            # 일반 사이트의 경우
            form_layout.addRow("ID:", self.id_edit)
            form_layout.addRow("Password:", self.pw_edit)
            form_layout.addRow("인증서 암호:", self.cert_pw_edit)
            
            self.id_edit.setText(current_data.get("id", ""))
            self.pw_edit.setText(current_data.get("pw", ""))
            self.cert_pw_edit.setText(current_data.get("cert_pw", ""))
        
        main_layout.addLayout(form_layout)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_button = QPushButton("저장")
        self.cancel_button = QPushButton("취소")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        self.save_button.clicked.connect(self.accept_and_save)
        self.cancel_button.clicked.connect(self.reject)

    def accept_and_save(self):
        """저장 버튼 클릭 시, 입력된 데이터를 new_data에 저장하고 닫습니다."""
        site_name = self.windowTitle().split(' - ')[1].replace("'", "")
        
        if site_name == "공인인증서":
            self.new_data = {"pw": self.pw_edit.text()}
        else:
            self.new_data = {
                "id": self.id_edit.text(),
                "pw": self.pw_edit.text(),
                "cert_pw": self.cert_pw_edit.text()
            }
        self.accept() # QDialog의 accept()를 호출하여 정상 종료 알림

    def get_new_data(self):
        """팝업이 성공적으로 닫혔을 때, 새 데이터를 반환합니다."""
        return self.new_data