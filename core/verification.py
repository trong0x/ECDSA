# core/verification.py - FIXED VERSION

from ecdsa import VerifyingKey, SECP256k1
import json
import hashlib
from core.wallet import get_wallet_info
from core.database import  _lock
from core.transaction import (
    get_transaction_by_id, 
    get_latest_transaction,
    update_transaction_status,
)
from core.fraud_detection import check_fraud

def verify_signature(transaction):
    """Xác minh chữ ký ECDSA - Database compatible"""
    try:
        signature_hex = transaction.get("signature")
        
        # ✅ Handle both 'from' and 'sender'
        from_user = transaction.get("sender") or transaction.get("from")

        if not signature_hex:
            return False, "Giao dịch chưa có chữ ký"
        if not from_user:
            return False, "Giao dịch thiếu thông tin người gửi"

        sender_wallet = get_wallet_info(from_user)
        if not sender_wallet:
            return False, f"Không tìm thấy ví của {from_user}"

        public_key_hex = sender_wallet["public_key"]
        public_key = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)

        # ✅ CRITICAL FIX: Use ORIGINAL field names from transaction
        # Get the field names exactly as they were when signing
        to_user = transaction.get("receiver") or transaction.get("to")
        
        # Build fields with EXACT same structure as in transaction.sign_transaction()
        fields_to_sign = {
            "id": transaction["id"],
            "from": from_user,  # Use the normalized value
            "to": to_user,      # Use the normalized value
            "amount": int(transaction["amount"]),  # ✅ FIX: Cast to int để tránh float mismatch
            "timestamp": transaction["timestamp"],
            "from_address": transaction.get("from_address", ""),
            "to_address": transaction.get("to_address", ""),
            "nonce": transaction.get("nonce", 0)
        }

        # Create the exact same JSON string as when signing
        json_string = json.dumps(fields_to_sign, sort_keys=True, separators=(',', ':'))
        message_hash = hashlib.sha256(json_string.encode('utf-8')).digest()

        signature_bytes = bytes.fromhex(signature_hex)
        
        try:
            public_key.verify(signature_bytes, message_hash)
            return True, "Chữ ký hợp lệ"
        except Exception as verify_error:
            # Debug: print what we're verifying
            print(f"❌ Signature verification failed!")
            print(f"   Expected to sign: {json_string[:100]}...")
            print(f"   From user: {from_user}")
            print(f"   To user: {to_user}")
            return False, f"Chữ ký không hợp lệ: {str(verify_error)}"

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
    """Kiểm tra format giao dịch - Database compatible"""
    # ✅ Check for both 'from'/'to' and 'sender'/'receiver'
    from_field = transaction.get("from") or transaction.get("sender")
    to_field = transaction.get("to") or transaction.get("receiver")
    
    # Required fields
    if not transaction.get("id"):
        return False, "Thiếu trường id"
    
    if not from_field:
        return False, "Thiếu trường from/sender"
    
    if not to_field:
        return False, "Thiếu trường to/receiver"
    
    if "amount" not in transaction:
        return False, "Thiếu trường amount"
    
    if not transaction.get("timestamp"):
        return False, "Thiếu trường timestamp"
    
    if not transaction.get("signature"):
        return False, "Thiếu trường signature"
    
    # Validate amount
    amount = transaction.get("amount")
    if not isinstance(amount, (int, float)) or amount <= 0:
        return False, "Số tiền phải lớn hơn 0 (không chấp nhận số âm hoặc 0)"
    
    # Validate sender != receiver
    if from_field == to_field:
        return False, "Người gửi và người nhận không thể giống nhau"
        
    return True, "Format hợp lệ"


def execute_transaction_atomic(transaction):
    """
    Thực hiện giao dịch ATOMIC với database transaction
    Đảm bảo balance update là atomic operation
    """
    # ✅ Handle both field names
    from_user = transaction.get("sender") or transaction.get("from")
    to_user = transaction.get("receiver") or transaction.get("to")
    amount = transaction["amount"]
    tx_id = transaction["id"]
    
    try:
        with _lock:
            from core.database import get_connection
            
            conn = get_connection()
            cursor = conn.cursor()
            
            try:
                # Begin transaction
                cursor.execute("BEGIN EXCLUSIVE")
                
                # 1. Get current balances (with lock)
                sender = cursor.execute(
                    "SELECT balance FROM wallets WHERE name = ?",
                    (from_user,)
                ).fetchone()
                
                receiver = cursor.execute(
                    "SELECT balance FROM wallets WHERE name = ?",
                    (to_user,)
                ).fetchone()
                
                if not sender or not receiver:
                    cursor.execute("ROLLBACK")
                    return False, "Wallet not found"
                
                sender_balance = sender[0]
                receiver_balance = receiver[0]
                
                # 2. Verify balance again (double-check)
                if sender_balance < amount:
                    cursor.execute("ROLLBACK")
                    return False, f"Insufficient balance: {sender_balance} < {amount}"
                
                # 3. Update balances atomically
                cursor.execute(
                    "UPDATE wallets SET balance = balance - ? WHERE name = ?",
                    (amount, from_user)
                )
                
                cursor.execute(
                    "UPDATE wallets SET balance = balance + ? WHERE name = ?",
                    (amount, to_user)
                )
                
                # 4. Mark transaction as executed
                cursor.execute(
                    "UPDATE transactions SET executed = 1, status = 'verified' WHERE id = ?",
                    (tx_id,)
                )
                
                # Commit transaction
                conn.commit()
                
                print(f"✅ Transaction executed: {amount:,} VND from {from_user} to {to_user}")
                
                # Print updated balances
                new_sender_balance = sender_balance - amount
                new_receiver_balance = receiver_balance + amount
                print(f"   {from_user}: {sender_balance:,} → {new_sender_balance:,} VND")
                print(f"   {to_user}: {receiver_balance:,} → {new_receiver_balance:,} VND")
                
                return True, "Transaction executed successfully"
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                return False, f"Database error: {str(e)}"
            
    except Exception as e:
        return False, f"Atomic execution error: {str(e)}"


