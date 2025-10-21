from ecdsa import SigningKey, SECP256k1
import hashlib
from datetime import datetime
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from core.database import init_db, execute, fetch_one, fetch_all


init_db()


def _derive_fernet_key(passphrase: str, salt: bytes) -> bytes:
    """Sinh key Fernet từ passphrase + salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def _encrypt_private_key_hex(private_key_hex: str, passphrase: str):
    salt = os.urandom(16)
    fernet_key = _derive_fernet_key(passphrase, salt)
    f = Fernet(fernet_key)
    ciphertext = f.encrypt(private_key_hex.encode())
    return ciphertext.hex(), salt.hex()


def _decrypt_private_key_hex(ciphertext_hex: str, passphrase: str, salt_hex: str):
    salt = bytes.fromhex(salt_hex)
    fernet_key = _derive_fernet_key(passphrase, salt)
    f = Fernet(fernet_key)
    plaintext = f.decrypt(bytes.fromhex(ciphertext_hex))
    return plaintext.decode()


def create_wallet(name, passphrase, initial_balance=1000000):
    """Tạo ví mới, lưu vào SQLite."""
    # Kiểm tra trùng tên
    existing = get_wallet_info(name)
    if existing:
        print(f"⚠️  Wallet '{name}' already exists")
        return existing

    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()
    public_key_hex = public_key.to_string().hex()

    address_hash = hashlib.sha256(public_key_hex.encode()).hexdigest()
    address = f"wallet_{address_hash[:16]}"

    private_key_hex = private_key.to_string().hex()
    enc_key, salt = _encrypt_private_key_hex(private_key_hex, passphrase)

    created_at = str(datetime.now())

   
    execute("""
        INSERT INTO wallets (name, address, public_key, encrypted_private_key, salt, balance, nonce, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, address, public_key_hex, enc_key, salt, initial_balance, 0, created_at))

    print(f"✅ Created wallet '{name}' with balance {initial_balance:,} VND")

    return {
        "name": name,
        "address": address,
        "public_key": public_key_hex,
        "balance": initial_balance,
        "nonce": 0,
        "created_at": created_at
    }


def get_wallet_info(name, safe=False):
    """Lấy thông tin ví từ SQLite."""
    row = fetch_one("SELECT * FROM wallets WHERE name = ?", (name,))
    if not row:
        return None

    wallet = dict(row)
    
    # Đảm bảo có nonce (backward compatible)
    if "nonce" not in wallet or wallet["nonce"] is None:
        wallet["nonce"] = 0
        # Update database
        try:
            execute("UPDATE wallets SET nonce = 0 WHERE name = ?", (name,))
        except:
            pass
    
    if safe:
        return {
            "name": wallet["name"],
            "address": wallet["address"],
            "balance": wallet["balance"],
            "nonce": wallet["nonce"],
            "created_at": wallet["created_at"]
        }
    return wallet


def get_all_wallets():
    """Lấy tất cả wallets (dành cho admin)."""
    rows = fetch_all("SELECT * FROM wallets")
    wallets = []
    for row in rows:
        wallet = dict(row)
        if "nonce" not in wallet or wallet["nonce"] is None:
            wallet["nonce"] = 0
        wallets.append(wallet)
    return wallets


def update_balance(name, new_balance):
    """Cập nhật số dư ví."""
    execute("UPDATE wallets SET balance = ? WHERE name = ?", (new_balance, name))
    return True


def get_private_key(name, passphrase):
    """Giải mã private key từ database."""
    wallet = get_wallet_info(name)
    if not wallet:
        raise Exception(f"Không tìm thấy ví {name}")

    enc = wallet.get("encrypted_private_key")
    salt = wallet.get("salt")
    if not enc or not salt:
        raise Exception("Ví chưa được mã hóa")

    try:
        private_key_hex = _decrypt_private_key_hex(enc, passphrase, salt)
        return SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    except Exception as e:
        raise Exception(f"Sai passphrase hoặc ví bị lỗi: {str(e)}")


def get_wallet_by_address(address):
    """Lấy thông tin ví từ địa chỉ."""
    row = fetch_one("SELECT * FROM wallets WHERE address = ?", (address,))
    if not row:
        return None
    
    wallet = dict(row)
    if "nonce" not in wallet or wallet["nonce"] is None:
        wallet["nonce"] = 0
    return wallet


def increment_nonce(wallet_name):
    """ Tăng nonce lên 1 Hàm này được gọi từ transaction.py khi tạo giao dịch mới """
    try:
        execute("""
            UPDATE wallets 
            SET nonce = COALESCE(nonce, 0) + 1 
            WHERE name = ?
        """, (wallet_name,))
        return True
    except Exception as e:
        print(f"⚠️  Error incrementing nonce: {e}")
        return False


def get_wallet_nonce(wallet_name):
    """ Lấy nonce hiện tại của wallet """
    wallet = get_wallet_info(wallet_name)
    if not wallet:
        return 0  # Default nonce nếu wallet không tồn tại
    return wallet.get("nonce", 0)


def reset_wallet_nonce(wallet_name):
    """ Reset nonce về 0 (dành cho admin, test)"""
    try:
        execute("UPDATE wallets SET nonce = 0 WHERE name = ?", (wallet_name,))
        print(f"✅ Reset nonce for wallet '{wallet_name}'")
        return True
    except Exception as e:
        print(f"❌ Error resetting nonce: {e}")
        return False


def load_wallets_from_file():
    """ Chỉ để backward compatibility  , Giờ dùng database thay vì file JSON
    """
    print("⚠️  load_wallets_from_file() is deprecated. Using database instead.")
    rows = fetch_all("SELECT * FROM wallets")
    wallets = {}
    for row in rows:
        wallet = dict(row)
        if "nonce" not in wallet or wallet["nonce"] is None:
            wallet["nonce"] = 0
        wallets[wallet["name"]] = wallet
    return wallets


def get_wallet_stats():
    """ Lấy thống kê tổng quan về wallets """
    try:
        rows = fetch_all("SELECT balance, nonce FROM wallets")
        
        if not rows:
            return {
                "total_wallets": 0,
                "total_balance": 0,
                "avg_balance": 0,
                "max_nonce": 0
            }
        
        total_wallets = len(rows)
        total_balance = sum(row["balance"] for row in rows)
        avg_balance = total_balance / total_wallets if total_wallets > 0 else 0
        max_nonce = max(row["nonce"] or 0 for row in rows)
        
        return {
            "total_wallets": total_wallets,
            "total_balance": total_balance,
            "avg_balance": avg_balance,
            "max_nonce": max_nonce
        }
    except Exception as e:
        print(f"⚠️  Error getting wallet stats: {e}")
        return {
            "total_wallets": 0,
            "total_balance": 0,
            "avg_balance": 0,
            "max_nonce": 0
        }