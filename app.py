# from flask import Flask, render_template, jsonify, request
# from core.wallet import create_wallet, get_wallet_info, load_wallets_from_file
# from core.transaction import create_transaction, sign_transaction, get_all_transactions
# from core.verification import full_verification_flow
# from security.fraud_detection import get_fraud_statistics
# import os

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/api/wallets', methods=['GET'])
# def get_wallets():
#     try:
#         wallets = load_wallets_from_file()
#         return jsonify(wallets)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/create-wallet', methods=['POST'])
# def api_create_wallet():
#     try:
#         data = request.json
#         name = data.get('name')
#         if not name:
#             return jsonify({'error': 'Tên ví không được để trống'}), 400
#         wallet_info = create_wallet(name)
#         return jsonify(wallet_info)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/create-transaction', methods=['POST'])
# def api_create_transaction():
#     try:
#         data = request.json
#         from_user = data.get('from_user')
#         to_user = data.get('to_user')
#         amount = data.get('amount')
#         if not all([from_user, to_user, amount]):
#             return jsonify({'error': 'Thiếu thông tin giao dịch'}), 400
#         transaction = create_transaction(from_user, to_user, amount)
#         signed_tx = sign_transaction(transaction, from_user)
#         return jsonify(signed_tx)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/verify-transaction', methods=['POST'])
# def api_verify_transaction():
#     try:
#         data = request.json
#         tx_id = data.get('tx_id')
#         result = full_verification_flow(tx_id)
#         return jsonify(result)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/wallet-info', methods=['GET'])
# def api_wallet_info():
#     try:
#         name = request.args.get('name')
#         if not name:
#             return jsonify({'error': 'Tên ví không được để trống'}), 400
#         wallet_info = get_wallet_info(name)
#         if not wallet_info:
#             return jsonify({'error': 'Không tìm thấy ví'}), 404
#         return jsonify(wallet_info)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/transactions', methods=['GET'])
# def api_get_transactions():
#     try:
#         transactions = get_all_transactions()
#         return jsonify(transactions)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/fraud-statistics', methods=['GET'])
# def api_fraud_statistics():
#     try:
#         stats = get_fraud_statistics()
#         wallets = load_wallets_from_file()
#         stats['total_wallets'] = len(wallets)
#         return jsonify(stats)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#     os.makedirs('templates', exist_ok=True)
#     os.makedirs('data', exist_ok=True)
#     app.run(debug=True)












from flask import Flask, render_template, jsonify, request
from core.wallet import create_wallet, get_wallet_info, load_wallets_from_file
from core.transaction import sign_transaction, load_transactions ,create_transaction
from core.verification import full_verification_flow
from core.fraud_detection import get_fraud_statistics

import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/wallets', methods=['GET'])
def get_wallets():
    try:
        wallets = load_wallets_from_file()
        # Ẩn private key đã mã hóa
        safe_wallets = {}
        for name, w in wallets.items():
            w_copy = w.copy()
            w_copy.pop("encrypted_private_key", None)
            w_copy.pop("salt", None)
            safe_wallets[name] = w_copy
        return jsonify(safe_wallets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-wallet', methods=['POST'])
def api_create_wallet():
    try:
        data = request.json
        name = data.get('name')
        passphrase = data.get('passphrase')
        if not name or not passphrase:
            return jsonify({'error': 'Tên ví và passphrase không được để trống'}), 400
        wallet_info = create_wallet(name, passphrase)
        # Ẩn private key mã hóa
        wallet_info.pop("encrypted_private_key", None)
        wallet_info.pop("salt", None)
        return jsonify(wallet_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-transaction', methods=['POST'])
def api_create_transaction():
    try:
        data = request.json
        from_user = data.get('from_user')
        to_user = data.get('to_user')
        amount = data.get('amount')
        passphrase = data.get('passphrase')

        if not all([from_user, to_user, amount, passphrase]):
            return jsonify({'error': 'Thiếu thông tin giao dịch hoặc passphrase'}), 400

        # Tạo giao dịch
        transaction = create_transaction(from_user, to_user, amount)
        signed_tx = sign_transaction(transaction, from_user, passphrase)

        # Trả về thông tin giao dịch đầy đủ
        return jsonify({
            "id": signed_tx.get("id"),
            "from": signed_tx.get("from"),
            "to": signed_tx.get("to"),
            "amount": amount,   # ✅ luôn có amount
            "status": signed_tx.get("status", "signed")
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-transaction', methods=['POST'])
def api_verify_transaction():
    try:
        data = request.json
        tx_id = data.get('tx_id')
        if not tx_id:
            return jsonify({'error': 'Thiếu transaction ID'}), 400
        result = full_verification_flow(tx_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wallet-info', methods=['GET'])
def api_wallet_info():
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({'error': 'Tên ví không được để trống'}), 400
        wallet_info = get_wallet_info(name)
        if not wallet_info:
            return jsonify({'error': 'Không tìm thấy ví'}), 404
        # Ẩn private key mã hóa
        wallet_info = wallet_info.copy()
        wallet_info.pop("encrypted_private_key", None)
        wallet_info.pop("salt", None)
        return jsonify(wallet_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def api_get_transactions():
    try:
        transactions = load_transactions()
        if isinstance(transactions, dict):
            transactions = list(transactions.values())
        return jsonify(transactions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fraud-statistics', methods=['GET'])
def api_fraud_statistics():
    try:
        stats = get_fraud_statistics()
        wallets = load_wallets_from_file()
        stats['total_wallets'] = len(wallets)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)
