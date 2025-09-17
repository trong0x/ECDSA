from ecdsa import SigningKey, VerifyingKey, SECP256k1
import json
import hashlib
from datetime import datetime
from core.wallet import get_wallet_info  # Import từ wallet.py

def create_transaction(from_user, to_user, amount):
    """Tạo giao dịch mới"""
    # 1. Kiểm tra ví tồn tại
    # 2. Tạo dict giao dịch
    # 3. Return giao dịch chưa ký
    
def sign_transaction(transaction, private_key):
    """Ký giao dịch bằng ECDSA"""
    # 1. Chuyển transaction thành JSON string
    # 2. Hash bằng SHA256
    # 3. Ký hash bằng private key
    # 4. Thêm signature vào transaction
    # 5. Return signed transaction
    
def save_transaction(signed_tx):
    """Lưu giao dịch vào file"""
    # Append vào data/transactions.json