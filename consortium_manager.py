import sys
import pickle
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox, QWidget,
    QLabel, QLineEdit, QDialogButtonBox, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag

class CompanyItemWidget(QWidget):
    delete_requested = Signal()
    def __init__(self, text, is_deletable=True):
        super().__init__(); layout = QHBoxLayout(); layout.setContentsMargins(5, 2, 5, 2)
        self.label = QLabel(text); layout.addWidget(self.label); layout.addStretch()
        if is_deletable:
            self.delete_button = QPushButton("X"); self.delete_button.setFixedSize(24, 24)
            self.delete_button.clicked.connect(self.delete_requested.emit); layout.addWidget(self.delete_button)
        self.setLayout(layout)

class AddCompanyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("업체 추가"); layout = QVBoxLayout(self)
        self.info_label = QLabel("추가할 업체명을 입력하세요 (예: 새로운건설 30%)")
        self.company_name_input = QLineEdit()
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.info_label); layout.addWidget(self.company_name_input); layout.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept); self.buttons.rejected.connect(self.reject)
    def get_company_info(self):
        name_text = self.company_name_input.text().strip()
        if name_text:
            parts = name_text.split(); name = " ".join(parts[:-1]) if len(parts) > 1 else name_text
            share_str = parts[-1] if len(parts) > 1 else "0%"; share = 0.0
            try: share = float(share_str.replace('%','')) / 100
            except: pass
            return {'name': name, 'share': share, 'etc': '신규'}
        return None

class DroppableListWidget(QListWidget):
    def __init__(self, parent_dialog, parent=None):
        super().__init__(parent); self.parent_dialog = parent_dialog
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    def startDrag(self, supportedActions):
        item = self.currentItem();
        if not item: return
        company_data = item.data(Qt.ItemDataRole.UserRole); encoded_data = pickle.dumps(company_data)
        mime_data = QMimeData(); mime_data.setData('application/x-company-data', encoded_data)
        drag = QDrag(self); drag.setMimeData(mime_data)
        pixmap = QWidget.grab(self.itemWidget(item)); drag.setPixmap(pixmap); drag.setHotSpot(pixmap.rect().center())
        if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.MoveAction: self.takeItem(self.row(item))
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-company-data'): event.acceptProposedAction()
        else: super().dragEnterEvent(event)
    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-company-data'): event.acceptProposedAction()
        else: super().dragMoveEvent(event)
    def dropEvent(self, event):
        if event.mimeData().hasFormat('application/x-company-data'):
            encoded_data = event.mimeData().data('application/x-company-data'); company_data = pickle.loads(encoded_data)
            self.parent_dialog.add_company_to_list(self, company_data, drop_event=event); event.acceptProposedAction()
        else: super().dropEvent(event)

class ConsortiumManagerDialog(QDialog):
    def __init__(self, consortiums_data, parent=None):
        super().__init__(parent); self.setWindowTitle("협정 결과 관리"); self.setMinimumSize(800, 600)
        main_layout = QHBoxLayout(); consortiums_area_layout = QHBoxLayout()
        self.consortium_list_widgets = []
        for i, consortium in enumerate(consortiums_data):
            group_box = QGroupBox(f"협정 {chr(65+i)}"); group_layout = QVBoxLayout()
            list_widget = DroppableListWidget(self)
            for company_data in consortium: self.add_company_to_list(list_widget, company_data)
            group_layout.addWidget(list_widget); group_box.setLayout(group_layout)
            consortiums_area_layout.addWidget(group_box); self.consortium_list_widgets.append(list_widget)
        standby_group_box = QGroupBox("대기중인 업체"); standby_layout = QVBoxLayout()
        self.standby_list_widget = DroppableListWidget(self)
        self.add_button = QPushButton("[+ 업체 추가]"); self.add_button.clicked.connect(self._handle_add_company)
        standby_layout.addWidget(self.add_button); standby_layout.addWidget(self.standby_list_widget); standby_group_box.setLayout(standby_layout)
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        dialog_buttons.accepted.connect(self.accept); dialog_buttons.rejected.connect(self.reject)
        left_widget = QWidget(); left_widget.setLayout(consortiums_area_layout)
        main_layout.addWidget(left_widget, 7); main_layout.addWidget(standby_group_box, 3)
        final_layout = QVBoxLayout(); final_layout.addLayout(main_layout); final_layout.addWidget(dialog_buttons)
        self.setLayout(final_layout)
    def add_company_to_list(self, list_widget, company_data, is_deletable=True, drop_event=None):
        item = QListWidgetItem(); item.setData(Qt.ItemDataRole.UserRole, company_data)
        display_text = f"{company_data.get('name', '')} {company_data.get('share', 0):.2%}"
        item_widget = CompanyItemWidget(display_text, is_deletable)
        item_widget.delete_requested.connect(lambda bound_item=item: self._handle_delete_item(bound_item))
        item.setSizeHint(item_widget.sizeHint())
        if drop_event:
            pos = drop_event.position().toPoint(); item_at_pos = list_widget.itemAt(pos)
            if item_at_pos: list_widget.insertItem(list_widget.row(item_at_pos), item)
            else: list_widget.addItem(item)
        else: list_widget.addItem(item)
        list_widget.setItemWidget(item, item_widget)
    def _handle_add_company(self):
        dialog = AddCompanyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            company_info = dialog.get_company_info()
            if company_info: self.add_company_to_list(self.standby_list_widget, company_info)
            else: QMessageBox.warning(self, "입력 오류", "업체 정보가 올바르지 않습니다.")
    def _handle_delete_item(self, item):
        for list_widget in self.consortium_list_widgets + [self.standby_list_widget]:
            row = list_widget.row(item)
            if row > -1: list_widget.takeItem(row); break
    def get_results(self):
        final_consortiums = [];
        for list_widget in self.consortium_list_widgets:
            consortium = [];
            for i in range(list_widget.count()):
                item = list_widget.item(i); company_data = item.data(Qt.ItemDataRole.UserRole)
                consortium.append(company_data)
            final_consortiums.append(consortium)
        return final_consortiums

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())