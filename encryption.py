# encryption.py
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

# PBKDF2 파라미터 (보안 강도와 관련)
SALT_SIZE = 16
ITERATIONS = 480000 # 2024년 권장치

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """사용자가 입력한 마스터 비밀번호와 salt를 사용해 암호화 키를 생성합니다."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_data(data: bytes, password: str) -> bytes:
    """데이터를 마스터 비밀번호로 암호화합니다."""
    salt = os.urandom(SALT_SIZE)
    key = generate_key_from_password(password, salt)
    f = Fernet(key)
    encrypted_data = f.encrypt(data)
    # 최종 결과물은 salt와 암호화된 데이터를 합친 형태입니다.
    return salt + encrypted_data

def decrypt_data(encrypted_data_with_salt: bytes, password: str) -> bytes:
    """암호화된 데이터를 마스터 비밀번호로 복호화합니다."""
    try:
        # 데이터에서 salt와 순수 암호화 데이터를 분리합니다.
        salt = encrypted_data_with_salt[:SALT_SIZE]
        encrypted_data = encrypted_data_with_salt[SALT_SIZE:]
        
        key = generate_key_from_password(password, salt)
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data
    except Exception as e:
        # 비밀번호가 틀렸거나 파일이 손상된 경우 오류 발생
        print(f"복호화 오류: {e}")
        return None