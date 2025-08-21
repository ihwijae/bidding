import subprocess

# 필수 라이브러리 목록 (레포 기준 최소 버전)
CORE_PACKAGES = ["pandas", "openpyxl", "PySide6", "cryptography", "requests"]

def export_freeze():
    """pip freeze 결과를 requirements_all.txt 로 저장"""
    with open("requirements_all.txt", "w", encoding="utf-8") as f:
        result = subprocess.run(["pip", "freeze"], capture_output=True, text=True)
        f.write(result.stdout)
    print("✅ requirements_all.txt 생성 완료")

def export_minimal():
    """requirements_all.txt 를 읽어서 필요한 핵심 패키지만 필터링"""
    minimal = []
    with open("requirements_all.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    for pkg in CORE_PACKAGES:
        for line in lines:
            if line.lower().startswith(pkg.lower() + "=="):
                minimal.append(line.strip())
                break

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(minimal) + "\n")

    print("✅ requirements.txt (최소 버전) 생성 완료")

if __name__ == "__main__":
    export_freeze()
    export_minimal()
