import hashlib
import json
import time
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PBFTBlock:
    def __init__(self, index: int, transactions: List[Dict], previous_hash: str, proposer: str, votes: Dict[str, bool], timestamp: Optional[float] = None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.proposer = proposer
        self.votes = votes
        self.timestamp = timestamp or time.time()
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "proposer": self.proposer,
            "timestamp": self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "proposer": self.proposer,
            "votes": self.votes,
            "timestamp": self.timestamp,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PBFTBlock':
        block = cls(
            index=data["index"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            proposer=data["proposer"],
            votes=data.get("votes", {}),
            timestamp=data["timestamp"]
        )
        block.hash = data["hash"]
        return block

class PBFTBlockchain:
    def __init__(self, validators: List[str], storage_path: Optional[str] = None):
        if len(validators) < 4:
            raise ValueError("PBFT requires at least 4 validators for fault tolerance")
        
        self.chain: List[PBFTBlock] = []
        self.pending_transactions: List[Dict] = []
        self.validators: List[str] = validators
        self.current_proposer_index = 0
        self.storage_path = Path(storage_path) if storage_path else Path("pbft_blockchain_data.json")
        
        self.create_genesis_block()
        self.load_blockchain()
    
    def create_genesis_block(self):
        if not self.chain:
            genesis_block = PBFTBlock(
                index=0,
                transactions=[{
                    "type": "genesis",
                    "data": "PBFT Healthcare Blockchain Genesis Block",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }],
                previous_hash="0",
                proposer="system",
                votes={v: True for v in self.validators}
            )
            self.chain.append(genesis_block)
            logger.info("PBFT Genesis block created")
    
    def get_next_proposer(self) -> str:
        proposer = self.validators[self.current_proposer_index]
        self.current_proposer_index = (self.current_proposer_index + 1) % len(self.validators)
        return proposer
    
    def validate_block(self, validator: str, block: PBFTBlock) -> bool:
        if block.previous_hash != self.get_latest_block().hash:
            return False
        
        if block.index != len(self.chain):
            return False
        
        for tx in block.transactions:
            if not self.is_valid_transaction(tx):
                return False
        
        return True
    
    def is_valid_transaction(self, transaction: Dict) -> bool:
        required_fields = ["type", "timestamp"]
        return all(field in transaction for field in required_fields)
    
    def vote_on_block(self, block: PBFTBlock) -> Dict[str, bool]:
        votes = {}
        for validator in self.validators:
            votes[validator] = self.validate_block(validator, block)
        return votes
    
    def has_consensus(self, votes: Dict[str, bool]) -> bool:
        yes_votes = sum(1 for v in votes.values() if v)
        required_votes = (2 * len(self.validators)) // 3 + 1
        return yes_votes >= required_votes
    
    def get_latest_block(self) -> PBFTBlock:
        return self.chain[-1]
    
    def add_transaction(self, transaction: Dict) -> str:
        if "timestamp" not in transaction:
            transaction["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        tx_string = json.dumps(transaction, sort_keys=True)
        tx_id = hashlib.sha256(tx_string.encode()).hexdigest()
        transaction["tx_id"] = tx_id
        
        self.pending_transactions.append(transaction)
        return tx_id
    
    def create_block(self) -> PBFTBlock:
        if not self.pending_transactions:
            raise ValueError("No pending transactions to create block")
        
        proposer = self.get_next_proposer()
        block = PBFTBlock(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            previous_hash=self.get_latest_block().hash,
            proposer=proposer,
            votes={}
        )
        
        votes = self.vote_on_block(block)
        block.votes = votes
        
        if self.has_consensus(votes):
            self.chain.append(block)
            self.pending_transactions = []
            self.save_blockchain()
            logger.info(f"Block #{block.index} created by {proposer} with consensus")
            return block
        else:
            raise ValueError(f"Consensus not reached for block #{block.index}")
    
    def add_transaction_and_mine(self, transaction: Dict) -> Dict:
        tx_id = self.add_transaction(transaction)
        block = self.create_block()
        
        return {
            "tx_id": tx_id,
            "block_hash": block.hash,
            "block_index": block.index,
            "proposer": block.proposer,
            "votes": block.votes,
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
            
            if not self.has_consensus(current_block.votes):
                logger.error(f"Block #{i} does not have consensus")
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
                "validators": self.validators,
                "current_proposer_index": self.current_proposer_index
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"PBFT Blockchain saved to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save PBFT blockchain: {e}")
    
    def load_blockchain(self):
        if not self.storage_path.exists():
            logger.info("No existing PBFT blockchain found. Creating new blockchain.")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.chain = [PBFTBlock.from_dict(block_data) for block_data in data.get("chain", [])]
            self.pending_transactions = data.get("pending_transactions", [])
            self.validators = data.get("validators", self.validators)
            self.current_proposer_index = data.get("current_proposer_index", 0)
            
            if not self.is_chain_valid():
                logger.warning("Loaded PBFT blockchain is invalid. Creating new chain.")
                self.chain = []
                self.create_genesis_block()
            else:
                logger.info(f"PBFT Blockchain loaded: {len(self.chain)} blocks")
        
        except Exception as e:
            logger.error(f"Failed to load PBFT blockchain: {e}. Creating new chain.")
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

