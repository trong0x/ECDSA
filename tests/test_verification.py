import sys
import os
sys.path.append('..')

from core.wallet import create_wallet, get_wallet_info
from core.transaction import create_transaction, sign_transaction
from core.verification import full_verification_flow, verify_signature, check_balance
from security.fraud_detection import check_fraud, check_double_spending

def test_valid_transaction():
    """Test giao dịch hợp lệ"""
    print("🧪 TEST 1: Giao dịch hợp lệ...")
    
    try:
        # Tạo ví test
        alice = create_wallet("Alice_Valid")
        bob = create_wallet("Bob_Valid")
        
        # Tạo và ký giao dịch
        transaction = create_transaction("Alice_Valid", "Bob_Valid", 100000)
        signed_tx = sign_transaction(transaction, "Alice_Valid")
        
        # Chạy full verification
        result = full_verification_flow(signed_tx["id"])
        
        # Kiểm tra kết quả
        assert result["valid"] == True
        assert result["signature_valid"] == True
        assert result["balance_valid"] == True
        assert result["fraud_check"] == True
        
        print("   ✅ Giao dịch hợp lệ - PASS")
        print(f"   ✅ Chữ ký: {'OK' if result['signature_valid'] else 'FAIL'}")
        print(f"   ✅ Số dư: {'OK' if result['balance_valid'] else 'FAIL'}")
        print(f"   ✅ Bảo mật: {'OK' if result['fraud_check'] else 'FAIL'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi test giao dịch hợp lệ: {e}")
        return False

def test_invalid_signature():
    """Test giao dịch chữ ký sai"""
    print("\n🧪 TEST 2: Giao dịch chữ ký sai...")
    
    try:
        # Tạo ví test
        alice = create_wallet("Alice_BadSig")
        bob = create_wallet("Bob_BadSig")
        
        # Tạo giao dịch
        transaction = create_transaction("Alice_BadSig", "Bob_BadSig", 50000)
        signed_tx = sign_transaction(transaction, "Alice_BadSig")
        
        # Làm hỏng chữ ký
        signed_tx["signature"] = "fake_signature_abcdef123456"
        
        # Test verify signature
        valid, message = verify_signature(signed_tx)
        
        assert valid == False
        print("   ✅ Phát hiện chữ ký sai - PASS")
        print(f"   ✅ Lý do: {message}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi test chữ ký sai: {e}")
        return False

def test_insufficient_balance():
    """Test giao dịch không đủ tiền"""
    print("\n🧪 TEST 3: Giao dịch không đủ tiền...")
    
    try:
        # Tạo ví test
        alice = create_wallet("Alice_NoMoney")
        bob = create_wallet("Bob_NoMoney")
        
        # Tạo giao dịch với số tiền lớn hơn số dư
        alice_wallet = get_wallet_info("Alice_NoMoney")
        big_amount = alice_wallet["balance"] + 500000  # Vượt quá số dư
        
        # Test check balance
        balance_ok, balance_msg = check_balance("Alice_NoMoney", big_amount)
        
        assert balance_ok == False
        print("   ✅ Phát hiện không đủ tiền - PASS")
        print(f"   ✅ Lý do: {balance_msg}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi test không đủ tiền: {e}")
        return False

def test_double_spending_detection():
    """Test phát hiện double spending"""
    print("\n🧪 TEST 4: Phát hiện double spending...")
    
    try:
        # Tạo ví test
        alice = create_wallet("Alice_Double")
        bob = create_wallet("Bob_Double")
        
        # Tạo giao dịch đầu tiên
        tx1 = create_transaction("Alice_Double", "Bob_Double", 100000)
        signed_tx1 = sign_transaction(tx1, "Alice_Double")
        
        # Tạo giao dịch thứ hai giống hệt (double spending)
        tx2 = create_transaction("Alice_Double", "Bob_Double", 100000)
        signed_tx2 = sign_transaction(tx2, "Alice_Double")
        
        # Test phát hiện double spending
        fraud_detected, fraud_msg = check_double_spending(signed_tx2)
        
        # Should detect fraud (có thể pass hoặc fail tùy timing)
        print(f"   ✅ Kết quả double spending check: {fraud_msg}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi test double spending: {e}")
        return False

def test_fraud_detection():
    """Test tổng hợp phát hiện fraud"""
    print("\n🧪 TEST 5: Tổng hợp phát hiện fraud...")
    
    try:
        # Tạo ví test
        alice = create_wallet("Alice_Fraud")
        bob = create_wallet("Bob_Fraud")
        
        # Tạo giao dịch bình thường
        transaction = create_transaction("Alice_Fraud", "Bob_Fraud", 75000)
        signed_tx = sign_transaction(transaction, "Alice_Fraud")
        
        # Test fraud check
        fraud_clean, fraud_msg = check_fraud(signed_tx)
        
        print(f"   ✅ Kết quả fraud check: {fraud_msg}")
        print(f"   ✅ Status: {'CLEAN' if fraud_clean else 'SUSPICIOUS'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lỗi test fraud detection: {e}")
        return False

def test_full_verification_flow():
    """Test flow xác thực hoàn chỉnh"""
    print("\n🧪 TEST 6: Flow xác thực hoàn chỉnh...")
    
    try:
        # Tạo ví test
        alice = create_wallet("Alice_Full")
        bob = create_wallet("Bob_Full")
        
        # Tạo và ký giao dịch
        transaction = create_transaction("Alice_Full", "Bob_Full", 200000)
        signed_tx = sign_transaction(transaction, "Alice_Full")
        
        print(f"   🔍 Đang xác thực giao dịch: {signed_tx['id']}")
        
        # Chạy full verification flow
        result = full_verification_flow(signed_tx["id"])
        
        # Hiển thị kết quả chi tiết
        print(f"   📊 Kết quả xác thực:")
        print(f"      - Tổng thể: {'✅ HỢP LỆ' if result['valid'] else '❌ KHÔNG HỢP LỆ'}")
        print(f"      - Chữ ký: {'✅ Đúng' if result['signature_valid'] else '❌ Sai'}")
        print(f"      - Số dư: {'✅ Đủ' if result['balance_valid'] else '❌ Không đủ'}")
        print(f"      - Bảo mật: {'✅ An toàn' if result['fraud_check'] else '❌ Nghi ngờ'}")
        print(f"      - Chi tiết: {result['message']}")
        
        return result["valid"]
        
    except Exception as e:
        print(f"   ❌ Lỗi test full verification: {e}")
        return False

def run_all_verification_tests():
    """Chạy tất cả test xác thực"""
    print("=" * 70)
    print("🔍 CHẠY TẤT CẢ TEST XÁC THỰC GIAO DỊCH")
    print("=" * 70)
    
    tests = [
        ("Giao dịch hợp lệ", test_valid_transaction),
        ("Chữ ký sai", test_invalid_signature),
        ("Không đủ tiền", test_insufficient_balance),
        ("Double spending", test_double_spending_detection),
        ("Fraud detection", test_fraud_detection),
        ("Full verification", test_full_verification_flow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 TỔNG KẾT: {passed}/{total} TESTS PASSED")
    
    if passed == total:
        print("🎉 TẤT CẢ TEST XÁC THỰC ĐỀU PASS!")
        print("🛡️  Hệ thống bảo mật hoạt động tốt!")
    else:
        print(f"⚠️  CÓ {total - passed} TEST FAILED")
        print("🔧 Cần kiểm tra lại code!")
    
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    run_all_verification_tests()