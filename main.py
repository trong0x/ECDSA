# main.py
import uuid
import time
import traceback
from getpass import getpass
from core.wallet import create_wallet, get_wallet_info, update_balance
from core.transaction import sign_transaction, load_transactions

def menu():
    print("1. Tạo ví mới")
    print("2. Xem thông tin ví")
    print("3. Tạo giao dịch")
    print("4. Danh sách giao dịch")
    print("5. Xem chi tiết giao dịch")
    print("6. Thoát")
    return input("Chọn chức năng: ")

def create_wallet_flow():
    name = input("Nhập tên ví: ")
    passphrase = getpass("Nhập passphrase để bảo vệ private key: ")
    wallet = create_wallet(name, passphrase)
    print(f"✅ Ví '{name}' đã tạo thành công!")
    print(json_pretty(wallet))

def show_wallet_info():
    name = input("Nhập tên ví: ")
    wallet = get_wallet_info(name)
    if not wallet:
        print("❌ Không tìm thấy ví")
        return
    safe_wallet = wallet.copy()
    safe_wallet.pop("encrypted_private_key", None)
    safe_wallet.pop("salt", None)
    print(json_pretty(safe_wallet))

def create_transaction_flow():

    amount = int(input("Số tiền: "))
    if amount <= 0:
       print("❌ Số tiền phải lớn hơn 0")
       return

    from_user = input("Người gửi (tên ví): ")
    to_user = input("Người nhận (tên ví): ")
    amount = int(input("Số tiền: "))

    from_wallet = get_wallet_info(from_user)
    to_wallet = get_wallet_info(to_user)

    if not from_wallet or not to_wallet:
        print("❌ Ví không tồn tại")
        return

    if from_wallet["balance"] < amount:
        print("❌ Số dư không đủ")
        return

    tx = {
        "id": str(uuid.uuid4()),
        "from": from_user,
        "to": to_user,
        "amount": amount,
        "timestamp": time.time(),  # ký vẫn chấp nhận số; lưu file dùng ISO trong create_transaction() flow
        "from_address": from_wallet["address"],
        "to_address": to_wallet["address"],
        "status": "created"
    }

    passphrase = getpass("Nhập passphrase của ví gửi để ký giao dịch: ")
    try:
        signed_tx = sign_transaction(tx, from_user, passphrase)
        print("✅ Giao dịch đã ký thành công:")
        print(json_pretty(signed_tx))

        update_balance(from_user, from_wallet["balance"] - amount)
        update_balance(to_user, to_wallet["balance"] + amount)

    except Exception as e:
        print("❌ Lỗi khi ký giao dịch:", str(e))
        traceback.print_exc()

def show_transactions():
    """Danh sách giao dịch (list)"""
    txs = load_transactions()
    if not txs:
        print("Chưa có giao dịch nào")
        return

    print("\n=== Danh sách giao dịch ===")
    # txs là list
    for tx in txs:
        print(f"- ID: {tx.get('id')} | {tx.get('from')} -> {tx.get('to')} | {tx.get('amount')} | {tx.get('status', 'unknown')}")

def show_transaction_detail():
    """Hiển thị chi tiết một giao dịch"""
    tx_id = input("Nhập Transaction ID: ")
    txs = load_transactions()
    tx = None
    for t in txs:
        if t.get("id") == tx_id:
            tx = t
            break

    if not tx:
        print("❌ Không tìm thấy giao dịch")
        return

    print("\n=== Chi tiết giao dịch ===")
    print(f"🔹 ID: {tx.get('id')}")
    print(f"🔹 Người gửi: {tx.get('from')} ({tx.get('from_address')})")
    print(f"🔹 Người nhận: {tx.get('to')} ({tx.get('to_address')})")
    print(f"🔹 Số tiền: {tx.get('amount')}")
    print(f"🔹 Thời gian: {tx.get('timestamp')}")
    print(f"🔹 Trạng thái: {tx.get('status', 'unknown')}")
    if tx.get("signature"):
        print(f"🔹 Chữ ký: {tx.get('signature')}")

def json_pretty(obj):
    import json
    return json.dumps(obj, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    while True:
        choice = menu()
        if choice == "1":
            create_wallet_flow()
        elif choice == "2":
            show_wallet_info()
        elif choice == "3":
            create_transaction_flow()
        elif choice == "4":
            show_transactions()
        elif choice == "5":
            show_transaction_detail()
        elif choice == "6":
            print("Thoát chương trình...")
            break
        else:
            print("❌ Lựa chọn không hợp lệ")
