import json
import hashlib
import time
from datetime import datetime
from core.database import (
    save_block, 
    load_all_blocks, 
    get_blockchain_metadata,
    set_blockchain_metadata,
    delete_all_blocks
)

class Block:
    """Khối blockchain chứa nhiều giao dịch"""
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Tính hash của block"""
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty):
        """Proof of Work - mining"""
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print(f"⛏️  Block mined: {self.hash[:32]}...")
        return self
    
    def to_dict(self):
        return {
            "index": self.index,
            "transactions": self.transactions,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class Blockchain:
    """Blockchain chính - SQLite3 version"""
    def __init__(self, difficulty=2):
        self.chain = []
        self.difficulty = int(get_blockchain_metadata("difficulty", difficulty))
        self.pending_transactions = []
        self.mining_reward = int(get_blockchain_metadata("mining_reward", 100))
        self.transaction_fee_rate = 0.001  
        self.max_transactions_per_block = 10
        
        # ✅ Load từ SQLite thay vì JSON
        self.load_blockchain()
        
        # Tạo genesis block nếu chưa có
        if len(self.chain) == 0:
            self.create_genesis_block()
    
    def create_genesis_block(self):
        """Tạo block đầu tiên"""
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_blockchain()
        print("✅ Genesis block created!")
    
    def get_latest_block(self):
        """Lấy block mới nhất"""
        return self.chain[-1] if self.chain else None
    
    def calculate_transaction_fee(self, amount):
        """Tính phí giao dịch dựa trên số tiền"""
        fee = int(amount * self.transaction_fee_rate)
        return max(fee, 100)  
    
    def add_transaction(self, transaction):
        """Thêm giao dịch vào pending pool"""
        # Kiểm tra transaction đã được verify chưa
        if transaction.get("status") != "verified":
            print(f"❌ Transaction {transaction['id'][:8]}... chưa được verify")
            return False
        
        # Kiểm tra double-spending trong pending pool
        for pending_tx in self.pending_transactions:
            if (pending_tx.get("sender") == transaction.get("sender") and 
                pending_tx["id"] != transaction["id"]):
                print(f"⚠️  Warning: User {transaction.get('sender')} có giao dịch pending khác")
        
        self.pending_transactions.append(transaction)
        print(f"📝 Transaction {transaction['id'][:8]}... added to pending pool")
        
        # Tự động mine nếu đủ số lượng
        if len(self.pending_transactions) >= self.max_transactions_per_block:
            self.mine_pending_transactions()
        
        return True
    
    def mine_pending_transactions(self, miner_address="system"):
        """Mine các giao dịch pending thành block mới"""
        if len(self.pending_transactions) == 0:
            print("⚠️  Không có giao dịch nào để mine")
            return None
        
        # Lấy tối đa max_transactions_per_block giao dịch
        transactions_to_mine = self.pending_transactions[:self.max_transactions_per_block]
        
        # Tính tổng fees từ các transactions
        total_fees = 0
        for tx in transactions_to_mine:
            fee = self.calculate_transaction_fee(tx.get("amount", 0))
            total_fees += fee
        
        # Tạo mining reward transaction
        reward_tx = {
            "id": f"reward_block_{len(self.chain)}",
            "from": "SYSTEM",
            "to": miner_address,
            "sender": "SYSTEM",
            "receiver": miner_address,
            "amount": self.mining_reward + total_fees,
            "timestamp": datetime.now().isoformat(),
            "type": "mining_reward",
            "status": "verified",
            "signature": "SYSTEM_REWARD",
            "executed": True
        }
        
        # Thêm reward vào danh sách transactions
        all_transactions = transactions_to_mine + [reward_tx]
        
        # Tạo block mới
        previous_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            transactions=all_transactions,
            timestamp=time.time(),
            previous_hash=previous_block.hash
        )
        
        print(f"⛏️  Mining block {new_block.index} with {len(transactions_to_mine)} transactions + reward...")
        new_block.mine_block(self.difficulty)
        
        # Thêm block vào chain
        self.chain.append(new_block)
        
        # Xóa các giao dịch đã mine khỏi pending pool
        self.pending_transactions = self.pending_transactions[self.max_transactions_per_block:]
        
        # ✅ Lưu vào SQLite
        self.save_blockchain()
        
        print(f"✅ Block {new_block.index} mined successfully!")
        print(f"   Reward: {self.mining_reward:,} VND")
        print(f"   Fees: {total_fees:,} VND")
        print(f"   Total: {self.mining_reward + total_fees:,} VND")
        print(f"📊 Remaining pending transactions: {len(self.pending_transactions)}")
        
        # Update balance của miner (nếu có wallet)
        if miner_address != "system":
            try:
                from core.wallet import get_wallet_info, update_balance
                miner_wallet = get_wallet_info(miner_address)
                if miner_wallet:
                    new_balance = miner_wallet["balance"] + self.mining_reward + total_fees
                    update_balance(miner_address, new_balance)
                    print(f"💰 Miner balance updated: {new_balance:,} VND")
            except Exception as e:
                print(f"⚠️  Could not update miner balance: {e}")
        
        return new_block
    
    def is_chain_valid(self):
        """Kiểm tra tính hợp lệ của blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Kiểm tra hash của block hiện tại
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Block {i} has invalid hash")
                return False
            
            # Kiểm tra liên kết với block trước
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Block {i} has invalid previous_hash")
                return False
            
            # Kiểm tra proof of work
            if not current_block.hash.startswith("0" * self.difficulty):
                print(f"❌ Block {i} has invalid proof of work")
                return False
        
        return True
    
    def get_balance(self, address):
        """Tính số dư của một địa chỉ từ blockchain"""
        balance = 0
        
        for block in self.chain:
            for tx in block.transactions:
                sender = tx.get("from") or tx.get("sender")
                receiver = tx.get("to") or tx.get("receiver")
                
                if sender == address:
                    balance -= tx.get("amount", 0)
                if receiver == address:
                    balance += tx.get("amount", 0)
        
        return balance
    
    def get_transaction_history(self, address):
        """Lấy lịch sử giao dịch của một địa chỉ"""
        history = []
        
        for block in self.chain:
            for tx in block.transactions:
                sender = tx.get("from") or tx.get("sender")
                receiver = tx.get("to") or tx.get("receiver")
                
                if sender == address or receiver == address:
                    history.append({
                        "block": block.index,
                        "transaction": tx,
                        "block_hash": block.hash,
                        "block_time": block.timestamp
                    })
        
        return history
    
    def find_transaction(self, tx_id):
        """Tìm giao dịch trong blockchain"""
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("id") == tx_id:
                    return {
                        "transaction": tx,
                        "block": block.index,
                        "block_hash": block.hash,
                        "confirmations": len(self.chain) - block.index
                    }
        return None
    
    def get_transaction_by_id(self, tx_id):
        """Lấy transaction theo ID từ blockchain"""
        result = self.find_transaction(tx_id)
        if result:
            return {
                "transaction": result["transaction"],
                "block_index": result["block"],
                "block_hash": result["block_hash"],
                "confirmations": result["confirmations"]
            }
        return None
    
    def get_chain_info(self):
        """Lấy thông tin tổng quan về blockchain"""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        return {
            "total_blocks": len(self.chain),
            "total_transactions": total_transactions,
            "difficulty": self.difficulty,
            "is_valid": self.is_chain_valid(),
            "latest_block_hash": self.get_latest_block().hash if self.chain else None,
            "pending_transactions": len(self.pending_transactions)
        }
    
    def reset_chain(self):
        """Reset blockchain (for testing only)"""
        self.chain = []
        self.pending_transactions = []
        delete_all_blocks()  # ✅ Xóa từ SQLite
        self.create_genesis_block()
        print("🔄 Blockchain reset complete")
    
    def save_blockchain(self):
        """✅ Lưu blockchain vào SQLite thay vì JSON"""
        try:
            # Save all blocks
            for block in self.chain:
                block_dict = block.to_dict()
                save_block(block_dict)
            
            # Save metadata
            set_blockchain_metadata("difficulty", self.difficulty)
            set_blockchain_metadata("mining_reward", self.mining_reward)
            
        except Exception as e:
            print(f"❌ Error saving blockchain: {e}")
    
    def load_blockchain(self):
        """✅ Load blockchain từ SQLite thay vì JSON"""
        try:
            blocks_data = load_all_blocks()
            
            if not blocks_data:
                print("ℹ️  No blocks found in database")
                return
            
            # Reconstruct chain
            for block_data in blocks_data:
                block = Block(
                    index=block_data["index"],
                    transactions=block_data["transactions"],
                    timestamp=block_data["timestamp"],
                    previous_hash=block_data["previous_hash"],
                    nonce=block_data["nonce"]
                )
                block.hash = block_data["hash"]
                self.chain.append(block)
            
            print(f"✅ Blockchain loaded from SQLite: {len(self.chain)} blocks")
            
        except Exception as e:
            print(f"❌ Error loading blockchain: {e}")
    
    def get_blockchain_stats(self):
        """Thống kê blockchain"""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        
        # Đếm mining rewards
        mining_rewards_count = 0
        total_rewards = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("type") == "mining_reward":
                    mining_rewards_count += 1
                    total_rewards += tx.get("amount", 0)
        
        return {
            "total_blocks": len(self.chain),
            "total_transactions": total_transactions,
            "pending_transactions": len(self.pending_transactions),
            "difficulty": self.difficulty,
            "mining_reward": self.mining_reward,
            "total_mining_rewards": total_rewards,
            "latest_block_hash": self.get_latest_block().hash if self.chain else None,
            "is_valid": self.is_chain_valid(),
            "storage": "SQLite3"  # ✅ Indicator
        }

# Singleton instance
_blockchain_instance = None

def get_blockchain():
    """Lấy instance blockchain (singleton pattern)"""
    global _blockchain_instance
    if _blockchain_instance is None:
        _blockchain_instance = Blockchain(difficulty=2)
    return _blockchain_instance