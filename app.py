from flask import Flask, render_template, jsonify, request
from core.wallet import create_wallet, get_wallet_info, load_wallets_from_file
from core.transaction import create_transaction, sign_transaction, get_all_transactions
from core.verification import full_verification_flow
from security.fraud_detection import get_fraud_statistics
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/wallets', methods=['GET'])
def get_wallets():
    try:
        wallets = load_wallets_from_file()
        return jsonify(wallets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-wallet', methods=['POST'])
def api_create_wallet():
    try:
        data = request.json
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Tên ví không được để trống'}), 400
        wallet_info = create_wallet(name)
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
        if not all([from_user, to_user, amount]):
            return jsonify({'error': 'Thiếu thông tin giao dịch'}), 400
        transaction = create_transaction(from_user, to_user, amount)
        signed_tx = sign_transaction(transaction, from_user)
        return jsonify(signed_tx)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-transaction', methods=['POST'])
def api_verify_transaction():
    try:
        data = request.json
        tx_id = data.get('tx_id')
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
        return jsonify(wallet_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def api_get_transactions():
    try:
        transactions = get_all_transactions()
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