import sqlite3
import threading
import os
import json

DATA_DIR = "data"
DB_FILE = os.path.join(DATA_DIR, "system.db")
_lock = threading.Lock()

def get_connection():
    """Trả về connection SQLite thread-safe."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Khởi tạo toàn bộ cấu trúc DB nếu chưa tồn tại."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with _lock, get_connection() as conn:
        conn.executescript("""
        -- Wallets table với nonce
        CREATE TABLE IF NOT EXISTS wallets (
            name TEXT PRIMARY KEY,
            address TEXT UNIQUE,
            public_key TEXT,
            encrypted_private_key TEXT,
            salt TEXT,
            balance REAL DEFAULT 0,
            nonce INTEGER DEFAULT 0,
            created_at TEXT
        );

        -- Transactions table với nonce và expires_at
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            sender TEXT,
            receiver TEXT,
            from_address TEXT,
            to_address TEXT,
            amount INTEGER,
            timestamp TEXT,
            expires_at TEXT,
            status TEXT,
            signature TEXT,
            nonce INTEGER,
            executed INTEGER DEFAULT 0
        );
        
        -- ✅ NEW: Blocks table for blockchain
        CREATE TABLE IF NOT EXISTS blocks (
            index_number INTEGER PRIMARY KEY,
            timestamp REAL NOT NULL,
            previous_hash TEXT NOT NULL,
            nonce INTEGER DEFAULT 0,
            hash TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        -- ✅ NEW: Block transactions junction table
        CREATE TABLE IF NOT EXISTS block_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER NOT NULL,
            transaction_data TEXT NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (block_index) REFERENCES blocks(index_number) ON DELETE CASCADE
        );
        
        -- ✅ NEW: Blockchain metadata
        CREATE TABLE IF NOT EXISTS blockchain_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        
        -- Indexes để tối ưu performance
        CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address);
        CREATE INDEX IF NOT EXISTS idx_wallets_balance ON wallets(balance);
        
        CREATE INDEX IF NOT EXISTS idx_tx_sender ON transactions(sender);
        CREATE INDEX IF NOT EXISTS idx_tx_receiver ON transactions(receiver);
        CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status);
        CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(timestamp);
        CREATE INDEX IF NOT EXISTS idx_tx_executed ON transactions(executed);
        
        CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks(hash);
        CREATE INDEX IF NOT EXISTS idx_block_tx_block_idx ON block_transactions(block_index);
        CREATE INDEX IF NOT EXISTS idx_block_tx_position ON block_transactions(block_index, position);
        """)
        conn.commit()
        
        # Initialize blockchain metadata if not exists
        cursor = conn.execute("SELECT COUNT(*) FROM blockchain_metadata WHERE key = 'difficulty'")
        if cursor.fetchone()[0] == 0:
            conn.execute("INSERT INTO blockchain_metadata (key, value) VALUES ('difficulty', '2')")
            conn.execute("INSERT INTO blockchain_metadata (key, value) VALUES ('mining_reward', '100')")
            conn.commit()


def execute(query, params=()):
    """Thực thi câu lệnh (INSERT, UPDATE, DELETE)."""
    with _lock, get_connection() as conn:
        conn.execute(query, params)
        conn.commit()


def fetch_one(query, params=()):
    """Lấy 1 dòng dữ liệu (trả về dict hoặc None)."""
    with _lock, get_connection() as conn:
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)


def fetch_all(query, params=()):
    """Lấy nhiều dòng dữ liệu (trả về list[dict])."""
    with _lock, get_connection() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def migrate_add_nonce():
    """
    Thêm nonce column nếu chưa có
    Chạy script này nếu database cũ chưa có nonce
    """
    try:
        with _lock, get_connection() as conn:
            # Check if nonce column exists in wallets
            cursor = conn.execute("PRAGMA table_info(wallets)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if "nonce" not in columns:
                print("🔄 Migrating: Adding nonce column to wallets...")
                conn.execute("ALTER TABLE wallets ADD COLUMN nonce INTEGER DEFAULT 0")
                conn.commit()
                print("✅ Migration completed!")
            
            # Check transactions table
            cursor = conn.execute("PRAGMA table_info(transactions)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if "nonce" not in columns:
                print("🔄 Migrating: Adding nonce column to transactions...")
                conn.execute("ALTER TABLE transactions ADD COLUMN nonce INTEGER")
                conn.commit()
                print("✅ Migration completed!")
            
            if "expires_at" not in columns:
                print("🔄 Migrating: Adding expires_at column to transactions...")
                conn.execute("ALTER TABLE transactions ADD COLUMN expires_at TEXT")
                conn.commit()
                print("✅ Migration completed!")
                
    except Exception as e:
        print(f"⚠️ Migration error: {e}")


# ============= BLOCKCHAIN DATABASE FUNCTIONS ============= #

def save_block(block_dict):
    """Lưu block vào database"""
    try:
        with _lock, get_connection() as conn:
            # Insert block
            conn.execute("""
                INSERT OR REPLACE INTO blocks 
                (index_number, timestamp, previous_hash, nonce, hash)
                VALUES (?, ?, ?, ?, ?)
            """, (
                block_dict["index"],
                block_dict["timestamp"],
                block_dict["previous_hash"],
                block_dict["nonce"],
                block_dict["hash"]
            ))
            
            # Delete old transactions for this block (if replacing)
            conn.execute("DELETE FROM block_transactions WHERE block_index = ?", 
                        (block_dict["index"],))
            
            # Insert block transactions
            for position, tx in enumerate(block_dict["transactions"]):
                conn.execute("""
                    INSERT INTO block_transactions (block_index, transaction_data, position)
                    VALUES (?, ?, ?)
                """, (block_dict["index"], json.dumps(tx, ensure_ascii=False), position))
            
            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Error saving block: {e}")
        return False


def load_all_blocks():
    """Load tất cả blocks từ database"""
    try:
        with _lock, get_connection() as conn:
            cursor = conn.execute("""
                SELECT index_number, timestamp, previous_hash, nonce, hash
                FROM blocks
                ORDER BY index_number ASC
            """)
            
            blocks = []
            for row in cursor.fetchall():
                block_dict = dict(row)
                
                # Load transactions for this block
                tx_cursor = conn.execute("""
                    SELECT transaction_data
                    FROM block_transactions
                    WHERE block_index = ?
                    ORDER BY position ASC
                """, (block_dict["index_number"],))
                
                transactions = []
                for tx_row in tx_cursor.fetchall():
                    transactions.append(json.loads(tx_row[0]))
                
                blocks.append({
                    "index": block_dict["index_number"],
                    "timestamp": block_dict["timestamp"],
                    "previous_hash": block_dict["previous_hash"],
                    "nonce": block_dict["nonce"],
                    "hash": block_dict["hash"],
                    "transactions": transactions
                })
            
            return blocks
    except Exception as e:
        print(f"❌ Error loading blocks: {e}")
        return []


def get_blockchain_metadata(key, default=None):
    """Lấy metadata của blockchain"""
    row = fetch_one("SELECT value FROM blockchain_metadata WHERE key = ?", (key,))
    if row:
        return row["value"]
    return default


def set_blockchain_metadata(key, value):
    """Set metadata của blockchain"""
    with _lock, get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO blockchain_metadata (key, value)
            VALUES (?, ?)
        """, (key, str(value)))
        conn.commit()


