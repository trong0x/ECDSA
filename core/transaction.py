import sqlite3
import os
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from threading import Lock
from core.wallet import get_private_key

DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "system.db")

os.makedirs(DATA_DIR, exist_ok=True)
_lock = Lock()

def _get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    """Khởi tạo bảng transactions nếu chưa có."""
    with _get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            sender TEXT,
            receiver TEXT,
            from_address TEXT,
            to_address TEXT,
            amount INTEGER,
            timestamp TEXT,
            expires_at TEXT,
            status TEXT,
            signature TEXT,
            nonce INTEGER,
            executed INTEGER DEFAULT 0
        )
        """)
        conn.commit()

_init_db()

# ------------------ CRUD ------------------ #

def create_transaction(from_user, to_user, amount, from_address=None, to_address=None):
    """Tạo giao dịch mới và lưu vào DB."""
    if int(amount) <= 0:
        raise ValueError("Số tiền giao dịch phải lớn hơn 0")

    # Get nonce from wallet
    from core.wallet import get_wallet_nonce, increment_nonce
    nonce = get_wallet_nonce(from_user)
    
    # Set expiry time (10 minutes from now)
    expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()

    tx_id = str(uuid.uuid4())
    tx_data = {
        "id": tx_id,
        "sender": from_user,
        "receiver": to_user,
        "from": from_user,  # Add for compatibility
        "to": to_user,      # Add for compatibility
        "from_address": from_address,
        "to_address": to_address,
        "amount": int(amount),
        "timestamp": datetime.now().isoformat(),
        "expires_at": expires_at,
        "status": "pending",
        "signature": None,
        "nonce": nonce,
        "executed": 0
    }

    with _lock, _get_connection() as conn:
        conn.execute("""
            INSERT INTO transactions 
            (id, sender, receiver, from_address, to_address, amount, timestamp, expires_at, status, signature, nonce, executed)
            VALUES (:id, :sender, :receiver, :from_address, :to_address, :amount, :timestamp, :expires_at, :status, :signature, :nonce, :executed)
        """, tx_data)
        conn.commit()
    
    # Increment nonce after creating transaction
    increment_nonce(from_user)

    return tx_data


def sign_transaction(transaction, from_user, passphrase):
    """Ký giao dịch bằng private key (ECDSA)."""
    private_key = get_private_key(from_user, passphrase)

    fields_to_sign = {
        "id": transaction["id"],
        "from": transaction.get("sender") or transaction.get("from"),
        "to": transaction.get("receiver") or transaction.get("to"),
        "amount": int(transaction["amount"]),  # ✅ FIX: Cast to int để consistent với verify
        "timestamp": transaction["timestamp"],
        "from_address": transaction.get("from_address", ""),
        "to_address": transaction.get("to_address", ""),
        "nonce": transaction.get("nonce", 0)
    }

    json_string = json.dumps(fields_to_sign, sort_keys=True, separators=(',', ':'))
    message_hash = hashlib.sha256(json_string.encode('utf-8')).digest()
    signature = private_key.sign(message_hash).hex()

    with _lock, _get_connection() as conn:
        conn.execute("""
            UPDATE transactions
            SET signature = ?, status = 'signed'
            WHERE id = ?
        """, (signature, transaction["id"]))
        conn.commit()

    transaction["signature"] = signature
    transaction["status"] = "signed"
    return transaction


def get_transaction_by_id(tx_id):
    """Lấy giao dịch theo ID."""
    with _get_connection() as conn:
        cur = conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
        row = cur.fetchone()
        if row:
            tx = dict(row)
            # Add compatibility fields
            if "sender" in tx:
                tx["from"] = tx["sender"]
            if "receiver" in tx:
                tx["to"] = tx["receiver"]
            return tx
        return None


def get_all_transactions():
    """Lấy toàn bộ giao dịch từ DB."""
    with _get_connection() as conn:
        cur = conn.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        rows = cur.fetchall()
        result = []
        for r in rows:
            tx = dict(r)
            # Add compatibility fields
            if "sender" in tx:
                tx["from"] = tx["sender"]
            if "receiver" in tx:
                tx["to"] = tx["receiver"]
            result.append(tx)
        return result


def get_pending_transactions(wallet_name=None):
    """Lấy các giao dịch đang pending."""
    with _get_connection() as conn:
        if wallet_name:
            cur = conn.execute("""
                SELECT * FROM transactions 
                WHERE sender = ? AND status IN ('pending', 'signed') AND executed = 0
                ORDER BY timestamp DESC
            """, (wallet_name,))
        else:
            cur = conn.execute("""
                SELECT * FROM transactions 
                WHERE status IN ('pending', 'signed') AND executed = 0
                ORDER BY timestamp DESC
            """)
        rows = cur.fetchall()
        result = []
        for r in rows:
            tx = dict(r)
            if "sender" in tx:
                tx["from"] = tx["sender"]
            if "receiver" in tx:
                tx["to"] = tx["receiver"]
            result.append(tx)
        return result


def get_transactions_by_wallet(wallet_name, limit=100):
    """Lấy lịch sử giao dịch của một ví."""
    with _get_connection() as conn:
        cur = conn.execute("""
            SELECT * FROM transactions 
            WHERE sender = ? OR receiver = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (wallet_name, wallet_name, limit))
        rows = cur.fetchall()
        result = []
        for r in rows:
            tx = dict(r)
            if "sender" in tx:
                tx["from"] = tx["sender"]
            if "receiver" in tx:
                tx["to"] = tx["receiver"]
            result.append(tx)
        return result


def get_latest_transaction():
    """Lấy giao dịch mới nhất."""
    with _get_connection() as conn:
        cur = conn.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            tx = dict(row)
            if "sender" in tx:
                tx["from"] = tx["sender"]
            if "receiver" in tx:
                tx["to"] = tx["receiver"]
            return tx
        return None


def update_transaction_status(tx_id, status):
    """Cập nhật trạng thái giao dịch."""
    with _lock, _get_connection() as conn:
        conn.execute("UPDATE transactions SET status = ? WHERE id = ?", (status, tx_id))
        conn.commit()


def mark_transaction_executed(tx_id):
    """Đánh dấu giao dịch đã thực thi."""
    with _lock, _get_connection() as conn:
        conn.execute("UPDATE transactions SET executed = 1 WHERE id = ?", (tx_id,))
        conn.commit()


def delete_all_transactions():
    """Xóa toàn bộ giao dịch (reset test)."""
    with _lock, _get_connection() as conn:
        conn.execute("DELETE FROM transactions")
        conn.commit()


def get_transaction_stats():
    """Lấy thống kê giao dịch."""
    with _get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        verified = conn.execute("SELECT COUNT(*) FROM transactions WHERE status = 'verified'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM transactions WHERE status = 'rejected'").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM transactions WHERE status IN ('pending', 'signed')").fetchone()[0]
        
        success_rate = f"{(verified/max(total,1)*100):.1f}%" if total > 0 else "0%"
        
        return {
            "total": total,
            "verified": verified,
            "rejected": rejected,
            "pending": pending,
            "success_rate": success_rate
        }