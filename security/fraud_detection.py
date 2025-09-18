import json
import os
from datetime import datetime, timedelta

def check_double_spending(transaction):
    """Kiểm tra chi tiêu kép"""
    try:
        transactions_file = "data/transactions.json"
        
        if not os.path.exists(transactions_file):
            return True, "Không có giao dịch trước đó để so sánh"
        
        # Đọc tất cả giao dịch
        with open(transactions_file, 'r', encoding='utf-8') as f:
            all_transactions = json.load(f)
        
        current_tx = transaction
        current_from = current_tx["from"]
        current_amount = current_tx["amount"]
        current_id = current_tx["id"]
        
        # Kiểm tra giao dịch trùng lặp
        for tx in all_transactions:
            # Bỏ qua giao dịch hiện tại
            if tx["id"] == current_id:
                continue
                
            # Kiểm tra cùng người gửi, cùng số tiền, trong thời gian ngắn
            if (tx["from"] == current_from and 
                tx["amount"] == current_amount and
                tx.get("status") in ["verified", "signed"]):
                
                # Kiểm tra thời gian (trong vòng 1 phút)
                tx_time = datetime.fromisoformat(tx["timestamp"])
                current_time = datetime.fromisoformat(current_tx["timestamp"])
                
                if abs((current_time - tx_time).total_seconds()) < 60:
                    return False, f"Phát hiện double spending: Giao dịch tương tự {tx['id']} đã tồn tại"
        
        return True, "Không phát hiện double spending"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra double spending: {str(e)}"

def check_replay_attack(transaction):
    """Kiểm tra tấn công phát lại"""
    try:
        # 1. Check timestamp có quá cũ không (hơn 10 phút)
        tx_time = datetime.fromisoformat(transaction["timestamp"])
        current_time = datetime.now()
        time_diff = (current_time - tx_time).total_seconds()
        
        if time_diff > 600:  # 10 phút
            return False, f"Giao dịch quá cũ ({time_diff/60:.1f} phút)"
        
        # 2. Check timestamp có trong tương lai không
        if time_diff < -60:  # Cho phép sai lệch 1 phút
            return False, "Giao dịch có timestamp trong tương lai"
        
        # 3. Check transaction ID có trùng không (nhưng cho phép giao dịch đang được xác thực)
        transactions_file = "data/transactions.json"
        
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r', encoding='utf-8') as f:
                all_transactions = json.load(f)
            
            # Đếm số lần transaction ID xuất hiện
            count = 0
            for tx in all_transactions:
                if tx["id"] == transaction["id"]:
                    count += 1
            
            # Nếu xuất hiện >= 2 lần thì mới coi là replay
            if count >= 2:
                return False, f"Transaction ID {transaction['id']} bị replay (xuất hiện {count} lần)"
        
        return True, "Không phát hiện replay attack"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra replay attack: {str(e)}"

def check_signature_tampering(transaction):
    """Kiểm tra chữ ký có bị thay đổi không"""
    try:
        # Kiểm tra signature có format hex hợp lệ không
        signature = transaction.get("signature", "")
        
        if not signature:
            return False, "Giao dịch không có chữ ký"
        
        # Kiểm tra độ dài signature (ECDSA signature thường ~64 bytes = 128 hex chars)
        if len(signature) < 64 or len(signature) > 140:
            return False, f"Chữ ký có độ dài bất thường: {len(signature)} characters"
        
        # Kiểm tra có phải hex hợp lệ không
        try:
            bytes.fromhex(signature)
        except ValueError:
            return False, "Chữ ký không phải hex hợp lệ"
        
        return True, "Chữ ký có format hợp lệ"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra signature tampering: {str(e)}"

def check_amount_manipulation(transaction):
    """Kiểm tra số tiền có bị thao túng không"""
    try:
        amount = transaction.get("amount", 0)
        
        # Kiểm tra số tiền hợp lý
        if amount <= 0:
            return False, "Số tiền phải lớn hơn 0"
        
        if amount > 100000000:  # 100 triệu VND
            return False, "Số tiền quá lớn (>100 triệu VND)"
        
        # Kiểm tra có phải số nguyên không
        if not isinstance(amount, int):
            return False, "Số tiền phải là số nguyên"
        
        return True, "Số tiền hợp lý"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra amount manipulation: {str(e)}"

def check_fraud(transaction):
    """Tổng hợp kiểm tra giả mạo"""
    try:
        print(f"🔒 Kiểm tra bảo mật cho giao dịch {transaction['id']}...")
        
        # 1. Kiểm tra double spending
        ds_check, ds_msg = check_double_spending(transaction)
        if not ds_check:
            return False, f"Double Spending: {ds_msg}"
        
        # 2. Kiểm tra replay attack
        ra_check, ra_msg = check_replay_attack(transaction)
        if not ra_check:
            return False, f"Replay Attack: {ra_msg}"
        
        # 3. Kiểm tra signature tampering
        st_check, st_msg = check_signature_tampering(transaction)
        if not st_check:
            return False, f"Signature Tampering: {st_msg}"
        
        # 4. Kiểm tra amount manipulation
        am_check, am_msg = check_amount_manipulation(transaction)
        if not am_check:
            return False, f"Amount Manipulation: {am_msg}"
        
        # Tất cả kiểm tra đều pass
        return True, "Tất cả kiểm tra bảo mật đều PASS"
        
    except Exception as e:
        return False, f"Lỗi kiểm tra fraud: {str(e)}"

def get_fraud_statistics():
    """Thống kê các loại tấn công đã phát hiện"""
    try:
        transactions_file = "data/transactions.json"
        
        if not os.path.exists(transactions_file):
            return {
                "total_transactions": 0,
                "verified_transactions": 0,
                "rejected_transactions": 0,
                "fraud_attempts": 0
            }
        
        with open(transactions_file, 'r', encoding='utf-8') as f:
            all_transactions = json.load(f)
        
        total = len(all_transactions)
        verified = len([tx for tx in all_transactions if tx.get("status") == "verified"])
        rejected = len([tx for tx in all_transactions if tx.get("status") == "rejected"])
        fraud_attempts = rejected  # Giả định rejected = fraud attempts
        
        return {
            "total_transactions": total,
            "verified_transactions": verified,
            "rejected_transactions": rejected,
            "fraud_attempts": fraud_attempts,
            "success_rate": f"{(verified/total*100):.1f}%" if total > 0 else "0%"
        }
        
    except Exception as e:
        return {"error": f"Lỗi lấy thống kê: {str(e)}"}