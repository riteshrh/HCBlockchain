
import hashlib
import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Block:
    def __init__(self, index: int, transactions: List[Dict], previous_hash: str, timestamp: Optional[float] = None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int = 2):
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        logger.debug(f"Block mined: {self.hash}")
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Block':
        block = cls(
            index=data["index"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            timestamp=data["timestamp"]
        )
        block.nonce = data["nonce"]
        block.hash = data["hash"]
        return block

class SimpleBlockchain:
    def __init__(self, storage_path: Optional[str] = None, difficulty: int = 2):
        self.chain: List[Block] = []
        self.pending_transactions: List[Dict] = []
        self.difficulty = difficulty
        self.storage_path = Path(storage_path) if storage_path else Path("blockchain_data.json")
        
        # Create genesis block
        self.create_genesis_block()
        
        # Load existing blockchain if it exists
        self.load_blockchain()
    
    def create_genesis_block(self):
        if not self.chain:
            genesis_block = Block(
                index=0,
                transactions=[{
                    "type": "genesis",
                    "data": "Healthcare Blockchain Genesis Block",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }],
                previous_hash="0"
            )
            genesis_block.mine_block(self.difficulty)
            self.chain.append(genesis_block)
            logger.info("Genesis block created")
    
    def get_latest_block(self) -> Block:
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict) -> str:
        # Add timestamp if not present
        if "timestamp" not in transaction:
            transaction["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Generate transaction ID
        tx_string = json.dumps(transaction, sort_keys=True)
        tx_id = hashlib.sha256(tx_string.encode()).hexdigest()
        transaction["tx_id"] = tx_id
        
        self.pending_transactions.append(transaction)
        logger.info(f"Transaction added: {tx_id}")
        
        return tx_id
    
    def mine_pending_transactions(self) -> Block:
        if not self.pending_transactions:
            raise ValueError("No pending transactions to mine")
        
        block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash
        )
        
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []
        
        # Save blockchain
        self.save_blockchain()
        
        logger.info(f"Block #{block.index} mined with {len(block.transactions)} transactions")
        return block
    
    def add_transaction_and_mine(self, transaction: Dict) -> Dict:
        tx_id = self.add_transaction(transaction)
        block = self.mine_pending_transactions()
        
        return {
            "tx_id": tx_id,
            "block_hash": block.hash,
            "block_index": block.index,
            "status": "confirmed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block hash is valid
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Block #{i} hash is invalid")
                return False
            
            # Check if block points to previous block
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Block #{i} previous hash is invalid")
                return False
        
        return True
    
    def query_transaction(self, tx_id: str) -> Optional[Dict]:
        # Search in all blocks
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("tx_id") == tx_id:
                    return {
                        "tx_id": tx_id,
                        "block_index": block.index,
                        "block_hash": block.hash,
                        "transaction": tx,
                        "timestamp": block.timestamp
                    }
        
        # Search in pending transactions
        for tx in self.pending_transactions:
            if tx.get("tx_id") == tx_id:
                return {
                    "tx_id": tx_id,
                    "block_index": None,
                    "block_hash": None,
                    "transaction": tx,
                    "status": "pending"
                }
        
        return None
    
    def query_by_type(self, transaction_type: str) -> List[Dict]:
        results = []
        
        for block in self.chain:
            for tx in block.transactions:
                if tx.get("type") == transaction_type:
                    results.append({
                        "tx_id": tx.get("tx_id"),
                        "block_index": block.index,
                        "block_hash": block.hash,
                        "transaction": tx,
                        "timestamp": block.timestamp
                    })
        
        return results
    
    def save_blockchain(self):
        try:
            data = {
                "chain": [block.to_dict() for block in self.chain],
                "pending_transactions": self.pending_transactions,
                "difficulty": self.difficulty
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Blockchain saved to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save blockchain: {e}")
    
    def load_blockchain(self):
        if not self.storage_path.exists():
            logger.info("No existing blockchain found. Creating new blockchain.")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Reconstruct chain
            self.chain = [Block.from_dict(block_data) for block_data in data.get("chain", [])]
            self.pending_transactions = data.get("pending_transactions", [])
            self.difficulty = data.get("difficulty", 2)
            
            # Validate loaded chain
            if not self.is_chain_valid():
                logger.warning("Loaded blockchain is invalid. Creating new chain.")
                self.chain = []
                self.create_genesis_block()
            else:
                logger.info(f"Blockchain loaded: {len(self.chain)} blocks")
        
        except Exception as e:
            logger.error(f"Failed to load blockchain: {e}. Creating new chain.")
            self.chain = []
            self.create_genesis_block()
    
    def get_chain_info(self) -> Dict:
        return {
            "chain_length": len(self.chain),
            "pending_transactions": len(self.pending_transactions),
            "difficulty": self.difficulty,
            "is_valid": self.is_chain_valid(),
            "latest_block_hash": self.get_latest_block().hash if self.chain else None
        }

# Global blockchain instance
_blockchain_instance: Optional[SimpleBlockchain] = None

def get_blockchain(storage_path: Optional[str] = None) -> SimpleBlockchain:
    global _blockchain_instance
    if _blockchain_instance is None:
        _blockchain_instance = SimpleBlockchain(storage_path=storage_path)
    return _blockchain_instance
