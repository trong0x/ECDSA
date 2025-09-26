import json
import os
import uuid
import hashlib
from datetime import datetime
from core.wallet import get_private_key

TRANSACTIONS_FILE = "data/transactions.json"

# ------------------ Load & Save ------------------ #
def load_transactions():
    """Load danh sách giao dịch từ file JSON, luôn trả về list."""
    if not os.path.exists(TRANSACTIONS_FILE):
        return []
    try:
        with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Nếu file trước đây là dict (id -> tx), chuyển sang list
            if isinstance(data, dict):
                return list(data.values())
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError):
        return []



def save_transactions(transactions):
    """Lưu toàn bộ danh sách giao dịch (list)."""
    os.makedirs(os.path.dirname(TRANSACTIONS_FILE) or ".", exist_ok=True)
    with open(TRANSACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2, ensure_ascii=False)

def save_transaction(tx):
    """Thêm hoặc cập nhật một giao dịch (dạng list trong file)."""
    transactions = load_transactions()
    # cập nhật nếu tồn tại
    for i, t in enumerate(transactions):
        if t.get("id") == tx.get("id"):
            transactions[i] = tx
            break
    else:
        transactions.append(tx)
    save_transactions(transactions)

# ------------------ Tạo & Ký ------------------ #
def create_transaction(from_user, to_user, amount, from_address=None, to_address=None):
    """Tạo một giao dịch mới (chưa ký). Timestamp ISO để tương thích kiểm tra."""

    if int(amount) <= 0:
       raise ValueError("Số tiền giao dịch phải lớn hơn 0")

    tx = {
        "id": str(uuid.uuid4()),
        "from": from_user,
        "to": to_user,
        "from_address": from_address,
        "to_address": to_address,
        "amount": int(amount),
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "signature": None,
        "executed": False
    }
    # Lưu tạm (chưa ký) để tồn tại trong lịch sử
    save_transaction(tx)
    return tx

def sign_transaction(transaction, from_user, passphrase):
    """Ký giao dịch bằng private key đã mã hóa (yêu cầu passphrase)."""
    # Ensure transaction is a dict
    if not isinstance(transaction, dict):
        raise ValueError("Transaction phải là dict")

    private_key = get_private_key(from_user, passphrase)

    fields_to_sign = {
        "id": transaction.get("id"),
        "from": transaction.get("from"),
        "to": transaction.get("to"),
        "amount": transaction.get("amount"),
        "timestamp": transaction.get("timestamp"),
        "from_address": transaction.get("from_address"),
        "to_address": transaction.get("to_address")
    }
    json_string = json.dumps(fields_to_sign, sort_keys=True, separators=(',', ':'))
    message_hash = hashlib.sha256(json_string.encode('utf-8')).digest()

    signature = private_key.sign(message_hash)
    transaction["signature"] = signature.hex()
    transaction["status"] = "signed"
    transaction["executed"] = False

    save_transaction(transaction)
    return transaction

# ------------------ Truy vấn ------------------ #
def get_all_transactions():
    """Trả về danh sách tất cả giao dịch (list)."""
    return load_transactions()

def get_transaction_by_id(tx_id):
    """Trả về giao dịch theo ID hoặc None nếu không có."""
    transactions = load_transactions()
    for tx in transactions:
        if tx.get("id") == tx_id:
            return tx
    return None

def get_latest_transaction():
    """Trả về giao dịch mới nhất (theo timestamp ISO)."""
    transactions = load_transactions()
    if not transactions:
        return None
    # timestamp là ISO string — so sánh lexicographically OK for ISO
    return max(transactions, key=lambda x: x.get("timestamp", ""))
