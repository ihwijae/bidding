# ui_pyside/company_select_popup.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox)
from PySide6.QtGui import QMovie
from PySide6.QtCore import QThread, Signal
import search_logic
import os

class PopupSearchWorker(QThread):
    finished = Signal(list)
    def __init__(self, file_path, name):
        super().__init__()
        self.file_path = file_path
        self.name = name
    def run(self):
        filters = {'name': self.name, 'region': '전체', 'min_sipyung': None, 'max_sipyung': None, 'min_perf_3y': None, 'max_perf_3y': None, 'min_perf_5y': None, 'max_perf_5y': None}
        results = search_logic.find_and_filter_companies(self.file_path, filters)
        self.finished.emit(results)

class CompanySelectPopupPyside(QDialog):
    company_selected = Signal(dict)

    # [핵심] 생성자에 existing_companies 추가
    def __init__(self, parent, controller, field_to_search, callback, existing_companies):
        super().__init__(parent)
        self.controller = controller
        self.field_to_search = field_to_search
        self.company_selected.connect(callback)
        self.existing_companies = existing_companies
        
        self.worker = None
        self.results_data = [] # 검색 결과를 저장할 리스트
        
        self.setWindowTitle(f"업체 선택 ({self.field_to_search} 분야)")
        self.setMinimumSize(600, 500)
        
        self.create_ui() # UI 생성 함수 호출

    # [create_ui 함수를 이 코드로 통째로 교체하세요]
    def create_ui(self):
        main_layout = QVBoxLayout(self)
        
        filter_layout = QHBoxLayout()
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText(f"{self.field_to_search} 업체명 검색...")
        self.search_button = QPushButton("검색")
        self.loading_label = QLabel(self)
        self.loading_movie = QMovie("loading.gif") 
        self.loading_label.setMovie(self.loading_movie)
        self.loading_label.setVisible(False)
        
        filter_layout.addWidget(self.search_entry)
        filter_layout.addWidget(self.search_button)
        filter_layout.addWidget(self.loading_label)
        main_layout.addLayout(filter_layout)

        self.results_table = QTableWidget()
        # [핵심 수정] 열 개수를 5개로 늘리고, 헤더 라벨을 수정
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["업체명", "대표자", "사업자번호", "지역", "구분"])
        
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # 업체명은 꽉 차게
        # 나머지 열들은 내용에 맞게 크기 조절
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.search_entry.returnPressed.connect(self.start_search)
        self.search_button.clicked.connect(self.start_search)
        self.results_table.doubleClicked.connect(self.on_select)
        
        main_layout.addWidget(self.results_table)

    def start_search(self):
        if self.worker and self.worker.isRunning(): return

        name = self.search_entry.text().strip()
        source = self.field_to_search
        filepath = self.controller.source_files.get(source)

        if not name:
            QMessageBox.warning(self, "입력 오류", "업체명을 입력하세요.")
            return
        if not filepath or not os.path.exists(filepath):
            QMessageBox.critical(self, "파일 오류", f"'{source}' 데이터의 엑셀 파일 경로를 확인하세요.")
            return
        
        self.results_table.setRowCount(0)
        self.search_entry.setEnabled(False)
        self.search_button.setEnabled(False)
        self.loading_label.setVisible(True)
        self.loading_movie.start()
        
        self.worker = PopupSearchWorker(filepath, name)
        self.worker.finished.connect(self.show_results)
        self.worker.start()

    # [show_results 함수를 이 코드로 통째로 교체하세요]
    def show_results(self, results):
        self.loading_movie.stop()
        self.loading_label.setVisible(False)
        self.search_entry.setEnabled(True)
        self.search_button.setEnabled(True)

        if not results or "오류" in results[0]:
            error_msg = results[0].get("오류", "알 수 없는 오류") if results else "결과 없음"
            QMessageBox.information(self, "검색 결과", error_msg)
            return
        
        self.results_data = results
        self.results_table.setRowCount(len(results))
        for row, data in enumerate(results):
            # [핵심 수정] 각 열에 맞는 데이터를 가져와서 채워넣음
            self.results_table.setItem(row, 0, QTableWidgetItem(data.get("검색된 회사")))
            self.results_table.setItem(row, 1, QTableWidgetItem(data.get("대표자")))
            self.results_table.setItem(row, 2, QTableWidgetItem(data.get("사업자번호")))
            self.results_table.setItem(row, 3, QTableWidgetItem(data.get("지역")))
            self.results_table.setItem(row, 4, QTableWidgetItem(self.field_to_search)) # '구분'은 검색한 분야 이름

    def on_select(self, model_index):
        if self.worker and self.worker.isRunning(): return
            
        row = model_index.row()
        
        # [핵심] self.results_data가 비어있지 않고, row가 유효한 범위 내에 있는지 확인
        if not self.results_data or row >= len(self.results_data):
            return

        selected_data = self.results_data[row]
        
        # 중복 검사
        company_name = selected_data.get("검색된 회사")

                # --- 디버깅용 print문 (문제가 해결되면 지워도 됩니다) ---
        print(f"선택한 업체: {company_name}")
        print(f"중복 검사 대상 목록: {self.existing_companies}")


        if company_name in self.existing_companies:
            QMessageBox.warning(self, "중복 선택", f"'{company_name}' 업체는 이미 협정에 추가되어 있습니다.")
            return

        # 중복이 아닐 경우, 원래대로 동작
        self.company_selected.emit(selected_data)
        self.accept()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()