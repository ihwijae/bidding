# credentials_manager.py
import json
from encryption import encrypt_data, decrypt_data

CRED_FILE_PATH = "credentials.json.enc"

class CredentialsManager:
    def __init__(self):
        self.credentials_data = None
        self.master_password = None

    def load_and_decrypt(self, password: str) -> bool:
        """암호화된 파일을 읽고 복호화하여 메모리에 저장합니다."""
        try:
            with open(CRED_FILE_PATH, "rb") as f:
                encrypted_data = f.read()
        except FileNotFoundError:
            # 파일이 없으면 기본 데이터 구조의 '틀'을 생성합니다.
            print(f"'{CRED_FILE_PATH}' 파일이 없어 새 데이터 구조를 생성합니다.")
            
            # 기본 사이트와 법인 목록
            default_sites = ["나라장터", "한전", "한수원", "한국도로공사", "국방부", "한국가스공사", "공인인증서"]
            our_corps = ["아람이엔테크", "우진일렉트", "에코엠이엔씨", "지음쏠라테크", "대흥디씨티", "지음이엔아이"]
            managed_corps = ["삼영플랜트", "이엘케이", "엠라이테크", "영웅개발", "주요이앤씨"]
            default_corps = our_corps + ["--- 구분선 ---"] + managed_corps
            # 기본 데이터 구조 생성
            corporations_data = {}
            for corp_name in default_corps:
                corporations_data[corp_name] = {site: {} for site in default_sites}

            self.credentials_data = {
                "sites": default_sites,
                "corporations": corporations_data
            }
            self.master_password = password
            
            # 생성된 기본 틀로 즉시 파일 저장
            self.encrypt_and_save()
            return True

        decrypted_bytes = decrypt_data(encrypted_data, password)
        
        if decrypted_bytes:
            self.credentials_data = json.loads(decrypted_bytes.decode('utf-8'))
            self.master_password = password
            return True
        else:
            # 복호화 실패 (비밀번호 오류 등)
            self.credentials_data = None
            self.master_password = None
            return False

    def encrypt_and_save(self) -> bool:
        """현재 메모리에 있는 데이터를 암호화하여 파일에 저장합니다."""
        if self.credentials_data is None or self.master_password is None:
            print("오류: 데이터가 로드되지 않았거나 마스터 비밀번호가 설정되지 않았습니다.")
            return False
            
        try:
            data_bytes = json.dumps(self.credentials_data, ensure_ascii=False).encode('utf-8')
            encrypted_data = encrypt_data(data_bytes, self.master_password)
            
            with open(CRED_FILE_PATH, "wb") as f:
                f.write(encrypted_data)
            
            print(f"'{CRED_FILE_PATH}' 파일에 성공적으로 저장되었습니다.")
            return True
        except Exception as e:
            print(f"파일 저장 중 오류 발생: {e}")
            return False

    def get_data(self):
        """메모리에 로드된 데이터를 반환합니다."""
        return self.credentials_data

    def update_credential(self, corp_name, site_name, new_data):
        """특정 법인의 사이트 정보를 업데이트합니다."""
        if self.credentials_data is None:
            return False
        
        if corp_name in self.credentials_data["corporations"]:
            if site_name in self.credentials_data["corporations"][corp_name]:
                self.credentials_data["corporations"][corp_name][site_name] = new_data
                return True
        return False

# 이 클래스를 다른 파일에서 쉽게 가져다 쓸 수 있도록 인스턴스 생성
credentials_manager = CredentialsManager()