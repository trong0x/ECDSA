import time
import random
import json
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.wallet import create_wallet, get_wallet_info, update_balance
from core.transaction import create_transaction, sign_transaction
from core.verification import full_verification_flow
from blockchain.blockchain import get_blockchain

class MassTransactionTester:
    """Test hệ thống với hàng nghìn tài khoản và giao dịch"""
    
    def __init__(self, num_accounts=1000):
        self.num_accounts = num_accounts
        self.accounts = []
        self.blockchain = get_blockchain()
        self.stats = {
            "total_transactions": 0,
            "successful_transactions": 0,
            "failed_transactions": 0,
            "double_spending_detected": 0,
            "replay_attacks_detected": 0,
            "invalid_signatures": 0,
            "insufficient_balance": 0
        }
    
    def create_mass_accounts(self):
        """Tạo hàng nghìn tài khoản"""
        print(f"\n🏭 Creating {self.num_accounts} accounts...")
        start_time = time.time()
        
        for i in range(self.num_accounts):
            account_name = f"user_{i:06d}"
            passphrase = f"pass_{i:06d}"
            
            try:
                # Kiểm tra xem account đã tồn tại chưa
                existing = get_wallet_info(account_name)
                if existing:
                    self.accounts.append({
                        "name": account_name,
                        "passphrase": passphrase,
                        "wallet": existing
                    })
                else:
                    wallet = create_wallet(account_name, passphrase)
                    # Set initial balance cao hơn để test
                    update_balance(account_name, random.randint(500000, 5000000))
                    
                    self.accounts.append({
                        "name": account_name,
                        "passphrase": passphrase,
                        "wallet": wallet
                    })
                
                if (i + 1) % 100 == 0:
                    print(f"  ✓ Created {i + 1}/{self.num_accounts} accounts...")
                    
            except Exception as e:
                print(f"  ⚠️  Error creating account {account_name}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Created {len(self.accounts)} accounts in {duration:.2f}s")
        print(f"⚡ Rate: {len(self.accounts)/duration:.2f} accounts/second")
    
    def generate_random_transaction(self):
        """Tạo một giao dịch ngẫu nhiên"""
        if len(self.accounts) < 2:
            return None
        
        # Chọn ngẫu nhiên người gửi và người nhận
        sender = random.choice(self.accounts)
        receiver = random.choice([acc for acc in self.accounts if acc["name"] != sender["name"]])
        
        # Số tiền ngẫu nhiên
        amount = random.randint(1000, 100000)
        
        sender_wallet = get_wallet_info(sender["name"])
        receiver_wallet = get_wallet_info(receiver["name"])

