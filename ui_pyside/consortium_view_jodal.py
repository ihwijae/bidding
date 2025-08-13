# ui_pyside/consortium_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QFrame, QSplitter, QApplication, QScrollArea,
                               QComboBox, QDateEdit, QRadioButton, QGroupBox, QCheckBox, QMenu)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
import utils
import config
import calculation_logic # [핵심] 누락되었던 import 문
from .company_select_popup import CompanySelectPopupPyside
from .review_dialog import ReviewDialogPyside
from .guided_copy_popup import GuidedCopyPopup
from .share_check_popup import ShareCheckPopup
from .text_display_popup import TextDisplayPopup
from PySide6.QtCore import QDateTime # 날짜/시간 처리를 위해 추가
from .api_popup import ApiPopup

class  ConsortiumViewJodal(QWidget):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.mode = "조달청"
        self.company_data_map = {}
        self.result_widgets = []
        self.announcement_date_modified = False
        self.setup_ui()
        self.connect_signals()
        self.update_ui_by_rule() # [핵심] 이 호출이 있어야 처음 UI가 올바르게 설정됨
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        input_panel = self.create_input_panel()
        self.result_scroll_area = self.create_result_scroll_area()
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(input_panel)
        splitter.addWidget(self.result_scroll_area)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setSizes([480, 270])
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        main_layout.addWidget(splitter)

    # [connect_signals 함수를 이 코드로 통째로 교체하세요]
    def connect_signals(self):

        self.api_search_button.clicked.connect(self.open_api_popup)
        # 공고 정보
        self.notice_base_amount_entry.textChanged.connect(self.calculate_performance_target)
        self.notice_base_amount_entry.textChanged.connect(self.calculate_tuchal_amount)
        
        # 입찰금액 정보
        self.tuchal_rate_entry.textChanged.connect(self.calculate_tuchal_amount)
        self.sajung_rate_entry.textChanged.connect(self.calculate_tuchal_amount)

        # 기타 모든 시그널 (기존과 동일)
        self.estimation_price_entry.textChanged.connect(self.update_ui_by_rule)
        self.tree.doubleClicked.connect(self.on_tree_double_click)
        self.tree.itemChanged.connect(self.on_share_changed)
        self.review_button.clicked.connect(self.open_review_dialog)
        self.add_result_button.clicked.connect(self.process_and_add_result)
        self.delete_all_button.clicked.connect(self.delete_all_results)
        self.rule_combo.currentTextChanged.connect(self.update_ui_by_rule)
        self.announcement_date_edit.dateChanged.connect(self.on_announcement_date_changed)
        self.sipyung_limit_check.stateChanged.connect(self.on_sipyung_limit_toggled)
        self.estimation_price_entry.textChanged.connect(self.update_sipyung_limit_amount) # 행안부 호환용
        self.pre_check_button.clicked.connect(self.run_pre_check)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.generate_messages_button.clicked.connect(self.generate_consortium_messages)
    # [이 함수로 create_input_panel 함수를 통째로 교체하세요]
    def create_input_panel(self):
        panel = QWidget()
        panel.setObjectName("filterBox")
        layout = QVBoxLayout(panel)
            
        # [핵심 추가] 최상단에 버튼 추가
        api_button_layout = QHBoxLayout()
        self.api_search_button = QPushButton("📡 API 공고 검색")
        api_button_layout.addStretch(1)
        api_button_layout.addWidget(self.api_search_button)
        layout.addLayout(api_button_layout)

        # --- 1. 상단 정보 입력 (하나의 그리드로 모두 제어) ---
        top_grid = QGridLayout()
        
        # 위젯 생성
        self.title_label = QLabel()
        self.gongo_no_entry = QLineEdit()
        self.gongo_title_entry = QLineEdit()
        self.announcement_date_edit = QDateEdit(QDate.currentDate()); self.announcement_date_edit.setCalendarPopup(True); self.announcement_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.gongo_field_combo = QComboBox(); self.gongo_field_combo.addItem("-- 분야 선택 --"); self.gongo_field_combo.addItems(self.controller.source_files.keys())
        self.rule_combo = QComboBox()
        if self.mode in config.CONSORTIUM_RULES: 
            self.rule_combo.addItems(config.CONSORTIUM_RULES[self.mode].keys())
        self.estimation_price_entry = QLineEdit()
        self.notice_base_amount_entry = QLineEdit()

        # --- [핵심] 레이아웃 최종 재배치 ---
        # 0행: 타이틀
        top_grid.addWidget(self.title_label, 0, 0, 1, 6) # 6칸 모두 사용
        
        # 1행: 공고번호, 공고일, 공고분야
        top_grid.addWidget(QLabel("공고번호:"), 1, 0); top_grid.addWidget(self.gongo_no_entry, 1, 1)
        top_grid.addWidget(QLabel("<b>공고일:</b>"), 1, 2);  top_grid.addWidget(self.announcement_date_edit, 1, 3)
        top_grid.addWidget(QLabel("<b>공고분야:</b>"), 1, 4); top_grid.addWidget(self.gongo_field_combo, 1, 5)

        # 2행: 공고제목, 심사기준
        top_grid.addWidget(QLabel("공고제목:"), 2, 0); top_grid.addWidget(self.gongo_title_entry, 2, 1, 1, 3) # 공고제목은 3칸 차지
        top_grid.addWidget(QLabel("<b>심사 기준:</b>"), 2, 4); top_grid.addWidget(self.rule_combo, 2, 5)
        
        # 3행: 추정가격, 기초금액
        top_grid.addWidget(QLabel("추정가격:"), 3, 0); top_grid.addWidget(self.estimation_price_entry, 3, 1)
        top_grid.addWidget(QLabel("기초금액:"), 3, 2); top_grid.addWidget(self.notice_base_amount_entry, 3, 3, 1, 3) # 기초금액은 3칸 차지

        # 열 너비 비율 조절
        top_grid.setColumnStretch(1, 1); top_grid.setColumnStretch(3, 1); top_grid.setColumnStretch(5, 1)
        layout.addLayout(top_grid)

        # --- 2. 입찰금액 정보 섹션 ---
        self.bid_amount_group = QGroupBox("입찰금액 정보 (조달청)")
        bid_amount_layout = QGridLayout(self.bid_amount_group)
        self.tuchal_rate_entry = QLineEdit(); self.tuchal_rate_entry.setText("88.745")
        self.sajung_rate_entry = QLineEdit(); self.sajung_rate_entry.setText("101.8")
        self.tuchal_amount_label = QLabel("0 원")
        
        bid_amount_layout.addWidget(QLabel("<b>투찰율(%):</b>"), 0, 0); bid_amount_layout.addWidget(self.tuchal_rate_entry, 0, 1)
        bid_amount_layout.addWidget(QLabel("<b>사정율(%):</b>"), 0, 2); bid_amount_layout.addWidget(self.sajung_rate_entry, 0, 3)
        bid_amount_layout.addWidget(QLabel("<b>예상 투찰금액:</b>"), 1, 0); bid_amount_layout.addWidget(self.tuchal_amount_label, 1, 1, 1, 3)
        bid_amount_layout.setColumnStretch(1, 1); bid_amount_layout.setColumnStretch(3, 1)
        layout.addWidget(self.bid_amount_group)

        # --- 3. 참가자격 제한 섹션 ---
        qualification_group = QGroupBox("참가자격 제한")
        qualification_layout = QGridLayout(qualification_group)
        self.region_limit_combo = QComboBox(); self.region_limit_combo.addItems(["전체", "서울", "경기", "인천", "강원", "충북", "충남", "대전", "세종", "전북", "전남", "광주", "경북", "경남", "대구", "울산", "부산", "제주"])
        self.duty_ratio_entry = QLineEdit(); self.duty_ratio_entry.setPlaceholderText("예: 49")
        self.sipyung_limit_check = QCheckBox("시평액 제한 있음")
        self.sipyung_limit_amount = QLineEdit(); self.sipyung_limit_amount.setPlaceholderText("제한 금액(추정가격 기준)"); self.sipyung_limit_amount.setEnabled(False)
        self.ratio_method_radio = QRadioButton("비율제"); self.ratio_method_radio.setChecked(True)
        self.sum_method_radio = QRadioButton("합산제")
        self.ratio_method_radio.setEnabled(False); self.sum_method_radio.setEnabled(False)
        method_layout = QHBoxLayout(); method_layout.addWidget(self.ratio_method_radio); method_layout.addWidget(self.sum_method_radio); method_layout.addStretch()
        
        qualification_layout.addWidget(QLabel("지역제한:"), 0, 0); qualification_layout.addWidget(self.region_limit_combo, 0, 1)
        qualification_layout.addWidget(QLabel("의무비율(%):"), 0, 2); qualification_layout.addWidget(self.duty_ratio_entry, 0, 3)
        qualification_layout.addWidget(self.sipyung_limit_check, 1, 0); qualification_layout.addWidget(self.sipyung_limit_amount, 1, 1)
        qualification_layout.addWidget(QLabel("계산방식:"), 1, 2); qualification_layout.addLayout(method_layout, 1, 3)
        
        self.performance_label = QLabel()
        self.performance_target_label = QLabel()
        qualification_layout.addWidget(self.performance_label, 2, 2, Qt.AlignRight)
        qualification_layout.addWidget(self.performance_target_label, 2, 3, Qt.AlignLeft)
        layout.addWidget(qualification_group)

        # --- 4. 업체 구성 테이블 ---
        self.tree = QTableWidget()
        self.tree.setRowCount(5); self.tree.setColumnCount(5)
        self.tree.setHorizontalHeaderLabels(["구분", "업체명", "지역", "5년실적", "지분율(%)"])
        self.tree.verticalHeader().setVisible(False)
        roles = ["대표사"] + [f"구성사 {i}" for i in range(1, 5)]
        for i, role in enumerate(roles):
            item_role = QTableWidgetItem(role); item_role.setFlags(item_role.flags() & ~Qt.ItemIsEditable); self.tree.setItem(i, 0, item_role)
            item_name = QTableWidgetItem("[더블클릭하여 업체 선택]"); item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable); self.tree.setItem(i, 1, item_name)
            for c in range(2, 5):
                item = QTableWidgetItem(""); item.setFlags(item.flags() & ~Qt.ItemIsEditable); self.tree.setItem(i, c, item)
            self.company_data_map[i] = {'role': role, 'data': None, 'share': 0, 'source_type': None}
        self.tree.resizeColumnsToContents(); self.tree.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tree, 1)
        
        # --- 5. 하단 버튼 ---
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self.pre_check_button = QPushButton("🔬 지분율 사전검토")
        self.review_button = QPushButton("📋 적격심사 검토")
        self.add_result_button = QPushButton("📊 결과 표 추가")
        button_layout.addWidget(self.pre_check_button); button_layout.addWidget(self.review_button); button_layout.addWidget(self.add_result_button)
        layout.addLayout(button_layout)
        
        self.update_ui_by_rule()
        return panel

    def create_result_scroll_area(self):
        container_widget = QWidget(); container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        top_button_layout = QHBoxLayout(); top_button_layout.addWidget(QLabel("<b>계산 결과 목록</b>"))
        top_button_layout.addStretch(1)

        self.generate_messages_button = QPushButton("✉️ 협정 문자 일괄 생성")
        top_button_layout.addWidget(self.generate_messages_button)

        self.delete_all_button = QPushButton("🗑️ 전체 삭제")
        top_button_layout.addWidget(self.delete_all_button); container_layout.addLayout(top_button_layout)
        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setObjectName("filterBox")
        scroll_content = QWidget(); self.results_layout = QVBoxLayout(scroll_content)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(scroll_content); container_layout.addWidget(scroll_area)
        return container_widget

    # [update_ui_by_rule 함수를 이 코드로 통째로 교체하세요]
    def update_ui_by_rule(self):
        selected_rule_key = self.rule_combo.currentText()
        
        # [핵심] 콤보박스가 비어있으면 아무것도 하지 않음
        if not selected_rule_key:
            self.title_label.setText(f"<b>공고 정보 ({self.mode})</b>")
            self.performance_label.setText("실적만점:")
            self.performance_target_label.setText("")
            return

        try:
            ruleset = config.CONSORTIUM_RULES.get(self.mode, {}).get(selected_rule_key, {})
            
            # 1. 화면 상단의 타이틀 설정
            self.title_label.setText(f"<b>공고 정보 ({ruleset.get('name', self.mode)})</b>")

            # 2. 실적만점 배수 표시 업데이트
            multiplier = ruleset.get('performance_multiplier', 1.0)
            self.performance_label.setText(f"실적만점({multiplier}배수):")

            # 3. [핵심] 심사 기준이 변경되었으므로, 실적만점을 다시 계산
            self.calculate_performance_target()
            
        except KeyError:
            # 오류 발생 시 UI 초기화
            self.title_label.setText(f"<b>공고 정보 ({self.mode})</b>")
            self.performance_label.setText("실적만점:")
            self.performance_target_label.setText("")
    
    # [calculate_performance_target 함수를 이 진단 모드 코드로 통째로 교체하세요]
    def calculate_performance_target(self):
        # --- 진단 시작 ---
        print("\n--- [진단] calculate_performance_target 함수 실행됨 ---")
        
        try:
            # 1. 현재 선택된 룰 가져오기
            selected_rule_key = self.rule_combo.currentText()
            print(f"  [1] 선택된 심사 기준: '{selected_rule_key}'")
            if not selected_rule_key:
                print("  [오류] 심사 기준이 선택되지 않아 계산을 중단합니다.")
                self.performance_target_label.setText("")
                print("---------------------------------------------------\n")
                return

            # 2. 룰셋에서 배수 가져오기
            ruleset = config.CONSORTIUM_RULES.get(self.mode, {}).get(selected_rule_key, {})
            multiplier = ruleset.get('performance_multiplier', 1.0)
            print(f"  [2] 적용 배수: {multiplier}")
            
            # 3. 기초금액 입력칸에서 텍스트 읽기
            base_amount_text = self.notice_base_amount_entry.text()
            print(f"  [3] '기초금액' 입력칸의 텍스트: '{base_amount_text}'")

            # 4. 텍스트를 숫자로 변환
            price_val = utils.parse_amount(base_amount_text)
            print(f"  [4] 숫자로 변환된 값: {price_val}")

            # 5. 최종 실적만점 계산
            target = price_val * multiplier if price_val else 0
            print(f"  [5] 계산된 최종 실적만점액: {target}")

            # 6. 라벨에 텍스트 설정
            final_text = f"{target:,.0f}" if target else ""
            self.performance_target_label.setText(final_text)
            print(f"  [6] 라벨에 설정할 텍스트: '{final_text}'")
            
        except Exception as e:
            print(f"  [치명적 오류] 함수 실행 중 예외 발생: {e}")
        
        print("--- [진단] 함수 실행 완료 ---")
        # --- 진단 끝 ---
    
    # [calculate_tuchal_amount 함수를 이 코드로 통째로 교체하세요]
    def calculate_tuchal_amount(self):
        try:
            # [핵심] 기준이 되는 기초금액을 self.notice_base_amount_entry에서 가져옴
            base_amount = utils.parse_amount(self.notice_base_amount_entry.text()) or 0
            tuchal_rate = float(self.tuchal_rate_entry.text()) or 0
            sajung_rate = float(self.sajung_rate_entry.text()) or 0
        except (ValueError, TypeError):
            self.tuchal_amount_label.setText("<b style='color:red;'>숫자만 입력하세요</b>")
            return

        if base_amount > 0 and tuchal_rate > 0 and sajung_rate > 0:
            tuchal_amount = base_amount * (tuchal_rate / 100.0) * (sajung_rate / 100.0)
            self.tuchal_amount_label.setText(f"<b style='color:blue;'>{tuchal_amount:,.0f} 원</b>")
        else:
            self.tuchal_amount_label.setText("0 원")

    def on_announcement_date_changed(self):
        self.announcement_date_modified = True

    def on_sipyung_limit_toggled(self, state):
        is_enabled = (state == Qt.CheckState.Checked.value)
        self.sipyung_limit_amount.setEnabled(is_enabled)
        self.ratio_method_radio.setEnabled(is_enabled)
        self.sum_method_radio.setEnabled(is_enabled)
        if is_enabled: self.update_sipyung_limit_amount()
        else: self.sipyung_limit_amount.clear()

    def update_sipyung_limit_amount(self):
        if self.sipyung_limit_check.isChecked():
            estimation_price_text = self.estimation_price_entry.text()
            self.sipyung_limit_amount.setText(estimation_price_text)

    def validate_inputs(self):
        # --- 상단부 유효성 검사는 기존과 동일 ---
        if not self.announcement_date_modified:
            QMessageBox.warning(self, "입력 필요", "정확한 계산을 위해 '공고일'을 반드시 설정해주세요.");
            return None
        announcement_date = self.announcement_date_edit.date().toPython()

        companies_data = [info for i, info in self.company_data_map.items() if
                          info and info['data'] and info.get('share', 0) > 0]
        if not companies_data:
            QMessageBox.warning(self, "입력 오류", "업체를 1곳 이상 선택하고, 지분율을 0보다 크게 입력하세요.");
            return None
        selected_rule_key = self.rule_combo.currentText()
        if not selected_rule_key:
            QMessageBox.warning(self, "선택 오류", "심사 기준을 선택하세요.");
            return None
        rule_info = (self.mode, selected_rule_key)
        region_limit = self.region_limit_combo.currentText()

        # ... (지역제한, 의무비율 검사 로직은 기존과 동일) ...

        # ▼▼▼▼▼ [핵심 수정] 모든 금액 정보를 price_data 딕셔너리로 묶기 ▼▼▼▼▼

        # 1. 추정가격 검증
        estimation_price_val = utils.parse_amount(self.estimation_price_entry.text())
        if not estimation_price_val:
            QMessageBox.warning(self, "입력 오류", "추정가격을 정확히 입력해주세요.");
            return None

        # 2. 기초금액 가져오기 (행안부/조달청 UI 자동 호환)
        base_amount_val = 0
        if hasattr(self, 'notice_base_amount_entry'):  # 조달청 UI에 해당 위젯이 있으면
            base_amount_val = utils.parse_amount(self.notice_base_amount_entry.text())
        elif hasattr(self, 'base_amount_entry'):  # 행안부 UI에 해당 위젯이 있으면
            base_amount_val = utils.parse_amount(self.base_amount_entry.text())

        # 3. 투찰금액 가져오기
        tuchal_amount_text = self.tuchal_amount_label.text().replace("<b>", "").replace("</b>", "").replace(" 원",
                                                                                                            "").replace(
            ",", "")
        tuchal_amount_val = utils.parse_amount(tuchal_amount_text) or 0

        # 4. 모든 금액 정보를 하나의 딕셔너리로 생성
        price_data = {
            "estimation_price": estimation_price_val,
            "notice_base_amount": base_amount_val,
            "tuchal_amount": tuchal_amount_val
        }

        # ▲▲▲▲▲ [핵심 수정] 여기까지 ▲▲▲▲▲

        sipyung_info = {
            "is_limited": self.sipyung_limit_check.isChecked(),
            "limit_amount": utils.parse_amount(self.sipyung_limit_amount.text()) or 0,
            "method": "비율제" if self.ratio_method_radio.isChecked() else "합산제",
            "tuchal_amount": price_data["tuchal_amount"]  # 위에서 계산한 값을 사용
        }

        # [수정] 반환값에서 estimation_price 대신 price_data를 반환
        return (companies_data, price_data, announcement_date, rule_info, sipyung_info, region_limit)

    def open_review_dialog(self):
        validated_data = self.validate_inputs()
        if not validated_data: return
        companies_data, price_data, announcement_date, rule_info, sipyung_info, region_limit = validated_data

        if not self.check_regional_requirements(companies_data):
            return

        result = calculation_logic.calculate_consortium(companies_data, price_data, announcement_date, rule_info, sipyung_info, region_limit)
        if not result: QMessageBox.critical(self, "계산 오류", "점수 계산 중 오류가 발생했습니다."); return
        review_dialog = ReviewDialogPyside(result, self)
        review_dialog.exec()

        # [process_and_add_result 함수를 이 코드로 통째로 교체하세요]
    def process_and_add_result(self):
        # 1. 현재 추가하려는 컨소시엄의 유효성 검사 (입력값 등)
        validated_data = self.validate_inputs()
        if not validated_data: return

        # 현재 추가하려는 업체 목록
        companies_data, estimation_price, announcement_date, rule_info, sipyung_info, region_limit = validated_data

        if not self.check_regional_requirements(companies_data):
            return

        current_company_names = {comp['data'].get("검색된 회사") for comp in companies_data}

        # 2. [핵심] "계산 결과 목록" 전체를 대상으로 중복 검사
        existing_company_names = set()
        for result_widget in self.result_widgets:
            if hasattr(result_widget, 'result_data'):
                for detail in result_widget.result_data.get("company_details", []):
                    existing_company_names.add(detail.get("name"))

        # 현재 업체 목록과 기존 전체 목록 사이에 겹치는 업체가 있는지 확인
        overlapping_companies = current_company_names.intersection(existing_company_names)
        
        if overlapping_companies:
            # 겹치는 업체들의 이름을 쉼표로 연결하여 메시지에 표시
            names_str = ", ".join(overlapping_companies)
            QMessageBox.critical(self, "중복 오류", 
                f"이미 다른 결과에 포함된 업체가 있습니다: [{names_str}]\n\n"
                "기존 결과를 삭제하거나 다른 업체로 구성해주세요.")
            return

        # 3. 모든 중복 검사를 통과한 경우, 계산 및 결과 표 추가 실행
        result = calculation_logic.calculate_consortium(companies_data, estimation_price, announcement_date, rule_info, sipyung_info, region_limit)
        if not result:
            QMessageBox.critical(self, "계산 오류", "점수 계산 중 오류가 발생했습니다.")
            return
            
        result['gongo_title'] = self.gongo_title_entry.text()
        result['gongo_no'] = self.gongo_no_entry.text()
        
        result_index = len(self.result_widgets)
        result_widget = self.create_single_result_widget(result, result_index)
        
        self.results_layout.addWidget(result_widget)
        self.result_widgets.append(result_widget)

  # [on_tree_double_click 함수를 이 코드로 통째로 교체하세요]
    def on_tree_double_click(self, model_index):
        row = model_index.row()
        col = model_index.column()
        if col != 1: return

        selected_field = self.gongo_field_combo.currentText()
        if selected_field == "-- 분야 선택 --":
            QMessageBox.warning(self, "선택 필요", "먼저 '공고분야'를 선택해주세요."); return

        # [핵심] 현재 테이블에 추가된 업체들의 이름 목록을 다시 정확하게 생성합니다.
        existing_companies = []
        for r in range(self.tree.rowCount()):
            # 더블클릭한 자기 자신 행은 중복 검사에서 제외해야 합니다.
            if r == row: continue
            
            # company_data_map에서 업체 정보를 가져옵니다.
            company_info = self.company_data_map.get(r)
            if company_info and company_info.get('data'):
                company_name = company_info['data'].get("검색된 회사")
                if company_name:
                    existing_companies.append(company_name)
        
        # --- 디버깅용 print문 (문제가 해결되면 지워도 됩니다) ---
        print(f"중복 검사를 위해 팝업으로 전달하는 업체 목록: {existing_companies}")
        
        # --- 콜백 함수 정의 ---
        def update_company_info(selected_company_data):
            self.tree.blockSignals(True)
            self.company_data_map[row]['data'] = selected_company_data
            self.company_data_map[row]['source_type'] = selected_field
            company_name = selected_company_data.get("검색된 회사", "")
            region = selected_company_data.get("지역", "")
            perf_5y = utils.parse_amount(selected_company_data.get("5년 실적"))
            self.tree.setItem(row, 1, QTableWidgetItem(company_name))
            self.tree.setItem(row, 2, QTableWidgetItem(region))
            self.tree.setItem(row, 3, QTableWidgetItem(f"{perf_5y:,.0f}" if perf_5y is not None else "0"))
            self.tree.blockSignals(False)
            self.tree.setItem(row, 4, QTableWidgetItem("0"))
            self.tree.resizeColumnsToContents()
            self.tree.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.pre_check_passed = False

        # --- 팝업창 생성 및 실행 ---
        self.popup = CompanySelectPopupPyside(self, self.controller, selected_field, update_company_info, existing_companies)
        self.popup.show()

    def on_share_changed(self, item):
        if item.column() == 4:  # 지분율(%) 열
            try:
                # 사용자가 입력한 텍스트를 100으로 나누어 0.51과 같은 형태로 저장
                share_value = float(item.text()) / 100.0
                self.company_data_map[item.row()]['share'] = share_value
            except (ValueError, TypeError):
                self.company_data_map[item.row()]['share'] = 0
            
    def delete_all_results(self):
        reply = QMessageBox.question(self, "전체 삭제", "모든 계산 결과를 삭제하시겠습니까?")
        if reply == QMessageBox.StandardButton.Yes:
            for widget in self.result_widgets: widget.deleteLater()
            self.result_widgets.clear()
            
    # [delete_single_result 함수를 이 코드로 통째로 교체하세요]
    def delete_single_result(self, widget_to_delete):
        # 1. 사용자에게 삭제 여부를 먼저 확인합니다.
        reply = QMessageBox.question(self, "결과 삭제", "선택한 계산 결과를 삭제하시겠습니까?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                    QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return
        
    # [create_single_result_widget 함수를 이 코드로 통째로 교체하세요]
    def create_single_result_widget(self, result_data, index):
        frame = QFrame(); 
        frame.result_data = result_data
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setLineWidth(1) 
        layout = QVBoxLayout(frame)
        top_layout = QHBoxLayout()
        notice_info_label = QLabel(f"<b>#{index+1} | 공고:</b> {result_data.get('gongo_title', '없음')}")
        top_layout.addWidget(notice_info_label)
        top_layout.addStretch(1)

        # [핵심] 수정 버튼 추가
        edit_button = QPushButton("✏️ 수정")
        # lambda의 인자로 result_data와 frame 위젯 자체를 넘겨줌
        edit_button.clicked.connect(lambda _, r=result_data, w=frame: self.edit_result(r, w))
        top_layout.addWidget(edit_button)

        copy_button = QPushButton("엑셀에 안전 복사")
        report_table = QTableWidget()
        copy_button.clicked.connect(lambda: self.start_guided_copy(report_table, index))
        
        delete_button = QPushButton("X")
        delete_button.setFixedWidth(30)
        delete_button.clicked.connect(lambda: self.delete_single_result(frame))

        top_layout.addWidget(copy_button)
        top_layout.addWidget(delete_button)
        layout.addLayout(top_layout)
        
        self.populate_report_table(report_table, result_data)
        layout.addWidget(report_table)
        
        status_label = QLabel()
        status_label.setStyleSheet("color: blue; font-size: 11px; padding-left: 5px;")
        credit_applied = any(d['business_score_details'].get('basis') == '신용평가' for d in result_data.get('company_details', []))
        if credit_applied:
            status_label.setText("<b>(*) 일부 경영점수는 신용평가 기준으로 산정되었습니다.</b>")
        layout.addWidget(status_label)
        
        return frame

     # [populate_report_table 함수를 이 코드로 통째로 교체하세요]
    def populate_report_table(self, table, result_data):
        # --- 1. 테이블 기본 설정 ---
        table.clear()
        table.setColumnCount(32) 
        table.setRowCount(3)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)
        
        # [핵심] '업체명' 열(0~5)의 너비를 150으로, 나머지는 60으로 설정
        for i in range(6):
            table.setColumnWidth(i, 150) # 기존 100 -> 150으로 대폭 증가
        for i in range(6, 32):
            table.setColumnWidth(i, 60) # 나머지는 60 유지
            
        for i in range(3):
            table.setRowHeight(i, 28)
        table.setFixedHeight(table.horizontalHeader().height() + table.rowHeight(0) * 3)

        # --- 2. 헤더 생성 (기존과 동일) ---
        self.merge_and_set_item(table, 0, 0, 1, 6, "업체명")
        self.merge_and_set_item(table, 0, 6, 1, 7, "지분")
        self.merge_and_set_item(table, 0, 13, 1, 6, "경영상태")
        self.merge_and_set_item(table, 0, 19, 1, 7, "시공실적")
        self.merge_and_set_item(table, 0, 26, 1, 6, "시공능력") 

        headers2_base = ["대표사", "구성원1", "구성원2", "구성원3", "구성원4", "비고", "대표사", "구성원1", "구성원2", "구성원3", "구성원4", "합산지분", "가점", "대표사", "구성원1", "구성원2", "구성원3", "구성원4", "경영(15)", "대표사", "구성원1", "구성원2", "구성원3", "구성원4", "실적비율", "실적점수"]
        headers2_sipyung = ["시공능력 대표사", "시공능력 구성사1", "시공능력 구성사2", "시공능력 구성사3", "시공능력 구성사4", "시공능력+시공비율"]
        headers2 = headers2_base + headers2_sipyung
        for c, h in enumerate(headers2):
            self.merge_and_set_item(table, 1, c, 1, 1, h)

        # --- 3. 데이터 채우기 (기존과 동일) ---
        details = result_data.get("company_details", [])
        data_row = 2
        for comp_detail in details:
            role = comp_detail.get('role'); col_offset = 0
            if role == "대표사": col_offset = 0
            elif role.startswith("구성사"):
                try: col_offset = int(role.split(' ')[1])
                except: continue
            business_score = comp_detail.get('business_score_details', {}).get('total', 0)
            performance_5y = comp_detail.get('performance_5y', 0)

            self.set_item(table, data_row, col_offset, comp_detail.get('name', ''))

            # ▼▼▼▼▼ [핵심 수정] 지분율을 100 곱해서 퍼센트로 표시 ▼▼▼▼▼
            share_decimal = comp_detail.get('share', 0)  # 1.0, 0.51 같은 소수점 값
            share_percent = share_decimal * 100.0  # 100, 51과 같은 퍼센트 값
            self.set_item(table, data_row, col_offset + 6, f"{share_percent:.1f}%")
            # ▲▲▲▲▲ [핵심 수정] 여기까지 ▲▲▲▲▲

            self.set_item(table, data_row, col_offset + 13, f"{business_score:.4f}")
            self.set_item(table, data_row, col_offset + 19, f"{performance_5y:,.0f}" if performance_5y else "0")
            sipyung_amount = utils.parse_amount(str(comp_detail['data'].get("시평", 0))) or 0
            self.set_item(table, data_row, col_offset + 26, f"{sipyung_amount:,.0f}" if sipyung_amount else "0")

        final_biz_score = result_data.get('final_business_score', 0)
        biz_score_item = self.set_item(table, data_row, 18, f"{final_biz_score:.4f}")
        if abs(final_biz_score - 15.0) > 0.001: biz_score_item.setForeground(QColor("red"))

        # --- 4. 스타일 적용 (기존과 동일) ---
        header_font = QFont(); header_font.setBold(True); header_bg_color = QColor("#F0F0F0")
        for r in range(2):
            for c in range(32):
                item = table.item(r, c)
                if item: item.setFont(header_font); item.setBackground(header_bg_color); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        for c in range(32):
            item = table.item(data_row, c)
            if item: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def set_item(self, table, r, c, text):
        item = QTableWidgetItem(str(text)); table.setItem(r, c, item); return item
    def merge_and_set_item(self, table, r, c, r_span, c_span, text):
        if r_span > 1 or c_span > 1: table.setSpan(r, c, r_span, c_span)
        self.set_item(table, r, c, text)
        
    # [start_guided_copy 함수를 이 코드로 통째로 교체하세요]
    def start_guided_copy(self, table, result_index):
        excel_start_row = 3 + result_index
        
        # [핵심 수정] 복사할 데이터 덩어리(chunks)에 '시공능력' 부분 추가
        chunks = [
            {"name": "업체명/지분", "cols": range(0, 11), "start_cell": f"A{excel_start_row}"}, 
            {"name": "경영상태", "cols": range(13, 18), "start_cell": f"N{excel_start_row}"}, 
            {"name": "시공실적", "cols": range(19, 24), "start_cell": f"T{excel_start_row}"},
            # 새로운 '시공능력' 덩어리 추가. 26번 열부터 31번 열까지.
            # 마지막 "시공능력+시공비율" 열은 비워둬야 하므로, 26~30번 열(5개)만 복사.
            {"name": "시공능력", "cols": range(26, 31), "start_cell": f"AA{excel_start_row}"} 
        ]
        
        copy_chunks_data = []
        for chunk in chunks:
            row_items = []
            for c in chunk["cols"]:
                item = table.item(2, c)
                row_items.append(item.text() if item else "")
            
            # 팝업창에 표시될 안내 메시지 개선
            instruction = f"<b>{chunk['name']}</b> 데이터를 엑셀의 <b>{chunk['start_cell']}</b> 셀에 붙여넣으세요."
            copy_chunks_data.append({"instruction": instruction, "data": "\t".join(row_items)})
            
        self.guided_popup = GuidedCopyPopup(copy_chunks_data, self)
        self.guided_popup.exec()

    # [run_pre_check 함수를 이 코드로 통째로 교체하세요]
    def run_pre_check(self):
        """'지분율 사전검토' 버튼 클릭 시 실행됩니다."""
        
        # [핵심 수정] 특정 텍스트 대신, 관련 UI 그룹박스가 활성화되어 있는지로 조건을 변경
        if not self.bid_amount_group.isVisible():
            # 이 메시지는 거의 표시될 일이 없지만, 만약을 대비한 방어 코드입니다.
            QMessageBox.information(self, "알림", "이 기능은 입찰금액 정보가 필요한 심사 기준에만 적용됩니다.")
            return

        # 2. 투찰금액이 있는지 확인
        tuchal_amount_text = self.tuchal_amount_label.text().replace("<b>", "").replace("</b>", "").replace(" 원", "").replace(",", "")
        tuchal_amount = utils.parse_amount(tuchal_amount_text) or 0
        if tuchal_amount <= 0:
            # 조달청은 '공고 정보'의 기초금액을 먼저 입력해야 함을 안내
            if self.mode == '조달청':
                QMessageBox.warning(self, "입력 필요", "'공고 정보'의 '기초금액'을 입력하여 투찰금액을 먼저 계산해주세요.")
            else: # 행안부
                QMessageBox.warning(self, "입력 필요", "'입찰금액 정보'의 '기초금액'을 입력하여 투찰금액을 먼저 계산해주세요.")
            return
            
        # 3. 참여 업체 정보 수집
        companies_data = [info for i, info in self.company_data_map.items() if info and info['data'] and info.get('share', 0) > 0]
        if not companies_data:
            QMessageBox.warning(self, "입력 필요", "검토할 업체를 먼저 선택하고 지분율을 입력해주세요.")
            return

        if not self.check_regional_requirements(companies_data):
            return  # 사용자가 '아니오'를 누르면 여기서 중단

        # 4. 실제 계산 로직 호출
        results = calculation_logic.check_share_limit(companies_data, tuchal_amount)
        
        # 5. 통과 여부 상태 업데이트
        if any(res['is_problem'] for res in results):
            self.pre_check_passed = False
        else:
            self.pre_check_passed = True
            QMessageBox.information(self, "사전검토 통과", "모든 업체의 지분율이 참여 가능 한도 내에 있습니다.")
        
        # 6. 결과 팝업창 표시
        popup = ShareCheckPopup(results, self)
        popup.exec()

    def show_context_menu(self, pos):
        """테이블에서 우클릭 시 컨텍스트 메뉴를 표시합니다."""
        item = self.tree.itemAt(pos)
        if not item:
            return  # 빈 공간을 클릭하면 메뉴를 띄우지 않음

        row_index = item.row()
        # 이미 비어있는 행에는 '제거' 메뉴를 보여줄 필요 없음
        if not self.company_data_map[row_index]['data']:
            return

        menu = QMenu()
        remove_action = menu.addAction("선택한 업체 제거")
        
        # '제거' 액션을 클릭하면 remove_selected_company 함수를 실행
        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        
        if action == remove_action:
            self.remove_selected_company(row_index)

    # [remove_selected_company 함수를 이 코드로 통째로 교체하세요]
    def remove_selected_company(self, row_index, silent=False):
        """
        선택된 행의 업체 정보를 초기화합니다.
        silent=True이면, 완료 메시지를 띄우지 않습니다.
        """
        # 1. UI 테이블의 내용을 초기 상태로 되돌립니다.
        self.tree.blockSignals(True) # itemChanged 시그널이 불필요하게 실행되는 것을 방지
        
        self.tree.setItem(row_index, 1, QTableWidgetItem("[더블클릭하여 업체 선택]"))
        self.tree.setItem(row_index, 2, QTableWidgetItem("")) # 지역
        self.tree.setItem(row_index, 3, QTableWidgetItem("")) # 5년실적
        self.tree.setItem(row_index, 4, QTableWidgetItem("0"))  # 지분율
        
        self.tree.blockSignals(False)

        # 2. 내부 데이터 저장소(map)의 정보도 초기화합니다.
        self.company_data_map[row_index]['data'] = None
        self.company_data_map[row_index]['share'] = 0
        self.company_data_map[row_index]['source_type'] = None

        # 3. 컨소시엄 구성이 변경되었으므로, 사전검토 상태를 리셋합니다.
        self.pre_check_passed = False

        # 4. silent 모드가 아닐 때만 완료 메시지를 표시합니다.
        if not silent:
            QMessageBox.information(self, "알림", f"{row_index + 1}번째 행의 업체 정보가 초기화되었습니다.")

    def generate_consortium_messages(self):
        """'협정 문자 일괄 생성' 버튼 클릭 시, 모든 결과에 대한 문자를 생성합니다."""
        if not self.result_widgets:
            QMessageBox.warning(self, "알림", "먼저 '결과 표 추가' 버튼으로 계산 결과를 추가해주세요.")
            return

        all_messages = []
        for result_widget in self.result_widgets:
            if not hasattr(result_widget, 'result_data'): continue

            result_data = result_widget.result_data

            gongo_no = result_data.get('gongo_no', 'N/A')
            gongo_title = result_data.get('gongo_title', 'N/A')

            message_parts = [f"공고번호: {gongo_no}", f"공고명: {gongo_title}", ""]

            details = result_data.get("company_details", [])

            for comp_detail in details:
                name = comp_detail.get('name', 'N/A')

                # ▼▼▼▼▼ [핵심 수정] 지분율을 100 곱해서 퍼센트로 표시 ▼▼▼▼▼
                share_decimal = comp_detail.get('share', 0)  # 0.51과 같은 소수점 값
                share_percent = share_decimal * 100.0  # 51과 같은 퍼센트 값
                line = f"{name} {'%g' % share_percent}%"
                # ▲▲▲▲▲ [핵심 수정] 여기까지 ▲▲▲▲▲

                role = comp_detail.get('role', '구성사')
                if role != "대표사":
                    biz_no = comp_detail.get('data', {}).get('사업자번호', '번호없음')
                    line += f" [{biz_no}]"
                message_parts.append(line)

            message_parts.append("")

            if len(details) == 1:
                message_parts.append("입찰참여 부탁드립니다")
            else:
                message_parts.append("협정 부탁드립니다")

            all_messages.append("\n".join(message_parts))

        if not all_messages:
            QMessageBox.warning(self, "오류", "메시지를 생성할 유효한 결과가 없습니다.")
            return

        final_text = "\n\n---------------------\n\n".join(all_messages)

        popup = TextDisplayPopup("협정 안내 문자 (전체 복사)", final_text, self)
        popup.exec()

    # [클래스 내부에 새로운 함수 2개를 추가하세요]
    def open_api_popup(self):
        # ApiPopup을 생성하고, gongo_selected 시그널을 fill_gongo_data 슬롯에 연결
        self.api_popup = ApiPopup(self)
        self.api_popup.gongo_selected.connect(self.fill_gongo_data)
        self.api_popup.exec()


    # [fill_gongo_data 함수를 이 코드로 통째로 교체하세요]
    def fill_gongo_data(self, gongo_data):
        # 1. API 데이터에서 필요한 모든 값을 안전하게 추출합니다.
        self.gongo_no_entry.setText(f"{gongo_data.get('bidNtceNo', '')}-{gongo_data.get('bidNtceOrd', '')}")
        self.gongo_title_entry.setText(f"{gongo_data.get('bidNtceNm', '')}")
        
        estimation_price_str = gongo_data.get('presmptPrce', '0')
        cnstty_name = gongo_data.get('mainCnsttyNm', '')
        rgst_dt_str = gongo_data.get('rgstDt', '')
        
        # 조달청 기초금액(배정예산) 값을 'bdgtAmt' 또는 'bssamt' 키로 가져옴
        base_price_str = gongo_data.get('bdgtAmt', gongo_data.get('bssamt', '0'))

        # 2. 추출한 데이터로 UI 위젯의 값을 채웁니다.
        # 추정가격 설정
        try:
            price_val = int(float(estimation_price_str))
            self.estimation_price_entry.setText(f"{price_val:,}")
        except (ValueError, TypeError):
            self.estimation_price_entry.setText(estimation_price_str)
                
        # 공고일 설정
        if rgst_dt_str:
            date_part = rgst_dt_str.split(' ')[0]
            q_date = QDate.fromString(date_part, "yyyy-MM-dd")
            if q_date.isValid():
                self.announcement_date_edit.setDate(q_date)

        # 분야 자동 선택
        if "전기" in cnstty_name: self.gongo_field_combo.setCurrentText("전기")
        elif "정보통신" in cnstty_name: self.gongo_field_combo.setCurrentText("통신")
        elif "소방" in cnstty_name: self.gongo_field_combo.setCurrentText("소방")
        else: self.gongo_field_combo.setCurrentText("기타")
        
        # [핵심] '기초금액' 자동 입력 시, 조달청의 올바른 위젯 이름인 'notice_base_amount_entry'를 사용
        if base_price_str:
            try:
                base_val = int(float(base_price_str))
                self.notice_base_amount_entry.setText(f"{base_val:,}")
            except (ValueError, TypeError):
                self.notice_base_amount_entry.setText(base_price_str)
                
        QMessageBox.information(self, "정보 입력 완료", "API 공고 정보가 자동으로 입력되었습니다.")


            # [ConsortiumViewHaeng 클래스 내부에 이 함수를 통째로 추가하세요]
    def edit_result(self, result_data, widget_to_edit):
        reply = QMessageBox.question(self, "결과 수정", 
                                    "이 결과를 상단 입력창으로 불러와 수정하시겠습니까?\n"
                                    "수정 후 '결과 표 추가' 버튼을 다시 누르면 이 표가 업데이트됩니다.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return

        # 1. 공고 정보 불러오기 (result_data에 저장된 값을 사용)
        self.gongo_title_entry.setText(result_data.get('gongo_title', ''))
        self.gongo_no_entry.setText(result_data.get('gongo_no', ''))
        # 다른 공고 정보(추정가격, 공고일 등)는 result_data에 없으므로,
        # 사용자가 다시 설정해야 합니다. 이 부분은 현재 로직을 유지합니다.
        
        # 2. 업체 구성 불러오기
        # 먼저 현재 입력 테이블 초기화
        for i in range(self.tree.rowCount()):
            self.remove_selected_company(i, silent=True)
            
        details = result_data.get("company_details", [])
        for comp_detail in details:
            role = comp_detail.get('role')
            # 역할(대표사/구성사)에 따라 테이블의 행 인덱스를 결정
            row_index = 0 
            if role.startswith("구성사"):
                try:
                    row_index = int(role.split(' ')[1])
                except (ValueError, IndexError):
                    continue
            
            # 테이블의 해당 행에 업체 정보를 다시 채워넣음
            self.tree.blockSignals(True)
            self.company_data_map[row_index]['data'] = comp_detail['data']
            self.company_data_map[row_index]['share'] = comp_detail['share']
            company_name = comp_detail.get("name", "")
            region = comp_detail['data'].get("지역", "")
            perf_5y = utils.parse_amount(comp_detail['data'].get("5년 실적"))
            self.tree.setItem(row_index, 1, QTableWidgetItem(company_name))
            self.tree.setItem(row_index, 2, QTableWidgetItem(region))
            self.tree.setItem(row_index, 3, QTableWidgetItem(f"{perf_5y:,.0f}" if perf_5y is not None else "0"))
            self.tree.setItem(row_index, 4, QTableWidgetItem(str(comp_detail['share'])))
            self.tree.blockSignals(False)

        # 3. 기존 결과 위젯 삭제
        self._remove_widget_from_list(widget_to_edit)
        
        QMessageBox.information(self, "불러오기 완료", "선택한 결과가 상단 입력창에 로드되었습니다.\n수정 후 '결과 표 추가' 버튼을 눌러주세요.")



            # [ConsortiumViewHaeng 클래스 내부에 이 함수를 통째로 추가하세요]
    def _remove_widget_from_list(self, widget_to_delete):
        """확인창 없이 위젯을 화면과 리스트에서 제거합니다."""
        widget_to_delete.deleteLater()
        if widget_to_delete in self.result_widgets:
            self.result_widgets.remove(widget_to_delete)


    def check_regional_requirements(self, companies_data):
        """지역제한 및 의무비율을 검사하고, 미충족 시 사용자에게 계속 진행할지 묻습니다."""
        region_limit = self.region_limit_combo.currentText()
        duty_ratio_str = self.duty_ratio_entry.text().strip()

        if region_limit != "전체" and duty_ratio_str:
            try:
                duty_ratio = float(duty_ratio_str)  # 사용자가 입력한 의무비율 (예: 49.0)
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "'의무비율'에는 숫자만 입력해주세요.")
                return False

            # 지역사 지분 합계 계산 (결과는 0.49와 같은 소수)
            region_share_sum_decimal = sum(
                comp.get('share', 0) for comp in companies_data
                if region_limit in comp.get('data', {}).get('지역', '')
            )

            # ▼▼▼▼▼ [핵심 수정] ▼▼▼▼▼
            # 비교 및 표시를 위해 소수점 합계를 퍼센트(%)로 변환
            region_share_sum_percent = region_share_sum_decimal * 100.0
            # ▲▲▲▲▲ [핵심 수정] ▲▲▲▲▲

            # 의무비율 미달 시 (49.0 < 49.0 -> False)
            if region_share_sum_percent < duty_ratio:
                reply = QMessageBox.question(self, "의무 비율 경고",
                                             # 경고창에 올바른 퍼센트 값을 표시
                                             f"필수 지역 '{region_limit}' 업체의 지분 합계가 {region_share_sum_percent:.2f}%입니다.\n"
                                             f"의무 비율({duty_ratio}%)에 미달합니다.\n\n"
                                             "감점을 감수하고 계속 진행하시겠습니까?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.No)

                if reply == QMessageBox.StandardButton.No:
                    return False

        return True