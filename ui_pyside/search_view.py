# ui_pyside/search_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QRadioButton, QMessageBox,
                               QApplication, QFileDialog)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont

import config, utils, search_logic
import os

class SearchWorker(QThread):
    finished = Signal(list)
    def __init__(self, file_path, filters):
        super().__init__()
        self.file_path = file_path
        self.filters = filters
    def run(self):
        results = search_logic.find_and_filter_companies(self.file_path, self.filters)
        self.finished.emit(results)

class SearchViewPyside(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.is_searching = False
        self.last_search_results = []
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10,10,10,10)
        
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

    def format_text_for_excel(self, cell_text):
        """엑셀 붙여넣기를 위해 텍스트를 포맷합니다."""
        text = str(cell_text)
        # 텍스트에 줄바꿈이나 큰따옴표가 포함되어 있으면
        if '\n' in text or '"' in text:
            # 기존 큰따옴표는 두 개로 만들고, 전체를 큰따옴표로 감쌉니다.
            return f'"{text.replace("\"", "\"\"")}"'
        return text

    def copy_all_details(self):
        if not self.details_table.item(0, 1) or not self.details_table.item(0, 1).text():
            QMessageBox.warning(self, "복사 실패", "복사할 정보가 없습니다.")
            return

        lines_to_copy = []
        for row in range(self.details_table.rowCount()):
            value_item = self.details_table.item(row, 1)
            value_text = value_item.text() if value_item else ""


            processed_text = self.format_text_for_excel(value_text)
            lines_to_copy.append(processed_text)



        clipboard_text = "\r\n".join(lines_to_copy)
        QApplication.clipboard().setText(clipboard_text)
        QMessageBox.information(self, "복사 완료", "모든 '값'이 클립보드에 복사되었습니다.")



    # [create_left_panel 함수를 이 ко드로 통째로 교체하세요]
    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        
        filter_box = self.create_filter_box()
        layout.addWidget(filter_box)
        
        results_box = QWidget()
        results_layout = QVBoxLayout(results_box)
        results_layout.setContentsMargins(0,10,0,0)
        
        # [핵심] 검색 결과 타이틀과 건수 표시를 위한 레이아웃
        results_title_layout = QHBoxLayout()
        title_label = QLabel("<b>검색 결과</b>")
        title_label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        self.results_count_label = QLabel("(총 0건)") # 건수 표시 라벨
        self.results_count_label.setStyleSheet("font-size: 11px; color: #5D6D7E; padding-top: 2px;")
        
        results_title_layout.addWidget(title_label)
        results_title_layout.addWidget(self.results_count_label)
        results_title_layout.addStretch(1)
        
        results_layout.addLayout(results_title_layout)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(1)
        self.results_table.setHorizontalHeaderLabels(["업체명"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results_table.cellClicked.connect(self.on_result_selected)
        
        results_layout.addWidget(self.results_table)
        layout.addWidget(results_box)
        
        return panel
    # [create_filter_box 함수를 이 코드로 통째로 교체하세요]
    def create_filter_box(self):
        box = QWidget(); box.setObjectName("filterBox"); box.setStyleSheet("QWidget#filterBox { background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E5E7E9; }")
        layout = QGridLayout(box); layout.addWidget(QLabel("<b>파일 경로</b>"), 0, 0, 1, 2)
        self.path_source_combo = QComboBox(); self.path_source_combo.addItems(self.controller.source_files.keys()); self.path_source_combo.currentTextChanged.connect(self.update_path_display)
        layout.addWidget(self.path_source_combo, 1, 0); path_button = QPushButton("경로 설정"); path_button.clicked.connect(self.set_file_path); layout.addWidget(path_button, 1, 1)
        self.current_path_label = QLabel("경로가 설정되지 않았습니다."); self.current_path_label.setStyleSheet("font-size: 11px; color: #797D7F;"); layout.addWidget(self.current_path_label, 2, 0, 1, 2)
        layout.addWidget(QLabel("<b>검색 대상</b>"), 3, 0, 1, 2)
        self.source_radio_group = QHBoxLayout(); self.source_var_group = {}
        for key in self.controller.source_files.keys():
            rb = QRadioButton(key)
            if key == list(self.controller.source_files.keys())[0]: rb.setChecked(True)
            self.source_radio_group.addWidget(rb); self.source_var_group[key] = rb
        layout.addLayout(self.source_radio_group, 4, 0, 1, 2)
        layout.addWidget(QLabel("<b>검색 조건</b>"), 5, 0, 1, 2)
        layout.addWidget(QLabel("회사 이름:"), 6, 0)
        self.search_entry = QLineEdit(); self.search_entry.setPlaceholderText("회사 이름의 일부..."); self.search_entry.returnPressed.connect(self.start_search); layout.addWidget(self.search_entry, 6, 1)
        layout.addWidget(QLabel("지역 필터:"), 7, 0)
        self.region_combo = QComboBox(); self.region_combo.addItems(["전체", "서울", "경기", "인천", "강원", "충북", "충남", "대전", "세종", "전북", "전남", "광주", "경북", "경남", "대구", "울산", "부산", "제주"]); layout.addWidget(self.region_combo, 7, 1)

        # [핵심] 담당자 필터 UI 추가
        layout.addWidget(QLabel("담당자:"), 8, 0)
        self.manager_entry = QLineEdit(); self.manager_entry.setPlaceholderText("담당자 이름으로 검색..."); self.manager_entry.returnPressed.connect(self.start_search); layout.addWidget(self.manager_entry, 8, 1)

        # 범위 필터들의 행 번호를 하나씩 밀어줌
        self.min_sipyung_entry, self.max_sipyung_entry = self.create_range_filter(layout, "시평액 범위:", 9)
        self.min_perf_3y_entry, self.max_perf_3y_entry = self.create_range_filter(layout, "3년 실적 범위:", 10)
        self.min_perf_5y_entry, self.max_perf_5y_entry = self.create_range_filter(layout, "5년 실적 범위:", 11)
        self.search_button = QPushButton("검색 실행"); self.search_button.setStyleSheet("padding: 12px; font-weight: bold;"); self.search_button.clicked.connect(self.start_search); layout.addWidget(self.search_button, 12, 0, 1, 2)
        self.update_path_display(); return box
        
    # [create_range_filter 함수를 이 ко드로 통째로 교체하세요]
    def create_range_filter(self, layout, label_text, row):
        layout.addWidget(QLabel(label_text), row, 0)
        range_layout = QHBoxLayout()
        min_entry = QLineEdit()
        min_entry.setPlaceholderText("최소 금액")
        max_entry = QLineEdit()
        max_entry.setPlaceholderText("최대 금액")
        
        # [핵심] 각 입력칸의 textChanged 시그널을 format_price_in_entry 함수에 연결
        min_entry.textChanged.connect(lambda: self.format_price_in_entry(min_entry))
        max_entry.textChanged.connect(lambda: self.format_price_in_entry(max_entry))
        
        range_layout.addWidget(min_entry)
        range_layout.addWidget(max_entry)
        layout.addLayout(range_layout, row, 1)
        
        return min_entry, max_entry
        
    # [이 함수를 추가하세요]
    def create_right_panel(self):
        """업체 상세 정보를 표시하는 오른쪽 패널을 생성합니다."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- [핵심 수정] 타이틀 레이아웃 ---
        title_layout = QHBoxLayout()
        
        # 1. 기존 '업체 상세 정보' 레이블
        label = QLabel("<b>업체 상세 정보</b>")
        label.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        title_layout.addWidget(label)

        # 2. (추가) 현재 데이터 소스를 표시할 레이블
        self.source_display_label = QLabel("") # self. 로 만들어 다른 함수에서 접근 가능하게 함
        self.source_display_label.setFont(QFont("맑은 고딕", 16, QFont.Bold))
        # 눈에 띄는 색상과 스타일 적용
        self.source_display_label.setStyleSheet("color: #2980B9; padding: 5px; border: 2px solid #3498DB; border-radius: 5px;")
        title_layout.addWidget(self.source_display_label)

        title_layout.addStretch(1) # 공간을 밀어주는 stretch

        # 3. '전체 복사' 버튼
        self.copy_all_button = QPushButton("📋 전체 복사")
        self.copy_all_button.setFixedWidth(120)
        self.copy_all_button.clicked.connect(self.copy_all_details)
        title_layout.addWidget(self.copy_all_button)
        
        layout.addLayout(title_layout)
        # --- 타이틀 레이아웃 끝 ---

        self.details_table = QTableWidget()
        self.details_table.setColumnCount(3)
        self.details_table.setHorizontalHeaderLabels(["항목", "내용", ""])
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.details_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.details_table.setWordWrap(True)
        
        fields = ["검색된 회사"] + list(config.RELATIVE_OFFSETS.keys())
        self.details_table.setRowCount(len(fields))
        for i, field in enumerate(fields):
            item = QTableWidgetItem(field)
            item.setFont(QFont("맑은 고딕", 9, QFont.Bold))
            self.details_table.setItem(i, 0, item)
            self.details_table.setItem(i, 1, QTableWidgetItem(""))
            if field in ["검색된 회사", "대표자", "사업자번호", "시평", "3년 실적", "5년 실적"]:
                btn = QPushButton("📋")
                btn.setFixedWidth(35)
                btn.clicked.connect(lambda checked, f=field: self.copy_field_value(f))
                self.details_table.setCellWidget(i, 2, btn)
                
        layout.addWidget(self.details_table)
        return panel
        
    # [start_search 함수를 이 코드로 통째로 교체하세요]
    def start_search(self):
        if self.is_searching:
            return

        source_key = ""
        for key, rb in self.source_var_group.items():
            if rb.isChecked():
                source_key = key
                break
        
        source_file = self.controller.source_files.get(source_key)
        if not source_file or not os.path.exists(source_file):
            QMessageBox.critical(self, "오류", f"'{source_key}' 파일 경로가 설정되지 않았습니다.\n'경로 설정' 버튼으로 파일을 지정해주세요.")
            return

        filters = {
            'name': self.search_entry.text().strip(),
            'region': self.region_combo.currentText(),
            # [핵심] 담당자 필터 값 추가
            'manager': self.manager_entry.text().strip(),
            'min_sipyung': utils.parse_amount(self.min_sipyung_entry.text()),
            'max_sipyung': utils.parse_amount(self.max_sipyung_entry.text()),
            'min_perf_3y': utils.parse_amount(self.min_perf_3y_entry.text()),
            'max_perf_3y': utils.parse_amount(self.max_perf_3y_entry.text()),
            'min_perf_5y': utils.parse_amount(self.min_perf_5y_entry.text()),
            'max_perf_5y': utils.parse_amount(self.max_perf_5y_entry.text())
        }

        self.search_button.setText("검색 중...")
        self.search_button.setEnabled(False)
        self.is_searching = True
        self.source_display_label.setText(f"[{source_key}]")

        self.worker = SearchWorker(source_file, filters)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.start()
        
        # [on_search_finished 함수를 이 ко드로 통째로 교체하세요]
    def on_search_finished(self, results):
        self.last_search_results = results
        self.is_searching = False
        self.search_button.setText("검색 실행")
        self.search_button.setEnabled(True)
        self.results_table.setRowCount(0)
        self.clear_details()

        if not results or "오류" in results[0]:
            error_msg = results[0].get("오류", "결과가 없습니다.") if results else "결과가 없습니다."
            QMessageBox.information(self, "검색 결과", error_msg)
            self.results_count_label.setText("(총 0건)") # [핵심] 에러 또는 결과 없음 시 0건 표시
            return
        
        # [핵심] 검색 건수 업데이트
        self.results_count_label.setText(f"(총 {len(results)}건)")
        
        self.results_table.setRowCount(len(results))
        for row, data in enumerate(results):
            item = QTableWidgetItem(data.get("검색된 회사", ""))
            self.results_table.setItem(row, 0, item)
            company_statuses = data.get("데이터상태", {})
            # [수정] 경영상태 대신, 데이터가 확실히 있는 '부채비율'을 기준으로 색상 표시
            main_status = company_statuses.get("부채비율", "미지정")
            color_hex = {"최신": "#E2EFDA", "1년 경과": "#DDEBF7", "1년 이상 경과": "#FDEDEC"}.get(main_status)
            if color_hex:
                item.setBackground(QColor(color_hex))
        
        if results:
            self.results_table.selectRow(0)
            self.display_company_details(results[0])
        
    def on_result_selected(self, row, column):
        if self.last_search_results and row < len(self.last_search_results): self.display_company_details(self.last_search_results[row])
        
    # [display_company_details 함수를 이 코드로 통째로 교체하세요]
    def display_company_details(self, data):
        if not data: self.clear_details(); return

        danger_color = QColor("#E74C3C")
        default_color = QColor("black")
        
        selected_source = ""
        for key, rb in self.source_var_group.items():
            if rb.isChecked(): selected_source = key; break
        thresholds = config.RATIO_THRESHOLDS.get(selected_source)

        # [핵심] 상세한 데이터 상태 딕셔너리를 가져옵니다.
        company_statuses = data.get("데이터상태", {})
        status_colors = {"최신": "#E2EFDA", "1년 경과": "#DDEBF7", "1년 이상 경과": "#FDEDEC", "미지정": "#FFFFFF"}

        for row in range(self.details_table.rowCount()):
            field_item = self.details_table.item(row, 0)
            if not field_item: continue
            
            field = field_item.text()
            value = data.get(field, "")
            
            value_item = self.details_table.item(row, 1)
            if not value_item:
                value_item = QTableWidgetItem()
                self.details_table.setItem(row, 1, value_item)
            
            value_item.setForeground(default_color)

            # 값(value)을 문자열(value_str)로 변환하는 로직
            value_str = ""
            if field in ["시평", "3년 실적", "5년 실적"]:
                parsed = utils.parse_amount(str(value)); value_str = f"{parsed:,.0f}" if parsed is not None else str(value)
            elif field in ["부채비율", "유동비율"]:
                if isinstance(value, (int, float)):
                    percent_value = value
                    value_str = f"{percent_value:.2f}%"
                    if thresholds:
                        is_danger = (field == "부채비율" and percent_value > thresholds.get("부채비율_초과", float('inf'))) or \
                                    (field == "유동비율" and percent_value <= thresholds.get("유동비율_이하", float('-inf')))
                        if is_danger: value_item.setForeground(danger_color)
                else: value_str = str(value)
            else: value_str = str(value)
            value_item.setText(value_str)

            # [핵심 수정] 배경색을 칠하는 로직
            # 각 필드(field)에 해당하는 상태를 직접 찾아서 배경색을 설정합니다.
            field_status = company_statuses.get(field, "미지정")
            bg_color_hex = status_colors.get(field_status, status_colors["미지정"])
            value_item.setBackground(QColor(bg_color_hex))
            
        self.details_table.resizeRowsToContents()


    def clear_details(self):
        for row in range(self.details_table.rowCount()):
            item = self.details_table.item(row, 1)
            if item: item.setText(""), item.setBackground(QColor("#FFFFFF")), item.setForeground(QColor("black"))
            else: self.details_table.setItem(row, 1, QTableWidgetItem(""))

    # [삭제한 위치에 이 올바른 함수를 추가하세요]
    def set_file_path(self):
        """파일 대화상자를 열어 엑셀 파일 경로를 설정하고 UI와 설정을 업데이트합니다."""
        # 1. 현재 콤보박스에서 선택된 소스 타입(예: "전기")을 가져옵니다.
        source_type = self.path_source_combo.currentText()
        
        # 2. 파일 선택 대화상자를 엽니다.
        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            f"{source_type} 파일 선택", 
            "",  # 기본 경로
            "Excel Files (*.xlsx *.xls)"
        )
        
        # 3. 사용자가 파일을 선택했을 경우에만 아래 로직을 실행합니다.
        if filepath: 
            # 3-1. 컨트롤러의 source_files 딕셔너리에 '문자열' 경로를 올바르게 저장합니다.
            self.controller.source_files[source_type] = filepath
            
            # 3-2. 화면의 경로 레이블을 업데이트하는 함수를 호출합니다.
            self.update_path_display()
            
            # 3-3. 변경된 경로 정보를 config.json 파일에 저장합니다.
            config.save_config(self.controller.source_files)
            
    def update_path_display(self, text=None):
        source_type = self.path_source_combo.currentText(); filepath = self.controller.source_files.get(source_type, "")
        if filepath and os.path.exists(filepath): self.current_path_label.setText(os.path.basename(filepath))
        else: self.current_path_label.setText("경로가 설정되지 않았습니다.")
        
    def copy_field_value(self, field):
        for row in range(self.details_table.rowCount()):
            if self.details_table.item(row, 0).text() == field:
                value_item = self.details_table.item(row, 1)
                if value_item and value_item.text(): QApplication.clipboard().setText(value_item.text()), QMessageBox.information(self, "복사 완료", f"'{field}' 값이 클립보드에 복사되었습니다.")
                return
            
    
        # [SearchViewPyside 클래스 내부에 이 새로운 함수를 추가하세요]
    def format_price_in_entry(self, widget):
        """QLineEdit 위젯의 텍스트에 실시간으로 콤마를 추가합니다."""
        # 현재 커서 위치를 기억
        cursor_pos = widget.cursorPosition()
        
        original_text = widget.text()
        
        # 텍스트에서 숫자만 추출
        try:
            number_str = ''.join(filter(str.isdigit, original_text))
            if not number_str:
                return # 숫자가 없으면 아무것도 하지 않음
            
            number = int(number_str)
            formatted_text = f"{number:,}"
        except (ValueError, TypeError):
            # 숫자로 변환할 수 없는 경우, 원본 텍스트를 유지
            return

        # 텍스트가 실제로 변경되었을 때만 업데이트 (무한 루프 방지)
        if original_text != formatted_text:
            # setText가 또다시 textChanged 시그널을 발생시키지 않도록 잠시 신호 연결을 끊음
            widget.blockSignals(True)
            widget.setText(formatted_text)
            widget.blockSignals(False)
            
            # 커서 위치 재조정 (숫자가 늘어난 만큼 커서 위치를 뒤로 이동)
            new_cursor_pos = cursor_pos + (len(formatted_text) - len(original_text))
            widget.setCursorPosition(max(0, new_cursor_pos))