# Nếu ví chưa tồn tại hoặc bị lỗi -> bỏ qua giao dịch này
        if not sender_wallet or not receiver_wallet:
           # tạo lại ví nếu bị thiếu
            print(f"⚠️ Ví bị thiếu — tạo lại {sender['name']} hoặc {receiver['name']}")
        if not sender_wallet:
            wallet = create_wallet(sender["name"], sender["passphrase"])
            update_balance(sender["name"], random.randint(500000, 5000000))
            sender_wallet = wallet
        if not receiver_wallet:
            wallet = create_wallet(receiver["name"], receiver["passphrase"])
            update_balance(receiver["name"], random.randint(500000, 5000000))
            receiver_wallet = wallet
        
        return {
            "from": sender["name"],
            "to": receiver["name"],
            "amount": amount,
            "passphrase": sender["passphrase"],
            "from_address": sender_wallet["address"],
            "to_address": receiver_wallet["address"]
        }
    
    def execute_transaction(self, tx_data):
        """Thực thi một giao dịch"""
        try:
            # Tạo transaction
            tx = create_transaction(
                tx_data["from"],
                tx_data["to"],
                tx_data["amount"],
                tx_data["from_address"],
                tx_data["to_address"]
            )
            
            # Ký transaction
            tx = sign_transaction(tx, tx_data["from"], tx_data["passphrase"])
            
            # Verify transaction
            result = full_verification_flow(tx["id"])
            
            self.stats["total_transactions"] += 1
            
            if result["valid"]:
                self.stats["successful_transactions"] += 1
                
                # Thêm vào blockchain
                self.blockchain.add_transaction(tx)
            else:
                self.stats["failed_transactions"] += 1
                
                # Phân loại lỗi
                if "double spending" in result["message"].lower():
                    self.stats["double_spending_detected"] += 1
                elif "replay" in result["message"].lower():
                    self.stats["replay_attacks_detected"] += 1
                elif "chữ ký" in result["message"].lower() or "signature" in result["message"].lower():
                    self.stats["invalid_signatures"] += 1
                elif "số dư" in result["message"].lower() or "balance" in result["message"].lower():
                    self.stats["insufficient_balance"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_transactions"] += 1
            return {"valid": False, "error": str(e)}
    
    def run_sequential_test(self, num_transactions=10000):
        """Test tuần tự với nhiều giao dịch"""
        print(f"\n📊 Running sequential test with {num_transactions} transactions...")
        start_time = time.time()
        
        for i in range(num_transactions):
            tx_data = self.generate_random_transaction()
            if tx_data:
                self.execute_transaction(tx_data)
            
            if (i + 1) % 1000 == 0:
                print(f"  ✓ Processed {i + 1}/{num_transactions} transactions...")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Sequential test completed in {duration:.2f}s")
        print(f"⚡ Rate: {num_transactions/duration:.2f} tx/second")
        self.print_stats()
    
    def run_concurrent_test(self, num_transactions=10000, max_workers=10):
        """Test đồng thời với nhiều threads"""
        print(f"\n🔀 Running concurrent test with {num_transactions} transactions...")
        print(f"   Workers: {max_workers} threads")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for i in range(num_transactions):
                tx_data = self.generate_random_transaction()
                if tx_data:
                    future = executor.submit(self.execute_transaction, tx_data)
                    futures.append(future)
            
            # Wait for completion
            completed = 0
            for future in as_completed(futures):
                completed += 1
                if completed % 1000 == 0:
                    print(f"  ✓ Completed {completed}/{num_transactions} transactions...")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Concurrent test completed in {duration:.2f}s")
        print(f"⚡ Rate: {num_transactions/duration:.2f} tx/second")
        self.print_stats()
    
    def simulate_double_spending_attack(self, num_attacks=100):
        """Mô phỏng tấn công double spending"""
        print(f"\n💣 Simulating {num_attacks} double-spending attacks...")
        
        attack_stats = {
            "attempted": 0,
            "blocked": 0,
            "succeeded": 0
        }
        
        for i in range(num_attacks):
            if len(self.accounts) < 2:
                break
            
            # Chọn kẻ tấn công
            attacker = random.choice(self.accounts)
            attacker_wallet = get_wallet_info(attacker["name"])
            
            # Chọn 2 nạn nhân
            victims = random.sample([acc for acc in self.accounts if acc["name"] != attacker["name"]], 2)
            
            amount = min(attacker_wallet["balance"] - 10000, 50000)
            if amount <= 0:
                continue
            
            attack_stats["attempted"] += 1
            
            # Tạo 2 giao dịch cùng lúc với cùng số tiền
            tx1_data = {
                "from": attacker["name"],
                "to": victims[0]["name"],
                "amount": amount,
                "passphrase": attacker["passphrase"],
                "from_address": attacker_wallet["address"],
                "to_address": get_wallet_info(victims[0]["name"])["address"]
            }
            
            tx2_data = {
                "from": attacker["name"],
                "to": victims[1]["name"],
                "amount": amount,
                "passphrase": attacker["passphrase"],
                "from_address": attacker_wallet["address"],
                "to_address": get_wallet_info(victims[1]["name"])["address"]
            }
            
            # Thực thi gần như đồng thời
            result1 = self.execute_transaction(tx1_data)
            time.sleep(0.01)  # Delay rất ngắn
            result2 = self.execute_transaction(tx2_data)
            
            # Kiểm tra kết quả
            if result1["valid"] and result2["valid"]:
                attack_stats["succeeded"] += 1
                print(f"  ⚠️  ALERT: Double-spending succeeded! (Attack #{i+1})")
            else:
                attack_stats["blocked"] += 1
        
        print(f"\n🛡️  Double-Spending Attack Results:")
        print(f"   Attempted: {attack_stats['attempted']}")
        print(f"   Blocked: {attack_stats['blocked']}")
        print(f"   Succeeded: {attack_stats['succeeded']}")
        
        if attack_stats['succeeded'] == 0:
            print("   ✅ ALL ATTACKS BLOCKED!")
        else:
            print(f"   ⚠️  {attack_stats['succeeded']} attacks succeeded!")
    
    def simulate_replay_attacks(self, num_attacks=50):
        """Mô phỏng tấn công replay"""
        print(f"\n🔄 Simulating {num_attacks} replay attacks...")
        
        attack_stats = {
            "attempted": 0,
            "blocked": 0,
            "succeeded": 0
        }
        
        # Tạo một số giao dịch hợp lệ trước
        valid_transactions = []
        
        for i in range(num_attacks):
            tx_data = self.generate_random_transaction()
            if tx_data:
                result = self.execute_transaction(tx_data)
                if result.get("valid"):
                    valid_transactions.append(result.get("transaction_id"))
        
        print(f"   Created {len(valid_transactions)} valid transactions")
        
        # Thử replay các giao dịch
        for tx_id in valid_transactions[:num_attacks]:
            attack_stats["attempted"] += 1
            
            # Thử verify lại giao dịch cũ
            result = full_verification_flow(tx_id)
            
            if result["valid"]:
                attack_stats["succeeded"] += 1
                print(f"  ⚠️  ALERT: Replay attack succeeded! TX: {tx_id[:8]}...")
            else:
                attack_stats["blocked"] += 1
        
        print(f"\n🛡️  Replay Attack Results:")
        print(f"   Attempted: {attack_stats['attempted']}")
        print(f"   Blocked: {attack_stats['blocked']}")
        print(f"   Succeeded: {attack_stats['succeeded']}")
        
        if attack_stats['succeeded'] == 0:
            print("   ✅ ALL REPLAY ATTACKS BLOCKED!")
        else:
            print(f"   ⚠️  {attack_stats['succeeded']} replay attacks succeeded!")
    
    def print_stats(self):
        """In thống kê"""
        print(f"\n📈 Transaction Statistics:")
        print(f"   Total: {self.stats['total_transactions']}")
        print(f"   Successful: {self.stats['successful_transactions']} ({self.stats['successful_transactions']/max(self.stats['total_transactions'],1)*100:.1f}%)")
        print(f"   Failed: {self.stats['failed_transactions']} ({self.stats['failed_transactions']/max(self.stats['total_transactions'],1)*100:.1f}%)")
        print(f"\n🔍 Fraud Detection:")
        print(f"   Double Spending: {self.stats['double_spending_detected']}")
        print(f"   Replay Attacks: {self.stats['replay_attacks_detected']}")
        print(f"   Invalid Signatures: {self.stats['invalid_signatures']}")
        print(f"   Insufficient Balance: {self.stats['insufficient_balance']}")
        
        # Blockchain stats
        bc_stats = self.blockchain.get_blockchain_stats()
        print(f"\n⛓️  Blockchain Statistics:")
        print(f"   Total Blocks: {bc_stats['total_blocks']}")
        print(f"   Total Transactions in Chain: {bc_stats['total_transactions']}")
        print(f"   Pending Transactions: {bc_stats['pending_transactions']}")
        print(f"   Chain Valid: {bc_stats['is_valid']}")
    
    def save_report(self):
        """Lưu báo cáo"""
        os.makedirs("data/reports", exist_ok=True)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_config": {
                "num_accounts": self.num_accounts,
                "total_transactions": self.stats["total_transactions"]
            },
            "statistics": self.stats,
            "blockchain_stats": self.blockchain.get_blockchain_stats()
        }
        
        filename = f"data/reports/mass_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Report saved: {filename}")

