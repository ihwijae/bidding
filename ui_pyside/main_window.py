# ui_pyside/main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from .search_view import SearchViewPyside
from .consortium_view_haeng import ConsortiumViewHaeng
from .consortium_view_jodal import ConsortiumViewJodal
import config
from .message_generator_view import MessageGeneratorViewPyside
from .account_view import AccountViewPyside # <-- import 문 확인
import os
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MainWindow(QMainWindow):
    def __init__(self, source_files_config):
        super().__init__()
        self.source_files = source_files_config
        
        self.setWindowTitle("협력업체 정보 조회 프로그램 (v7.2 - Consortium)")
        self.setGeometry(100, 100, 1500, 950)

        app_icon = QIcon(resource_path("logo.ico"))
        self.setWindowIcon(app_icon)



        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)

        nav_bar = self.create_navigation_bar()
        main_layout.addWidget(nav_bar)

        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(content_container, 1)

        # 뷰(화면)들을 생성하고 스택 위젯에 추가
        self.search_view = SearchViewPyside(self)

        self.consortium_view_haeng = ConsortiumViewHaeng(self)
        self.consortium_view_jodal = ConsortiumViewJodal(self)
        self.message_generator_view = MessageGeneratorViewPyside(self)
        self.account_view = AccountViewPyside(self) # [핵심] 계정 관리 뷰 생성
        
        self.stacked_widget.addWidget(self.search_view)
        self.stacked_widget.addWidget(self.consortium_view_haeng)
        self.stacked_widget.addWidget(self.consortium_view_jodal)
        self.stacked_widget.addWidget(self.message_generator_view)
        self.stacked_widget.addWidget(self.account_view) # [핵심] 스택 위젯에 계정 관리 뷰 추가
       
        
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        self.nav_list.setCurrentRow(0)

        self.apply_stylesheet()
    
# [on_nav_changed 함수를 이 코드로 통째로 교체하세요]
    def on_nav_changed(self, index):
        """[최종 진단 모드] 네비게이션 리스트의 선택이 변경될 때 호출됩니다."""
        
        # 1. 화면을 먼저 전환합니다.
        self.stacked_widget.setCurrentIndex(index)
        
        # 2. 방금 화면에 표시된 위젯의 상태를 상세히 진단합니다.
        current_widget = self.stacked_widget.widget(index)

        print(f"\n==================== 최종 진단 시작 (인덱스: {index}) ====================")
        if current_widget:
            widget_name = current_widget.__class__.__name__
            print(f"  [1] 현재 위젯: {widget_name}")
            print(f"  [2] 위젯의 부모: {current_widget.parent().__class__.__name__}")
            print(f"  [3] 위젯의 현재 크기 (가로x세로): {current_widget.size().width()} x {current_widget.size().height()}")
            print(f"  [4] 위젯이 화면에 보이는지 (isVisible): {current_widget.isVisible()}")

            # AccountViewPyside일 경우, 그 안의 테이블까지 상세 진단
            if isinstance(current_widget, AccountViewPyside):
                print("  ------ AccountView 상세 진단 ------")
                if hasattr(current_widget, 'table'):
                    print(f"  [5] 내부 테이블(self.table)의 크기: {current_widget.table.size().width()} x {current_widget.table.size().height()}")
                    print(f"  [6] 내부 테이블이 화면에 보이는지 (isVisible): {current_widget.table.isVisible()}")
                else:
                    print("  [5] 오류: 내부에 self.table 위젯이 존재하지 않습니다.")
            
        else:
            print(f"  [1] 오류: 인덱스 {index}에 해당하는 위젯을 찾을 수 없습니다.")
        
        print("========================= 최종 진단 끝 =========================\n")

        # 3. 원래의 잠금 해제 로직을 실행합니다.
        if isinstance(current_widget, AccountViewPyside) and not current_widget.is_unlocked:
            current_widget.check_and_unlock()
    
    def create_navigation_bar(self):
        nav_widget = QWidget(); nav_widget.setObjectName("navBar"); nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop); nav_layout.setContentsMargins(0, 10, 0, 10)
        title_label = QLabel("업무 자동화"); title_label.setFont(QFont("맑은 고딕", 20, QFont.Bold)); title_label.setAlignment(Qt.AlignmentFlag.AlignCenter); title_label.setContentsMargins(0, 10, 0, 20)
        
        self.nav_list = QListWidget(); self.nav_list.setFixedWidth(220)
        QListWidgetItem("📁 업체 조회", self.nav_list)
        QListWidgetItem("🤝 협정 (행안부)", self.nav_list)
        QListWidgetItem("🤝 협정 (조달청)", self.nav_list)
        QListWidgetItem("💬 협정 문자 생성", self.nav_list)
        QListWidgetItem("🔐 계정 관리", self.nav_list) # [핵심] 왼쪽 메뉴에 이름 추가
     

        nav_layout.addWidget(title_label)
        nav_layout.addWidget(self.nav_list)
        return nav_widget
    
    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #F0F0F0; }
            QWidget#navBar { background-color: #EAECEE; border-right: 1px solid #D5D8DC; }
            QListWidget { border: none; font-size: 15px; font-weight: bold; outline: 0; }
            QListWidget::item { padding: 12px; border-radius: 5px; margin: 2px 5px; }
            QListWidget::item:hover { background-color: #DAEAF7; }
            QListWidget::item:selected { background-color: #3498DB; color: white; }
            QWidget#filterBox { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E5E7E9; }
            QLabel { font-size: 13px; }
            QPushButton { font-size: 13px; padding: 8px; background-color: #3498DB; color: white; border: none; border-radius: 4px; }
            QPushButton:hover { background-color: #5DADE2; }
            QLineEdit, QComboBox { padding: 5px; border: 1px solid #BDC3C7; border-radius: 4px; font-size: 13px; }
            QTableWidget { border: 1px solid #BDC3C7; }
            QHeaderView::section { background-color: #F2F3F4; padding: 4px; border: 1px solid #BDC3C7; font-weight: bold; }
        """)
        
    def closeEvent(self, event):
        config.save_config(self.source_files)
        event.accept()