import sys
sys.path.append('..')  # Để import được từ folder cha

from core.transaction import create_transaction, sign_transaction
from core.verification import verify_signature

def test_signing():
    """Test ký giao dịch"""
    # 1. Tạo giao dịch test
    # 2. Ký giao dịch
    # 3. Kiểm tra có signature không
    # 4. Print kết quả
    
def test_verification():
    """Test xác minh chữ ký"""  
    # 1. Tạo giao dịch đã ký
    # 2. Verify signature
    # 3. Test với signature sai
    # 4. Print kết quả

if __name__ == "__main__":
    test_signing()
    test_verification()