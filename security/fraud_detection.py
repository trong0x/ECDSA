import json
from datetime import datetime

def check_double_spending(transaction):
    """Kiểm tra chi tiêu kép"""
    # 1. Đọc data/transactions.json
    # 2. Tìm giao dịch trùng từ cùng người
    # 3. Return True/False
    
def check_replay_attack(transaction):
    """Kiểm tra tấn công phát lại"""
    # 1. Check timestamp có quá cũ không
    # 2. Check transaction ID có trùng không
    # 3. Return True/False
    
def check_fraud(transaction):
    """Tổng hợp kiểm tra giả mạo"""
    # 1. Gọi check_double_spending()
    # 2. Gọi check_replay_attack()  
    # 3. Có thể thêm check khác
    # 4. Return True nếu có fraud, False nếu clean