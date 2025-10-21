#!/usr/bin/env python3
"""
Script deploy hệ thống lên Ganache
Hướng dẫn:
1. Cài đặt Ganache: https://trufflesuite.com/ganache/
2. Chạy Ganache trên port 7545
3. Chạy script này để deploy smart contract
"""

import json
import os
import time
from web3 import Web3
from solcx import compile_source, install_solc

class GanacheDeployer:
    """Deploy hệ thống lên Ganache"""
    
    def __init__(self, ganache_url="http://127.0.0.1:7545"):
        self.ganache_url = ganache_url
        self.w3 = None
        self.contract = None
        self.contract_address = None
        
    def connect(self):
        """Kết nối tới Ganache"""
        print("🔌 Connecting to Ganache...")
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.ganache_url))
            
            if self.w3.is_connected():
                print(f"✅ Connected to Ganache")
                print(f"   Chain ID: {self.w3.eth.chain_id}")
                print(f"   Latest Block: {self.w3.eth.block_number}")
                print(f"   Accounts: {len(self.w3.eth.accounts)}")
                return True
            else:
                print("❌ Cannot connect to Ganache")
                print("💡 Please start Ganache on http://127.0.0.1:7545")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def compile_contract(self):
        """Compile smart contract"""
        print("\n📝 Compiling smart contract...")
        
        # Smart Contract source code
        contract_source = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransactionVerifier {
    
    // Cấu trúc giao dịch
    struct Transaction {
        string txId;
        address from;
        address to;
        uint256 amount;
        uint256 timestamp;
        string signature;
        bool verified;
        bool executed;
        string status;
    }
    
    // Lưu trữ
    mapping(string => Transaction) public transactions;
    mapping(address => uint256) public balances;
    mapping(address => uint256) public nonces;
    string[] public transactionIds;
    
    // Events
    event TransactionCreated(string txId, address indexed from, address indexed to, uint256 amount);
    event TransactionVerified(string txId, bool verified);
    event TransactionExecuted(string txId, uint256 amount);
    event BalanceUpdated(address indexed account, uint256 newBalance);
    event FraudDetected(string txId, string reason);
    
    // Modifiers
    modifier onlyValidTransaction(string memory txId) {
        require(bytes(transactions[txId].txId).length > 0, "Transaction does not exist");
        _;
    }
    
    // Constructor
    constructor() {
        // Initialize contract
    }
    
    // Tạo giao dịch
    function createTransaction(
        string memory txId,
        address to,
        uint256 amount,
        string memory signature
    ) public returns (bool) {
        // Kiểm tra giao dịch đã tồn tại chưa
        require(bytes(transactions[txId].txId).length == 0, "Transaction already exists");
        
        // Kiểm tra số dư
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // Tạo transaction
        transactions[txId] = Transaction({
            txId: txId,
            from: msg.sender,
            to: to,
            amount: amount,
            timestamp: block.timestamp,
            signature: signature,
            verified: false,
            executed: false,
            status: "pending"
        });
        
        transactionIds.push(txId);
        
        emit TransactionCreated(txId, msg.sender, to, amount);
        return true;
    }
    
    // Verify giao dịch
    function verifyTransaction(string memory txId, bool isValid, string memory reason) 
        public 
        onlyValidTransaction(txId) 
        returns (bool) 
    {
        Transaction storage tx = transactions[txId];
        
        // Kiểm tra giao dịch chưa được thực thi
        require(!tx.executed, "Transaction already executed");
        
        tx.verified = isValid;
        
        if (isValid) {
            tx.status = "verified";
            emit TransactionVerified(txId, true);
            
            // Tự động thực thi nếu verified
            return executeTransaction(txId);
        } else {
            tx.status = "rejected";
            emit FraudDetected(txId, reason);
            emit TransactionVerified(txId, false);
            return false;
        }
    }
    
    // Thực thi giao dịch
    function executeTransaction(string memory txId) 
        internal 
        onlyValidTransaction(txId) 
        returns (bool) 
    {
        Transaction storage tx = transactions[txId];
        
        // Kiểm tra các điều kiện
        require(tx.verified, "Transaction not verified");
        require(!tx.executed, "Transaction already executed");
        require(balances[tx.from] >= tx.amount, "Insufficient balance");
        
        // Thực hiện chuyển tiền
        balances[tx.from] -= tx.amount;
        balances[tx.to] += tx.amount;
        
        // Cập nhật nonce
        nonces[tx.from]++;
        
        // Đánh dấu đã thực thi
        tx.executed = true;
        tx.status = "executed";
        
        emit TransactionExecuted(txId, tx.amount);
        emit BalanceUpdated(tx.from, balances[tx.from]);
        emit BalanceUpdated(tx.to, balances[tx.to]);
        
        return true;
    }
    
    // Nạp tiền vào ví
    function deposit() public payable {
        balances[msg.sender] += msg.value;
        emit BalanceUpdated(msg.sender, balances[msg.sender]);
    }
    
    // Nạp tiền cho địa chỉ cụ thể (for testing)
    function depositTo(address account, uint256 amount) public {
        balances[account] += amount;
        emit BalanceUpdated(account, balances[account]);
    }
    
    // Lấy số dư
    function getBalance(address account) public view returns (uint256) {
        return balances[account];
    }
    
    // Lấy thông tin giao dịch
    function getTransaction(string memory txId) 
        public 
        view 
        onlyValidTransaction(txId)
        returns (
            string memory,
            address,
            address,
            uint256,
            uint256,
            bool,
            bool,
            string memory
        ) 
    {
        Transaction memory tx = transactions[txId];
        return (
            tx.txId,
            tx.from,
            tx.to,
            tx.amount,
            tx.timestamp,
            tx.verified,
            tx.executed,
            tx.status
        );
    }
    
    // Lấy nonce
    function getNonce(address account) public view returns (uint256) {
        return nonces[account];
    }
    
    // Lấy tổng số giao dịch
    function getTotalTransactions() public view returns (uint256) {
        return transactionIds.length;
    }
    
    // Kiểm tra double spending
    function checkDoubleSpending(address sender, uint256 amount, uint256 timeWindow) 
        public 
        view 
        returns (bool, string memory) 
    {
        uint256 currentTime = block.timestamp;
        uint256 pendingAmount = 0;
        
        // Duyệt qua các giao dịch
        for (uint256 i = 0; i < transactionIds.length; i++) {
            Transaction memory tx = transactions[transactionIds[i]];
            
            // Chỉ kiểm tra giao dịch của sender trong time window
            if (tx.from == sender && 
                !tx.executed && 
                currentTime - tx.timestamp <= timeWindow) {
                pendingAmount += tx.amount;
            }
        }
        
        // Kiểm tra tổng pending + amount mới có vượt quá balance không
        if (pendingAmount + amount > balances[sender]) {
            return (true, "Double spending detected");
        }
        
        return (false, "No double spending");
    }
}
'''
        
        try:
            # Cài đặt solc nếu chưa có
            try:
                install_solc('0.8.0')
            except:
                pass
            
            # Compile
            compiled_sol = compile_source(
                contract_source,
                output_values=['abi', 'bin']
            )
            
            contract_id, contract_interface = compiled_sol.popitem()
            
            self.abi = contract_interface['abi']
            self.bytecode = contract_interface['bin']
            
            print("✅ Contract compiled successfully")
            return True
            
        except Exception as e:
            print(f"❌ Compilation error: {e}")
            print("\n💡 Alternative: Use Remix IDE to compile")
            print("   1. Go to https://remix.ethereum.org")
            print("   2. Create new file: TransactionVerifier.sol")
            print("   3. Paste the contract code")
            print("   4. Compile and deploy to Ganache")
            return False
    
    def deploy_contract(self):
        """Deploy contract lên Ganache"""
        print("\n🚀 Deploying contract to Ganache...")
        
        if not self.w3:
            print("❌ Not connected to Ganache")
            return False
        
        try:
            # Lấy account để deploy
            deployer_account = self.w3.eth.accounts[0]
            print(f"   Deployer account: {deployer_account}")
            
            # Tạo contract instance
            Contract = self.w3.eth.contract(
                abi=self.abi,
                bytecode=self.bytecode
            )
            
            # Ước tính gas
            gas_estimate = Contract.constructor().estimate_gas({
                'from': deployer_account
            })
            print(f"   Estimated gas: {gas_estimate}")
            
            # Deploy
            tx_hash = Contract.constructor().transact({
                'from': deployer_account,
                'gas': gas_estimate * 2
            })
            
            print(f"   Transaction hash: {tx_hash.hex()}")
            print("   Waiting for confirmation...")
            
            # Đợi transaction được mine
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.contract_address = tx_receipt.contractAddress
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.abi
            )
            
            print(f"✅ Contract deployed at: {self.contract_address}")
            print(f"   Gas used: {tx_receipt['gasUsed']}")
            
            # Lưu thông tin contract
            self.save_contract_info()
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_contract_info(self):
        """Lưu thông tin contract"""
        os.makedirs("data", exist_ok=True)
        
        contract_info = {
            "address": self.contract_address,
            "abi": self.abi,
            "deployer": self.w3.eth.accounts[0],
            "deployed_at": time.time(),
            "chain_id": self.w3.eth.chain_id,
            "ganache_url": self.ganache_url
        }
        
        with open("data/contract_info.json", 'w') as f:
            json.dump(contract_info, f, indent=2)
        
        print(f"📄 Contract info saved to: data/contract_info.json")
    
    def test_contract(self):
        """Test contract sau khi deploy"""
        print("\n🧪 Testing deployed contract...")
        
        if not self.contract:
            print("❌ Contract not deployed")
            return False
        
        try:
            # Test 1: Deposit
            account = self.w3.eth.accounts[0]
            print(f"\n1. Testing deposit for {account}...")
            
            tx_hash = self.contract.functions.depositTo(
                account,
                1000000
            ).transact({'from': account})
            
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            balance = self.contract.functions.getBalance(account).call()
            print(f"   ✅ Balance: {balance}")
            
            # Test 2: Create transaction
            print(f"\n2. Testing transaction creation...")
            
            tx_id = "test_tx_001"
            to_account = self.w3.eth.accounts[1]
            amount = 50000
            
            tx_hash = self.contract.functions.createTransaction(
                tx_id,
                to_account,
                amount,
                "test_signature_hex"
            ).transact({'from': account})
            
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"   ✅ Transaction created: {tx_id}")
            
            # Test 3: Verify transaction
            print(f"\n3. Testing transaction verification...")
            
            tx_hash = self.contract.functions.verifyTransaction(
                tx_id,
                True,
                "Valid transaction"
            ).transact({'from': account})
            
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"   ✅ Transaction verified and executed")
            
            # Check balances
            balance_from = self.contract.functions.getBalance(account).call()
            balance_to = self.contract.functions.getBalance(to_account).call()
            
            print(f"   From balance: {balance_from}")
            print(f"   To balance: {balance_to}")
            
            print("\n✅ All contract tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def deploy_full_system(self):
        """Deploy toàn bộ hệ thống"""
        print("="*70)
        print("🚀 DEPLOYING FULL SYSTEM TO GANACHE")
        print("="*70)
        
        # Step 1: Connect
        if not self.connect():
            return False
        
        # Step 2: Compile
        if not self.compile_contract():
            print("\n⚠️  Using pre-compiled contract or manual deployment required")
            return False
        
        # Step 3: Deploy
        if not self.deploy_contract():
            return False
        
        # Step 4: Test
        if not self.test_contract():
            print("⚠️  Contract deployed but tests failed")
        
        print("\n" + "="*70)
        print("✅ DEPLOYMENT COMPLETED!")
        print("="*70)
        print(f"\n📋 Contract Address: {self.contract_address}")
        print(f"🔗 Ganache URL: {self.ganache_url}")
        print(f"📄 ABI saved to: data/contract_info.json")
        
        return True

def main():
    """Main deployment function"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         GANACHE DEPLOYMENT TOOL                              ║
║         E-Wallet Transaction Verification System             ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("Prerequisites:")
    print("  ✓ Ganache installed and running on http://127.0.0.1:7545")
    print("  ✓ Python packages: web3, py-solc-x")
    print("")
    
    input("Press Enter to start deployment...")
    
    deployer = GanacheDeployer()
    
    if deployer.deploy_full_system():
        print("\n🎉 System is ready for testing!")
        print("\nNext steps:")
        print("  1. Run: python security_tests.py")
        print("  2. Run: python run_1000_accounts.py")
        print("  3. Check blockchain stats in main menu")
    else:
        print("\n❌ Deployment failed!")
        print("\n💡 Manual deployment steps:")
        print("  1. Start Ganache")
        print("  2. Use Remix IDE (https://remix.ethereum.org)")
        print("  3. Deploy TransactionVerifier.sol")
        print("  4. Save contract address to data/contract_info.json")

if __name__ == "__main__":
    main()