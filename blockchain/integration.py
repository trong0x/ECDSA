from datetime import datetime
from blockchain.blockchain import Blockchain
from core.wallet import get_wallet_info
from core.fraud_detection import check_fraud
from core.transaction import (
    get_all_transactions,
    get_transaction_by_id,
    update_transaction_status
)
from core.database import fetch_all, execute

class BlockchainIntegration:
    """Quản lý blockchain cho hệ thống - PURE DB VERSION"""
    
    def __init__(self, difficulty=4):
        self.blockchain = Blockchain(difficulty=difficulty)
        self.mempool = []  # Pool chứa transactions chờ mine
        self.sync_with_database()  # ✅ Sync from DB, not JSON
        
    def sync_with_database(self):
        """Đồng bộ transactions từ DATABASE vào blockchain"""
        try:
            #  Lấy từ DATABASE 
            db_txs = get_all_transactions()  # From database.py
            
            #Lấy các verified transactions chưa có trong blockchain
            blockchain_tx_ids = set()
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    blockchain_tx_ids.add(tx["id"])
            
            #  Chỉ sync transactions đã verified và executed
            pending_verified = [
                tx for tx in db_txs 
                if tx.get("status") == "verified" 
                and tx.get("executed") == 1
                and tx["id"] not in blockchain_tx_ids
            ]
            
            if pending_verified:
                print(f"🔄 Đồng bộ {len(pending_verified)} transactions từ DATABASE vào blockchain...")
                for tx in pending_verified:
                    self.blockchain.add_transaction(tx)
                
                # Mine block nếu có transactions
                if self.blockchain.pending_transactions:
                    self.blockchain.mine_pending_transactions("system_sync")
                    print(f"✅ Đã đồng bộ vào blockchain")
                    
        except Exception as e:
            print(f"⚠️ Lỗi đồng bộ: {e}")
            import traceback
            traceback.print_exc()
    
    def add_transaction_to_mempool(self, transaction):
        """
        Thêm transaction vào mempool (chờ mine)
        Chỉ thêm nếu transaction đã được verified và executed
        """
        try:
            # Validate transaction format
            if not transaction.get("signature"):
                return False, "❌ Transaction chưa có chữ ký"
            
            if transaction.get("status") not in ["signed", "pending"]:
                return False, f"❌ Transaction không ở trạng thái hợp lệ: {transaction.get('status')}"
            
            # ✅ Check if already in blockchain
            existing = self.blockchain.find_transaction(transaction["id"])
            if existing:
                return False, "❌ Transaction already in blockchain"
            
            # ✅ Check if already in mempool
            if any(tx["id"] == transaction["id"] for tx in self.mempool):
                return False, "❌ Transaction already in mempool"
            
            # Check fraud
            fraud_passed, fraud_msg = check_fraud(transaction)
            if not fraud_passed:
                update_transaction_status(transaction["id"], "rejected")
                return False, f"❌ Fraud check failed: {fraud_msg}"
            
            # Check balance
            sender_wallet = get_wallet_info(transaction.get("sender") or transaction.get("from"))
            if not sender_wallet:
                return False, f"❌ Không tìm thấy ví: {transaction.get('sender')}"
            
            if sender_wallet["balance"] < transaction["amount"]:
                update_transaction_status(transaction["id"], "rejected")
                return False, f"❌ Số dư không đủ: {sender_wallet['balance']:,} < {transaction['amount']:,}"
            
            # ✅ Add to mempool (NOT executed yet)
            self.mempool.append(transaction)
            update_transaction_status(transaction["id"], "pending_in_mempool")
            
            print(f"✅ Added transaction {transaction['id'][:8]}... to mempool")
            
            return True, f"✅ Transaction added to mempool (waiting for mining)"
            
        except Exception as e:
            return False, f"❌ Error adding to mempool: {str(e)}"
    
    def mine_block(self, miner_address="system"):
        """
        Mine block từ các transactions trong mempool
        """
        try:
            if not self.mempool:
                return False, "⚠️ No transactions in mempool"
            
            print(f"\n⛏️ Mining {len(self.mempool)} transactions...")
            
            valid_transactions = []
            rejected_transactions = []
            
            for tx in self.mempool:
                try:
                    # ✅ Check if transaction is already verified and executed
                    if tx.get("status") == "verified" and tx.get("executed"):
                        valid_transactions.append(tx)
                        print(f"✅ Including: {tx['id'][:8]}... (already verified & executed)")
                    else:
                        print(f"⚠️ Skipping: {tx['id'][:8]}... (status: {tx.get('status')}, executed: {tx.get('executed')})")
                        rejected_transactions.append(tx)
                        
                except Exception as e:
                    update_transaction_status(tx["id"], "rejected")
                    rejected_transactions.append(tx)
                    print(f"❌ Error processing {tx['id'][:8]}...: {e}")
            
            # Update rejected transactions
            for tx in rejected_transactions:
                update_transaction_status(tx["id"], "rejected")
            
            if not valid_transactions:
                self.mempool = []
                return False, f"⚠️ No valid transactions to mine ({len(rejected_transactions)} rejected)"
            
            # ✅ Add to blockchain
            for tx in valid_transactions:
                self.blockchain.add_transaction(tx)
            
            # Mine block
            import time
            start_time = time.time()
            block = self.blockchain.mine_pending_transactions(miner_address)
            end_time = time.time()
            
            # Clear mempool
            self.mempool = []
            
            if block:
                mining_time = end_time - start_time
                print(f"✅ Block {block.index} mined in {mining_time:.2f}s with {len(valid_transactions)} transactions")
                print(f"   Hash: {block.hash[:32]}...")
                print(f"   Rejected: {len(rejected_transactions)} transactions")
                
                return True, {
                    "block_index": block.index,
                    "block_hash": block.hash,
                    "transactions_count": len(valid_transactions),
                    "rejected_count": len(rejected_transactions),
                    "mining_time": f"{mining_time:.2f}s"
                }
            else:
                return False, "❌ Failed to mine block"
                
        except Exception as e:
            return False, f"❌ Mining error: {str(e)}"
    
    def add_verified_transaction(self, transaction):
        """Thêm transaction đã verified và executed vào blockchain"""
        try:
            # Verify transaction is actually verified and executed
            if transaction.get("status") != "verified":
                return False, f"Transaction not verified: status={transaction.get('status')}"
            
            if not transaction.get("executed"):
                return False, "Transaction not executed yet"
            
            # Check if already in blockchain
            existing = self.blockchain.find_transaction(transaction["id"])
            if existing:
                return False, "Transaction already in blockchain"
            
            # Add to blockchain
            self.blockchain.add_transaction(transaction)
            print(f"✅ Added verified transaction to blockchain: {transaction['id'][:8]}...")
            
            # Auto-mine if enough transactions
            if len(self.blockchain.pending_transactions) >= self.blockchain.max_transactions_per_block:
                self.blockchain.mine_pending_transactions()
                print(f"✅ Auto-mined block with {self.blockchain.max_transactions_per_block} transactions")
            
            return True, "Transaction added to blockchain"
            
        except Exception as e:
            return False, f"Error adding to blockchain: {str(e)}"
    
    def get_transaction_status(self, tx_id):
        """Lấy status của transaction"""
        # Check mempool
        for tx in self.mempool:
            if tx["id"] == tx_id:
                return {
                    "status": "pending_in_mempool",
                    "location": "mempool",
                    "confirmations": 0,
                    "message": "Waiting for mining"
                }
        
        # Check blockchain
        result = self.blockchain.get_transaction_by_id(tx_id)
        if result:
            return {
                "status": "confirmed",
                "location": "blockchain",
                "block_index": result["block_index"],
                "block_hash": result["block_hash"],
                "confirmations": result["confirmations"],
                "message": f"Confirmed in block {result['block_index']}"
            }
        
        # Check DATABASE (not JSON)
        tx = get_transaction_by_id(tx_id)
        if tx:
            return {
                "status": tx.get("status", "unknown"),
                "location": "database",
                "confirmations": 0,
                "message": f"Status: {tx.get('status')}"
            }
        
        return None
    
    def get_blockchain_stats(self):
        """Thống kê blockchain"""
        chain_info = self.blockchain.get_chain_info()
        
        # Thống kê từ DATABASE 
        db_txs = get_all_transactions()
        db_verified = len([tx for tx in db_txs if tx.get("status") == "verified"])
        db_rejected = len([tx for tx in db_txs if tx.get("status") == "rejected"])
        db_pending = len([tx for tx in db_txs if tx.get("status") in ["pending", "signed"]])
        
        return {
            "blockchain": {
                "total_blocks": chain_info["total_blocks"],
                "total_transactions": chain_info["total_transactions"],
                "difficulty": chain_info["difficulty"],
                "is_valid": chain_info["is_valid"],
                "latest_block_hash": chain_info["latest_block_hash"]
            },
            "mempool": {
                "pending_in_mempool": len(self.mempool)
            },
            "database": {  # Changed from "json_store" to "database"
                "verified": db_verified,
                "rejected": db_rejected,
                "pending": db_pending,
                "total": len(db_txs)
            }
        }
    
    def validate_chain(self):
        """Validate toàn bộ blockchain"""
        is_valid = self.blockchain.is_chain_valid()
        
        if is_valid:
            print("✅ Blockchain is valid")
        else:
            print("❌ Blockchain is INVALID!")
        
        return is_valid
    
    def get_all_transactions(self):
        """Lấy tất cả transactions (blockchain + mempool + database)"""
        blockchain_txs = []
        for block in self.blockchain.chain:
            blockchain_txs.extend(block.transactions)
        
        # Lấy từ DATABASE (not JSON)
        db_txs = get_all_transactions()
        
        # Merge (Ưu tiên blockchain)
        blockchain_tx_ids = {tx["id"] for tx in blockchain_txs}
        
        all_confirmed = blockchain_txs
        all_pending = self.mempool + [
            tx for tx in db_txs 
            if tx["id"] not in blockchain_tx_ids and tx.get("status") in ["pending", "signed"]
        ]
        
        return {
            "confirmed": all_confirmed,
            "pending": all_pending,
            "total": len(all_confirmed) + len(all_pending)
        }
    
    def reset_blockchain(self):
        """Reset blockchain (only for testing)"""
        self.blockchain.reset_chain()
        self.mempool = []
        print("🔄 Blockchain reset complete")
    
    def get_block_by_index(self, index):
        """Lấy block theo index"""
        if 0 <= index < len(self.blockchain.chain):
            return self.blockchain.chain[index].to_dict()
        return None
    
    def get_all_blocks(self):
        """Lấy tất cả blocks"""
        return [block.to_dict() for block in self.blockchain.chain]


