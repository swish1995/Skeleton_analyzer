#!/usr/bin/env python3
"""라이센스 키 생성 도구

사용법:
    python license_keygen.py <hardware_id>
    python license_keygen.py --batch <file>

예시:
    python license_keygen.py ABCDEF1234567890
    python license_keygen.py --batch hardware_ids.txt
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.license.license_validator import LicenseValidator


def generate_key(hardware_id: str) -> str:
    """하드웨어 ID로 라이센스 키 생성

    Args:
        hardware_id: 16자리 하드웨어 ID

    Returns:
        XXXX-XXXX-XXXX-XXXX 형식의 라이센스 키
    """
    validator = LicenseValidator()
    return validator.generate_test_key(hardware_id)


def validate_key(key: str, hardware_id: str) -> bool:
    """키 유효성 검증

    Args:
        key: 라이센스 키
        hardware_id: 하드웨어 ID

    Returns:
        유효 여부
    """
    validator = LicenseValidator()
    from src.license.license_validator import ValidationResult
    result = validator.validate(key, hardware_id)
    return result == ValidationResult.VALID


def process_batch(file_path: str) -> list:
    """배치 파일 처리

    Args:
        file_path: 하드웨어 ID 목록 파일 경로

    Returns:
        (hardware_id, key) 튜플 리스트
    """
    results = []
    with open(file_path, 'r') as f:
        for line in f:
            hardware_id = line.strip()
            if hardware_id and not hardware_id.startswith('#'):
                key = generate_key(hardware_id)
                results.append((hardware_id, key))
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Skeleton Analyzer 라이센스 키 생성 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python license_keygen.py ABCDEF1234567890
    python license_keygen.py --batch hardware_ids.txt
    python license_keygen.py --validate ABCD-1234-SA25-XXXX ABCDEF1234567890
        """
    )

    # 위치 인자
    parser.add_argument('hardware_id', nargs='?', help='16자리 하드웨어 ID')

    # batch 옵션
    parser.add_argument('--batch', '-b', metavar='FILE',
                       help='하드웨어 ID 목록 파일 (한 줄에 하나)')

    # validate 옵션
    parser.add_argument('--validate', '-v', nargs=2, metavar=('KEY', 'HWID'),
                       help='키 유효성 검증')

    # output 옵션
    parser.add_argument('--output', '-o', metavar='FILE',
                       help='결과 출력 파일 (배치 모드용)')

    args = parser.parse_args()

    # 검증 모드
    if args.validate:
        key, hardware_id = args.validate
        is_valid = validate_key(key, hardware_id)
        if is_valid:
            print(f"✓ 유효한 키입니다.")
            sys.exit(0)
        else:
            print(f"✗ 유효하지 않은 키입니다.")
            sys.exit(1)

    # 배치 모드
    if args.batch:
        results = process_batch(args.batch)

        if args.output:
            with open(args.output, 'w') as f:
                for hwid, key in results:
                    f.write(f"{hwid}\t{key}\n")
            print(f"✓ {len(results)}개의 키가 {args.output}에 저장되었습니다.")
        else:
            print("Hardware ID\t\t\tLicense Key")
            print("-" * 60)
            for hwid, key in results:
                print(f"{hwid}\t{key}")

        sys.exit(0)

    # 단일 키 생성
    if args.hardware_id:
        key = generate_key(args.hardware_id)
        print(f"Hardware ID: {args.hardware_id}")
        print(f"License Key: {key}")
        sys.exit(0)

    # 인자 없이 실행시 도움말
    parser.print_help()
    sys.exit(1)


if __name__ == '__main__':
    main()
