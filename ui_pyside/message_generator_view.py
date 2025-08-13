# [message_generator_view.py 파일 전체를 이 코드로 교체하세요]
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QHBoxLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton,
                               QTextEdit, QMessageBox, QApplication, QTableWidget,
                               QTableWidgetItem, QHeaderView, QDateTimeEdit)
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QFont
import utils

from ui_pyside.api_popup import ApiPopup

class MessageGeneratorViewPyside(QWidget):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        ann_box = QWidget(); ann_box.setObjectName("filterBox")
        ann_layout = QVBoxLayout(ann_box)
        ann_title_layout = QHBoxLayout()
        ann_title_layout.addWidget(QLabel("<b>1. 공고 정보 입력 (여러 건 추가 가능)</b>"))
        ann_title_layout.addStretch(1)

        self.api_search_button = QPushButton("🔍 API 공고 검색")
        self.add_row_button = QPushButton("➕ 행 추가")
        self.remove_row_button = QPushButton("➖ 선택 행 삭제")
        ann_title_layout.addWidget(self.api_search_button)
        ann_title_layout.addWidget(self.add_row_button); ann_title_layout.addWidget(self.remove_row_button)
        
        self.announcement_table = QTableWidget()
        self.announcement_table.setColumnCount(4)
        self.announcement_table.setHorizontalHeaderLabels(["공고명", "공고번호", "추정가격(원)", "투찰마감일"])
        self.announcement_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.announcement_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.announcement_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.announcement_table.setColumnWidth(3, 200)
        self.add_announcement_row() # 프로그램 시작 시 기본 한 줄 추가

        ann_layout.addLayout(ann_title_layout); ann_layout.addWidget(self.announcement_table)

        common_box = QWidget(); common_box.setObjectName("filterBox")
        common_layout = QGridLayout(common_box)
        common_layout.addWidget(QLabel("<b>2. 공통 및 업체 정보</b>"), 0, 0, 1, 4)
        
        region_list = ["전체", "서울", "경기", "인천", "강원", "충북", "충남", "대전", "세종", "전북", "전남", "광주", "경북", "경남", "대구", "울산", "부산", "제주"]
        self.region_combo1 = QComboBox(); self.region_combo1.addItems(region_list)
        self.region_combo2 = QComboBox(); self.region_combo2.addItems([""] + region_list)
        self.region_combo2.setMinimumContentsLength(5)
        region_layout = QHBoxLayout(); region_layout.setContentsMargins(0,0,0,0)
        region_layout.addWidget(self.region_combo1); region_layout.addWidget(QLabel("/")); region_layout.addWidget(self.region_combo2)
        region_layout.addStretch(1)
        self.gongo_field_combo = QComboBox(); self.gongo_field_combo.addItems(["전기", "통신", "소방", "기타"])
        self.company_name_entry = QLineEdit(); self.company_name_entry.setPlaceholderText("협정 제안할 업체명")
        self.manager_name_entry = QLineEdit()
        
        common_layout.addWidget(QLabel("ㆍ지역제한:"), 1, 0); common_layout.addLayout(region_layout, 1, 1)
        common_layout.addWidget(QLabel("ㆍ종목:"), 2, 0);     common_layout.addWidget(self.gongo_field_combo, 2, 1)
        common_layout.addWidget(QLabel("ㆍ업체명:"), 3, 0);     common_layout.addWidget(self.company_name_entry, 3, 1)
        common_layout.addWidget(QLabel("ㆍ담당자명:"), 4, 0);   common_layout.addWidget(self.manager_name_entry, 4, 1)
        
        result_box = QWidget(); result_box.setObjectName("filterBox"); result_layout = QVBoxLayout(result_box)
        result_label = QLabel("<b>생성된 문자 내용</b>"); result_label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        self.result_text = QTextEdit(); self.result_text.setReadOnly(True); self.result_text.setFont(QFont("맑은 고딕", 11))
        result_layout.addWidget(result_label); result_layout.addWidget(self.result_text)

        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("🚀 문자 생성"); self.copy_button = QPushButton("📋 클립보드로 복사"); self.clear_button = QPushButton("🗑️ 내용 지우기")
        button_layout.addStretch(1); button_layout.addWidget(self.generate_button); button_layout.addWidget(self.copy_button); button_layout.addWidget(self.clear_button)
        
        main_layout.addWidget(ann_box); main_layout.addWidget(common_box); main_layout.addWidget(result_box, 1); main_layout.addLayout(button_layout)

    def connect_signals(self):
        self.api_search_button.clicked.connect(self.open_api_popup)
        self.add_row_button.clicked.connect(self.add_announcement_row)
        self.remove_row_button.clicked.connect(self.remove_announcement_row)
        self.generate_button.clicked.connect(self.generate_message)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.clear_button.clicked.connect(self.clear_fields)
        self.announcement_table.cellChanged.connect(self.format_price_in_cell)

    def open_api_popup(self):
        popup = ApiPopup(self)
        popup.gongo_selected.connect(self.fill_from_api)
        popup.exec()

    def fill_from_api(self, gongo_data):
        # [핵심] '빈 행' 판단 로직 수정
        target_row = -1
        # 테이블의 모든 행을 거꾸로 순회 (맨 아래부터)
        for row in range(self.announcement_table.rowCount() - 1, -1, -1):
            title_item = self.announcement_table.item(row, 0)
            # '공고명' 칸이 비어있거나, 텍스트가 없으면 이 행을 타겟으로 설정
            if title_item is None or title_item.text().strip() == "":
                target_row = row
                break # 타겟을 찾았으니 반복 중단
        
        # 만약 모든 행이 다 차있어서 빈 행을 못 찾았다면, 새로운 행을 추가
        if target_row == -1:
            self.add_announcement_row()
            target_row = self.announcement_table.rowCount() - 1
            
        # --- 이하 로직은 동일 ---
        title = gongo_data.get('bidNtceNm', '')
        gongo_no = f"{gongo_data.get('bidNtceNo', '')}-{gongo_data.get('bidNtceOrd', '')}"
        price_str = str(gongo_data.get('presmptPrce', '0'))
        deadline_str = gongo_data.get('bidClseDt', '')
        cnstty_name = gongo_data.get('mainCnsttyNm', '')
        region_name_full = gongo_data.get('jntcontrctDutyRgnNm1', '')

        self.announcement_table.setItem(target_row, 0, QTableWidgetItem(title))
        self.announcement_table.setItem(target_row, 1, QTableWidgetItem(gongo_no))
        price = utils.parse_amount(price_str)
        if price is not None:
            self.announcement_table.setItem(target_row, 2, QTableWidgetItem(f"{price:,}"))
        
        datetime_widget = self.announcement_table.cellWidget(target_row, 3)
        if datetime_widget and deadline_str:
            deadline_dt = QDateTime.fromString(deadline_str.split('.')[0], "yyyy-MM-dd HH:mm:ss")
            if deadline_dt.isValid():
                datetime_widget.setDateTime(deadline_dt)
        
        if "전기" in cnstty_name: self.gongo_field_combo.setCurrentText("전기")
        elif "정보통신" in cnstty_name: self.gongo_field_combo.setCurrentText("통신")
        elif "소방" in cnstty_name: self.gongo_field_combo.setCurrentText("소방")
        else: self.gongo_field_combo.setCurrentText("기타")
        
        region_map = { "서울특별시": "서울", "경기도": "경기", "인천광역시": "인천", "강원특별자치도": "강원", "충청북도": "충북", "충청남도": "충남", "대전광역시": "대전", "세종특별자치시": "세종", "전북특별자치도": "전북", "전라남도": "전남", "광주광역시": "광주", "경상북도": "경북", "경상남도": "경남", "대구광역시": "대구", "울산광역시": "울산", "부산광역시": "부산", "제주특별자치도": "제주" }
        short_region_name = region_map.get(region_name_full, "전체")
        self.region_combo1.setCurrentText(short_region_name)
        
        QMessageBox.information(self, "정보 입력 완료", f"공고 정보가 {target_row + 1}번째 행에 입력되었습니다.")


    def add_announcement_row(self):
        row_count = self.announcement_table.rowCount()
        self.announcement_table.insertRow(row_count)
        datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        datetime_edit.setCalendarPopup(True)
        datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.announcement_table.setCellWidget(row_count, 3, datetime_edit)

    def remove_announcement_row(self):
        current_row = self.announcement_table.currentRow()
        if current_row >= 0: self.announcement_table.removeRow(current_row)
        else: QMessageBox.warning(self, "선택 오류", "삭제할 행을 먼저 선택하세요.")

    def format_price_in_cell(self, row, column):
        if column != 2: return
        item = self.announcement_table.item(row, column)
        if not item: return
        self.announcement_table.blockSignals(True)
        text = item.text()
        price = utils.parse_amount(text)
        if price is not None: item.setText(f"{price:,}")
        self.announcement_table.blockSignals(False)

    # message_generator_view.py 파일의 generate_message 함수

    def generate_message(self):
        # 1. 테이블에서 모든 공고 정보 수집
        announcements = []
        for row in range(self.announcement_table.rowCount()):
            title_item = self.announcement_table.item(row, 0)
            gongo_title = title_item.text().strip() if title_item else ""
            if not gongo_title: continue

            no_item = self.announcement_table.item(row, 1)
            price_item = self.announcement_table.item(row, 2)
            datetime_widget = self.announcement_table.cellWidget(row, 3)

            gongo_no = no_item.text().strip() if no_item else ""
            price_text = price_item.text().strip() if price_item else "0"
            deadline = datetime_widget.text() if datetime_widget else ""

            announcements.append({
                "title": gongo_title, "no": gongo_no,
                "price": price_text, "deadline": deadline
            })

        if not announcements:
            QMessageBox.warning(self, "입력 오류", "최소 하나 이상의 공고 정보를 입력해주세요.");
            return

        # 2. 공통 정보 수집
        region1 = self.region_combo1.currentText()
        region2 = self.region_combo2.currentText()
        region = region1
        if region2 and region1 != region2: region = f"{region1}/{region2}"

        gongo_field = self.gongo_field_combo.currentText()
        company_name = self.company_name_entry.text().strip()
        manager_name = self.manager_name_entry.text().strip()
        if not company_name:
            QMessageBox.warning(self, "입력 오류", "'업체명'은 필수 입력 항목입니다.");
            return

        # 3. 각 항목별로 데이터 가공
        titles = [ann['title'] for ann in announcements]
        nos = [ann['no'] for ann in announcements]
        deadlines = [ann['deadline'] for ann in announcements]

        # ▼▼▼▼▼ [수정 1] 추정가격 소수점 제거 ▼▼▼▼▼
        prices = []
        for ann in announcements:
            # 텍스트로 된 가격을 다시 숫자로 변환
            price_val = utils.parse_amount(ann['price'])
            if price_val is not None:
                # 정수(int)로 만들어 소수점을 없애고, 쉼표를 포함하여 원을 붙임
                prices.append(f"{int(price_val):,}원")
            else:
                prices.append("0원")
        # ▲▲▲▲▲ [수정 1] 여기까지 ▲▲▲▲▲

        # 4. 각 블록별 텍스트 조합
        gongo_block = f"ㆍ공고명 : {titles[0]}"
        if len(titles) > 1:
            gongo_block += "\n" + "\n".join([f"       {t}" for t in titles[1:]])

        no_block = f"ㆍ공고번호 : {nos[0]}"
        if len(nos) > 1:
            no_block += "\n" + "\n".join([f"        {n}" for n in nos[1:]])

        price_block = f"ㆍ추정가격 : {prices[0]}"
        if len(prices) > 1:
            price_block += "\n" + "\n".join([f"        {p}" for p in prices[1:]])

        unique_deadlines = sorted(list(set(deadlines)))
        deadline_block = f"ㆍ투찰마감일 : {unique_deadlines[0]}"
        if len(unique_deadlines) > 1:
            deadline_block += "\n" + "\n".join([f"         {d}" for d in unique_deadlines[1:]])

        # ▼▼▼▼▼ [수정 2] 협정 건수 1건일 때 숫자 미표시 ▼▼▼▼▼
        num_announcements = len(announcements)
        if num_announcements > 1:
            closing_line = f"{num_announcements}건 협정 가능할까요?"
        else:
            closing_line = "협정 가능할까요?"
        # ▲▲▲▲▲ [수정 2] 여기까지 ▲▲▲▲▲

        # 5. 최종 메시지 조합
        message_parts = [
            gongo_block,
            no_block,
            f"ㆍ지역제한 : {region}",
            f"ㆍ종목 : {gongo_field}",
            price_block,
            deadline_block,
            "",
            company_name,
            "",
            closing_line,  # 수정된 closing_line 사용
            ""
        ]

        if manager_name:
            message_parts.append(manager_name)

        final_text = "\n".join(message_parts)
        self.result_text.setText(final_text)

    def copy_to_clipboard(self):
        message = self.result_text.toPlainText()
        if not message: QMessageBox.warning(self, "복사 실패", "먼저 문자를 생성해주세요."); return
        clipboard = QApplication.clipboard(); clipboard.setText(message)
        QMessageBox.information(self, "복사 완료", "생성된 문자 내용이 클립보드에 복사되었습니다.")

    def clear_fields(self):
        self.announcement_table.setRowCount(0); self.add_announcement_row()
        self.region_combo1.setCurrentIndex(0); self.region_combo2.setCurrentIndex(0)
        self.company_name_entry.clear(); self.manager_name_entry.clear()
        self.result_text.clear(); self.gongo_field_combo.setCurrentIndex(0)