# Singleton instance
_blockchain_instance = None

def get_blockchain_instance():
    """Lấy blockchain instance (singleton)"""
    global _blockchain_instance
    if _blockchain_instance is None:
        _blockchain_instance = BlockchainIntegration(difficulty=4)
    return _blockchain_instance


if __name__ == "__main__":
    print("🔗 Blockchain Integration - PURE DATABASE VERSION\n")
    
    bc = get_blockchain_instance()
    
    # Test
    from core.wallet import create_wallet, get_wallet_info
    from core.transaction import create_transaction, sign_transaction
    from core.verification import full_verification_flow
    
    try:
        alice = create_wallet("db_alice", "alice123", 1000000)
        bob = create_wallet("db_bob", "bob123", 1000000)
        print(f"✅ Created wallets\n")
    except:
        print("⚠️ Wallets already exist\n")
    
    # Create transaction
    tx = create_transaction("db_alice", "db_bob", 50000)
    tx = sign_transaction(tx, "db_alice", "alice123")
    print(f"✅ Transaction created: {tx['id'][:8]}...\n")
    
    # Verify and execute
    result = full_verification_flow(tx["id"])
    print(f"{'✅' if result['valid'] else '❌'} Verification: {result['valid']}\n")
    
    if result['valid']:
        # Add to blockchain
        success, msg = bc.add_verified_transaction(tx)
        print(f"{'✅' if success else '❌'} {msg}\n")
    
    # Stats
    stats = bc.get_blockchain_stats()
    print(f"📊 Stats:")
    print(f"   Blocks: {stats['blockchain']['total_blocks']}")
    print(f"   DB verified: {stats['database']['verified']}")
    print(f"   DB pending: {stats['database']['pending']}")