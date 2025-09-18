import sys
import os
sys.path.append('..')  # Để import được từ folder cha

from core.wallet import create_wallet, get_wallet_info
from core.transaction import create_transaction, sign_transaction
from core.verification import verify_signature

def test_create_wallet():
    """Test tạo ví"""
    print("🧪 TEST 1: Tạo ví ECDSA...")
    
    try:
        # Tạo ví test
        wallet_info = create_wallet("TestUser")
        
        # Kiểm tra kết quả
        assert wallet_info is not None
        assert "name" in wallet_info
        assert "address" in wallet_info
        assert "public_key" in wallet_info
        assert "private_key" in wallet_info
        assert wallet_info["balance"] > 0
        
        print(f"   ✅ Tạo ví thành công: {wallet_info['name']}")
        print(f"   ✅ Địa chỉ: {wallet_info['address']}")
        print(f"   ✅ Số dư ban đầu: {wallet_info['balance']:,} VND")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi tạo ví: {e}")
        return False

def test_signing_transaction():
    """Test ký giao dịch"""
    print("\n🧪 TEST 2: Ký giao dịch bằng ECDSA...")
    
    try:
        # Tạo 2 ví test
        alice = create_wallet("Alice_Test")
        bob = create_wallet("Bob_Test")
        
        # Tạo giao dịch
        transaction = create_transaction("Alice_Test", "Bob_Test", 50000)
        print(f"   ✅ Tạo giao dịch: {transaction['id']}")
        
        # Ký giao dịch
        signed_tx = sign_transaction(transaction, "Alice_Test")
        
        # Kiểm tra kết quả
        assert "signature" in signed_tx
        assert signed_tx["signature"] != ""
        assert len(signed_tx["signature"]) > 50  # Signature có độ dài hợp lý
        
        print(f"   ✅ Ký giao dịch thành công")
        print(f"   ✅ Signature: {signed_tx['signature'][:30]}...")
        
        return signed_tx
        
    except Exception as e:
        print(f"   ❌ Lỗi ký giao dịch: {e}")
        return None

def test_verify_signature():
    """Test xác minh chữ ký"""
    print("\n🧪 TEST 3: Xác minh chữ ký ECDSA...")
    
    try:
        # Lấy giao dịch đã ký từ test trước
        signed_tx = test_signing_transaction()
        if not signed_tx:
            print("   ❌ Không có giao dịch để test")
            return False
        
        # Xác minh chữ ký đúng
        valid, message = verify_signature(signed_tx)
        
        assert valid == True
        print(f"   ✅ Xác minh chữ ký hợp lệ: {message}")
        
        # Test chữ ký sai
        fake_tx = signed_tx.copy()
        fake_tx["signature"] = "fake_signature_12345"
        
        invalid, error_msg = verify_signature(fake_tx)
        assert invalid == False
        print(f"   ✅ Phát hiện chữ ký giả: {error_msg}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi xác minh chữ ký: {e}")
        return False

def test_signature_tampering():
    """Test phát hiện chữ ký bị thay đổi"""
    print("\n🧪 TEST 4: Phát hiện chữ ký bị thay đổi...")
    
    try:
        # Tạo giao dịch hợp lệ
        alice = create_wallet("Alice_Tamper")
        bob = create_wallet("Bob_Tamper") 
        
        transaction = create_transaction("Alice_Tamper", "Bob_Tamper", 30000)
        signed_tx = sign_transaction(transaction, "Alice_Tamper")
        
        # Xác minh giao dịch gốc
        valid_original, _ = verify_signature(signed_tx)
        assert valid_original == True
        print("   ✅ Giao dịch gốc hợp lệ")
        
        # Thay đổi amount (tampering)
        tampered_tx = signed_tx.copy()
        tampered_tx["amount"] = 999999  # Thay đổi số tiền
        
        # Xác minh giao dịch bị thay đổi
        valid_tampered, error_msg = verify_signature(tampered_tx)
        assert valid_tampered == False
        print(f"   ✅ Phát hiện tampering: {error_msg}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi test tampering: {e}")
        return False

def run_all_signature_tests():
    """Chạy tất cả test về chữ ký"""
    print("=" * 60)
    print("🔐 CHẠY TẤT CẢ TEST CHỮ KÝ ECDSA")
    print("=" * 60)
    
    tests = [
        test_create_wallet,
        test_signing_transaction,
        test_verify_signature,
        test_signature_tampering
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"   ❌ Test {test_func.__name__} failed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 KẾT QUẢ TEST: {passed}/{total} PASSED")
    
    if passed == total:
        print("🎉 TẤT CẢ TEST ĐỀU PASS!")
    else:
        print(f"⚠️  CÓ {total - passed} TEST FAILED")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    run_all_signature_tests()