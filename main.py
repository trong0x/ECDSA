from core.wallet import create_wallet, get_wallet_info
from core.transaction import create_transaction, sign_transaction
from core.verification import full_verification_flow

def main():
    """Menu chính"""
    print(" HỆ THỐNG XÁC THỰC VÍ ĐIỆN TỬ ECDSA ")
    
    while True:
        print("\n" + "="*50)
        print("1. Tạo ví mới")
        print("2. Tạo giao dịch")
        print("3. Xác thực giao dịch")  # Chức năng chính
        print("4. Xem thông tin ví")
        print("0. Thoát")
        print("="*50)
        
        choice = input("Chọn chức năng: ")
        
        if choice == "1":
            # Tạo ví mới
            print("\nTẠO VÍ MỚI")
            name = input("Nhập tên chủ ví: ")
            try:
                wallet_info = create_wallet(name)
                print(f"Tạo ví thành công!")
                print(f"Tên: {wallet_info['name']}")
                print(f"Địa chỉ: {wallet_info['address']}")
                print(f"Số dư ban đầu: {wallet_info['balance']:,} VND")
            except Exception as e:
                print(f"Lỗi tạo ví: {e}")
                
        elif choice == "2":
            # Tạo và ký giao dịch
            print("\nTẠO GIAO DỊCH")
            from_user = input("Người gửi: ")
            to_user = input("Người nhận: ")
            try:
                amount = int(input("Số tiền (VND): "))
                
                # Tạo giao dịch
                transaction = create_transaction(from_user, to_user, amount)
                
                # Ký giao dịch
                signed_tx = sign_transaction(transaction, from_user)
                
                print("Tạo và ký giao dịch thành công!")
                print(f"ID giao dịch: {signed_tx['id']}")
                print(f"Từ: {signed_tx['from']} → Đến: {signed_tx['to']}")
                print(f"Số tiền: {signed_tx['amount']:,} VND")
                print(f"Đã ký: {'Có' if signed_tx.get('signature') else 'Không'}")
                
            except ValueError:
                print("Số tiền không hợp lệ!")
            except Exception as e:
                print(f"Lỗi tạo giao dịch: {e}")
                
        elif choice == "3":
            # Xác thực giao dịch - CHỨC NĂNG CHÍNH
            print("\nXÁC THỰC GIAO DỊCH")
            print("Chọn cách xác thực:")
            print("1. Xác thực giao dịch mới nhất")
            print("2. Xác thực theo ID giao dịch")
            
            sub_choice = input("Chọn: ")
            
            try:
                if sub_choice == "1":
                    # Lấy giao dịch mới nhất để verify
                    result = full_verification_flow()
                    
                elif sub_choice == "2":
                    tx_id = input("Nhập ID giao dịch: ")
                    result = full_verification_flow(tx_id)
                    
                else:
                    print("Lựa chọn không hợp lệ!")
                    continue
                
                # Hiển thị kết quả xác thực
                print("\n🔍 KẾT QUẢ XÁC THỰC:")
                print(f"Trạng thái: {'HỢP LỆ' if result['valid'] else ' KHÔNG HỢP LỆ'}")
                print(f"Chữ ký: {'Đúng' if result['signature_valid'] else ' Sai'}")
                print(f"Số dư: {'Đủ' if result['balance_valid'] else ' Không đủ'}")
                print(f"Bảo mật: {'An toàn' if result['fraud_check'] else ' Nghi ngờ giả mạo'}")
                
                if result['message']:
                    print(f"Chi tiết: {result['message']}")
                    
            except Exception as e:
                print(f"Lỗi xác thực: {e}")
                
        elif choice == "4":
            # Xem thông tin ví
            print("\n--- THÔNG TIN VÍ ---")
            name = input("Nhập tên chủ ví: ")
            try:
                wallet_info = get_wallet_info(name)
                if wallet_info:
                    print(f"Chủ ví: {wallet_info['name']}")
                    print(f"Địa chỉ: {wallet_info['address']}")
                    print(f"Số dư: {wallet_info['balance']:,} VND")
                    print(f"Khóa công khai: {wallet_info['public_key'][:20]}...")
                else:
                    print("Không tìm thấy ví!")
            except Exception as e:
                print(f"Lỗi: {e}")
                
        elif choice == "0":
            print("\n Cảm ơn bạn đã sử dụng hệ thống!")
            print("Dự án: Xác thực giao dịch ví điện tử bằng chữ ký số ECDSA")
            break
            
        else:
            print(" Lựa chọn không hợp lệ! Vui lòng chọn 0-4.")
            
        # Dừng một chút để user đọc kết quả
        input("\nNhấn Enter để tiếp tục...")

if __name__ == "__main__":
    main()