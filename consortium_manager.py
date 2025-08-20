# consortium_manager.py

import sys
import pickle
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QGroupBox, QWidget,
    QLabel, QLineEdit, QDialogButtonBox, QMessageBox,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QTimer
from PySide6.QtGui import QDrag, QDoubleValidator, QPixmap, QFont
import calculation_logic
from ui_pyside.company_select_popup import CompanySelectPopupPyside


# ▼▼▼ 1. CompanyItemWidget 클래스 (지역업체 강조 기능 추가) ▼▼▼
class CompanyItemWidget(QWidget):
    delete_requested = Signal(QWidget)
    data_updated = Signal(object, dict)

    def __init__(self, company_data, is_regional=False, is_deletable=True):
        super().__init__()
        self.company_data = company_data
        self.is_editing = False
        self.drag_start_position = None

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # [핵심] is_regional 값에 따라 배경색과 hover 색상을 결정
        if is_regional:
            bg_color = "#fffbe6"  # 연한 노란색
            hover_color = "#fcf8e3"
        else:
            bg_color = "#ffffff"  # 흰색
            hover_color = "#f7f9fc"

        self.setStyleSheet(f"""
            CompanyItemWidget {{
                background-color: {bg_color};
                border-bottom: 1px solid #f0f0f0;
                border-radius: 0px;
            }}
            CompanyItemWidget:hover {{
                background-color: {hover_color};
            }}
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)

        self.name_label = QLabel(self.company_data.get('name', ''))
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.name_label.setStyleSheet("color: #2c3e50; border: none; background: transparent;")

        self.share_editor = QLineEdit()
        self.share_editor.setValidator(QDoubleValidator(0.00, 100.00, 2))
        self.share_editor.editingFinished.connect(self._finish_editing)
        self.share_editor.setMaximumWidth(60)
        self.share_editor.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.percent_label = QLabel("%")
        self.percent_label.setStyleSheet("color: #7f8c8d; border: none; background: transparent;")

        self._set_view_mode()
        main_layout.addWidget(self.name_label)
        main_layout.addStretch(1)
        main_layout.addWidget(self.share_editor)
        main_layout.addWidget(self.percent_label)

        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(22, 22)
        self.delete_button.setStyleSheet("""
                QPushButton {{
                    font-size: 14px; color: #95a5a6; background-color: transparent;
                    border: none; border-radius: 11px;
                }}
                QPushButton:hover {{
                    background-color: #e8eaed; color: #e74c3c;
                }}
            """)
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self))
        main_layout.addWidget(self.delete_button)

    # ... (mousePressEvent, mouseMoveEvent 등 다른 함수는 이전과 동일) ...
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.drag_start_position = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton): return
        if self.drag_start_position is None: return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance(): return
        drag = QDrag(self); mime_data = QMimeData(); encoded_data = pickle.dumps(self.company_data)
        mime_data.setData('application/x-company-data', encoded_data); drag.setMimeData(mime_data)
        pixmap = self.grab(); drag.setPixmap(pixmap); drag.setHotSpot(event.position().toPoint())
        if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.MoveAction: self.deleteLater()

    def _set_view_mode(self):
        share_value = self.company_data.get('share', 0) * 100
        self.share_editor.setText(f"{share_value:.2f}")
        self.share_editor.setReadOnly(True)
        self.share_editor.setStyleSheet(
            "color: #34495e; background-color: transparent; border: none; font-weight: bold;")

    def _set_edit_mode(self):
        self.share_editor.setReadOnly(False)
        self.share_editor.setStyleSheet(
            "color: #2980b9; background-color: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; font-weight: bold;")
        self.share_editor.selectAll();
        self.share_editor.setFocus()

    def mouseDoubleClickEvent(self, event):
        self.is_editing = True; self._set_edit_mode()

    def _finish_editing(self):
        if not self.is_editing: return
        try:
            new_share = float(self.share_editor.text()) / 100.0
            self.company_data['share'] = new_share
            self.data_updated.emit(self, self.company_data)
        except (ValueError, TypeError):
            pass
        self.is_editing = False;
        self._set_view_mode()


# ▼▼▼ 2. AddCompanyDialog 클래스 (이전과 동일) ▼▼▼
class AddCompanyDialog(QDialog):
    # ... (이전 코드와 동일, 변경 없음) ...
    def __init__(self, parent=None):
        super().__init__(parent);
        self.setWindowTitle("업체 추가");
        layout = QVBoxLayout(self)
        self.info_label = QLabel("추가할 업체명을 입력하세요 (예: 새로운건설 30%)");
        self.company_name_input = QLineEdit()
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.info_label);
        layout.addWidget(self.company_name_input);
        layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept);
        self.buttons.rejected.connect(self.reject)

    def get_company_info(self):
        name_text = self.company_name_input.text().strip()
        if name_text:
            parts = name_text.split();
            name = " ".join(parts[:-1]) if len(parts) > 1 else name_text
            share_str = parts[-1] if len(parts) > 1 else "0%";
            share = 0.0
            try:
                share = float(share_str.replace('%', '')) / 100.0
            except:
                pass
            return {'name': name, 'share': share, 'etc': '신규'}
        return None


# ▼▼▼ 3. DropTargetWidget 클래스 (이전과 동일) ▼▼▼
class DropTargetWidget(QWidget):
    # ... (이전 코드와 동일, 변경 없음) ...
    def __init__(self, parent_dialog, parent=None):
        super().__init__(parent)
        self.parent_dialog = parent_dialog
        self.setAcceptDrops(True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-company-data'): event.acceptProposedAction()

    def dropEvent(self, event):
        encoded_data = event.mimeData().data('application/x-company-data')
        company_data = pickle.loads(encoded_data)
        self.parent_dialog.add_company_to_layout(self.layout, company_data, event.position().toPoint())
        event.acceptProposedAction()


# ▼▼▼ 4. ConsortiumManagerDialog 클래스 (지역업체 강조 기능 추가) ▼▼▼
class ConsortiumManagerDialog(QDialog):
    def __init__(self, consortiums_data, region_limit, calculation_context, parent=None):
        super().__init__(parent)
        self.setWindowTitle("협정 결과 상세 편집")
        self.setMinimumSize(1000, 600)
        self.setFont(QFont("맑은 고딕", 9))
        self.region_limit = region_limit  # 지역제한 정보 저장
        self.setStyleSheet(parent.styleSheet() + """
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dfe4ea;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                margin-left: 10px;
            }
            QScrollArea { border: none; }
            QWidget#listContainer { background-color: #ffffff; }
        """)
        self.calculation_context = calculation_context  # 전달받은 문맥 정보 저장
        self.scoreboard_labels = []  # 미니 점수판 QLabel들을 저장할 리스트

        # ... (이하 __init__ 함수 구조는 이전과 동일) ...
        container_widget = QWidget()
        container_widget.setStyleSheet("background: transparent;")
        consortiums_area_layout = QHBoxLayout(container_widget)

        self.consortium_layouts = []

        for i, result_data in enumerate(consortiums_data):
            details_list = result_data.get('company_details', [])
            group_box = QGroupBox(f"협정 {chr(65 + i)}")
            group_box.setMinimumWidth(300)

            list_scroll_area = QScrollArea()
            list_scroll_area.setWidgetResizable(True)
            list_content_widget = DropTargetWidget(self)
            list_content_widget.setObjectName("listContainer")
            list_scroll_area.setWidget(list_content_widget)
            list_layout = list_content_widget.layout
            self.consortium_layouts.append(list_layout)

            scoreboard_label = QLabel("점수: 계산 중...")
            scoreboard_label.setStyleSheet("font-size: 8pt; color: #555; padding: 2px 5px; border-top: 1px solid #eee;")
            self.scoreboard_labels.append(scoreboard_label)

            group_main_layout = QVBoxLayout(group_box)
            group_main_layout.setContentsMargins(1, 15, 1, 1)
            group_main_layout.addWidget(list_scroll_area)
            group_main_layout.addWidget(scoreboard_label)
            consortiums_area_layout.addWidget(group_box)

            for company_data in details_list:
                self.add_company_to_layout(list_layout, company_data)


        consortiums_area_layout.addStretch(1)

        top_scroll_area = QScrollArea()
        top_scroll_area.setWidgetResizable(True)
        top_scroll_area.setWidget(container_widget)

        main_layout = QHBoxLayout()
        standby_group_box = QGroupBox("대기중인 업체")
        standby_scroll = QScrollArea()
        standby_scroll.setWidgetResizable(True)
        standby_content = DropTargetWidget(self)
        standby_content.setObjectName("listContainer")
        standby_scroll.setWidget(standby_content)
        self.standby_layout = standby_content.layout

        self.add_button = QPushButton("✚ 업체 추가")
        self.add_button.clicked.connect(self._handle_add_company)

        standby_main_layout = QVBoxLayout(standby_group_box)
        standby_main_layout.setContentsMargins(5, 15, 5, 5)
        standby_main_layout.addWidget(self.add_button)
        standby_main_layout.addWidget(standby_scroll)

        dialog_buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.setObjectName("saveButton")
        cancel_button.setObjectName("cancelButton")
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        dialog_buttons_layout.addStretch(1)
        dialog_buttons_layout.addWidget(save_button)
        dialog_buttons_layout.addWidget(cancel_button)

        main_layout.addWidget(top_scroll_area, 7)
        main_layout.addWidget(standby_group_box, 3)

        final_layout = QVBoxLayout(self)
        final_layout.addLayout(main_layout)
        final_layout.addLayout(dialog_buttons_layout)
        self.recalculate_and_refresh_all()

    def add_company_to_layout(self, layout, company_data, pos=None):
        company_region = company_data.get('data', {}).get('지역', '')
        is_regional = (self.calculation_context['region_limit'] != "전체" and self.calculation_context[
            'region_limit'] in company_region)

        # ▼▼▼ [버그 수정 1] 삭제 버튼이 항상 보이도록 is_deletable=True를 명시적으로 전달 ▼▼▼
        item_widget = CompanyItemWidget(company_data, is_regional=is_regional, is_deletable=True)
        item_widget.delete_requested.connect(self._handle_delete_item)
        item_widget.data_updated.connect(self._handle_data_update)

        if pos:
            insert_index = -1
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if pos.y() < widget.y() + widget.height() / 2: insert_index = i; break
            if insert_index == -1:
                layout.addWidget(item_widget)
            else:
                layout.insertWidget(insert_index, item_widget)
        else:
            layout.addWidget(item_widget)

        # QTimer.singleShot(0, self.recalculate_and_refresh_all)

        if layout in self.consortium_layouts:
            QTimer.singleShot(0, self.recalculate_and_refresh_all)

    def _handle_add_company(self):
        """[+ 업체 추가] 버튼 클릭 시, CompanySelectPopupPyside를 엽니다."""
        existing_companies = []
        all_layouts = self.consortium_layouts + [self.standby_layout]
        for layout in all_layouts:
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, CompanyItemWidget):
                    existing_companies.append(widget.company_data.get('name'))

        # ▼▼▼ [핵심 수정] 복잡한 경로 대신 최상위 컨트롤러(MainWindow)를 직접 찾아서 전달합니다 ▼▼▼
        parent_dialog = self.parent()
        # parent_dialog는 ResultManagementDialog, .controller는 ConsortiumViewHaeng
        # .controller.controller가 바로 MainWindow입니다.
        main_controller = parent_dialog.controller.controller if parent_dialog and hasattr(parent_dialog,
                                                                                           'controller') else None
        field_to_search = self.calculation_context.get("field_to_search", "-- 분야 선택 --")

        if not main_controller or field_to_search == "-- 분야 선택 --":
            QMessageBox.warning(self, "오류", "업체 검색에 필요한 최상위 컨트롤러나 공고분야 정보가 없습니다.")
            return

        # 팝업의 controller로 main_controller(MainWindow)를 전달
        self.search_popup = CompanySelectPopupPyside(self, main_controller, field_to_search,
                                                     self._on_company_selected_from_popup,
                                                     existing_companies)
        self.search_popup.exec()



    def _handle_delete_item(self, widget_to_delete):
        # 1. 삭제가 일어난 위젯이 어느 레이아웃에 속해있는지 먼저 찾습니다.
        deleted_from_layout = None
        for layout in self.consortium_layouts + [self.standby_layout]:
            for i in range(layout.count()):
                if layout.itemAt(i).widget() == widget_to_delete:
                    deleted_from_layout = layout
                    break
            if deleted_from_layout:
                break

        # 2. 위젯을 화면에서 제거합니다.
        widget_to_delete.deleteLater()

        # ▼▼▼ [버그 수정 3] '대기열'이 아닌, 실제 협정 레이아웃에서 삭제됐을 때만 재계산 ▼▼▼
        if deleted_from_layout in self.consortium_layouts:
            QTimer.singleShot(0, self.recalculate_and_refresh_all)

    def _handle_data_update(self, widget, new_data):
        # 1. 위젯이 가지고 있는 내부 데이터를 먼저 업데이트합니다.
        widget.company_data = new_data
        print(f"데이터 업데이트: {new_data['name']}의 지분이 {new_data['share']:.2%}로 변경됨")

        # 2. 변경이 일어난 위젯이 어느 레이아웃에 속해있는지 찾습니다.
        updated_layout = None
        for layout in self.consortium_layouts + [self.standby_layout]:
            for i in range(layout.count()):
                if layout.itemAt(i).widget() == widget:
                    updated_layout = layout
                    break
            if updated_layout:
                break

        # ▼▼▼ [핵심] '대기열'이 아닌, 실제 협정 레이아웃에서 변경이 일어났을 때만 재계산 호출 ▼▼▼
        if updated_layout in self.consortium_layouts:
            self.recalculate_and_refresh_all()

    def get_results(self):
        final_consortiums_details = []
        for layout in self.consortium_layouts:
            consortium_details = []
            for i in range(layout.count()):
                widget = layout.itemAt(i).widget()
                if isinstance(widget, CompanyItemWidget):
                    consortium_details.append(widget.company_data)
            final_consortiums_details.append(consortium_details)
        return final_consortiums_details



    def recalculate_single_consortium(self, index):
        """특정 인덱스의 협정 점수를 다시 계산하고 결과 데이터를 반환합니다."""
        layout = self.consortium_layouts[index]
        companies_data = []
        for j in range(layout.count()):
            widget = layout.itemAt(j).widget()
            if isinstance(widget, CompanyItemWidget):
                companies_data.append(widget.company_data)

        if not companies_data:
            self.scoreboard_labels[index].setText("구성된 업체가 없습니다.")
            return {}  # 빈 딕셔너리 반환

        try:
            context_for_calc = self.calculation_context.copy()
            context_for_calc.pop('field_to_search', None)  # 'field_to_search' 키를 안전하게 제거

            new_result = calculation_logic.calculate_consortium(
                companies_data, **context_for_calc
            )
            if new_result:
                biz_score = new_result.get('final_business_score', 0)
                perf_score = new_result.get('final_performance_score', 0)
                total_score = new_result.get('expected_score', 0)
                score_text = f"경영: {biz_score:.4f} | 실적: {perf_score:.4f} | <b>총점: {total_score:.4f}</b>"
                self.scoreboard_labels[index].setText(score_text)
                return new_result  # 재계산된 결과 반환
            else:
                self.scoreboard_labels[index].setText("<span style='color:red;'>계산 오류</span>")
        except Exception as e:
            print(f"점수 재계산 오류: {e}")
            self.scoreboard_labels[index].setText("<span style='color:red;'>계산 오류 발생</span>")
        return {}  # 오류 발생 시 빈 딕셔너리 반환

    def recalculate_and_refresh_all(self):
        """모든 협정의 점수를 다시 계산하고 미니 점수판을 업데이트합니다."""
        for i in range(len(self.consortium_layouts)):
            self.recalculate_single_consortium(i)

    def _on_company_selected_from_popup(self, selected_data):
        """검색 팝업에서 업체가 선택되었을 때 실행되는 콜백 함수"""
        import utils
        new_company_data = {
            'role': '구성사 ?', 'name': selected_data.get('검색된 회사'), 'data': selected_data,
            'business_score_details': {}, 'performance_5y': utils.parse_amount(selected_data.get("5년 실적", 0)) or 0,
            'share': 0.0
        }
        self.add_company_to_layout(self.standby_layout, new_company_data)