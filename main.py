# main.py
import sys
from PySide6.QtWidgets import QApplication
import config
from ui_pyside.main_window import MainWindow
import ctypes

myappid = 'mycompany.myproduct.bidding_app.1.0'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)



def main():
    """PySide6 애플리케이션을 초기화하고 실행합니다."""
    # 1. 설정 파일 로드
    source_files = config.load_config()
    
    # 2. QApplication 인스턴스 생성
    app = QApplication(sys.argv)
    
    # 3. 메인 윈도우 생성 (설정값 전달)
    window = MainWindow(source_files_config=source_files)
    window.show()

    # 4. 앱 실행
    sys.exit(app.exec())

if __name__ == "__main__":
    main()