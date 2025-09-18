from ecdsa import SigningKey, SECP256k1
import json
import os
import hashlib
from datetime import datetime

def create_wallet(name):
    """Tạo ví mới với khóa ECDSA"""
    try:
        # 1. Tạo khóa riêng ECDSA
        private_key = SigningKey.generate(curve=SECP256k1)
        
        # 2. Tạo khóa công khai
        public_key = private_key.get_verifying_key()
        
        # 3. Tạo địa chỉ ví từ khóa công khai (20 ký tự đầu của hash)
        public_key_hex = public_key.to_string().hex()
        address_hash = hashlib.sha256(public_key_hex.encode()).hexdigest()
        address = f"wallet_{address_hash[:16]}"
        
        # 4. Thông tin ví
        wallet_info = {
            "name": name,
            "address": address,
            "public_key": public_key_hex,
            "private_key": private_key.to_string().hex(),  # Lưu tạm để demo
            "balance": 1000000,  # Số dư ban đầu 1 triệu VND
            "created_at": str(datetime.now())
        }
        
        # 5. Lưu vào file data/wallets.json
        save_wallet_to_file(wallet_info)
        
        return wallet_info
        
    except Exception as e:
        raise Exception(f"Lỗi tạo ví: {str(e)}")

def get_wallet_info(name):
    """Lấy thông tin ví từ JSON"""
    try:
        wallets = load_wallets_from_file()
        
        if name in wallets:
            return wallets[name]
        else:
            return None
            
    except Exception as e:
        raise Exception(f"Lỗi lấy thông tin ví: {str(e)}")

def update_balance(name, new_balance):
    """Cập nhật số dư ví"""
    try:
        wallets = load_wallets_from_file()
        
        if name in wallets:
            wallets[name]["balance"] = new_balance
            save_all_wallets_to_file(wallets)
            return True
        else:
            return False
            
    except Exception as e:
        raise Exception(f"Lỗi cập nhật số dư: {str(e)}")

def get_private_key(name):
    """Lấy khóa riêng của ví (để ký giao dịch)"""
    try:
        wallet_info = get_wallet_info(name)
        if wallet_info:
            private_key_hex = wallet_info["private_key"]
            private_key = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
            return private_key
        else:
            raise Exception("Không tìm thấy ví")
            
    except Exception as e:
        raise Exception(f"Lỗi lấy khóa riêng: {str(e)}")

def load_wallets_from_file():
    """Đọc danh sách ví từ file"""
    wallet_file = "data/wallets.json"
    
    # Tạo thư mục data nếu chưa có
    os.makedirs("data", exist_ok=True)
    
    if os.path.exists(wallet_file):
        with open(wallet_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}

def save_wallet_to_file(wallet_info):
    """Lưu ví mới vào file"""
    wallets = load_wallets_from_file()
    wallets[wallet_info["name"]] = wallet_info
    save_all_wallets_to_file(wallets)

def save_all_wallets_to_file(wallets):
    """Lưu tất cả ví vào file"""
    wallet_file = "data/wallets.json"
    
    with open(wallet_file, 'w', encoding='utf-8') as f:
        json.dump(wallets, f, indent=2, ensure_ascii=False)