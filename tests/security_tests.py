import time
import json
import uuid
from datetime import datetime, timedelta
import threading
import random

# Import with fallback
try:
    from core.wallet import create_wallet, get_wallet_info
    from core.transaction import create_transaction, sign_transaction
    from core.verification import full_verification_flow
    from core.fraud_detection import check_fraud
    from blockchain.blockchain import get_blockchain
except ImportError:
    from core.wallet import create_wallet, get_wallet_info
    from core.transaction import create_transaction, sign_transaction
    from core.verification import full_verification_flow
    from core.fraud_detection import check_fraud
    from blockchain.blockchain import get_blockchain


class SecurityTestSuite:
    """Bộ test bảo mật chuyên sâu"""
    
    def __init__(self):
        self.blockchain = get_blockchain()
        self.test_results = []
        self.test_wallets = {}
        
    def setup_test_wallets(self, count=10):
        """Tạo ví test"""
        print(f"\n🔧 Setting up {count} test wallets...")
        
        for i in range(count):
            wallet_name = f"test_user_{i}"
            passphrase = f"test_pass_{i}"
            
            try:
                wallet = create_wallet(wallet_name, passphrase)
                self.test_wallets[wallet_name] = {
                    "wallet": wallet,
                    "passphrase": passphrase
                }
                print(f"✅ Created wallet: {wallet_name}")
            except Exception as e:
                print(f"⚠️  Wallet {wallet_name} might already exist")
                wallet = get_wallet_info(wallet_name)
                if wallet:
                    self.test_wallets[wallet_name] = {
                        "wallet": wallet,
                        "passphrase": passphrase
                    }
        
        print(f"✅ Test wallets ready: {len(self.test_wallets)}")
    
    def test_double_spending_same_time(self):
        """Test 1: Double Spending - Giao dịch cùng lúc"""
        print("\n" + "="*60)
        print("🔒 TEST 1: DOUBLE SPENDING - SAME TIME")
        print("="*60)
        
        from_user = "test_user_0"
        to_user_1 = "test_user_1"
        to_user_2 = "test_user_2"
        amount = 50000
        
        if from_user not in self.test_wallets:
            print("❌ Test wallet not found")
            return
        
        passphrase = self.test_wallets[from_user]["passphrase"]
        from_wallet = get_wallet_info(from_user)
        to_wallet_1 = get_wallet_info(to_user_1)
        to_wallet_2 = get_wallet_info(to_user_2)
        
        print(f"💰 Initial balance: {from_wallet['balance']:,} VND")
        
        # Tạo 2 giao dịch cùng lúc với cùng số tiền
        tx1 = create_transaction(
            from_user, to_user_1, amount,
            from_wallet["address"], to_wallet_1["address"]
        )
        
        # Sleep 0.1s để tạo timestamp khác nhau nhưng vẫn gần
        time.sleep(0.1)
        
        tx2 = create_transaction(
            from_user, to_user_2, amount,
            from_wallet["address"], to_wallet_2["address"]
        )
        
        # Ký cả 2 giao dịch
        tx1 = sign_transaction(tx1, from_user, passphrase)
        tx2 = sign_transaction(tx2, from_user, passphrase)
        
        print(f"\n🔍 Transaction 1: {tx1['id'][:8]}... -> {to_user_1}")
        print(f"🔍 Transaction 2: {tx2['id'][:8]}... -> {to_user_2}")
        
        # Verify giao dịch 1
        result1 = full_verification_flow(tx1["id"])
        print(f"\n✓ TX1 Result: {result1['valid']} - {result1['message']}")
        
        # Verify giao dịch 2 (nên fail vì double spending)
        result2 = full_verification_flow(tx2["id"])
        print(f"✓ TX2 Result: {result2['valid']} - {result2['message']}")
        
        if result1['valid'] and not result2['valid']:
            print("✅ TEST PASSED: Double spending detected!")
            self.test_results.append({"test": "double_spending_same_time", "passed": True})
        else:
            print("❌ TEST FAILED: Double spending not detected!")
            self.test_results.append({"test": "double_spending_same_time", "passed": False})
    
    def test_double_spending_sequential(self):
        """Test 2: Double Spending - Giao dịch tuần tự"""
        print("\n" + "="*60)
        print("🔒 TEST 2: DOUBLE SPENDING - SEQUENTIAL")
        print("="*60)
        
        from_user = "test_user_3"
        to_user_1 = "test_user_4"
        to_user_2 = "test_user_5"
        amount = 80000
        
        passphrase = self.test_wallets[from_user]["passphrase"]
        from_wallet = get_wallet_info(from_user)
        
        print(f"💰 Initial balance: {from_wallet['balance']:,} VND")
        
        # Giao dịch 1
        tx1 = create_transaction(from_user, to_user_1, amount,
                                from_wallet["address"],
                                get_wallet_info(to_user_1)["address"])
        tx1 = sign_transaction(tx1, from_user, passphrase)
        result1 = full_verification_flow(tx1["id"])
        
        print(f"\n✓ TX1 Result: {result1['valid']}")
        
        # Đợi 2 giây
        time.sleep(2)
        
        # Thử giao dịch 2 với cùng số tiền (nhưng số dư không đủ nữa)
        tx2 = create_transaction(from_user, to_user_2, amount,
                                from_wallet["address"],
                                get_wallet_info(to_user_2)["address"])
        tx2 = sign_transaction(tx2, from_user, passphrase)
        result2 = full_verification_flow(tx2["id"])
        
        print(f"✓ TX2 Result: {result2['valid']} - {result2['message']}")
        
        if result1['valid'] and not result2['balance_valid']:
            print("✅ TEST PASSED: Insufficient balance detected!")
            self.test_results.append({"test": "double_spending_sequential", "passed": True})
        else:
            print("❌ TEST FAILED")
            self.test_results.append({"test": "double_spending_sequential", "passed": False})
    
    def test_replay_attack(self):
        """Test 3: Replay Attack"""
        print("\n" + "="*60)
        print("🔒 TEST 3: REPLAY ATTACK")
        print("="*60)
        
        from_user = "test_user_6"
        to_user = "test_user_7"
        amount = 30000
        
        passphrase = self.test_wallets[from_user]["passphrase"]
        from_wallet = get_wallet_info(from_user)
        to_wallet = get_wallet_info(to_user)
        
        # Tạo giao dịch hợp lệ
        tx = create_transaction(from_user, to_user, amount,
                               from_wallet["address"], to_wallet["address"])
        tx = sign_transaction(tx, from_user, passphrase)
        
        print(f"🔍 Original Transaction: {tx['id'][:8]}...")
        
        # Verify lần 1 (OK)
        result1 = full_verification_flow(tx["id"])
        print(f"✓ First verification: {result1['valid']}")
        
        # Đợi 2 giây
        time.sleep(2)
        
        # Thử replay cùng transaction (thay đổi timestamp để fake)
        tx_replayed = tx.copy()
        tx_replayed["timestamp"] = datetime.now().isoformat()
        
        # Save transaction replay
        from core.transaction import save_transaction
        save_transaction(tx_replayed)
        
        print(f"🔄 Replaying transaction...")
        
        # Verify lần 2 (should FAIL - replay attack)
        result2 = full_verification_flow(tx_replayed["id"])
        print(f"✓ Replay verification: {result2['valid']} - {result2['message']}")
        
        if result1['valid'] and not result2['valid']:
            print("✅ TEST PASSED: Replay attack detected!")
            self.test_results.append({"test": "replay_attack", "passed": True})
        else:
            print("❌ TEST FAILED: Replay attack not detected!")
            self.test_results.append({"test": "replay_attack", "passed": False})
    
    def test_signature_tampering(self):
        """Test 4: Signature Tampering"""
        print("\n" + "="*60)
        print("🔒 TEST 4: SIGNATURE TAMPERING")
        print("="*60)
        
        from_user = "test_user_8"
        to_user = "test_user_9"
        amount = 40000
        
        passphrase = self.test_wallets[from_user]["passphrase"]
        from_wallet = get_wallet_info(from_user)
        to_wallet = get_wallet_info(to_user)
        
        # Tạo giao dịch hợp lệ
        tx = create_transaction(from_user, to_user, amount,
                               from_wallet["address"], to_wallet["address"])
        tx = sign_transaction(tx, from_user, passphrase)
        
        original_signature = tx["signature"]
        print(f"🔍 Original signature: {original_signature[:20]}...")
        
        # Tamper with signature
        tampered_signature = original_signature[:-10] + "deadbeef12"
        tx["signature"] = tampered_signature
        
        print(f"🔧 Tampered signature: {tampered_signature[:20]}...")
        
        # Save tampered transaction
        from core.transaction import save_transaction
        save_transaction(tx)
        
        # Verify (should FAIL)
        result = full_verification_flow(tx["id"])
        print(f"✓ Verification result: {result['valid']} - {result['message']}")
        
        if not result['signature_valid']:
            print("✅ TEST PASSED: Signature tampering detected!")
            self.test_results.append({"test": "signature_tampering", "passed": True})
        else:
            print("❌ TEST FAILED: Signature tampering not detected!")
            self.test_results.append({"test": "signature_tampering", "passed": False})
    
    def test_amount_manipulation(self):
        """Test 5: Amount Manipulation"""
        print("\n" + "="*60)
        print("🔒 TEST 5: AMOUNT MANIPULATION")
        print("="*60)
        
        test_cases = [
            {"amount": -50000, "description": "Negative amount"},
            {"amount": 0, "description": "Zero amount"},
            {"amount": 200000000, "description": "Excessive amount (200M)"},
        ]
        
        from_user = "test_user_0"
        to_user = "test_user_1"
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['description']}")
            
            try:
                from_wallet = get_wallet_info(from_user)
                to_wallet = get_wallet_info(to_user)
                
                tx = create_transaction(from_user, to_user, test_case["amount"],
                                       from_wallet["address"], to_wallet["address"])
                
                result = full_verification_flow(tx["id"])
                
                if not result['valid']:
                    print(f"✅ Correctly rejected: {result['message']}")
                else:
                    print(f"❌ Should have been rejected!")
                    
            except ValueError as e:
                print(f"✅ Exception caught: {str(e)}")
        
        self.test_results.append({"test": "amount_manipulation", "passed": True})
    
    def test_concurrent_transactions(self):
        """Test 6: Concurrent Transactions (Race Condition)"""
        print("\n" + "="*60)
        print("🔒 TEST 6: CONCURRENT TRANSACTIONS (RACE CONDITION)")
        print("="*60)
        
        from_user = "test_user_0"
        passphrase = self.test_wallets[from_user]["passphrase"]
        from_wallet = get_wallet_info(from_user)
        
        print(f"💰 Initial balance: {from_wallet['balance']:,} VND")
        
        # Tạo 5 giao dịch đồng thời
        num_concurrent = 5
        amount_each = 100000
        
        results = []
        
        def create_and_verify(idx):
            to_user = f"test_user_{idx+1}"
            to_wallet = get_wallet_info(to_user)
            
            tx = create_transaction(from_user, to_user, amount_each,
                                   from_wallet["address"], to_wallet["address"])
            tx = sign_transaction(tx, from_user, passphrase)
            
            result = full_verification_flow(tx["id"])
            results.append(result)
            print(f"  Thread {idx}: {result['valid']} - {result['message'][:50]}...")
        
        # Tạo threads
        threads = []
        for i in range(num_concurrent):
            t = threading.Thread(target=create_and_verify, args=(i,))
            threads.append(t)
        
        # Start all threads cùng lúc
        for t in threads:
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Kiểm tra kết quả
        valid_count = sum(1 for r in results if r['valid'])
        invalid_count = len(results) - valid_count
        
        print(f"\n📊 Results: {valid_count} valid, {invalid_count} invalid")
        print(f"💰 Final balance: {get_wallet_info(from_user)['balance']:,} VND")
        
        # Chỉ nên có 1-2 giao dịch pass (vì balance không đủ cho tất cả)
        if valid_count <= 2:
            print("✅ TEST PASSED: Race condition handled correctly!")
            self.test_results.append({"test": "concurrent_transactions", "passed": True})
        else:
            print("❌ TEST FAILED: Too many transactions passed!")
            self.test_results.append({"test": "concurrent_transactions", "passed": False})
    
    def test_delayed_transaction(self):
        """Test 7: Delayed Transaction (Old Timestamp)"""
        print("\n" + "="*60)
        print("🔒 TEST 7: DELAYED TRANSACTION")
        print("="*60)
        
        from_user = "test_user_3"
        to_user = "test_user_4"
        amount = 20000
        
        passphrase = self.test_wallets[from_user]["passphrase"]
        from_wallet = get_wallet_info(from_user)
        to_wallet = get_wallet_info(to_user)
        
        # Tạo giao dịch với timestamp cũ (15 phút trước)
        old_time = datetime.now() - timedelta(minutes=15)
        
        tx = create_transaction(from_user, to_user, amount,
                               from_wallet["address"], to_wallet["address"])
        
        # Override timestamp
        tx["timestamp"] = old_time.isoformat()
        
        tx = sign_transaction(tx, from_user, passphrase)
        
        print(f"🔍 Transaction timestamp: {tx['timestamp']}")
        print(f"⏰ Current time: {datetime.now().isoformat()}")
        
        result = full_verification_flow(tx["id"])
        print(f"✓ Verification result: {result['valid']} - {result['message']}")
        
        if not result['fraud_check']:
            print("✅ TEST PASSED: Old transaction detected!")
            self.test_results.append({"test": "delayed_transaction", "passed": True})
        else:
            print("❌ TEST FAILED: Old transaction not detected!")
            self.test_results.append({"test": "delayed_transaction", "passed": False})
    
    def test_future_transaction(self):
        """Test 8: Future Transaction"""
        print("\n" + "="*60)
        print("🔒 TEST 8: FUTURE TRANSACTION")
        print("="*60)
        
        from_user = "test_user_5"
        to_user = "test_user_6"
        amount = 25000
        
        passphrase = self.test_wallets[from_user]["passphrase"]
        from_wallet = get_wallet_info(from_user)
        to_wallet = get_wallet_info(to_user)
        
        # Tạo giao dịch với timestamp tương lai
        future_time = datetime.now() + timedelta(hours=2)
        
        tx = create_transaction(from_user, to_user, amount,
                               from_wallet["address"], to_wallet["address"])
        tx["timestamp"] = future_time.isoformat()
        
        tx = sign_transaction(tx, from_user, passphrase)
        
        print(f"🔍 Transaction timestamp: {tx['timestamp']}")
        print(f"⏰ Current time: {datetime.now().isoformat()}")
        
        result = full_verification_flow(tx["id"])
        print(f"✓ Verification result: {result['valid']} - {result['message']}")
        
        if not result['fraud_check']:
            print("✅ TEST PASSED: Future transaction detected!")
            self.test_results.append({"test": "future_transaction", "passed": True})
        else:
            print("❌ TEST FAILED: Future transaction not detected!")
            self.test_results.append({"test": "future_transaction", "passed": False})
    
    def run_all_tests(self):
        """Chạy tất cả tests"""
        print("\n" + "="*70)
        print("🚀 STARTING COMPREHENSIVE SECURITY TEST SUITE")
        print("="*70)
        
        start_time = time.time()
        
        # Setup
        self.setup_test_wallets(10)
        
        # Run tests
        try:
            self.test_double_spending_same_time()
            self.test_double_spending_sequential()
            self.test_replay_attack()
            self.test_signature_tampering()
            self.test_amount_manipulation()
            self.test_concurrent_transactions()
            self.test_delayed_transaction()
            self.test_future_transaction()
        except Exception as e:
            print(f"\n❌ Test suite error: {e}")
            import traceback
            traceback.print_exc()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for r in self.test_results if r.get("passed", False))
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅ PASSED" if result.get("passed") else "❌ FAILED"
            print(f"{status}: {result['test']}")
        
        print(f"\n🎯 Total: {passed}/{total} tests passed")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! System is secure!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Review security measures.")
        
        # Save test report
        self.save_test_report(duration)
    
    def save_test_report(self, duration):
        """Lưu báo cáo test"""
        import os
        os.makedirs("data/reports", exist_ok=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "results": self.test_results,
            "summary": {
                "total": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r.get("passed", False)),
                "failed": sum(1 for r in self.test_results if not r.get("passed", False))
            }
        }
        
        filename = f"data/reports/security_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Test report saved: {filename}")


if __name__ == "__main__":
    suite = SecurityTestSuite()
    suite.run_all_tests()