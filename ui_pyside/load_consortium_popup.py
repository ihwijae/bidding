from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                               QPushButton, QListWidgetItem, QComboBox, QLabel,
                               QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
import os
import json


class LoadConsortiumPopup(QDialog):
    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"[{mode}] 협정 파일 불러오기 (체크하여 다중 선택 가능)")
        self.setMinimumSize(600, 500)
        self.selected_data_list = []  # 여러 데이터를 담을 리스트
        self.data_folder = os.path.join("saved_data", mode)

        self.all_files_data = self.scan_and_read_files()

        self.setup_ui()
        self.populate_list()

    def scan_and_read_files(self):
        """데이터 폴더를 스캔하여 각 파일의 내용과 '파일 이름'을 함께 읽어옵니다."""
        all_data = []
        if not os.path.exists(self.data_folder):
            return all_data

        for filename in os.listdir(self.data_folder):
            if not filename.endswith('.json'): continue

            file_path = os.path.join(self.data_folder, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = json.load(f)
                    if isinstance(file_content, dict):
                        # ▼▼▼▼▼ [핵심 수정] 파일 내용에 'filename' 키를 추가하여 저장 ▼▼▼▼▼
                        file_content['filename'] = filename
                        all_data.append(file_content)
            except Exception:
                continue
        return all_data

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        filter_layout = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItem("전체 공사")
        unique_types = sorted(list(set(d.get("project_type", "기타") for d in self.all_files_data)))
        self.type_combo.addItems(unique_types)

        self.region_combo = QComboBox()
        self.region_combo.addItem("전체 지역")
        unique_regions = sorted(list(set(d.get("region_limit", "전체") for d in self.all_files_data)))
        self.region_combo.addItems(unique_regions)

        filter_layout.addWidget(QLabel("공사종류:"))
        filter_layout.addWidget(self.type_combo)
        filter_layout.addWidget(QLabel("지역제한:"))
        filter_layout.addWidget(self.region_combo)
        filter_layout.addStretch(1)
        main_layout.addLayout(filter_layout)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget::item { border-top: 1px solid #D5D8DC; padding: 5px; }")
        main_layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        self.delete_button = QPushButton("🗑️ 선택 파일 삭제")  # <--- 추가
        button_layout.addWidget(self.delete_button)  # <--- 추가
        button_layout.addStretch(1)
        self.load_button = QPushButton("선택 항목 불러오기")
        self.cancel_button = QPushButton("취소")
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.type_combo.currentTextChanged.connect(self.populate_list)
        self.region_combo.currentTextChanged.connect(self.populate_list)
        self.cancel_button.clicked.connect(self.reject)
        self.load_button.clicked.connect(self.on_load_clicked)
        self.delete_button.clicked.connect(self.delete_selected_file)

    def populate_list(self):
        """필터 조건에 맞게 목록을 채웁니다."""
        self.list_widget.clear()
        selected_type = self.type_combo.currentText()
        selected_region = self.region_combo.currentText()
        color_map = {"전기": QColor("#FFFACD"), "통신": QColor("#E0FFFF"), "소방": QColor("#FFE4E1")}

        sorted_data = sorted(self.all_files_data, key=lambda x: x.get("saved_date", ""), reverse=True)

        for data in sorted_data:
            type_match = (selected_type == "전체 공사" or data.get("project_type") == selected_type)
            region_match = (selected_region == "전체 지역" or data.get("region_limit") == selected_region)

            if type_match and region_match:
                # [수정] 날짜를 포함한 최종 텍스트 형식
                saved_name = data.get('saved_name', '이름 없음')
                saved_date = data.get('saved_date', '').split(' ')[0]
                region = data.get('region_limit', '전체')
                proj_type = data.get('project_type', '기타')
                display_text = f"[{saved_date}] {saved_name}  [{region}] [{proj_type}]"

                item = QListWidgetItem(display_text)

                # [수정] 체크박스 기능
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)

                if data.get('project_type') in color_map:
                    item.setBackground(QBrush(color_map[data['project_type']]))

                item.setData(Qt.ItemDataRole.UserRole, data)
                self.list_widget.addItem(item)

    def on_load_clicked(self):
        """체크된 모든 항목의 데이터를 가져옵니다."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                self.selected_data_list.append(item.data(Qt.ItemDataRole.UserRole))

        if not self.selected_data_list:
            QMessageBox.information(self, "알림", "불러올 항목을 하나 이상 체크해주세요.")
            return

        self.accept()

    def get_selected_data(self):
        return self.selected_data_list

    def delete_selected_file(self):
        """체크된 모든 저장 파일을 실제로 삭제합니다."""
        print("\n--- [디버깅] 삭제 기능 시작 ---")
        items_to_delete = []

        # 목록의 모든 아이템을 하나씩 확인하며 상태를 출력
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            # [핵심] 각 항목의 실제 체크 상태를 터미널에 출력합니다.
            print(f"  -> {i}번째 항목 '{item.text()}'의 체크 상태: {item.checkState()}")
            if item.checkState() == Qt.CheckState.Checked:
                items_to_delete.append(item)

        print(f"[디버깅] 체크된 것으로 확인된 항목 수: {len(items_to_delete)}")

        if not items_to_delete:
            QMessageBox.warning(self, "선택 오류", "먼저 삭제할 파일을 목록에서 체크하세요.")
            return

        # --- 이하 삭제 확인 및 실행 로직 (기존과 동일) ---
        filenames_to_delete = []
        for item in items_to_delete:
            file_data = item.data(Qt.ItemDataRole.UserRole)
            filename = file_data.get('filename')
            if filename:
                filenames_to_delete.append(filename)

        reply = QMessageBox.question(self, "파일 삭제 확인",
                                     f"선택한 {len(filenames_to_delete)}개의 파일을 정말로 삭제하시겠습니까?\n\n"
                                     f"삭제 목록:\n - {'\n - '.join(filenames_to_delete)}\n\n"
                                     "이 작업은 되돌릴 수 없습니다.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            for filename in filenames_to_delete:
                try:
                    file_path = os.path.join(self.data_folder, filename)
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    QMessageBox.critical(self, "삭제 실패", f"'{filename}' 파일 삭제 중 오류가 발생했습니다:\n{e}")

            if deleted_count > 0:
                QMessageBox.information(self, "삭제 완료", f"{deleted_count}개의 파일을 삭제했습니다.")

            self.all_files_data = self.scan_and_read_files()
            self.populate_list()