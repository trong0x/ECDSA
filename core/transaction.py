from ecdsa import SigningKey, VerifyingKey, SECP256k1
import json
import hashlib
import os
from datetime import datetime
from core.wallet import get_wallet_info, get_private_key

def create_transaction(from_user, to_user, amount):
    """Tạo giao dịch mới"""
    try:
        # 1. Kiểm tra ví người gửi tồn tại
        sender_wallet = get_wallet_info(from_user)
        if not sender_wallet:
            raise Exception(f"Không tìm thấy ví của {from_user}")
        
        # 2. Kiểm tra ví người nhận tồn tại  
        receiver_wallet = get_wallet_info(to_user)
        if not receiver_wallet:
            raise Exception(f"Không tìm thấy ví của {to_user}")
            
        # 3. Kiểm tra số dư đủ không
        if sender_wallet["balance"] < amount:
            raise Exception(f"Số dư không đủ. Có: {sender_wallet['balance']:,}, Cần: {amount:,}")
        
        # 4. Tạo ID giao dịch unique
        timestamp = datetime.now().isoformat()
        tx_string = f"{from_user}{to_user}{amount}{timestamp}"
        tx_id = hashlib.sha256(tx_string.encode()).hexdigest()[:16]
        
        # 5. Tạo dict giao dịch
        transaction = {
            "id": f"TX_{tx_id}",
            "from": from_user,
            "to": to_user,
            "amount": amount,
            "timestamp": timestamp,
            "from_address": sender_wallet["address"],
            "to_address": receiver_wallet["address"],
            "status": "pending"
        }
        
        return transaction
        
    except Exception as e:
        raise Exception(f"Lỗi tạo giao dịch: {str(e)}")

def sign_transaction(transaction, from_user):
    """Ký giao dịch bằng ECDSA"""
    try:
        # 1. Lấy khóa riêng của người gửi
        private_key = get_private_key(from_user)
        
        # 2. Chuyển transaction thành JSON string (loại bỏ signature nếu có)
        transaction_copy = transaction.copy()
        if "signature" in transaction_copy:
            del transaction_copy["signature"]
            
        # Sắp xếp keys để đảm bảo consistent
        json_string = json.dumps(transaction_copy, sort_keys=True, separators=(',', ':'))
        
        # 3. Hash bằng SHA256
        message_hash = hashlib.sha256(json_string.encode('utf-8')).digest()
        
        # 4. Ký hash bằng private key
        signature = private_key.sign(message_hash)
        
        # 5. Thêm signature vào transaction
        signed_transaction = transaction.copy()
        signed_transaction["signature"] = signature.hex()
        signed_transaction["status"] = "signed"
        
        # 6. Lưu giao dịch đã ký
        save_transaction(signed_transaction)
        
        return signed_transaction
        
    except Exception as e:
        raise Exception(f"Lỗi ký giao dịch: {str(e)}")

def save_transaction(signed_tx):
    """Lưu giao dịch vào file"""
    try:
        transactions_file = "data/transactions.json"
        
        # Tạo thư mục data nếu chưa có
        os.makedirs("data", exist_ok=True)
        
        # Đọc transactions hiện tại
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r', encoding='utf-8') as f:
                transactions = json.load(f)
        else:
            transactions = []
        
        # Thêm giao dịch mới
        transactions.append(signed_tx)
        
        # Ghi lại file
        with open(transactions_file, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Đã lưu giao dịch {signed_tx['id']}")
        
    except Exception as e:
        raise Exception(f"Lỗi lưu giao dịch: {str(e)}")

def get_transaction_by_id(tx_id):
    """Lấy giao dịch theo ID"""
    try:
        transactions_file = "data/transactions.json"
        
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r', encoding='utf-8') as f:
                transactions = json.load(f)
                
            for tx in transactions:
                if tx["id"] == tx_id:
                    return tx
                    
        return None
        
    except Exception as e:
        raise Exception(f"Lỗi tìm giao dịch: {str(e)}")

def get_latest_transaction():
    """Lấy giao dịch mới nhất"""
    try:
        transactions_file = "data/transactions.json"
        
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r', encoding='utf-8') as f:
                transactions = json.load(f)
                
            if transactions:
                return transactions[-1]  # Giao dịch cuối cùng
                
        return None
        
    except Exception as e:
        raise Exception(f"Lỗi lấy giao dịch mới nhất: {str(e)}")

def get_all_transactions():
    """Lấy tất cả giao dịch"""
    try:
        transactions_file = "data/transactions.json"
        
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []
            
    except Exception as e:
        raise Exception(f"Lỗi lấy danh sách giao dịch: {str(e)}")