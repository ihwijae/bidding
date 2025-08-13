# [api_popup.py 파일 전체를 이 코드로 교체하세요]
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit, QWidget, QComboBox)
from PySide6.QtCore import QDate, Qt, Signal, QThread
import requests
import json
import config
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl

class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        context = ssl.create_default_context(); context.set_ciphers('DEFAULT@SECLEVEL=1'); context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_context=context)

class ApiSearchWorker(QThread):
    finished = Signal(object)
    def __init__(self, params, endpoint):
        super().__init__(); self.params = params; self.endpoint = endpoint
    def run(self):
        try:
            session = requests.Session(); session.mount('https://', TLSAdapter())
            response = session.get(self.endpoint, params=self.params, timeout=15)
            response.raise_for_status()
            self.finished.emit(response.text)
        except requests.exceptions.RequestException as e:
            self.finished.emit(f"API 요청 오류: {e}")

class ApiPopup(QDialog):
    gongo_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("나라장터 공고 검색"); self.setMinimumSize(900, 700); self.search_results = []
        BASE_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
        self.endpoints = {
            "공사": f"{BASE_URL}/getBidPblancListInfoCnstwk",
            "용역": f"{BASE_URL}/getBidPblancListInfoServc",
            "물품": f"{BASE_URL}/getBidPblancListInfoThng"
        }
        self.setup_ui(); self.connect_signals()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        search_box = QWidget(); search_box.setObjectName("filterBox"); search_layout = QGridLayout(search_box)
        self.start_date_edit = QDateEdit(QDate.currentDate().addDays(-365)); self.start_date_edit.setCalendarPopup(True); self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit = QDateEdit(QDate.currentDate()); self.end_date_edit.setCalendarPopup(True); self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.keyword_entry = QLineEdit(); self.keyword_entry.setPlaceholderText("공고번호를 입력하세요")
        self.search_button = QPushButton("🔍 공고번호 검색")
        self.biz_field_combo = QComboBox(); self.biz_field_combo.addItems(self.endpoints.keys())
        search_layout.addWidget(QLabel("<b>공고일자:</b>"), 0, 0); search_layout.addWidget(self.start_date_edit, 0, 1); search_layout.addWidget(QLabel("~"), 0, 2, Qt.AlignCenter); search_layout.addWidget(self.end_date_edit, 0, 3)
        search_layout.addWidget(QLabel("<b>업종:</b>"), 1, 0); search_layout.addWidget(self.biz_field_combo, 1, 1)
        search_layout.addWidget(QLabel("<b>공고번호:</b>"), 1, 2); search_layout.addWidget(self.keyword_entry, 1, 3)
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5); self.result_table.setHorizontalHeaderLabels(["공고번호-차수", "공고명", "발주기관", "추정가격", "입찰마감일시"])
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        button_layout = QHBoxLayout(); button_layout.addStretch(1); button_layout.addWidget(self.search_button)
        self.select_button = QPushButton("✅ 선택 완료"); self.close_button = QPushButton("닫기")
        button_layout.addWidget(self.select_button); button_layout.addWidget(self.close_button)
        main_layout.addWidget(search_box); main_layout.addWidget(self.result_table, 1); main_layout.addLayout(button_layout)

    def connect_signals(self):
        self.search_button.clicked.connect(self.start_list_search)
        self.select_button.clicked.connect(self.on_select)
        self.result_table.doubleClicked.connect(self.on_select)
        self.close_button.clicked.connect(self.reject)
        # [핵심] 텍스트 입력창의 내용이 바뀔 때마다 on_keyword_changed 함수를 호출
        self.keyword_entry.textChanged.connect(self.on_keyword_changed)

    # [핵심] 입력창의 텍스트를 실시간으로 감지하고 정리하는 함수
    def on_keyword_changed(self, text):
        # 입력된 텍스트에 '-'가 포함되어 있다면
        if '-' in text:
            # '-' 앞부분만 잘라냄
            cleaned_text = text.split('-')[0]
            # 무한 루프를 방지하기 위해, 변경된 내용이 있을 때만 setText를 호출
            if text != cleaned_text:
                # setText가 또다시 textChanged 시그널을 발생시키지 않도록 잠시 신호 연결을 끊음
                self.keyword_entry.blockSignals(True)
                self.keyword_entry.setText(cleaned_text)
                # 커서를 맨 뒤로 이동시켜서 사용자 입력을 편하게 함
                self.keyword_entry.setCursorPosition(len(cleaned_text))
                # 신호 연결을 다시 복구
                self.keyword_entry.blockSignals(False)

    def start_list_search(self):
        conf = config.load_config()
        service_key = conf.get("api_service_key", "").strip()
        if not service_key:
            QMessageBox.critical(self, "인증키 오류", "config.json 또는 config.ini 파일에 'api_service_key'가 올바르게 설정되지 않았습니다."); return

        self.search_button.setEnabled(False); self.search_button.setText("검색 중...")
        # 이제 입력창의 텍스트는 항상 정리된 상태이므로, 바로 사용 가능
        keyword = self.keyword_entry.text().strip()
        if not keyword:
            QMessageBox.warning(self, "입력 오류", "공고번호를 입력해주세요."); 
            self.search_button.setEnabled(True); self.search_button.setText("🔍 공고번호 검색")
            return

        params = {
            'serviceKey': service_key,
            'pageNo': '1',
            'numOfRows': '100',
            'type': 'json',
            'inqryDiv': '2',
            'bidNtceNo': keyword # 이미 정리된 텍스트를 사용
        }
        
        selected_biz_field = self.biz_field_combo.currentText()
        endpoint = self.endpoints[selected_biz_field]
        self.worker = ApiSearchWorker(params, endpoint)
        self.worker.finished.connect(self.on_list_search_finished)
        self.worker.start()

    def on_list_search_finished(self, result_text):
        self.search_button.setEnabled(True); self.search_button.setText("🔍 공고번호 검색")
        if not result_text or not result_text.strip().startswith('{'):
            QMessageBox.critical(self, "API 응답 오류", f"서버로부터 유효한 JSON 응답을 받지 못했습니다.\n응답 내용: {result_text}"); return
        try:
            data = json.loads(result_text)
            response = data.get('response', {})
            header = response.get('header', {})
            result_code = header.get('resultCode')
            result_msg = header.get('resultMsg', '알 수 없는 오류')
            if str(result_code) != '00':
                QMessageBox.critical(self, "API 응답 오류", f"API 서버에서 오류가 발생했습니다: {result_msg}"); return
            
            body = response.get('body', {})
            items = body.get('items', [])
            if isinstance(items, dict): items = [items]
            
            if not items:
                self.result_table.setRowCount(0); QMessageBox.information(self, "검색 결과", "해당 조건의 공고를 찾을 수 없습니다."); return
            
            self.search_results.clear(); self.result_table.setRowCount(len(items))
            for row, item_data in enumerate(items):
                self.search_results.append(item_data)
                gongo_full_no = f"{item_data.get('bidNtceNo', '')}-{item_data.get('bidNtceOrd', '')}"
                price_str = str(item_data.get('presmptPrce', '0'))
                price = int(float(price_str)) if price_str and price_str.replace('.', '', 1).isdigit() else 0
                self.result_table.setItem(row, 0, QTableWidgetItem(gongo_full_no))
                self.result_table.setItem(row, 1, QTableWidgetItem(item_data.get('bidNtceNm', ''))) 
                self.result_table.setItem(row, 2, QTableWidgetItem(item_data.get('ntceInsttNm', '')))
                self.result_table.setItem(row, 3, QTableWidgetItem(f"{price:,}"))
                self.result_table.setItem(row, 4, QTableWidgetItem(item_data.get('bidClseDt', '')))

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON 파싱 오류", f"서버 응답을 처리할 수 없습니다. 응답 원본:\n{result_text}")
        except Exception as e:
            QMessageBox.critical(self, "처리 오류", f"알 수 없는 오류 발생: {type(e).__name__} - {e}")

    def on_select(self):
        current_row = self.result_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "먼저 목록에서 공고를 선택하세요."); return
        selected_gongo_data = self.search_results[current_row]
        self.gongo_selected.emit(selected_gongo_data)
        self.accept()