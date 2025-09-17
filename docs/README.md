<div align="center">

# 🔐 Xác thực giao dịch ví điện tử bằng chữ ký số ECDSA

**🎯 Ngăn chặn giao dịch giả mạo trong hệ thanh toán điện tử**

</div>


## 🎯 Mục tiêu chính

- ✅ Tạo và quản lý ví điện tử với khóa ECDSA
- ✅ Ký giao dịch bằng thuật toán ECDSA 
- ✅ Xây dựng flow xác thực giao dịch
- ✅ Phát hiện và ngăn chặn giao dịch giả mạo
- ✅ Demo hệ thống hoạt động

## 🛠️ Công nghệ sử dụng

<div align="center">

| Công nghệ | Mô tả | Badge |
|-----------|--------|-------|
| **Python** | Ngôn ngữ lập trình chính | ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) |
| **ECDSA** | Thuật toán chữ ký số | ![Crypto](https://img.shields.io/badge/cryptography-ECDSA-red?style=for-the-badge) |
| **JSON** | Lưu trữ dữ liệu | ![JSON](https://img.shields.io/badge/json-%23000000.svg?style=for-the-badge&logo=json&logoColor=white) |
| **VS Code** | IDE phát triển | ![VS Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white) |

</div>

## 📁 Cấu trúc dự án

```
ECDSA/
│
├── main.py                    # Chương trình chính
├── requirements.txt           # Thư viện cần thiết
├── README.md                  # File này
│
├── core/                      # Chức năng chính
│   ├── wallet.py             # Quản lý ví
│   ├── transaction.py        # Tạo và ký giao dịch
│   └── verification.py       # Xác thực giao dịch
│
├── security/                  # Bảo mật
│   └── fraud_detection.py    # Phát hiện giả mạo
│
├── data/                      # Dữ liệu JSON
│   ├── wallets.json          # Thông tin ví
│   └── transactions.json     # Lịch sử giao dịch
│
└── tests/                     # Kiểm thử
    ├── test_signature.py     # Test chữ ký
    └── test_verification.py  # Test xác thực
```

## ⚙️ Hướng dẫn cài đặt

### Bước 1: Clone/Download dự án
```bash
# Tải về hoặc copy folder dự án
cd ECDSA
```

### Bước 2: Cài đặt Python
- Tải Python 3.8+ từ: https://python.org
- Kiểm tra: `python --version`

### Bước 3: Cài đặt thư viện
```bash
pip install -r requirements.txt
```

Hoặc cài thủ công:
```bash
pip install ecdsa
```

### Bước 4: Tạo thư mục data (nếu chưa có)
```bash
mkdir data
```

## 🚀 Hướng dẫn sử dụng

<details>
<summary><b>🎮 Menu chương trình</b></summary>

### Chạy chương trình:
```bash
python main.py
```

| Tùy chọn | Chức năng | Mô tả |
|----------|-----------|-------|
| **1** | 🏦 Tạo ví mới | Tạo khóa ECDSA và cấp số dư ban đầu |
| **2** | 💸 Tạo giao dịch | Ký giao dịch bằng thuật toán ECDSA |
| **3** | 🔍 Xác thực giao dịch | **CHỨC NĂNG CHÍNH** - Kiểm tra tính hợp lệ |
| **4** | 👤 Xem thông tin ví | Hiển thị địa chỉ, số dư, khóa công khai |
| **0** | 🚪 Thoát | Kết thúc chương trình |

</details>

## 🔐 Tính năng bảo mật

### Xác thực chữ ký ECDSA
- Sử dụng đường cong SECP256k1
- Xác minh chữ ký với khóa công khai
- Phát hiện chữ ký giả mạo

### Kiểm tra giao dịch
- ✅ Kiểm tra số dư đầy đủ
- ✅ Xác minh định dạng giao dịch
- ✅ Phát hiện double spending
- ✅ Ngăn chặn replay attack

### Lưu trữ an toàn
- Khóa riêng được mã hóa
- Lịch sử giao dịch bất biến
- Audit trail đầy đủ

## 🧪 Chạy Test

```bash
# Test chữ ký ECDSA
python tests/test_signature.py

# Test xác thực
python tests/test_verification.py

# Chạy tất cả test
python tests/run_all_tests.py
```

## 📊 Demo kết quả

<div align="center">

### ✅ Giao dịch hợp lệ
```diff
🔍 KẾT QUẢ XÁC THỰC:
+ Trạng thái: ✅ HỢP LỆ
+ Chữ ký: ✅ Đúng
+ Số dư: ✅ Đủ  
+ Bảo mật: ✅ An toàn
```

### ❌ Giao dịch giả mạo  
```diff
🔍 KẾT QUẢ XÁC THỰC:
- Trạng thái: ❌ KHÔNG HỢP LỆ
- Chữ ký: ❌ Sai
+ Số dư: ✅ Đủ
- Bảo mật: ❌ Nghi ngờ giả mạo
! Chi tiết: Chữ ký không khớp với người gửi
```

</div>

## 🏆 Kết quả đạt được

- [x] Tạo ví với khóa ECDSA thành công
- [x] Ký giao dịch bằng thuật toán ECDSA
- [x] Xây dựng flow xác thực hoàn chỉnh  
- [x] Phát hiện được giao dịch giả mạo
- [x] Demo hệ thống hoạt động ổn định
- [x] Viết test case đầy đủ

## ⚠️ Lưu ý

- Đây là dự án học tập, không dùng trong thực tế
- Khóa riêng lưu trữ đơn giản, chưa có bảo mật cao
- Chỉ demo cơ bản, chưa có networking
- Số dư ảo, không liên kết ngân hàng thật

## 📚 Tài liệu tham khảo

- [ECDSA Algorithm](https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm)
- [Python ECDSA Library](https://pypi.org/project/ecdsa/)
- [Digital Signatures](https://en.wikipedia.org/wiki/Digital_signature)

---

<div align="center">


### 🌟 Nếu thấy hữu ích, hãy cho dự án một ⭐!

[![GitHub stars](https://img.shields.io/github/stars/yourusername/ecdsa-wallet?style=social)]
[![GitHub forks](https://img.shields.io/github/forks/yourusername/ecdsa-wallet?style=social)]


</div>