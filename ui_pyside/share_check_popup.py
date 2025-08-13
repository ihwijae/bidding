# ui_pyside/share_check_popup.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QHeaderView,
                               QTableWidgetItem, QPushButton)
from PySide6.QtGui import QColor

class ShareCheckPopup(QDialog):
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("지분율 사전검토 결과")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["업체명", "입력 지분율", "최대 가능 지분율", "결과"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setRowCount(len(results))

        for row, res in enumerate(results):
            table.setItem(row, 0, QTableWidgetItem(res['name']))
            
            # [핵심 수정] 소수점 둘째 자리에서 '절사(버림)'하여 표시
            input_share_truncated = int(res['input_share'] * 100) / 100.0
            max_share_truncated = int(res['max_share'] * 100) / 100.0

            table.setItem(row, 1, QTableWidgetItem(f"{input_share_truncated:.2f}%"))
            table.setItem(row, 2, QTableWidgetItem(f"{max_share_truncated:.2f}%"))
            
            result_item = QTableWidgetItem()
            if res['is_problem']:
                diff = res['difference']
                result_item.setText(f"시평액 부족 ({diff:+.2f}%)") # 차이값은 가독성을 위해 반올림 표시
                result_item.setForeground(QColor("red"))
            else:
                result_item.setText("충족")
                result_item.setForeground(QColor("green"))
            table.setItem(row, 3, result_item)
            
        layout.addWidget(table)
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)