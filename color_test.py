# color_test.py
from openpyxl import load_workbook

# --- !!! 사용자가 직접 수정해야 할 부분 !!! ---
# 1. 테스트할 엑셀 파일의 전체 경로를 입력하세요.
#    (백슬래시'\'는 두 개씩 '\\' 쓰거나, 슬래시'/'로 바꿔주세요)
FILE_PATH = r"C:\Users\user\Desktop\3.협력업체요약(2023년소방)2025..06.18.xlsx"

# 2. 엑셀 파일 안에서 테스트할 시트의 이름을 정확히 입력하세요.
SHEET_NAME = "서울"  # 또는 "통신", "소방" 등

# 3. 색상이 칠해져 있는 셀의 주소를 입력하세요. (예: "E5")
#    '지움이앤아이(주)'의 '시평' 셀 주소를 예시로 넣어보세요.
CELL_TO_TEST = "B19" 
# ---------------------------------------------


try:
    # 엑셀 파일 열기
    workbook = load_workbook(filename=FILE_PATH)
    sheet = workbook[SHEET_NAME]
    
    # 지정된 셀 객체 가져오기
    cell = sheet[CELL_TO_TEST]
    
    print(f"--- 셀 [{CELL_TO_TEST}]의 색상 정보 분석 ---")
    
    # openpyxl이 색상 정보를 저장하는 모든 속성을 출력해봅니다.
    print(f"1. 셀 채우기(Fill) 객체: {cell.fill}")
    print(f"2. 전경색(ForegroundColor) 객체: {cell.fill.fgColor}")
    print(f"3. 전경색 타입: {cell.fill.fgColor.type}")
    print(f"4. RGB 값 (우리가 사용하려던 것): {cell.fill.fgColor.rgb}")
    print(f"5. 테마 인덱스: {cell.fill.fgColor.theme}")
    print(f"6. 틴트/음영 값: {cell.fill.fgColor.tint}")
    print("-" * 30)

except Exception as e:
    print(f"테스트 중 오류 발생: {e}")