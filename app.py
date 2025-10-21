"""
Flask Web Application - E-Wallet Transaction Verification System
Database version (no JSON files)
"""
from flask import Flask, render_template, jsonify, request  
import os

# ✅ Fixed imports - use database functions
from core.wallet import create_wallet, get_wallet_info, get_all_wallets
from core.transaction import (
    create_transaction, 
    sign_transaction, 
    get_all_transactions,  # ✅ Changed from load_transactions
    get_transaction_by_id
)
from core.verification import full_verification_flow
from core.fraud_detection import get_fraud_statistics

app = Flask(__name__)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/wallets', methods=['GET'])
def get_wallets():
    """Lấy danh sách ví - chỉ thông tin công khai."""
    try:
        # ✅ Use database function
        wallets = get_all_wallets()
        
        safe_wallets = {}
        for wallet in wallets:
            safe_wallets[wallet["name"]] = {
                "name": wallet["name"],
                "address": wallet["address"],
                "balance": wallet.get("balance", 0),
                "created_at": wallet.get("created_at")
            }
        return jsonify(safe_wallets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-wallet', methods=['POST'])
def api_create_wallet():
    """Create new wallet"""
    try:
        data = request.json
        name = data.get('name')
        passphrase = data.get('passphrase')
        
        if not name or not passphrase:
            return jsonify({'error': 'Tên ví và passphrase không được để trống'}), 400
        
        wallet_info = create_wallet(name, passphrase)
        
        # Ẩn private key mã hóa
        wallet_info_safe = {
            "name": wallet_info["name"],
            "address": wallet_info["address"],
            "balance": wallet_info.get("balance", 0),
            "created_at": wallet_info.get("created_at")
        }
        
        return jsonify(wallet_info_safe)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-transaction', methods=['POST'])
def api_create_transaction():
    """Create and sign transaction"""
    try:
        data = request.json
        from_user = data.get('from_user')
        to_user = data.get('to_user')
        amount = data.get('amount')
        passphrase = data.get('passphrase')

        if not all([from_user, to_user, amount, passphrase]):
            return jsonify({'error': 'Thiếu thông tin giao dịch hoặc passphrase'}), 400

        # Validate amount
        try:
            amount = int(amount)
            if amount <= 0:
                return jsonify({'error': 'Số tiền phải lớn hơn 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Số tiền không hợp lệ'}), 400

        # Get wallet addresses
        from_wallet = get_wallet_info(from_user)
        to_wallet = get_wallet_info(to_user)
        
        if not from_wallet:
            return jsonify({'error': f'Không tìm thấy ví: {from_user}'}), 404
        if not to_wallet:
            return jsonify({'error': f'Không tìm thấy ví: {to_user}'}), 404

        # Create transaction
        transaction = create_transaction(
            from_user, to_user, amount,
            from_wallet["address"], to_wallet["address"]
        )
        
        # Sign transaction
        signed_tx = sign_transaction(transaction, from_user, passphrase)

        # Return full transaction info
        return jsonify({
            "id": signed_tx.get("id"),
            "from": signed_tx.get("sender"),  # ✅ Changed from "from"
            "to": signed_tx.get("receiver"),   # ✅ Changed from "to"
            "amount": signed_tx.get("amount"),
            "timestamp": signed_tx.get("timestamp"),
            "status": signed_tx.get("status", "signed"),
            "signature": signed_tx.get("signature")[:32] + "..."
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Lỗi tạo giao dịch: {str(e)}'}), 500

@app.route('/api/verify-transaction', methods=['POST'])
def api_verify_transaction():
    """Verify transaction"""
    try:
        data = request.json
        tx_id = data.get('tx_id') if data else None
        
        result = full_verification_flow(tx_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wallet-info', methods=['GET'])
def api_wallet_info():
    """Lấy thông tin ví công khai"""
    try:
        name = request.args.get('name')
        if not name:
            return jsonify({'error': 'Tên ví không được để trống'}), 400

        wallet_info = get_wallet_info(name, safe=True)
        if not wallet_info:
            return jsonify({'error': 'Không tìm thấy ví'}), 404

        return jsonify(wallet_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def api_get_transactions():
    """Get all transactions from database"""
    try:
        # ✅ Use database function
        transactions = get_all_transactions()
        
        # Format transactions for API
        formatted_txs = []
        for tx in transactions:
            formatted_txs.append({
                "id": tx.get("id"),
                "from": tx.get("sender"),
                "to": tx.get("receiver"),
                "amount": tx.get("amount"),
                "timestamp": tx.get("timestamp"),
                "status": tx.get("status"),
                "executed": tx.get("executed")
            })
        
        return jsonify(formatted_txs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fraud-statistics', methods=['GET'])
def api_fraud_statistics():
    """Get fraud detection statistics"""
    try:
        stats = get_fraud_statistics()
        
        # ✅ Get wallet count from database
        wallets = get_all_wallets()
        stats['total_wallets'] = len(wallets)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure directories exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Run Flask app
    print("🚀 Starting E-Wallet Web Server (Database Mode)...")
    print("📱 Open browser: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)