# ui_pyside/company_select_popup.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox)
from PySide6.QtGui import QMovie
from PySide6.QtCore import QThread, Signal, Qt
import search_logic
import os
import traceback


class PopupSearchWorker(QThread):
    finished = Signal(list)

    def __init__(self, file_path, name, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.name = name

    def run(self):
        filters = {'name': self.name, 'region': '전체', 'min_sipyung': None, 'max_sipyung': None, 'min_perf_3y': None,
                   'max_perf_3y': None, 'min_perf_5y': None, 'max_perf_5y': None}
        results = search_logic.find_and_filter_companies(self.file_path, filters)
        self.finished.emit(results)


class CompanySelectPopupPyside(QDialog):
    company_selected = Signal(dict)

    def __init__(self, parent, controller, field_to_search, callback, existing_companies):
        super().__init__(parent)
        self.controller = controller
        self.field_to_search = field_to_search
        self.company_selected.connect(callback)
        self.existing_companies = existing_companies

        self.worker = None
        self.results_data = []

        self.setWindowTitle(f"업체 선택 ({self.field_to_search} 분야)")
        self.setMinimumSize(600, 500)

        self.create_ui()

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
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["업체명", "대표자", "사업자번호", "지역", "구분"])

        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
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
        if self.worker is not None and self.worker.isRunning():
            return

        name = self.search_entry.text().strip()
        source = self.field_to_search
        filepath = self.controller.source_files.get(source)

        if not name:
            QMessageBox.warning(self, "입력 오류", "업체명을 입력하세요.")
            return
        if not filepath or not os.path.exists(filepath):
            QMessageBox.critical(self, "파일 오류", f"'{source}' 데이터의 엑셀 파일 경로를 확인하세요.")
            return

        self.set_ui_for_search(True)

        self.worker = PopupSearchWorker(filepath, name, self)
        self.worker.finished.connect(self.show_results)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def show_results(self, results):
        try:
            if not self.isVisible():  # 창이 이미 닫혔다면 아무것도 하지 않음
                return

            if not results or "오류" in results[0]:
                error_msg = results[0].get("오류", "알 수 없는 오류") if results else "결과 없음"
                QMessageBox.information(self, "검색 결과", error_msg)
            else:
                self.results_data = results
                self.results_table.setRowCount(len(results))
                for row, data in enumerate(results):
                    self.results_table.setItem(row, 0, QTableWidgetItem(data.get("검색된 회사")))
                    self.results_table.setItem(row, 1, QTableWidgetItem(data.get("대표자")))
                    self.results_table.setItem(row, 2, QTableWidgetItem(data.get("사업자번호")))
                    self.results_table.setItem(row, 3, QTableWidgetItem(data.get("지역")))
                    self.results_table.setItem(row, 4, QTableWidgetItem(self.field_to_search))
        except Exception as e:
            print(f"!!! CRITICAL ERROR in show_results: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "치명적 오류", f"결과를 표시하는 중 오류가 발생했습니다:\n{e}")
        finally:
            self.set_ui_for_search(False)
            self.worker = None

    def set_ui_for_search(self, is_searching):
        """검색 중/완료 상태에 따라 UI를 설정합니다."""
        self.search_entry.setEnabled(not is_searching)
        self.search_button.setEnabled(not is_searching)
        self.loading_label.setVisible(is_searching)
        if is_searching:
            self.results_table.setRowCount(0)
            self.loading_movie.start()
        else:
            self.loading_movie.stop()

    def on_select(self, model_index):
        if self.worker is not None and self.worker.isRunning():
            return

        row = model_index.row()

        if not self.results_data or row >= len(self.results_data):
            return

        selected_data = self.results_data[row]
        company_name = selected_data.get("검색된 회사")

        if company_name in self.existing_companies:
            QMessageBox.warning(self, "중복 선택", f"'{company_name}' 업체는 이미 협정에 추가되어 있습니다.")
            return

        self.company_selected.emit(selected_data)
        self.accept()

    def closeEvent(self, event):
        """창 닫기 이벤트를 가로채서 워커가 실행 중일 때는 닫히지 않도록 합니다."""
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "알림", "검색이 진행 중입니다. 잠시만 기다려주세요.")
            event.ignore()  # 창 닫기 이벤트를 무시
        else:
            event.accept()  # 워커가 없으면 창을 닫음
