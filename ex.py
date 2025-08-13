import sys
import pickle  # 아이템 데이터를 전달하기 위해 추가
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox, QWidget,
    QLabel, QLineEdit, QDialogButtonBox, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag


# CompanyItemWidget, AddCompanyDialog 클래스는 이전과 동일합니다.
# (스크롤 편의를 위해 여기에 다시 포함합니다)

class CompanyItemWidget(QWidget):
    delete_requested = Signal()

    def __init__(self, text, is_deletable=True):
        super().__init__()
        layout = QHBoxLayout();
        layout.setContentsMargins(5, 2, 5, 2)
        self.label = QLabel(text)
        layout.addWidget(self.label);
        layout.addStretch()
        if is_deletable:
            self.delete_button = QPushButton("X");
            self.delete_button.setFixedSize(24, 24)
            self.delete_button.clicked.connect(self.delete_requested.emit)
            layout.addWidget(self.delete_button)
        self.setLayout(layout)


class AddCompanyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("업체 추가")
        layout = QVBoxLayout(self)
        self.info_label = QLabel("추가할 업체명을 입력하세요 (예: 새로운건설 30%)")
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
                share = float(share_str.replace('%', '')) / 100
            except:
                pass
            return {'name': name, 'share': share, 'etc': '신규'}
        return None


# ------------------------------------------------------------------------------------
# ▼▼▼▼▼ [핵심 수정] 드래그 앤 드롭 로직을 처리하는 커스텀 리스트 위젯 ▼▼▼▼▼
# ------------------------------------------------------------------------------------
class DroppableListWidget(QListWidget):
    def __init__(self, parent_dialog, parent=None):
        super().__init__(parent)
        self.parent_dialog = parent_dialog  # 부모 다이얼로그의 함수를 호출하기 위해 저장
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def startDrag(self, supportedActions):
        """드래그 시작 시, 아이템의 실제 데이터(딕셔너리)를 포장해서 전달"""
        item = self.currentItem()
        if not item:
            return

        # 아이템에 저장된 딕셔너리 데이터를 가져옴
        company_data = item.data(Qt.ItemDataRole.UserRole)

        # 데이터를 pickle을 이용해 바이트 형태로 변환
        encoded_data = pickle.dumps(company_data)

        mime_data = QMimeData()
        # 커스텀 데이터 타입으로 설정 (이 타입을 가진 데이터만 드롭을 허용하기 위함)
        mime_data.setData('application/x-company-data', encoded_data)

        drag = QDrag(self)
        drag.setMimeData(mime_data)

        # 드래그 시 마우스 커서에 보일 이미지 생성
        pixmap = QWidget.grab(self.itemWidget(item))
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())

        # 드래그 실행. MoveAction이 성공하면 원본 아이템 삭제
        if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.MoveAction:
            self.takeItem(self.row(item))

    def dragEnterEvent(self, event):
        """드래그가 리스트 위젯 영역에 들어왔을 때, 받을 수 있는 데이터 타입인지 확인"""
        if event.mimeData().hasFormat('application/x-company-data'):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-company-data'):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """다른 리스트에서 아이템을 드롭했을 때, 데이터를 풀어서 새 아이템을 생성"""
        if event.mimeData().hasFormat('application/x-company-data'):
            encoded_data = event.mimeData().data('application/x-company-data')
            company_data = pickle.loads(encoded_data)

            # 부모 다이얼로그의 헬퍼 함수를 이용해 새 아이템을 현재 위치에 추가
            self.parent_dialog.add_company_to_list(self, company_data, drop_event=event)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# ------------------------------------------------------------------------------------
