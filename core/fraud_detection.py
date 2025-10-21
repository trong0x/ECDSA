from datetime import datetime, timedelta
from core.transaction import get_pending_transactions, get_transactions_by_wallet

def check_double_spending(transaction):
    """
    ✅ Kiểm tra chi tiêu kép với nonce
    Nếu có nonce → check nonce
    Nếu không có nonce → check theo thời gian (legacy)
    """
    try:
        current_tx = transaction
        current_from = current_tx.get("sender") or current_tx.get("from")
        current_nonce = current_tx.get("nonce")
        
        # Nếu có nonce → check nonce trùng
        if current_nonce is not None:
            pending_txs = get_pending_transactions(current_from)
            
            for tx in pending_txs:
                if tx["id"] == current_tx["id"]:
                    continue
                
                # Kiểm tra nonce trùng
                if tx.get("nonce") == current_nonce:
                    return False, f"⚠️ Double spending detected: Duplicate nonce {current_nonce}"
            
            return True, "✅ No double spending (nonce unique)"
        
        # Legacy check (không có nonce)
        current_amount = current_tx["amount"]
        current_id = current_tx["id"]
        
        pending_txs = get_pending_transactions(current_from)
        
        for tx in pending_txs:
            if tx["id"] == current_id:
                continue
            
            # Kiểm tra cùng người gửi, cùng số tiền
            if tx["amount"] == current_amount:
                try:
                    tx_time = datetime.fromisoformat(tx["timestamp"])
                    current_time = datetime.fromisoformat(current_tx["timestamp"])
                    
                    time_diff = abs((current_time - tx_time).total_seconds())
                    
                    if time_diff < 120:  # 2 phút
                        return False, f"⚠️ Phát hiện double spending: Giao dịch tương tự {tx['id'][:8]}... ({time_diff:.0f}s trước)"
                except Exception as e:
                    print(f"Lỗi parse timestamp: {e}")
                    continue
        
        return True, "✅ Không phát hiện double spending"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra double spending: {str(e)}"


def check_replay_attack(transaction):
    """
    ✅ Kiểm tra tấn công phát lại với nonce
    """
    try:
        tx_nonce = transaction.get("nonce")
        
        # Nếu có nonce → check nonce đã dùng chưa
        if tx_nonce is not None:
            from_user = transaction.get("sender") or transaction.get("from")
            
            # Lấy tất cả transactions của user
            all_txs = get_transactions_by_wallet(from_user, limit=1000)
            
            for tx in all_txs:
                if tx["id"] == transaction["id"]:
                    continue
                
                # Nếu nonce đã được dùng trong transaction verified
                if tx.get("nonce") == tx_nonce and tx.get("status") == "verified":
                    return False, f"⚠️ Replay attack: Nonce {tx_nonce} đã được sử dụng"
            
            return True, "✅ Không phát hiện replay (nonce chưa dùng)"
        
        # Legacy check (timestamp)
        tx_time = datetime.fromisoformat(transaction["timestamp"])
        current_time = datetime.now()
        time_diff = (current_time - tx_time).total_seconds()
        
        if time_diff > 600:  # 10 phút
            return False, f"⚠️ Giao dịch quá cũ ({time_diff/60:.1f} phút)"
        
        if time_diff < -60:  # Cho phép sai lệch 1 phút
            return False, "⚠️ Giao dịch có timestamp trong tương lai"
        
        # Check transaction ID có bị replay không
        from_user = transaction.get("sender") or transaction.get("from")
        all_txs = get_transactions_by_wallet(from_user, limit=100)
        
        count = 0
        for tx in all_txs:
            if (tx["id"] == transaction["id"] and 
                tx.get("status") in ["verified", "signed"]):
                count += 1
        
        if count >= 1:
            return False, f"⚠️ Transaction ID {transaction['id'][:8]}... bị replay"
        
        return True, "✅ Không phát hiện replay attack"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra replay attack: {str(e)}"


