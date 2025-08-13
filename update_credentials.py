# update_credentials.py
import json
from credentials_manager import credentials_manager # 기존 관리자 모듈 재사용

def main():
    print("--- 기존 계정 정보 파일 업데이트 시작 ---")

    # 1. 사용자로부터 마스터 비밀번호를 입력받습니다.
    master_password = input("기존 마스터 비밀번호를 입력하세요: ")

    # 2. 기존 파일 복호화를 시도합니다.
    if not credentials_manager.load_and_decrypt(master_password):
        print("오류: 비밀번호가 틀렸거나 'credentials.json.enc' 파일이 없습니다.")
        return

    # 3. 복호화된 기존 데이터를 가져옵니다.
    current_data = credentials_manager.get_data()
    if not current_data:
        print("오류: 데이터를 불러오지 못했습니다.")
        return

    print("기존 데이터 로드 성공!")

    # 4. 새로운 법인 목록과 사이트 목록을 정의합니다.
    our_corps = ["아람이엔테크", "우진일렉트", "에코엠이엔씨", "지음쏠라테크", "대흥디씨티", "지음이엔아이"]
    managed_corps = ["삼영플랜트", "이엘케이", "엠라이테크", "영웅개발", "주요이앤씨"]
    
    new_corp_list = our_corps + ["--- 구분선 ---"] + managed_corps
    new_site_list = ["나라장터", "한전", "한수원", "한국도로공사", "국방부", "한국가스공사", "공인인증서"]
    
    # 5. 새로운 데이터 구조의 '틀'을 만듭니다.
    new_corporations_data = {}
    for corp_name in new_corp_list:
        new_corporations_data[corp_name] = {site: {} for site in new_site_list}
        
    # 6. [핵심] 기존 데이터를 새 틀에 덮어씁니다.
    # 기존에 있던 법인들의 정보만 새 틀로 복사됩니다.
    for corp_name, sites_data in current_data.get("corporations", {}).items():
        if corp_name in new_corporations_data:
            new_corporations_data[corp_name] = sites_data

    # 7. 업데이트된 데이터로 교체합니다.
    credentials_manager.credentials_data = {
        "sites": new_site_list,
        "corporations": new_corporations_data
    }

    # 8. 새로운 데이터로 파일을 다시 암호화하여 저장합니다.
    if credentials_manager.encrypt_and_save():
        print("\n성공! 'credentials.json.enc' 파일이 새로운 법인 목록으로 업데이트되었습니다.")
    else:
        print("\n오류! 파일 업데이트에 실패했습니다.")


if __name__ == "__main__":
    main()