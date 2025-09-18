from ecdsa import VerifyingKey, SECP256k1
import json
import hashlib
import os
from core.wallet import get_wallet_info, update_balance
from core.transaction import get_transaction_by_id, get_latest_transaction
from security.fraud_detection import check_fraud

def verify_signature(transaction):
    """Xác minh chữ ký ECDSA"""
    try:
        # 1. Lấy thông tin cần thiết từ giao dịch
        signature_hex = transaction.get("signature")
        from_user = transaction.get("from")
        
        if not signature_hex:
            return False, "Giao dịch chưa có chữ ký"
            
        if not from_user:
            return False, "Giao dịch thiếu thông tin người gửi"
        
        # 2. Lấy khóa công khai của người gửi
        sender_wallet = get_wallet_info(from_user)
        if not sender_wallet:
            return False, f"Không tìm thấy ví của {from_user}"
        
        public_key_hex = sender_wallet["public_key"]
        public_key = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        
        # 3. Tái tạo hash từ transaction data (không bao gồm signature)
        transaction_copy = transaction.copy()
        if "signature" in transaction_copy:
            del transaction_copy["signature"]
            
        json_string = json.dumps(transaction_copy, sort_keys=True, separators=(',', ':'))
        message_hash = hashlib.sha256(json_string.encode('utf-8')).digest()
        
        # 4. Verify signature với public key
        signature_bytes = bytes.fromhex(signature_hex)
        
        try:
            public_key.verify(signature_bytes, message_hash)
            return True, "Chữ ký hợp lệ"
        except:
            return False, "Chữ ký không hợp lệ"
            
    except Exception as e:
        return False, f"Lỗi xác minh chữ ký: {str(e)}"

def check_balance(from_user, amount):
    """Kiểm tra số dư đủ không"""
    try:
        wallet_info = get_wallet_info(from_user)
        if not wallet_info:
            return False, f"Không tìm thấy ví của {from_user}"
            
        current_balance = wallet_info["balance"]
        
        if current_balance >= amount:
            return True, f"Số dư đủ: {current_balance:,} >= {amount:,}"
        else:
            return False, f"Số dư không đủ: {current_balance:,} < {amount:,}"
            
    except Exception as e:
        return False, f"Lỗi kiểm tra số dư: {str(e)}"

def validate_transaction_format(transaction):
    """Kiểm tra format giao dịch"""
    required_fields = ["id", "from", "to", "amount", "timestamp", "signature"]
    
    for field in required_fields:
        if field not in transaction:
            return False, f"Thiếu trường {field}"
            
    # Kiểm tra amount phải là số dương
    if not isinstance(transaction["amount"], (int, float)) or transaction["amount"] <= 0:
        return False, "Số tiền phải là số dương"
        
    # Kiểm tra người gửi và nhận khác nhau
    if transaction["from"] == transaction["to"]:
        return False, "Người gửi và người nhận không thể giống nhau"
        
    return True, "Format hợp lệ"

def execute_transaction(transaction):
    """Thực hiện giao dịch (chuyển tiền)"""
    try:
        from_user = transaction["from"]
        to_user = transaction["to"]
        amount = transaction["amount"]
        
        # Lấy thông tin ví
        sender_wallet = get_wallet_info(from_user)
        receiver_wallet = get_wallet_info(to_user)
        
        # Tính số dư mới
        new_sender_balance = sender_wallet["balance"] - amount
        new_receiver_balance = receiver_wallet["balance"] + amount
        
        # Cập nhật số dư
        update_balance(from_user, new_sender_balance)
        update_balance(to_user, new_receiver_balance)
        
        return True, f"Chuyển tiền thành công: {amount:,} VND từ {from_user} đến {to_user}"
        
    except Exception as e:
        return False, f"Lỗi thực hiện giao dịch: {str(e)}"

def update_transaction_status(tx_id, new_status):
    """Cập nhật status của giao dịch trong file JSON"""
    try:
        transactions_file = "data/transactions.json"
        
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r', encoding='utf-8') as f:
                transactions = json.load(f)
            
            # Tìm và cập nhật transaction
            for tx in transactions:
                if tx["id"] == tx_id:
                    tx["status"] = new_status
                    break
            
            # Ghi lại file
            with open(transactions_file, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, indent=2, ensure_ascii=False)
                
    except Exception as e:
        print(f"Lỗi cập nhật transaction status: {e}")

def full_verification_flow(tx_id=None):
    """Flow xác thực hoàn chỉnh - TRỌNG TÂM ĐỀ TÀI"""
    try:
        # Lấy giao dịch cần xác thực
        if tx_id:
            transaction = get_transaction_by_id(tx_id)
            if not transaction:
                return {
                    "valid": False,
                    "signature_valid": False,
                    "balance_valid": False,
                    "fraud_check": False,
                    "message": f"Không tìm thấy giao dịch {tx_id}"
                }
        else:
            transaction = get_latest_transaction()
            if not transaction:
                return {
                    "valid": False,
                    "signature_valid": False,
                    "balance_valid": False,
                    "fraud_check": False,
                    "message": "Không có giao dịch nào để xác thực"
                }
        
        print(f"🔍 Đang xác thực giao dịch: {transaction['id']}")
        
        # 1. Kiểm tra format transaction
        format_valid, format_msg = validate_transaction_format(transaction)
        if not format_valid:
            return {
                "valid": False,
                "signature_valid": False,
                "balance_valid": False,
                "fraud_check": False,
                "message": f"Format không hợp lệ: {format_msg}"
            }
        
        # 2. Verify chữ ký ECDSA
        signature_valid, sig_msg = verify_signature(transaction)
        
        # 3. Check số dư
        balance_valid, balance_msg = check_balance(transaction["from"], transaction["amount"])
        
        # 4. Check fraud (gọi fraud_detection)
        fraud_check_passed, fraud_msg = check_fraud(transaction)
        
        # 5. Tổng hợp kết quả (CHƯA execute)
        all_checks_passed = signature_valid and balance_valid and fraud_check_passed
        
        # 6. Nếu pass hết → Execute transaction SAU KHI xác thực xong
        execution_msg = ""
        if all_checks_passed:
            execute_success, exec_msg = execute_transaction(transaction)
            execution_msg = f" | {exec_msg}"
            
            # Cập nhật status giao dịch TRONG file JSON
            update_transaction_status(transaction["id"], "verified" if execute_success else "failed")
        else:
            # Cập nhật status là rejected
            update_transaction_status(transaction["id"], "rejected")
        
        # 7. Return kết quả chi tiết  
        final_status = "verified" if all_checks_passed else "rejected"
        result = {
            "valid": all_checks_passed,
            "signature_valid": signature_valid,
            "balance_valid": balance_valid,
            "fraud_check": fraud_check_passed,
            "message": f"{sig_msg} | {balance_msg} | {fraud_msg}{execution_msg}",
            "transaction_id": transaction["id"],
            "transaction_status": final_status
        }
        
        print(f"✅ Xác thực hoàn tất: {'PASS' if all_checks_passed else 'FAIL'}")
        return result
        
    except Exception as e:
        return {
            "valid": False,
            "signature_valid": False,
            "balance_valid": False,
            "fraud_check": False,
            "message": f"Lỗi trong quá trình xác thực: {str(e)}"
        }