def delete_all_blocks():
    """Xóa tất cả blocks (for testing/reset)"""
    with _lock, get_connection() as conn:
        conn.execute("DELETE FROM block_transactions")
        conn.execute("DELETE FROM blocks")
        conn.commit()


def get_block_count():
    """Đếm số lượng blocks"""
    with get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM blocks")
        return cursor.fetchone()[0]


def get_latest_block():
    """Lấy block mới nhất"""
    row = fetch_one("""
        SELECT index_number, timestamp, previous_hash, nonce, hash
        FROM blocks
        ORDER BY index_number DESC
        LIMIT 1
    """)
    
    if not row:
        return None
    
    block_dict = dict(row)
    
    # Load transactions
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT transaction_data
            FROM block_transactions
            WHERE block_index = ?
            ORDER BY position ASC
        """, (block_dict["index_number"],))
        
        transactions = []
        for tx_row in cursor.fetchall():
            transactions.append(json.loads(tx_row[0]))
    
    return {
        "index": block_dict["index_number"],
        "timestamp": block_dict["timestamp"],
        "previous_hash": block_dict["previous_hash"],
        "nonce": block_dict["nonce"],
        "hash": block_dict["hash"],
        "transactions": transactions
    }


def migrate_blockchain_from_json():
    """Migration: Chuyển blockchain từ JSON sang SQLite"""
    import os
    json_file = "data/blockchain.json"
    
    if not os.path.exists(json_file):
        print("ℹ️  No JSON blockchain file found. Skipping migration.")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        blocks = data.get("chain", [])
        if not blocks:
            print("ℹ️  No blocks to migrate")
            return
        
        print(f"🔄 Migrating {len(blocks)} blocks from JSON to SQLite...")
        
        for block in blocks:
            save_block(block)
        
        # Save metadata
        if "difficulty" in data:
            set_blockchain_metadata("difficulty", data["difficulty"])
        if "mining_reward" in data:
            set_blockchain_metadata("mining_reward", data["mining_reward"])
        
        print(f"✅ Migrated {len(blocks)} blocks successfully!")
        
        # Backup and remove old file
        backup_file = json_file + ".backup"
        os.rename(json_file, backup_file)
        print(f"📦 Old JSON file backed up to: {backup_file}")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()


def get_db_stats():
    """Lấy thống kê database tổng quan"""
    with get_connection() as conn:
        wallet_count = conn.execute("SELECT COUNT(*) FROM wallets").fetchone()[0]
        tx_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        tx_verified = conn.execute("SELECT COUNT(*) FROM transactions WHERE status = 'verified'").fetchone()[0]
        tx_pending = conn.execute("SELECT COUNT(*) FROM transactions WHERE status IN ('pending', 'signed')").fetchone()[0]
        block_count = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
        
        return {
            "total_wallets": wallet_count,
            "total_transactions": tx_count,
            "verified_transactions": tx_verified,
            "pending_transactions": tx_pending,
            "total_blocks": block_count
        }


# Tự động khởi tạo và migrate khi module được import
init_db()
migrate_add_nonce()

# Auto-migrate từ JSON nếu có
if get_block_count() == 0:
    migrate_blockchain_from_json()