# ▼▼▼▼▼ [수정] 관리창이 DroppableListWidget을 사용하도록 변경 ▼▼▼▼▼
# ------------------------------------------------------------------------------------
class ConsortiumManagerDialog(QDialog):
    def __init__(self, consortiums_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("협정 결과 관리")
        self.setMinimumSize(800, 600)

        main_layout = QHBoxLayout(self)
        consortiums_area_layout = QHBoxLayout()

        self.consortium_list_widgets = []
        for i, consortium in enumerate(consortiums_data):
            group_box = QGroupBox(f"협정 {chr(65 + i)}")
            group_layout = QVBoxLayout()

            # QListWidget -> DroppableListWidget 으로 교체
            list_widget = DroppableListWidget(self)  # self(dialog)를 넘겨줌

            for company_data in consortium:
                self.add_company_to_list(list_widget, company_data)

            group_layout.addWidget(list_widget)
            group_box.setLayout(group_layout)
            consortiums_area_layout.addWidget(group_box)
            self.consortium_list_widgets.append(list_widget)

        standby_group_box = QGroupBox("대기중인 업체")
        standby_layout = QVBoxLayout()
        # QListWidget -> DroppableListWidget 으로 교체
        self.standby_list_widget = DroppableListWidget(self)

        self.add_button = QPushButton("[+ 업체 추가]")
        self.add_button.clicked.connect(self._handle_add_company)
        standby_layout.addWidget(self.add_button)
        standby_layout.addWidget(self.standby_list_widget)
        standby_group_box.setLayout(standby_layout)

        dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)

        left_widget = QWidget();
        left_widget.setLayout(consortiums_area_layout)
        right_widget = QWidget();


        main_layout.addWidget(left_widget, 7)
        main_layout.addWidget(right_widget, 3)
        final_layout = QVBoxLayout();
        final_layout.addLayout(main_layout);
        final_layout.addWidget(dialog_buttons)
        self.setLayout(final_layout)

    def add_company_to_list(self, list_widget, company_data, is_deletable=True, drop_event=None):
        """헬퍼 함수 수정: 드롭된 위치에 아이템을 추가할 수 있도록 변경"""
        item = QListWidgetItem()  # 리스트 위젯을 나중에 지정
        item.setData(Qt.ItemDataRole.UserRole, company_data)
        display_text = f"{company_data['name']} {company_data['share']:.2%}"
        item_widget = CompanyItemWidget(display_text, is_deletable)
        item_widget.delete_requested.connect(lambda bound_item=item: self._handle_delete_item(bound_item))
        item.setSizeHint(item_widget.sizeHint())

        if drop_event:
            # 드롭된 위치를 계산하여 아이템 삽입
            pos = drop_event.position().toPoint()
            item_at_pos = list_widget.itemAt(pos)
            if item_at_pos:
                list_widget.insertItem(list_widget.row(item_at_pos), item)
            else:
                list_widget.addItem(item)
        else:
            list_widget.addItem(item)

        list_widget.setItemWidget(item, item_widget)

    def _handle_add_company(self):
        dialog = AddCompanyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            company_info = dialog.get_company_info()
            if company_info:
                self.add_company_to_list(self.standby_list_widget, company_info)
            else:
                QMessageBox.warning(self, "입력 오류", "업체 정보가 올바르지 않습니다.")

    def _handle_delete_item(self, item):
        # 아이템이 속한 리스트 위젯을 찾아서 제거
        for list_widget in self.consortium_list_widgets + [self.standby_list_widget]:
            row = list_widget.row(item)
            if row > -1:
                list_widget.takeItem(row)
                break

    def get_results(self):
        # ... (이전과 동일)
        final_consortiums = []
        for list_widget in self.consortium_list_widgets:
            consortium = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                company_data = item.data(Qt.ItemDataRole.UserRole)
                consortium.append(company_data)
            final_consortiums.append(consortium)
        return final_consortiums


# MainWindow 클래스는 이전과 동일합니다.
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("협정 관리 프로그램 (PySide6 - 최종본)")
        self.setGeometry(100, 100, 400, 300)
        self.consortiums_data = [
            [{'name': '지음이엔아이', 'share': 0.51, 'etc': 'some_data_1'},
             {'name': '대한종합산전', 'share': 0.49, 'etc': 'some_data_2'}],
            [{'name': '우진일렉트', 'share': 0.51, 'etc': 'some_data_3'},
             {'name': '경우전기', 'share': 0.49, 'etc': 'some_data_4'}]
        ]
        central_widget = QWidget();
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.label = QLabel("아래 버튼을 눌러 협정 관리를 시작하세요.")
        self.manage_button = QPushButton("협정 관리창 열기")
        self.manage_button.clicked.connect(self.open_manager)
        layout.addWidget(self.label);
        layout.addWidget(self.manage_button)

    def open_manager(self):
        dialog = ConsortiumManagerDialog(self.consortiums_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.consortiums_data = dialog.get_results()
            QMessageBox.information(self, "저장 완료", "협정 내용이 성공적으로 업데이트 되었습니다.")
            print("--- 업데이트된 협정 결과 (PySide6) ---")
            for i, consortium in enumerate(self.consortiums_data):
                print(f"협정 {chr(65 + i)}:")
                for company in consortium:
                    print(f"  - {company['name']} ({company['share']:.2%})")
            print("---------------------------------")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())