def main():
    """Main function"""
    print("="*70)
    print("🚀 MASS TRANSACTION TESTING SYSTEM")
    print("="*70)
    
    # Menu
    print("\nSelect test mode:")
    print("1. Quick test (100 accounts, 1000 transactions)")
    print("2. Medium test (1000 accounts, 10000 transactions)")
    print("3. Heavy test (5000 accounts, 50000 transactions)")
    print("4. Attack simulation only")
    print("5. Custom test")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        num_accounts, num_transactions = 100, 1000
    elif choice == "2":
        num_accounts, num_transactions = 1000, 10000
    elif choice == "3":
        num_accounts, num_transactions = 5000, 50000
    elif choice == "4":
        num_accounts, num_transactions = 100, 0
    elif choice == "5":
        num_accounts = int(input("Number of accounts: "))
        num_transactions = int(input("Number of transactions: "))
    else:
        print("Invalid choice!")
        return
    
    # Initialize tester
    tester = MassTransactionTester(num_accounts)
    
    # Create accounts
    tester.create_mass_accounts()
    
    # Run tests
    if num_transactions > 0:
        # Sequential test
        print("\n" + "="*70)
        print("PHASE 1: SEQUENTIAL TESTING")
        print("="*70)
        tester.run_sequential_test(num_transactions // 2)
        
        # Concurrent test
        print("\n" + "="*70)
        print("PHASE 2: CONCURRENT TESTING")
        print("="*70)
        tester.run_concurrent_test(num_transactions // 2, max_workers=20)
    
    # Attack simulations
    print("\n" + "="*70)
    print("PHASE 3: SECURITY ATTACK SIMULATIONS")
    print("="*70)
    
    tester.simulate_double_spending_attack(100)
    tester.simulate_replay_attacks(50)
    
    # Final stats
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    tester.print_stats()
    
    # Save report
    tester.save_report()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()