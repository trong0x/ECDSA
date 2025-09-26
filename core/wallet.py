from ecdsa import SigningKey, SECP256k1
import json
import os
import hashlib
from datetime import datetime
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

DATA_DIR = "data"
WALLET_FILE = os.path.join(DATA_DIR, "wallets.json")


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


def create_wallet(name, passphrase):
    """Tạo ví mới, private key được mã hóa bằng passphrase."""
    private_key = SigningKey.generate(curve=SECP256k1)
    public_key = private_key.get_verifying_key()

    public_key_hex = public_key.to_string().hex()
    address_hash = hashlib.sha256(public_key_hex.encode()).hexdigest()
    address = f"wallet_{address_hash[:16]}"

    private_key_hex = private_key.to_string().hex()
    encrypted_private_key_hex, salt_hex = _encrypt_private_key_hex(private_key_hex, passphrase)

    wallet_info = {
        "name": name,
        "address": address,
        "public_key": public_key_hex,
        "encrypted_private_key": encrypted_private_key_hex,
        "salt": salt_hex,
        "balance": 1000000,
        "created_at": str(datetime.now())
    }

    save_wallet_to_file(wallet_info)
    return wallet_info


def get_wallet_info(name):
    wallets = load_wallets_from_file()
    return wallets.get(name)


def update_balance(name, new_balance):
    wallets = load_wallets_from_file()
    if name in wallets:
        wallets[name]["balance"] = new_balance
        save_all_wallets_to_file(wallets)
        return True
    return False


def get_private_key(name, passphrase):
    """Giải mã private key bằng passphrase, trả về SigningKey."""
    wallet_info = get_wallet_info(name)
    if not wallet_info:
        raise Exception("Không tìm thấy ví")

    enc = wallet_info.get("encrypted_private_key")
    salt = wallet_info.get("salt")
    if not enc or not salt:
        raise Exception("Ví chưa được mã hóa")

    private_key_hex = _decrypt_private_key_hex(enc, passphrase, salt)
    return SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)


def load_wallets_from_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_wallet_to_file(wallet_info):
    wallets = load_wallets_from_file()
    wallets[wallet_info["name"]] = wallet_info
    save_all_wallets_to_file(wallets)


def save_all_wallets_to_file(wallets):
    with open(WALLET_FILE, 'w', encoding='utf-8') as f:
        json.dump(wallets, f, indent=2, ensure_ascii=False)


def migrate_encrypt_existing_wallet(name, passphrase):
    """Chuyển ví cũ (có private_key thô) sang encrypted_private_key."""
    wallets = load_wallets_from_file()
    if name not in wallets:
        raise Exception("Không tìm thấy ví")

    w = wallets[name]
    if "private_key" not in w:
        raise Exception("Ví không có private_key thô")

    private_key_hex = w.pop("private_key")
    enc, salt = _encrypt_private_key_hex(private_key_hex, passphrase)
    w["encrypted_private_key"] = enc
    w["salt"] = salt
    wallets[name] = w
    save_all_wallets_to_file(wallets)
    return True
