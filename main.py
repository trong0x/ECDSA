import traceback
from getpass import getpass
from core.wallet import create_wallet, get_wallet_info, get_all_wallets
from core.transaction import (
    create_transaction, sign_transaction, 
    get_transaction_by_id, get_all_transactions
)
from core.verification import full_verification_flow
from blockchain.blockchain import get_blockchain
from core.fraud_detection import get_fraud_statistics

def xoa_man_hinh():
    """Xóa màn hình terminal"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def menu_chinh():
    """Hiển thị menu chính và nhận lựa chọn của người dùng"""
    print("\n" + "─"*70)
    print(" BẢNG ĐIỀU KHIỂN")
    print("─"*70)
    print("1.  Tạo ví mới")
    print("2.  Xem thông tin ví")
    print("3.  Tạo giao dịch mới")
    print("4.  Xác thực giao dịch")
    print("5.  Xem danh sách giao dịch")
    print("6.  Xem chi tiết giao dịch")
    print("7.  Xem thông tin Blockchain")
    print("8.  Thống kê hệ thống")
    print("9.  Thống kê bảo mật")
    print("10. Chạy kiểm tra bảo mật (Security Tests)")
    print("11. Chạy kiểm tra giao dịch hàng loạt (Mass Test)")
    print("0.  Thoát chương trình")
    print("─"*70)
    return input(" Mời bạn chọn chức năng: ").strip()

def quy_trinh_tao_vi():
    """Quy trình tạo một ví điện tử mới"""
    print("\n" + "="*70)
    print(" TẠO VÍ MỚI")
    print("="*70)
    
    ten_vi = input(" Nhập tên ví: ").strip()
    if not ten_vi:
        print(" Tên ví không được để trống!")
        return
    
    # Kiểm tra xem ví đã tồn tại chưa
    vi_hien_co = get_wallet_info(ten_vi)
    if vi_hien_co:
        print(f" Ví '{ten_vi}' đã tồn tại!")
        return
    
    cum_mat_khau = getpass(" Nhập cụm mật khẩu (để bảo vệ khóa riêng tư): ")
    xac_nhan_cum_mat_khau = getpass(" Xác nhận lại cụm mật khẩu: ")
    
    if cum_mat_khau != xac_nhan_cum_mat_khau:
        print(" Cụm mật khẩu không khớp!")
        return
    
    try:
        vi = create_wallet(ten_vi, cum_mat_khau)
        print(f"\n✅ Tạo ví '{ten_vi}' thành công!")
        print(f" Địa chỉ ví: {vi['address']}")
        print(f" Số dư ban đầu: {vi['balance']:,} VND")
        print(f" Khóa công khai: {vi['public_key'][:32]}...")
    except Exception as e:
        print(f" Lỗi khi tạo ví: {e}")

def hien_thi_thong_tin_vi():
    """Hiển thị thông tin chi tiết của một ví"""
    print("\n" + "="*70)
    print(" THÔNG TIN VÍ")
    print("="*70)
    
    ten_vi = input(" Nhập tên ví cần xem: ").strip()
    vi = get_wallet_info(ten_vi)
    
    if not vi:
        print(" Không tìm thấy ví này.")
        return
    
    print(f"\n Thông tin ví '{ten_vi}':")
    print(f"   - Địa chỉ: {vi['address']}")
    print(f"   - Số dư: {vi['balance']:,} VND")
    print(f"   - Khóa công khai: {vi['public_key'][:32]}...")
    print(f"   - Nonce: {vi.get('nonce', 0)}")
    print(f"   - Ngày tạo: {vi['created_at']}")

def quy_trinh_tao_giao_dich():
    """Quy trình tạo một giao dịch mới"""
    print("\n" + "="*70)
    print(" TẠO GIAO DỊCH MỚI")
    print("="*70)
    
    nguoi_gui = input(" Tên ví người gửi: ").strip()
    nguoi_nhan = input(" Tên ví người nhận: ").strip()
    
    try:
        so_tien = int(input(" Số tiền (VND): ").strip())
    except ValueError:
        print(" Số tiền không hợp lệ!")
        return
    
    if so_tien <= 0:
        print(" Số tiền phải lớn hơn 0!")
        return
    
    # Kiểm tra thông tin ví
    vi_gui = get_wallet_info(nguoi_gui)
    vi_nhan = get_wallet_info(nguoi_nhan)
    
    if not vi_gui:
        print(f" Không tìm thấy ví người gửi: {nguoi_gui}")
        return
    
    if not vi_nhan:
        print(f" Không tìm thấy ví người nhận: {nguoi_nhan}")
        return
    
    if vi_gui["balance"] < so_tien:
        print(f" Số dư không đủ! (Hiện có: {vi_gui['balance']:,} VND)")
        return
    
    # Tạo giao dịch
    try:
        giao_dich = create_transaction(
            nguoi_gui, nguoi_nhan, so_tien,
            vi_gui["address"], vi_nhan["address"]
        )
        
        print(f"\n✅ Giao dịch đã được tạo thành công!")
        print(f"   - ID Giao dịch: {giao_dich['id']}")
        print(f"   - Từ: {nguoi_gui} ({vi_gui['address'][:16]}...)")
        print(f"   - Đến: {nguoi_nhan} ({vi_nhan['address'][:16]}...)")
        print(f"   - Số tiền: {so_tien:,} VND")
        print(f"   - Thời gian: {giao_dich['timestamp']}")
        print(f"   - Nonce: {giao_dich.get('nonce', 0)}")
        print(f"   - Trạng thái: {giao_dich['status']}")
        
        # Ký giao dịch
        print(f"\n Vui lòng ký để xác thực giao dịch...")
        cum_mat_khau = getpass(f" Nhập cụm mật khẩu của ví '{nguoi_gui}': ")
        
        giao_dich_da_ky = sign_transaction(giao_dich, nguoi_gui, cum_mat_khau)
        
        print(f"\n✅ Giao dịch đã được ký thành công!")
        print(f"   - Chữ ký: {giao_dich_da_ky['signature'][:32]}...")
        print(f"   - Trạng thái: {giao_dich_da_ky['status']}")
        
        # Hỏi có muốn xác thực ngay không
        xac_thuc_ngay = input("\n Bạn có muốn xác thực giao dịch ngay bây giờ? (y/n): ").strip().lower()
        if xac_thuc_ngay == 'y':
            print("\n Đang xác thực giao dịch...")
            ket_qua = full_verification_flow(giao_dich_da_ky['id'])
            
            print(f"\n Kết quả xác thực:")
            print(f"   - Hợp lệ: {ket_qua['valid']}")
            print(f"   - Chữ ký hợp lệ: {ket_qua['signature_valid']}")
            print(f"   - Số dư hợp lệ: {ket_qua['balance_valid']}")
            print(f"   - Kiểm tra gian lận: {ket_qua['fraud_check']}")
            print(f"   - Thông báo: {ket_qua['message']}")
            
            if ket_qua['valid']:
                print(f"\n✅ Giao dịch thành công!")
                
                # ✅ Cập nhật lại giao_dich_da_ky từ DB để lấy trạng thái mới
                giao_dich_da_ky = get_transaction_by_id(giao_dich_da_ky['id'])
                
                # Hiển thị số dư mới
                vi_gui_moi = get_wallet_info(nguoi_gui)
                vi_nhan_moi = get_wallet_info(nguoi_nhan)
                print(f"\n💰 Số dư cập nhật:")
                print(f"   - {nguoi_gui}: {vi_gui_moi['balance']:,} VND")
                print(f"   - {nguoi_nhan}: {vi_nhan_moi['balance']:,} VND")
                
                # Thêm vào blockchain
                blockchain = get_blockchain()
                success = blockchain.add_transaction(giao_dich_da_ky)
                if success:
                    print(f"\n⛓️  Giao dịch đã được thêm vào blockchain thành công!")
                else:
                    print(f"\n⚠️  Giao dịch đã được xác thực nhưng không thêm được vào blockchain!")
        
    except Exception as e:
        print(f" Lỗi: {e}")
        traceback.print_exc()

def quy_trinh_xac_thuc_giao_dich():
    """Quy trình xác thực một giao dịch đã có"""
    print("\n" + "="*70)
    print(" XÁC THỰC GIAO DỊCH")
    print("="*70)
    
    id_giao_dich = input(" Nhập ID Giao dịch (hoặc Enter để xác thực giao dịch mới nhất): ").strip()
    
    if not id_giao_dich:
        id_giao_dich = None
    
    print(f"\n Đang xác thực giao dịch...")
    
    try:
        ket_qua = full_verification_flow(id_giao_dich)
        
        print(f"\n{'='*70}")
        print(f" KẾT QUẢ XÁC THỰC")
        print(f"{'='*70}")
        print(f" ID Giao dịch: {ket_qua.get('transaction_id', 'Không có')}")
        print(f" Hợp lệ: {'✓ CÓ' if ket_qua['valid'] else '✗ KHÔNG'}")
        print(f" Chữ ký hợp lệ: {'✓ CÓ' if ket_qua['signature_valid'] else '✗ KHÔNG'}")
        print(f" Số dư hợp lệ: {'✓ CÓ' if ket_qua['balance_valid'] else '✗ KHÔNG'}")
        print(f" Kiểm tra gian lận: {'✓ ĐẠT' if ket_qua['fraud_check'] else '✗ THẤT BẠI'}")
        print(f" Thông báo: {ket_qua['message']}")
        print(f" Trạng thái giao dịch: {ket_qua.get('transaction_status', 'Không xác định')}")
        
        if ket_qua['valid']:
            print(f"\n✅ Giao dịch hợp lệ và đã được thực thi!")
            
            # Thêm vào blockchain nếu chưa có
            blockchain = get_blockchain()
            giao_dich = get_transaction_by_id(ket_qua['transaction_id'])
            if giao_dich:
                blockchain.add_transaction(giao_dich)
                print(f"⛓️  Đã thêm giao dịch vào blockchain.")
        else:
            print(f"\n❌ Giao dịch bị từ chối!")
            
    except Exception as e:
        print(f" Lỗi xác thực: {e}")
        traceback.print_exc()

def hien_thi_danh_sach_giao_dich():
    """Hiển thị danh sách tất cả các giao dịch"""
    print("\n" + "="*70)
    print(" DANH SÁCH GIAO DỊCH")
    print("="*70)
    
    danh_sach_gd = get_all_transactions()
    
    if not danh_sach_gd:
        print(" Chưa có giao dịch nào được thực hiện.")
        return
    
    print(f"\n Tổng số: {len(danh_sach_gd)} giao dịch\n")
    
    # Phân loại theo trạng thái
    cac_trang_thai = {}
    for gd in danh_sach_gd:
        trang_thai = gd.get('status', 'unknown')
        if trang_thai not in cac_trang_thai:
            cac_trang_thai[trang_thai] = []
        cac_trang_thai[trang_thai].append(gd)
    
    # Hiển thị theo từng trạng thái
    for trang_thai, danh_sach in cac_trang_thai.items():
        bieu_tuong = {
            'pending': '⏳',
            'signed': '✍',
            'verified': '✓',
            'rejected': '✗',
            'executed': '🎉'
        }.get(trang_thai, '•')
        
        print(f"\n{bieu_tuong} {trang_thai.upper()} ({len(danh_sach)} giao dịch):")
        print("─"*70)
        
        for gd in danh_sach[:10]:  # Hiển thị tối đa 10 giao dịch
            id_rut_gon = gd.get('id', 'N/A')[:8]
            nguoi_gui = gd.get('from') or gd.get('sender', 'N/A')
            nguoi_nhan = gd.get('to') or gd.get('receiver', 'N/A')
            so_tien = gd.get('amount', 0)
            thoi_gian = gd.get('timestamp', 'N/A')
            executed = '✅' if gd.get('executed') else '⏳'
            
            print(f"  • {id_rut_gon}... | {nguoi_gui} → {nguoi_nhan} | {so_tien:,} VND | {executed} | {thoi_gian[:19]}")
        
        if len(danh_sach) > 10:
            print(f"  ... và {len(danh_sach) - 10} giao dịch khác")
    
    print("\n Gợi ý: Dùng chức năng 6 để xem chi tiết một giao dịch.")

def hien_thi_chi_tiet_giao_dich():
    """Hiển thị thông tin chi tiết của một giao dịch cụ thể"""
    print("\n" + "="*70)
    print(" CHI TIẾT GIAO DỊCH")
    print("="*70)
    
    id_giao_dich = input(" Nhập ID Giao dịch: ").strip()
    
    giao_dich = get_transaction_by_id(id_giao_dich)
    
    if not giao_dich:
        print(" Không tìm thấy giao dịch.")
        return
    
    print(f"\n{'='*70}")
    print(f" ID Giao dịch: {giao_dich.get('id')}")
    print(f"{'='*70}")
    print(f" Người gửi: {giao_dich.get('from') or giao_dich.get('sender')}")
    print(f"   - Địa chỉ: {giao_dich.get('from_address')}")
    print(f" Người nhận: {giao_dich.get('to') or giao_dich.get('receiver')}")
    print(f"   - Địa chỉ: {giao_dich.get('to_address')}")
    print(f" Số tiền: {giao_dich.get('amount'):,} VND")
    print(f" Thời gian: {giao_dich.get('timestamp')}")
    print(f" Nonce: {giao_dich.get('nonce', 'N/A')}")
    print(f" Hết hạn: {giao_dich.get('expires_at', 'N/A')}")
    print(f" Trạng thái: {giao_dich.get('status', 'Không xác định')}")
    print(f" Đã thực thi: {'CÓ' if giao_dich.get('executed') else 'KHÔNG'}")
    
    if giao_dich.get('signature'):
        print(f" Chữ ký: {giao_dich.get('signature')[:64]}...")
    
    # Kiểm tra trong blockchain
    blockchain = get_blockchain()
    gd_trong_blockchain = blockchain.find_transaction(giao_dich.get('id'))
    
    if gd_trong_blockchain:
        print(f"\n⛓️  THÔNG TIN TRÊN BLOCKCHAIN:")
        print(f"   - Khối (Block): #{gd_trong_blockchain['block']}")
        print(f"   - Mã hash của khối: {gd_trong_blockchain['block_hash'][:32]}...")
        print(f"   - Số lần xác nhận: {gd_trong_blockchain['confirmations']}")

def hien_thi_blockchain():
    """Hiển thị thông tin về chuỗi khối (blockchain)"""
    print("\n" + "="*70)
    print(" TRÌNH KHÁM PHÁ BLOCKCHAIN")
    print("="*70)
    
    blockchain = get_blockchain()
    
    if len(blockchain.chain) == 0:
        print(" Blockchain hiện đang trống.")
        return
    
    print(f"\n Tổng số khối: {len(blockchain.chain)}")
    print(f" Tính hợp lệ của chuỗi: {'✓ HỢP LỆ' if blockchain.is_chain_valid() else '✗ KHÔNG HỢP LỆ'}")
    
    # Hiển thị các khối
    print(f"\n{'='*70}")
    
    for i, block in enumerate(blockchain.chain[-10:]):  # 10 khối gần nhất
        block_dict = block.to_dict() if hasattr(block, 'to_dict') else block
        
        print(f"\n📦 KHỐI #{block_dict['index']}")
        print(f"   - Hash: {block_dict['hash'][:32]}...")
        print(f"   - Hash khối trước: {block_dict['previous_hash'][:32]}...")
        print(f"   - Thời gian: {block_dict['timestamp']}")
        print(f"   - Nonce: {block_dict['nonce']}")
        print(f"   - Số giao dịch: {len(block_dict['transactions'])}")
        
        if len(block_dict['transactions']) > 0:
            print(f"   └─ Giao dịch:")
            for gd in block_dict['transactions'][:3]:  # 3 giao dịch đầu tiên
                from_user = gd.get('from') or gd.get('sender', 'N/A')
                to_user = gd.get('to') or gd.get('receiver', 'N/A')
                print(f"      • {gd.get('id', 'N/A')[:8]}... | {from_user} → {to_user} | {gd.get('amount', 0):,} VND")
            
            if len(block_dict['transactions']) > 3:
                print(f"      ... và {len(block_dict['transactions']) - 3} giao dịch khác")
    
    if len(blockchain.chain) > 10:
        print(f"\n... và {len(blockchain.chain) - 10} khối khác")
    
    # Giao dịch đang chờ
    if len(blockchain.pending_transactions) > 0:
        print(f"\n⏳ Giao dịch đang chờ xử lý: {len(blockchain.pending_transactions)}")

def hien_thi_thong_ke_he_thong():
    """Hiển thị các số liệu thống kê của hệ thống"""
    print("\n" + "="*70)
    print(" THỐNG KÊ HỆ THỐNG")
    print("="*70)
    
    # Thống kê Blockchain
    blockchain = get_blockchain()
    thong_ke_bc = blockchain.get_blockchain_stats()
    
    print(f"\n⛓️  BLOCKCHAIN:")
    print(f"   - Tổng số khối: {thong_ke_bc['total_blocks']}")
    print(f"   - Tổng giao dịch trong chuỗi: {thong_ke_bc['total_transactions']}")
    print(f"   - Giao dịch đang chờ: {thong_ke_bc['pending_transactions']}")
    print(f"   - Độ khó: {thong_ke_bc['difficulty']}")
    print(f"   - Chuỗi hợp lệ: {'✓ CÓ' if thong_ke_bc['is_valid'] else '✗ KHÔNG'}")
    
    # Thống kê giao dịch
    danh_sach_gd = get_all_transactions()
    
    print(f"\n💸 GIAO DỊCH:")
    print(f"   - Tổng số: {len(danh_sach_gd)}")
    
    cac_trang_thai = {}
    for gd in danh_sach_gd:
        trang_thai = gd.get('status', 'unknown')
        cac_trang_thai[trang_thai] = cac_trang_thai.get(trang_thai, 0) + 1
    
    for trang_thai, so_luong in cac_trang_thai.items():
        print(f"   - {trang_thai.capitalize()}: {so_luong}")
    
    # Thống kê ví
    danh_sach_vi = get_all_wallets()
    
    print(f"\n👛 VÍ ĐIỆN TỬ:")
    print(f"   - Tổng số ví: {len(danh_sach_vi)}")
    
    if danh_sach_vi:
        tong_so_du = sum(v.get('balance', 0) for v in danh_sach_vi)
        print(f"   - Tổng số dư toàn hệ thống: {tong_so_du:,} VND")
        
        # Top 5 ví giàu nhất
        vi_da_sap_xep = sorted(danh_sach_vi, key=lambda x: x.get('balance', 0), reverse=True)
        
        print(f"\n📊 Top 5 ví có số dư lớn nhất:")
        for i, vi in enumerate(vi_da_sap_xep[:5], 1):
            print(f"   {i}. {vi['name']}: {vi['balance']:,} VND")

def hien_thi_thong_ke_bao_mat():
    """Hiển thị các thống kê liên quan đến bảo mật"""
    print("\n" + "="*70)
    print(" THỐNG KÊ BẢO MẬT")
    print("="*70)
    
    thong_ke = get_fraud_statistics()
    
    print(f"\n🔒 THỐNG KÊ PHÁT HIỆN GIAN LẬN:")
    print(f"   - Tổng số giao dịch: {thong_ke.get('total_transactions', 0)}")
    print(f"   - Đã xác thực: {thong_ke.get('verified_transactions', 0)}")
    print(f"   - Bị từ chối: {thong_ke.get('rejected_transactions', 0)}")
    print(f"   - Nỗ lực gian lận: {thong_ke.get('fraud_attempts', 0)}")
    
    if 'success_rate' in thong_ke:
        print(f"   - Tỷ lệ thành công: {thong_ke['success_rate']}")
    
    # Thống kê từ blockchain
    blockchain = get_blockchain()
    
    print(f"\n🛡️  BẢO MẬT BLOCKCHAIN:")
    print(f"   - Toàn vẹn chuỗi: {'✓ HỢP LỆ' if blockchain.is_chain_valid() else '✗ KHÔNG HỢP LỆ'}")
    print(f"   - Số giao dịch đang chờ: {len(blockchain.pending_transactions)}")

def chay_kiem_tra_bao_mat():
    """Chạy các bài kiểm tra bảo mật tự động"""
    print("\n" + "="*70)
    print(" KIỂM TRA BẢO MẬT")
    print("="*70)
    
    print("\n Chức năng này sẽ chạy các bài kiểm tra bảo mật toàn diện bao gồm:")
    print("   • Phát hiện chi tiêu hai lần (Double-spending)")
    print("   • Phát hiện tấn công phát lại (Replay attack)")
    print("   • Phát hiện giả mạo chữ ký")
    print("   • Phát hiện thay đổi số tiền giao dịch")
    print("   • Xử lý các giao dịch đồng thời")
    
    xac_nhan = input("\n Bạn có muốn tiếp tục? (y/n): ").strip().lower()
    
    if xac_nhan != 'y':
        print(" Đã hủy.")
        return
    
    try:
        from tests.security_tests import SecurityTestSuite
        
        bo_kiem_tra = SecurityTestSuite()
        bo_kiem_tra.run_all_tests()
        
    except ImportError:
        print(" Không tìm thấy tệp security_tests.py!")
        print(" Vui lòng đảm bảo file security_tests.py nằm trong thư mục hiện tại.")
    except Exception as e:
        print(f" Lỗi khi chạy kiểm tra: {e}")
        traceback.print_exc()

def chay_kiem_tra_giao_dich_hang_loat():
    """Chạy kiểm tra hiệu năng với số lượng lớn giao dịch"""
    print("\n" + "="*70)
    print(" KIỂM TRA GIAO DỊCH HÀNG LOẠT")
    print("="*70)
    
    print("\nChọn chế độ kiểm tra:")
    print("1. Nhanh (100 tài khoản, 1,000 giao dịch)")
    print("2. Vừa (1,000 tài khoản, 10,000 giao dịch)")
    print("3. Nặng (5,000 tài khoản, 50,000 giao dịch)")
    print("4. Tùy chỉnh")
    
    lua_chon = input("\n Nhập lựa chọn: ").strip()
    
    if lua_chon not in ['1', '2', '3', '4']:
        print(" Lựa chọn không hợp lệ.")
        return
    
    try:
        from tests.run_1000_accounts import MassTransactionTester
        
        # Lấy tham số kiểm tra
        if lua_chon == '1':
            so_tai_khoan, so_giao_dich = 100, 1000
        elif lua_chon == '2':
            so_tai_khoan, so_giao_dich = 1000, 10000
        elif lua_chon == '3':
            so_tai_khoan, so_giao_dich = 5000, 50000
        else:  # Tùy chỉnh
            try:
                so_tai_khoan = int(input("Nhập số lượng tài khoản: "))
                so_giao_dich = int(input("Nhập số lượng giao dịch: "))
            except ValueError:
                print(" Dữ liệu nhập không hợp lệ!")
                return
        
        print(f"\n Bắt đầu kiểm tra với {so_tai_khoan} tài khoản và {so_giao_dich} giao dịch...")
        
        # Khởi tạo bộ kiểm tra
        bo_kiem_tra = MassTransactionTester(so_tai_khoan)
        bo_kiem_tra.create_mass_accounts()
        
        # Chạy kiểm tra
        if so_giao_dich > 0:
            print("\n" + "="*70)
            print("GIAI ĐOẠN 1: KIỂM TRA TUẦN TỰ")
            print("="*70)
            bo_kiem_tra.run_sequential_test(so_giao_dich // 2)
            
            print("\n" + "="*70)
            print("GIAI ĐOẠN 2: KIỂM TRA ĐỒNG THỜI")
            print("="*70)
            bo_kiem_tra.run_concurrent_test(so_giao_dich // 2, max_workers=20)
        
        print("\n" + "="*70)
        print("GIAI ĐOẠN 3: MÔ PHỎNG TẤN CÔNG BẢO MẬT")
        print("="*70)
        bo_kiem_tra.simulate_double_spending_attack(100)
        bo_kiem_tra.simulate_replay_attacks(50)
        
        print("\n" + "="*70)
        print("KẾT QUẢ CUỐI CÙNG")
        print("="*70)
        bo_kiem_tra.print_stats()
        bo_kiem_tra.save_report()
        
        print("\n✅ Kiểm tra hàng loạt hoàn tất!")
        
    except ImportError:
        print(" Lỗi: Không thể nhập mô-đun 'run_1000_accounts.py'!")
        print(" Vui lòng đảm bảo file run_1000_accounts.py nằm trong thư mục hiện tại.")
    except Exception as e:
        print(f" Lỗi: {e}")
        traceback.print_exc()

def ham_chinh():
    """Hàm chính điều khiển luồng của chương trình"""
    while True:
        xoa_man_hinh()
        
        
        lua_chon = menu_chinh()
        
        if lua_chon == "1":
            quy_trinh_tao_vi()
        elif lua_chon == "2":
            hien_thi_thong_tin_vi()
        elif lua_chon == "3":
            quy_trinh_tao_giao_dich()
        elif lua_chon == "4":
            quy_trinh_xac_thuc_giao_dich()
        elif lua_chon == "5":
            hien_thi_danh_sach_giao_dich()
        elif lua_chon == "6":
            hien_thi_chi_tiet_giao_dich()
        elif lua_chon == "7":
            hien_thi_blockchain()
        elif lua_chon == "8":
            hien_thi_thong_ke_he_thong()
        elif lua_chon == "9":
            hien_thi_thong_ke_bao_mat()
        elif lua_chon == "10":
            chay_kiem_tra_bao_mat()
        elif lua_chon == "11":
            chay_kiem_tra_giao_dich_hang_loat()
        elif lua_chon == "0":
            print("\n👋 Tạm biệt!")
            break
        else:
            print("❌ Lựa chọn không hợp lệ, vui lòng thử lại!")
        
        input("\n⏎ Nhấn Enter để tiếp tục...")

if __name__ == "__main__":
    try:
        ham_chinh()
    except KeyboardInterrupt:
        print("\n\n⚠️  Chương trình đã dừng.")
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
        traceback.print_exc()