def full_verification_flow(tx_id=None):
    """
    Flow xác thực hoàn chỉnh - DATABASE VERSION
    """
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
                    "message": f"Không tìm thấy giao dịch {tx_id}",
                    "transaction_id": tx_id,
                    "transaction_status": "not_found"
                }
        else:
            transaction = get_latest_transaction()
            if not transaction:
                return {
                    "valid": False,
                    "signature_valid": False,
                    "balance_valid": False,
                    "fraud_check": False,
                    "message": "Không có giao dịch nào để xác thực",
                    "transaction_id": None,
                    "transaction_status": "no_transaction"
                }
        
        print(f"🔍 Đang xác thực giao dịch: {transaction['id'][:8]}...")
        
        # ✅ Normalize transaction fields for verification
        if "sender" in transaction and "from" not in transaction:
            transaction["from"] = transaction["sender"]
        if "receiver" in transaction and "to" not in transaction:
            transaction["to"] = transaction["receiver"]
        
        # ✅ Check if already executed
        if transaction.get("executed"):
            print(f"⚠️  Transaction already executed")
            return {
                "valid": False,
                "signature_valid": False,
                "balance_valid": False,
                "fraud_check": False,
                "message": "Transaction already executed",
                "transaction_id": transaction["id"],
                "transaction_status": "executed"
            }
        
        # 1. Kiểm tra format transaction
        format_valid, format_msg = validate_transaction_format(transaction)
        if not format_valid:
            update_transaction_status(transaction["id"], "rejected")
            return {
                "valid": False,
                "signature_valid": False,
                "balance_valid": False,
                "fraud_check": False,
                "message": f"Format không hợp lệ: {format_msg}",
                "transaction_id": transaction["id"],
                "transaction_status": "rejected"
            }
        
        # 2. Verify chữ ký ECDSA
        signature_valid, sig_msg = verify_signature(transaction)
        
        # 3. Check số dư
        from_user = transaction.get("from") or transaction.get("sender")
        balance_valid, balance_msg = check_balance(from_user, transaction["amount"])
        
        # 4. Check fraud
        fraud_check_passed, fraud_msg = check_fraud(transaction)
        
        # 5. Tổng hợp kết quả
        all_checks_passed = signature_valid and balance_valid and fraud_check_passed
        
        # 6. Execute transaction ATOMICALLY if all checks pass
        execution_msg = ""
        
        if all_checks_passed:
            print(f"✅ All checks passed. Executing transaction...")
            success, exec_msg = execute_transaction_atomic(transaction)
            
            if success:
                execution_msg = f" | {exec_msg}"
                final_status = "verified"
                print(f"✅ Transaction executed successfully")
            else:
                execution_msg = f" | Execution failed: {exec_msg}"
                final_status = "rejected"
                all_checks_passed = False
                print(f"❌ Execution failed: {exec_msg}")
        else:
            update_transaction_status(transaction["id"], "rejected")
            execution_msg = " | Giao dịch bị từ chối"
            final_status = "rejected"
            print(f"❌ Verification failed")
        
        # 7. Return kết quả chi tiết
        result = {
            "valid": all_checks_passed,
            "signature_valid": signature_valid,
            "balance_valid": balance_valid,
            "fraud_check": fraud_check_passed,
            "message": f"{sig_msg} | {balance_msg} | {fraud_msg}{execution_msg}",
            "transaction_id": transaction["id"],
            "transaction_status": final_status
        }
        
        status_icon = "✅" if all_checks_passed else "❌"
        print(f"{status_icon} Xác thực hoàn tất: {'PASS' if all_checks_passed else 'FAIL'}")
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "valid": False,
            "signature_valid": False,
            "balance_valid": False,
            "fraud_check": False,
            "message": f"Lỗi trong quá trình xác thực: {str(e)}",
            "transaction_id": tx_id or "unknown",
            "transaction_status": "error"
        }