def check_transaction_expiry(transaction):
    """
    ✅ Kiểm tra transaction có hết hạn không
    """
    try:
        expires_at = transaction.get("expires_at")
        if not expires_at:
            return True, "No expiry set"
        
        expiry_time = datetime.fromisoformat(expires_at)
        
        if datetime.now() > expiry_time:
            return False, f"⚠️ Transaction expired at {expires_at}"
        
        return True, "✅ Transaction chưa hết hạn"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra expiry: {str(e)}"


def check_signature_tampering(transaction):
    """Kiểm tra chữ ký có bị thay đổi không"""
    try:
        signature = transaction.get("signature", "")
        
        if not signature:
            return False, "⚠️ Giao dịch không có chữ ký"
        
        # Kiểm tra độ dài signature (ECDSA signature thường ~64 bytes = 128 hex chars)
        if len(signature) < 64 or len(signature) > 140:
            return False, f"⚠️ Chữ ký có độ dài bất thường: {len(signature)} characters"
        
        # Kiểm tra có phải hex hợp lệ không
        try:
            bytes.fromhex(signature)
        except ValueError:
            return False, "⚠️ Chữ ký không phải hex hợp lệ"
        
        return True, "✅ Chữ ký có format hợp lệ"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra signature tampering: {str(e)}"


def check_amount_manipulation(transaction):
    """Kiểm tra số tiền có bị thao túng không - FIXED for float/int"""
    try:
        amount = transaction.get("amount", 0)
        
        if amount <= 0:
            return False, "⚠️ Số tiền phải lớn hơn 0"
        
        if amount > 100000000:  # 100 triệu VND
            return False, f"⚠️ Số tiền quá lớn (>100 triệu VND): {amount:,}"
        
        # ✅ FIX: Accept both int and float (database returns float)
        if not isinstance(amount, (int, float)):
            return False, "⚠️ Số tiền phải là số"
        
        return True, "✅ Số tiền hợp lý"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra amount manipulation: {str(e)}"


def check_fraud(transaction):
    """
    Tổng hợp kiểm tra gian lận
    """
    try:
        print(f"🔒 Kiểm tra bảo mật cho giao dịch {transaction['id'][:8]}...")
        
        fraud_results = []
        
        # 1. Kiểm tra double spending
        ds_check, ds_msg = check_double_spending(transaction)
        fraud_results.append(("Double Spending", ds_check, ds_msg))
        if not ds_check:
            return False, f"❌ {ds_msg}"
        
        # 2. Kiểm tra replay attack
        ra_check, ra_msg = check_replay_attack(transaction)
        fraud_results.append(("Replay Attack", ra_check, ra_msg))
        if not ra_check:
            return False, f"❌ {ra_msg}"
        
        # 3. ✅ Kiểm tra expiry
        ex_check, ex_msg = check_transaction_expiry(transaction)
        fraud_results.append(("Expiry", ex_check, ex_msg))
        if not ex_check:
            return False, f"❌ {ex_msg}"
        
        # 4. Kiểm tra signature tampering
        st_check, st_msg = check_signature_tampering(transaction)
        fraud_results.append(("Signature", st_check, st_msg))
        if not st_check:
            return False, f"❌ {st_msg}"
        
        # 5. Kiểm tra amount manipulation
        am_check, am_msg = check_amount_manipulation(transaction)
        fraud_results.append(("Amount", am_check, am_msg))
        if not am_check:
            return False, f"❌ {am_msg}"
        
        # In kết quả
        print("📊 Kết quả kiểm tra:")
        for check_name, passed, msg in fraud_results:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}: {msg}")
        
        return True, "✅ Tất cả kiểm tra bảo mật đều PASS"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra fraud: {str(e)}"


def get_fraud_statistics():
    """Thống kê các loại tấn công đã phát hiện"""
    try:
        from core.transaction import get_transaction_stats
        
        stats = get_transaction_stats()
        
        return {
            "total_transactions": stats["total"],
            "verified_transactions": stats["verified"],
            "rejected_transactions": stats["rejected"],
            "pending_transactions": stats["pending"],
            "fraud_attempts": stats["rejected"],
            "success_rate": stats["success_rate"],
            "fraud_rate": f"{(stats['rejected']/max(stats['total'],1)*100):.1f}%"
        }
        
    except Exception as e:
        return {"error": f"Lỗi lấy thống kê: {str(e)}"}