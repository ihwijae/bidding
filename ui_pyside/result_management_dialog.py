# ui_pyside/result_management_dialog.py

import os
import json
import copy
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QHeaderView, QSplitter, QLabel, QMessageBox,
                               QInputDialog)
from PySide6.QtCore import Qt, Signal
from .load_consortium_popup import LoadConsortiumPopup
from PySide6.QtWidgets import QFrame # QFrame 추가
from .text_display_popup import TextDisplayPopup
from consortium_manager import ConsortiumManagerDialog
import search_logic # search_logic 추가
import re

class ResultManagementDialog(QDialog):
    # 변경된 결과 목록을 메인 윈도우로 다시 전달하기 위한 시그널
    results_updated = Signal(list)

    def __init__(self, result_widgets, controller, parent=None):
        super().__init__(parent)
        self.result_widgets = result_widgets  # 메인 윈도우의 결과 목록을 복사해 옴
        self.controller = controller  # 메인 윈도우의 기능(엑셀 저장 등)을 호출하기 위함

        self.setWindowTitle("협정 결과 관리")
        self.setMinimumSize(1200, 600)



        # UI 설정
        self.setup_ui()
        # 데이터 채우기
        self.populate_consortium_list()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. 상단 툴바
        toolbar_layout = QHBoxLayout()
        self.save_button = QPushButton("💾 현재 목록 저장")
        self.generate_messages_button = QPushButton("✉️ 협정 문자 생성")
        self.excel_export_button = QPushButton("📊 엑셀로 내보내기")
        toolbar_layout.addWidget(self.save_button)
        toolbar_layout.addWidget(self.generate_messages_button)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.excel_export_button)
        main_layout.addLayout(toolbar_layout)

        # 2. 메인 컨텐츠 (좌/우 분할)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 2-1. 좌측 패널 (컨소시엄 목록)
        left_panel = QGroupBox("컨소시엄 목록")
        left_layout = QVBoxLayout(left_panel)
        self.consortium_list_table = QTableWidget()
        self.consortium_list_table.setColumnCount(4)
        self.consortium_list_table.setHorizontalHeaderLabels(["No.", "대표사", "구성사 수", "종합점수"])
        self.consortium_list_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.consortium_list_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.consortium_list_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        list_action_layout = QHBoxLayout()
        self.review_button = QPushButton("🔍 상세 검토")
        self.detailed_edit_button = QPushButton("📝 협정 상세 수정")
        self.move_up_button = QPushButton("▲ 위로")
        self.move_down_button = QPushButton("▼ 아래로")
        self.duplicate_button = QPushButton("📄 선택 복제")
        self.delete_button = QPushButton("❌ 선택 삭제")
        list_action_layout.addStretch(1)
        list_action_layout.addWidget(self.review_button)
        list_action_layout.addWidget(self.detailed_edit_button)# ▼▼▼▼▼ [추가] ▼▼▼▼▼
        list_action_layout.addWidget(self.move_up_button)
        list_action_layout.addWidget(self.move_down_button)
        list_action_layout.addWidget(self.duplicate_button)
        list_action_layout.addWidget(self.delete_button)

        left_layout.addWidget(self.consortium_list_table)
        left_layout.addLayout(list_action_layout)

        # 2-2. 우측 패널 (상세 정보)
        right_panel = QGroupBox("선택한 컨소시엄 상세정보")
        right_layout = QVBoxLayout(right_panel)
        self.detail_title_label = QLabel("← 왼쪽 목록에서 협정을 선택하세요.")
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(5)
        self.detail_table.setHorizontalHeaderLabels(["구분", "업체명", "지분율(%)", "경영점수", "5년실적"])
        self.detail_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        right_layout.addWidget(self.detail_title_label)
        right_layout.addWidget(self.detail_table)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 680])
        main_layout.addWidget(splitter)

        # 3. 하단 닫기 버튼
        self.close_button = QPushButton("닫기")
        main_layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignRight)

        # 4. 시그널 연결
        self.consortium_list_table.itemSelectionChanged.connect(self.update_detail_view)
        self.detailed_edit_button.clicked.connect(self._open_consortium_editor)
        self.close_button.clicked.connect(self.accept)
        self.delete_button.clicked.connect(self.delete_selected_consortium)
        self.review_button.clicked.connect(self.open_review_for_selected)
        self.duplicate_button.clicked.connect(self.duplicate_selected_consortium)
        self.move_up_button.clicked.connect(self.move_consortium_up)
        self.move_down_button.clicked.connect(self.move_consortium_down)
        self.excel_export_button.clicked.connect(self.controller.generate_excel_report)
        self.generate_messages_button.clicked.connect(self.generate_consortium_messages)
        self.save_button.clicked.connect(self.save_consortiums_list)

    def populate_consortium_list(self):
        """좌측 목록 테이블을 현재 데이터로 채웁니다."""
        self.consortium_list_table.setRowCount(len(self.result_widgets))
        for i, widget in enumerate(self.result_widgets):
            data = widget.result_data
            details = data.get("company_details", [])
            lead_company = details[0].get("name", "N/A") if details else "N/A"
            num_members = len(details)
            total_score = data.get("expected_score", 0)

            self.consortium_list_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.consortium_list_table.setItem(i, 1, QTableWidgetItem(lead_company))
            self.consortium_list_table.setItem(i, 2, QTableWidgetItem(f"{num_members} 개사"))
            self.consortium_list_table.setItem(i, 3, QTableWidgetItem(f"{total_score:.4f}"))
        self.consortium_list_table.resizeColumnsToContents()

    def update_detail_view(self):
        """선택된 컨소시엄의 상세 정보를 우측에 표시합니다."""
        selected_rows = self.consortium_list_table.selectionModel().selectedRows()
        if not selected_rows:
            self.detail_title_label.setText("← 왼쪽 목록에서 협정을 선택하세요.")
            self.detail_table.setRowCount(0)
            return

        selected_row = selected_rows[0].row()
        data = self.result_widgets[selected_row].result_data
        details = data.get("company_details", [])

        self.detail_title_label.setText(f"<b>No. {selected_row + 1} 상세정보</b> | {data.get('gongo_title', '')}")
        self.detail_table.setRowCount(len(details))

        for i, comp in enumerate(details):
            share_percent = comp.get('share', 0) * 100.0
            self.detail_table.setItem(i, 0, QTableWidgetItem(comp.get('role', '')))
            self.detail_table.setItem(i, 1, QTableWidgetItem(comp.get('name', '')))
            self.detail_table.setItem(i, 2, QTableWidgetItem(f"{share_percent:.2f}%"))
            self.detail_table.setItem(i, 3,
                                      QTableWidgetItem(f"{comp.get('business_score_details', {}).get('total', 0):.4f}"))
            self.detail_table.setItem(i, 4, QTableWidgetItem(f"{comp.get('performance_5y', 0):,}"))
        self.detail_table.resizeColumnsToContents()

    def delete_selected_consortium(self):
        selected_rows = self.consortium_list_table.selectionModel().selectedRows()
        if not selected_rows: return

        reply = QMessageBox.question(self, "삭제 확인", "선택한 협정 결과를 목록에서 삭제하시겠습니까?")
        if reply == QMessageBox.StandardButton.Yes:
            row_to_delete = selected_rows[0].row()
            del self.result_widgets[row_to_delete]
            self.populate_consortium_list()
            self.update_detail_view()

    def duplicate_selected_consortium(self):
        selected_rows = self.consortium_list_table.selectionModel().selectedRows()
        if not selected_rows: return

        row_to_copy = selected_rows[0].row()
        widget_to_copy = self.result_widgets[row_to_copy]

        # 깊은 복사를 통해 완전한 사본 생성
        new_widget = copy.deepcopy(widget_to_copy)

        self.result_widgets.insert(row_to_copy + 1, new_widget)
        self.populate_consortium_list()

    def move_consortium_up(self):
        selected_rows = self.consortium_list_table.selectionModel().selectedRows()
        if not selected_rows: return

        row = selected_rows[0].row()
        if row > 0:
            self.result_widgets.insert(row - 1, self.result_widgets.pop(row))
            self.populate_consortium_list()
            self.consortium_list_table.selectRow(row - 1)

    def move_consortium_down(self):
        selected_rows = self.consortium_list_table.selectionModel().selectedRows()
        if not selected_rows: return

        row = selected_rows[0].row()
        if row < len(self.result_widgets) - 1:
            self.result_widgets.insert(row + 1, self.result_widgets.pop(row))
            self.populate_consortium_list()
            self.consortium_list_table.selectRow(row + 1)

    def accept(self):
        # 창이 닫힐 때, 변경된 목록을 메인 윈도우에 알림
        self.results_updated.emit(self.result_widgets)
        super().accept()

    def open_review_for_selected(self):
        """선택한 협정의 상세 검토창(review_dialog)을 엽니다."""
        selected_rows = self.consortium_list_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "먼저 목록에서 검토할 협정을 선택하세요.")
            return

        selected_row = selected_rows[0].row()
        result_data = self.result_widgets[selected_row].result_data

        # 기존의 ReviewDialogPyside 클래스를 재사용
        # .review_dialog import 문이 파일 상단에 필요할 수 있습니다.
        from .review_dialog import ReviewDialogPyside
        dialog = ReviewDialogPyside(result_data, self)
        dialog.exec()

        # result_management_dialog.py 클래스 내부

        # result_management_dialog.py 클래스 내부

    def save_consortiums_list(self):
        """현재 목록에 있는 협정들을 '이름.json' 파일 하나로 저장합니다."""
        if not self.result_widgets:
            QMessageBox.warning(self, "알림", "저장할 협정 결과가 없습니다.")
            return

        save_name, ok = QInputDialog.getText(self, "협정 파일 저장", "저장할 파일 이름을 입력하세요:")
        if not ok or not save_name.strip():
            return

        safe_filename = "".join(c for c in save_name if c not in r'<>:"/\|?*') + ".json"

        current_mode = self.controller.mode
        data_folder = os.path.join("saved_data", current_mode)
        os.makedirs(data_folder, exist_ok=True)
        file_path = os.path.join(data_folder, safe_filename)

        if os.path.exists(file_path):
            reply = QMessageBox.question(self, "덮어쓰기 확인", f"'{safe_filename}' 파일이 이미 있습니다. 덮어쓰시겠습니까?")
            if reply == QMessageBox.StandardButton.No:
                return

        region_limit = self.controller.region_limit_combo.currentText()
        project_type = self.controller.gongo_field_combo.currentText()

        data_to_save = {
            "saved_name": save_name,
            "saved_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "region_limit": region_limit,
            "project_type": project_type,
            "consortiums": [widget.result_data for widget in self.result_widgets]
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "저장 완료", f"'{safe_filename}' 이름으로 협정을 저장했습니다.")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류가 발생했습니다:\n{e}")


    def load_consortiums_list(self):
        """저장된 협정 목록(result_data)을 불러와 목록에 추가합니다."""
        popup = LoadConsortiumPopup(self.controller.mode, self)
        if not popup.exec():
            return

        selected_data = popup.get_selected_data()
        if not selected_data:
            return

        # ▼▼▼▼▼ [핵심 수정] 저장된 result_data를 바로 위젯으로 만들어 추가 ▼▼▼▼▼
        new_widgets = []
        # 키 이름을 consortiums -> saved_results로 변경
        for result_data in selected_data.get("saved_results", []):
            widget = QFrame()
            widget.result_data = result_data
            new_widgets.append(widget)

        self.result_widgets.extend(new_widgets)
        self.populate_consortium_list()
        self.update_summary_display()  # 요약 창도 업데이트
        QMessageBox.information(self, "불러오기 완료", f"'{selected_data.get('saved_name')}' 협정을 불러왔습니다.")
        # ▲▲▲▲▲ [핵심 수정] 여기까지 ▲▲▲▲▲

    def generate_consortium_messages(self):
        """요청된 최종 양식에 맞춰 협정 안내 문자를 생성합니다."""
        if not self.result_widgets:
            QMessageBox.warning(self, "알림", "먼저 '결과 표 추가' 버튼으로 계산 결과를 추가해주세요.")
            return

        all_messages_parts = []
        for result_widget in self.result_widgets:
            if not hasattr(result_widget, 'result_data'): continue

            result_data = result_widget.result_data
            gongo_no = result_data.get('gongo_no', 'N/A')
            gongo_title = result_data.get('gongo_title', 'N/A')

            message_parts = [f"{gongo_no} {gongo_title}", ""]

            details = result_data.get("company_details", [])

            for index, comp_detail in enumerate(details):
                name = comp_detail.get('name', 'N/A')
                share_decimal = comp_detail.get('share', 0)
                share_percent = share_decimal * 100.0

                line = f"{name} {'%g' % share_percent}%"
                if index < len(details) - 1:
                    line += ","

                role = comp_detail.get('role', '구성사')
                if role != "대표사":
                    biz_no = comp_detail.get('data', {}).get('사업자번호', '번호없음')
                    line += f" [{biz_no}]"
                message_parts.append(line)

            message_parts.append("")

            # [수정] 단독/협정에 따라 다른 마무리 문구를 각 메시지 블록에 추가
            if len(details) == 1:
                message_parts.append("입찰참여 부탁드립니다")
            else:
                message_parts.append("협정 부탁드립니다")

            all_messages_parts.append("\n".join(message_parts))

        # [수정] 여러 메시지를 구분선으로 연결
        final_text = "\n\n---------------------\n\n".join(all_messages_parts)

        popup = TextDisplayPopup("협정 안내 문자 (전체 복사)", final_text, self)
        popup.exec()

    def _open_consortium_editor(self):
        """선택한 협정의 상세 편집창(ConsortiumManagerDialog)을 엽니다."""
        selected_rows = self.consortium_list_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "선택 오류", "먼저 목록에서 수정할 협정을 선택하세요.")
            return

        # [핵심] 현재는 목록 전체가 아니라 선택된 '하나'의 협정만 수정하도록 구현
        selected_row = selected_rows[0].row()
        widget_to_edit = self.result_widgets[selected_row]

        # ConsortiumManagerDialog가 요구하는 데이터 형식으로 변환
        # (컨소시엄 목록 안에 하나의 컨소시엄만 넣어서 전달)
        initial_data_for_dialog = [widget_to_edit.result_data['company_details']]

        # 수정 다이얼로그를 현재 데이터로 엽니다.
        dialog = ConsortiumManagerDialog(initial_data_for_dialog, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 수정된 최신 데이터를 받아옵니다.
            updated_data = dialog.get_results()

            # 수정된 협정 정보 (보통 첫 번째 항목)를 기존 데이터에 덮어씁니다.
            if updated_data:
                widget_to_edit.result_data['company_details'] = updated_data[0]

            # 목록과 상세 정보 화면을 새로고침합니다.
            self.populate_consortium_list()
            self.update_detail_view()
            QMessageBox.information(self, "수정 완료", "협정 정보가 성공적으로 수정되었습니다.")