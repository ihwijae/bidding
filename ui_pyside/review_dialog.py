# ui_pyside/review_dialog.py
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QWidget,
                               QLabel, QFormLayout, QTextEdit, QGroupBox,
                               QScrollArea, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import utils

class ReviewDialogPyside(QDialog):
    def __init__(self, result_data, parent=None):
        super().__init__(parent)
        self.result_data = result_data

        # 1. result_data에서 공고 정보 추출
        gongo_no = self.result_data.get('gongo_no', '번호 없음')
        gongo_title = self.result_data.get('gongo_title', '제목 없음')

        # 2. 창 제목을 새로운 형식으로 설정
        self.setWindowTitle(f"[{gongo_no}] {gongo_title} - 적격심사 검토 결과")

        self.setMinimumSize(1200, 700)
        
        self.setup_ui()
        self.populate_data()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)

        left_groupbox = QGroupBox("참여 업체 상세 정보")
        left_main_layout = QVBoxLayout(left_groupbox)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.company_info_container = QWidget()
        self.company_info_layout = QVBoxLayout(self.company_info_container)
        self.company_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.company_info_container)
        left_main_layout.addWidget(scroll_area)
        
        right_panel = QGroupBox("검토 결과 요약")
        right_layout = QVBoxLayout(right_panel)

        # ▼▼▼▼▼ [추가] 계산 기준 정보를 표시할 그룹박스 ▼▼▼▼▼
        info_groupbox = QGroupBox("계산 기준 정보")
        self.info_layout = QFormLayout(info_groupbox)
        self.info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(info_groupbox)
        # ▲▲▲▲▲ [추가] 여기까지 ▲▲▲▲▲

        score_form_layout = QFormLayout(); score_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.share_label = QLabel(); self.business_score_label = QLabel(); self.performance_score_label = QLabel()
        self.bidding_score_label = QLabel(); self.total_score_label = QLabel()
        bold_font = QFont(); bold_font.setBold(True); bold_font.setPointSize(12)
        self.total_score_label.setFont(bold_font); self.total_score_label.setStyleSheet("color: blue;")
        score_form_layout.addRow("<b>지분 합계:</b>", self.share_label)
        score_form_layout.addRow("<b>경영 점수:</b>", self.business_score_label)
        score_form_layout.addRow("<b>실적 점수:</b>", self.performance_score_label)
        score_form_layout.addRow("<b>입찰가격 점수:</b>", self.bidding_score_label)
        score_form_layout.addRow("<b>종합 점수 (최대 95점):</b>", self.total_score_label)
        
        solo_bid_layout = QVBoxLayout()
        solo_bid_layout.addWidget(QLabel("<b>개별 업체 단독입찰 검토</b>"))
        self.solo_bid_text = QTextEdit(); self.solo_bid_text.setReadOnly(True)
        self.solo_bid_text.setFont(QFont("맑은 고딕", 10)); self.solo_bid_text.setFixedHeight(80)
        solo_bid_layout.addWidget(self.solo_bid_text)

        sipyung_form_layout = QFormLayout(); sipyung_form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.sipyung_sum_label = QLabel(); self.sipyung_ratio_label = QLabel()
        sipyung_form_layout.addRow("<b>시평액 (단순합산):</b>", self.sipyung_sum_label)
        sipyung_form_layout.addRow("<b>시평액 (비율제):</b>", self.sipyung_ratio_label)

        deduction_layout = QVBoxLayout()
        deduction_layout.addWidget(QLabel("<b>주요 검토 사항 (감점 요인 등)</b>"))
        self.deduction_text = QTextEdit(); self.deduction_text.setReadOnly(True)
        self.deduction_text.setFont(QFont("맑은 고딕", 10)); deduction_layout.addWidget(self.deduction_text)

        right_layout.addLayout(score_form_layout)
        right_layout.addLayout(solo_bid_layout)
        right_layout.addLayout(sipyung_form_layout)
        right_layout.addLayout(deduction_layout)

        formula_groupbox = QGroupBox("상세 계산식")
        self.formula_layout = QVBoxLayout(formula_groupbox)
        right_layout.addWidget(formula_groupbox)

        main_layout.addWidget(left_groupbox, 2)
        main_layout.addWidget(right_panel, 1)

    def populate_data(self):
        self.populate_left_panel()
        self.populate_right_panel()

   # [create_company_card 함수를 이 코드로 통째로 교체하세요]
    def create_company_card(self, company_detail):
        role = company_detail.get('role', '구성사');
        name = company_detail.get('name', 'N/A')
        share_decimal = company_detail.get('share', 0)  # 0.49와 같은 소수점 값
        share_percent = share_decimal * 100.0  # 49.0과 같은 퍼센트 값

        company_data = company_detail.get('data', {})
        data_status = company_data.get('데이터상태', {})
        
        card = QGroupBox(f"{role} - {name} (지분: {share_percent}%)"); card.setFont(QFont("맑은 고딕", 11, QFont.Bold))
        card.setStyleSheet("QGroupBox { border: 1px solid #D5D8DC; border-radius: 5px; margin-top: 1ex; padding: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }")
        card_layout = QVBoxLayout(card)
        
        info_layout = QFormLayout(); info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        fields_to_show = ["대표자", "지역", "시평", "5년 실적", "부채비율", "유동비율", "신용평가"]
        for field in fields_to_show:
            value = company_data.get(field, ""); value_str = ""
            if field in ["시평", "5년 실적"]: parsed = utils.parse_amount(str(value)); value_str = f"{parsed:,.0f}" if parsed is not None else str(value)
            elif field in ["부채비율", "유동비율"]: value_str = f"{value:.2f}%" if isinstance(value, (int, float)) else str(value)
            else: value_str = str(value)
            info_layout.addRow(f"<b>{field}:</b>", QLabel(value_str))
        card_layout.addLayout(info_layout)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setFrameShadow(QFrame.Shadow.Sunken); card_layout.addWidget(line)
        
        score_layout = QFormLayout(); score_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        management_related_fields = ['부채비율', '유동비율']
        performance_related_fields = ['시평', '3년 실적', '5년 실적']

        is_management_data_valid = all(data_status.get(f, '미지정') == '최신' for f in management_related_fields)
        if not is_management_data_valid:
            score_layout.addRow(QLabel("<b style='color:red;'>[재무 데이터 최신 아님]</b>"))
        is_performance_data_valid = all(data_status.get(f, '미지정') == '최신' for f in performance_related_fields)
        if not is_performance_data_valid:
            score_layout.addRow(QLabel("<b style='color:red;'>[실적/시평 데이터 최신 아님]</b>"))

        score_details = company_detail.get('business_score_details', {}); 
        debt_score = score_details.get('debt_score', 0); current_score = score_details.get('current_score', 0)
        total_business_score = score_details.get('total', 0); credit_score = score_details.get('credit_score', 0)
        basis = score_details.get('basis', 'N/A'); credit_status = score_details.get('credit_valid', '자료없음')

        score_layout.addRow("부채 점수:", QLabel(f"{debt_score:.4f}"))
        score_layout.addRow("유동 점수:", QLabel(f"{current_score:.4f}"))
        ruleset = self.result_data.get('ruleset', {})
        if ruleset.get('use_duration_score', True): score_layout.addRow("기간 점수:", QLabel("구현 예정"))
        else: score_layout.addRow("기간 점수:", QLabel("해당 없음"))
        
        total_score_label = QLabel(f"<b>{total_business_score:.4f}</b>")
        if basis == "신용평가": total_score_label.setStyleSheet("color: green; font-weight: bold;")
        elif abs(total_business_score - 15.0) < 0.001: total_score_label.setStyleSheet("color: blue; font-weight: bold;")
        else: total_score_label.setStyleSheet("font-weight: bold;")
        score_layout.addRow("<b>경영 점수 (최종):</b>", total_score_label)
        
        status_text = ""
        if credit_status == "유효": status_text = f"{credit_score:.4f} 점 <span style='color:green; font-weight:bold;'>(유효)</span>"
        elif credit_status == "기간만료": status_text = f"<span style='color:red; font-weight:bold;'>기간만료</span>"
        elif credit_status == "형식오류": status_text = f"<span style='color:orange; font-weight:bold;'>형식오류</span>"
        else: status_text = f"<span style='color:gray; font-weight:bold;'>자료 없음</span>"
        credit_score_label = QLabel(status_text)
        score_layout.addRow("신용평가 점수:", credit_score_label)
        
        card_layout.addLayout(score_layout)
        return card

    def populate_left_panel(self):
        details = self.result_data.get("company_details", [])
        if not details: return
        for i in reversed(range(self.company_info_layout.count())): 
            widget = self.company_info_layout.itemAt(i).widget()
            if widget is not None: widget.setParent(None)
        for comp_detail in details:
            company_card = self.create_company_card(comp_detail)
            self.company_info_layout.addWidget(company_card)

    # [populate_right_panel 함수를 이 코드로 통째로 교체하세요]
    def populate_right_panel(self):

        total_share_decimal = sum(comp.get('share', 0) for comp in self.result_data.get("company_details", []))
        total_share_percent = total_share_decimal * 100.0
        final_business_score = self.result_data.get('final_business_score', 0)
        final_performance_score = self.result_data.get('final_performance_score', 0)
        
        self.share_label.setText(f"<b>{total_share_percent:.2f} %</b>")
        self.business_score_label.setText(f"{final_business_score:.4f} / 15.0")
        self.performance_score_label.setText(f"{final_performance_score:.4f} / 15.0")
        self.bidding_score_label.setText(f"{self.result_data.get('bid_score', 0)} / 65.0")
        self.total_score_label.setText(f"{self.result_data.get('expected_score', 0):.4f} / 95.0")
        
        sipyung_sum = sum(utils.parse_amount(str(comp['data'].get("시평", 0))) or 0 for comp in self.result_data.get("company_details", []))
        sipyung_ratio = sum((utils.parse_amount(str(comp['data'].get("시평", 0))) or 0) * (comp.get('share', 0) / 100.0) for comp in self.result_data.get("company_details", []))
        self.sipyung_sum_label.setText(f"{sipyung_sum:,.0f} 원")
        self.sipyung_ratio_label.setText(f"{sipyung_ratio:,.0f} 원")

        # --- 2. [신규] 계산 기준 정보 채우기 ---
        while self.info_layout.count():
            self.info_layout.takeAt(0).widget().deleteLater()

        ruleset = self.result_data.get('ruleset', {})
        price_data = self.result_data.get('price_data', {})
        base_key = ruleset.get("performance_base_key", "estimation_price")
        base_amount = price_data.get(base_key, 0)
        base_key_name = "기초금액" if base_key == "notice_base_amount" else "추정가격"

        self.info_layout.addRow(f"<b>적용 기준:</b>", QLabel(ruleset.get('name', '')))
        self.info_layout.addRow(f"<b>실적 기준금액 ({base_key_name}):</b>", QLabel(f"{base_amount:,.0f} 원"))

        # --- 3. [신규] 상세 계산식 채우기 ---
        while self.formula_layout.count():
            self.formula_layout.takeAt(0).widget().deleteLater()

        details = self.result_data.get("company_details", [])

        # 경영점수 계산식
        biz_parts = [
            f"({comp.get('business_score_details', {}).get('total', 0):.4f} × {comp.get('share', 0) * 100.0:.1f}%)" for
            comp in details]
        biz_formula = " + ".join(biz_parts)
        self.formula_layout.addWidget(QLabel(f"<b>- 경영점수:</b> {biz_formula} = <b>{final_business_score:.4f}</b>"))

        # 실적점수 계산식
        method = ruleset.get("performance_method")
        total_perf = self.result_data.get('total_weighted_performance', 0)

        if method == "ratio_table":
            perf_formula = f"(실적합계 {total_perf:,.0f} / 기준금액 {base_amount:,.0f}) × 100 = {self.result_data.get('performance_ratio', 0):.2f}%"
            self.formula_layout.addWidget(QLabel(f"<b>- 실적비율:</b> {perf_formula}"))
            self.formula_layout.addWidget(QLabel(
                f"<b>- 실적점수:</b> {self.result_data.get('performance_ratio', 0):.2f}% → <b>{final_performance_score:.4f}점</b> (점수표)"))
        elif method == "direct_formula_v1":
            params = ruleset.get("performance_params", {})
            multiplier = params.get("base_multiplier", 1.0)
            max_score = params.get("max_score", 15.0)
            perf_formula = f"({total_perf:,.0f} / ({base_amount:,.0f} × {multiplier})) × {max_score}"
            self.formula_layout.addWidget(
                QLabel(f"<b>- 실적점수:</b> {perf_formula} = <b>{final_performance_score:.4f}점</b>"))

        # --- 4. 기존 검토 사항 표시 (사용자 코드와 동일) ---
        
        solo_results = self.result_data.get("solo_bid_results", [])
        solo_bid_html_parts = []
        has_possible = False
        for result in solo_results:
            if result["possible"]:
                has_possible = True
                line = (f"<span style='color:orange;'><b>❗ ({result['role']}) {result['name']}: 단독입찰 가능</b> ({result['reason']})</span>")
            else:
                line = (f"<span style='color:gray;'>- ({result['role']}) {result['name']}: 단독입찰 불가 ({result['reason']})</span>")
            solo_bid_html_parts.append(line)
        if not solo_results: solo_bid_html_parts.append("<span style='color:gray;'>참여 업체 없음</span>")
        elif not has_possible: solo_bid_html_parts.insert(0, "<b style='color:green;'>✔ 모든 업체가 협정이 필요한 상태입니다. (정상)</b>")
        self.solo_bid_text.setHtml("<br>".join(solo_bid_html_parts))

        report_lines = []
        
        individual_sipyung = self.result_data.get("individual_sipyung_results", [])

        if individual_sipyung:
            all_passed = all(res["passed"] for res in individual_sipyung)
            if all_passed: report_lines.append("<b style='color:green;'>✔ 개별 시평액: 모든 업체가 지분율을 충족합니다.</b>")
            else: report_lines.append("<b style='color:red;'>❌ 개별 시평액: 시평액이 부족한 업체가 있습니다. (입찰 불가)</b>")
            for res in individual_sipyung:
                if res["passed"]: line = f"   └ <span style='color:green;'>✔ {res['name']}: 충족</span>"
                else: line = f"   └ <span style='color:red;'>❌ {res['name']}: 미충족</span>"
                report_lines.append(line)
                report_lines.append(f"      └ <span style='color:#555;'>{res['message']}</span>")

                # ▼▼▼▼▼ [수정] total_share 변수를 total_share_percent 로 변경 ▼▼▼▼▼
        if abs(total_share_percent - 100.0) < 0.01:
            report_lines.append("<span style='color:green;'><b>✔ 지분 합계:</b> 100% 충족</span>")
        else:
            report_lines.append(
                    f"<span style='color:red;'><b>❌ 지분 합계:</b> {total_share_percent:.2f}% (100% 미충족)</span>")

        if abs(final_business_score - 15.0) < 0.001: report_lines.append("<span style='color:green;'><b>✔ 경영 점수:</b> 15.0점 만점</span>")
        else:
            deduction = 15.0 - final_business_score
            report_lines.append(f"<span style='color:red;'><b>❌ 경영 점수:</b> 만점에서 -{deduction:.4f}점 감점</span>")
            for comp in self.result_data.get("company_details", []):
                if comp['business_score_details'].get('total', 15) < 15: report_lines.append(f"   └ <span style='color:#555;'>{comp['name']}: {comp['business_score_details']['total']:.4f}점 ({comp['business_score_details']['basis']})</span>")

        if abs(final_performance_score - 15.0) < 0.001: report_lines.append("<span style='color:green;'><b>✔ 실적 점수:</b> 15.0점 만점</span>")
        else:
            perf_ratio = self.result_data.get('performance_ratio', 0)
            report_lines.append(f"<span style='color:red;'><b>❌ 실적 점수:</b> {final_performance_score:.4f}점 (만점 아님)</span>")
            report_lines.append(f"   └ <span style='color:#555;'>실적 평가비율: {perf_ratio:.2f}%</span>")

        report_lines.append("<b>- 데이터 상태:</b>")
        management_outdated = [c['name'] for c in self.result_data.get("company_details", []) if any(c['data'].get('데이터상태', {}).get(f, '미지정') != '최신' for f in ['부채비율', '유동비율'])]
        performance_outdated = [c['name'] for c in self.result_data.get("company_details", []) if any(c['data'].get('데이터상태', {}).get(f, '미지정') != '최신' for f in ['시평', '3년 실적', '5년 실적'])]
        if not management_outdated: report_lines.append("<span style='color:green;'>   └ ✔ 재무 데이터 모두 최신</span>")
        else: report_lines.append(f"<span style='color:red;'>   └ ❌ 재무 데이터 갱신 필요: {', '.join(management_outdated)}</span>")
        if not performance_outdated: report_lines.append("<span style='color:green;'>   └ ✔ 실적/시평 데이터 모두 최신</span>")
        else: report_lines.append(f"<span style='color:red;'>   └ ❌ 실적/시평 데이터 갱신 필요: {', '.join(performance_outdated)}</span>")

        # [핵심] 누락되었던 시평액 제한 (컨소시엄 전체) 리포트 추가
        sipyung_result = self.result_data.get("sipyung_check_result", {})
        if sipyung_result and sipyung_result.get("message") != "시평액 제한 없음":
            if sipyung_result.get("passed"):
                report_lines.append(f"<span style='color:green;'><b>✔ 시평액 제한:</b> 충족</span>")
            else:
                report_lines.append(f"<span style='color:red;'><b>❌ 시평액 제한:</b> 미충족</span>")
            report_lines.append(f"   └ <span style='color:#555;'>{sipyung_result['message']}</span>")
                
        self.deduction_text.setHtml("<br><br>".join(report_lines))