import hashlib
import json
import random
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class POSBlock:
    def __init__(self, index: int, transactions: List[Dict], previous_hash: str, validator: str, timestamp: Optional[float] = None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.validator = validator
        self.timestamp = timestamp or time.time()
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "validator": self.validator,
            "timestamp": self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "validator": self.validator,
            "timestamp": self.timestamp,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'POSBlock':
        block = cls(
            index=data["index"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            validator=data["validator"],
            timestamp=data["timestamp"]
        )
        block.hash = data["hash"]
        return block

class ProofOfStakeBlockchain:
    def __init__(self, storage_path: Optional[str] = None):
        self.chain: List[POSBlock] = []
        self.pending_transactions: List[Dict] = []
        self.validators: Dict[str, float] = {}
        self.storage_path = Path(storage_path) if storage_path else Path("pos_blockchain_data.json")
        
        self.create_genesis_block()
        self.load_blockchain()
    
    def create_genesis_block(self):
        if not self.chain:
            genesis_block = POSBlock(
                index=0,
                transactions=[{
                    "type": "genesis",
                    "data": "PoS Healthcare Blockchain Genesis Block",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }],
                previous_hash="0",
                validator="system"
            )
            self.chain.append(genesis_block)
            logger.info("PoS Genesis block created")
    
    def add_validator(self, validator_id: str, stake: float):
        if stake <= 0:
            raise ValueError("Stake must be positive")
        self.validators[validator_id] = stake
        logger.info(f"Validator {validator_id} added with stake {stake}")
    
    def select_validator(self) -> str:
        if not self.validators:
            return "default_validator"
        
        total_stake = sum(self.validators.values())
        if total_stake == 0:
            return list(self.validators.keys())[0] if self.validators else "default_validator"
        
        random_value = random.uniform(0, total_stake)
        current = 0
        
        for validator_id, stake in self.validators.items():
            current += stake
            if random_value <= current:
                return validator_id
        
        return list(self.validators.keys())[-1]
    
    def get_latest_block(self) -> POSBlock:
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict) -> str:
        if "timestamp" not in transaction:
            transaction["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        tx_string = json.dumps(transaction, sort_keys=True)
        tx_id = hashlib.sha256(tx_string.encode()).hexdigest()
        transaction["tx_id"] = tx_id
        
        self.pending_transactions.append(transaction)
        return tx_id
    
    def create_block(self) -> POSBlock:
        if not self.pending_transactions:
            raise ValueError("No pending transactions to create block")
        
        validator = self.select_validator()
        block = POSBlock(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash,
            validator=validator
        )
        
        self.chain.append(block)
        self.pending_transactions = []
        self.save_blockchain()
        
        logger.info(f"Block #{block.index} created by validator {validator}")
        return block
    
    def add_transaction_and_mine(self, transaction: Dict) -> Dict:
        tx_id = self.add_transaction(transaction)
        block = self.create_block()
        
        return {
            "tx_id": tx_id,
            "block_hash": block.hash,
            "block_index": block.index,
            "validator": block.validator,
            "status": "confirmed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Block #{i} hash is invalid")
                return False
            
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Block #{i} previous hash is invalid")
                return False
        
        return True
    
    def query_transaction(self, tx_id: str) -> Optional[Dict]:
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
    
    def save_blockchain(self):
        try:
            data = {
                "chain": [block.to_dict() for block in self.chain],
                "pending_transactions": self.pending_transactions,
                "validators": self.validators
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"PoS Blockchain saved to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save PoS blockchain: {e}")
    
    def load_blockchain(self):
        if not self.storage_path.exists():
            logger.info("No existing PoS blockchain found. Creating new blockchain.")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.chain = [POSBlock.from_dict(block_data) for block_data in data.get("chain", [])]
            self.pending_transactions = data.get("pending_transactions", [])
            self.validators = data.get("validators", {})
            
            if not self.is_chain_valid():
                logger.warning("Loaded PoS blockchain is invalid. Creating new chain.")
                self.chain = []
                self.create_genesis_block()
            else:
                logger.info(f"PoS Blockchain loaded: {len(self.chain)} blocks")
        
        except Exception as e:
            logger.error(f"Failed to load PoS blockchain: {e}. Creating new chain.")
            self.chain = []
            self.create_genesis_block()
    
    def get_chain_info(self) -> Dict:
        return {
            "chain_length": len(self.chain),
            "pending_transactions": len(self.pending_transactions),
            "validators_count": len(self.validators),
            "is_valid": self.is_chain_valid(),
            "latest_block_hash": self.get_latest_block().hash if self.chain else None
        }

