from ecdsa import SigningKey, SECP256k1
import json
import os

def create_wallet(name):
    """Tạo ví mới với khóa ECDSA"""
    # 1. Tạo khóa riêng
    # 2. Tạo khóa công khai  
    # 3. Tạo địa chỉ ví
    # 4. Lưu vào data/wallets.json
    
def get_wallet_info(name):
    """Lấy thông tin ví từ JSON"""
    # Đọc file data/wallets.json
    
def update_balance(name, amount):
    """Cập nhật số dư"""
    # Đọc → sửa → ghi lại JSON