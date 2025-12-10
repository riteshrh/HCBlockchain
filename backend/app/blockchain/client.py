
from typing import Dict, Optional, List
from app.config import settings
import httpx
import logging
from pathlib import Path

from app.blockchain.simple_blockchain import get_blockchain

logger = logging.getLogger(__name__)

# Try to import BigchainDB driver (optional)
try:
    from bigchaindb_driver import BigchainDB
    from bigchaindb_driver.crypto import generate_keypair
    BIGCHAINDB_AVAILABLE = True
except ImportError:
    BIGCHAINDB_AVAILABLE = False
    logger.info("BigchainDB driver not available. Using SimpleBlockchain.")

class BlockchainClient:
    def __init__(self):
        self.provider = settings.blockchain_provider
        self.node_url = settings.blockchain_node
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Initialize SimpleBlockchain (primary)
        # Store blockchain data in backend directory
        backend_dir = Path(__file__).resolve().parent.parent.parent
        blockchain_storage = backend_dir / "blockchain_data.json"
        self.blockchain = get_blockchain(storage_path=str(blockchain_storage))
        logger.info(f"SimpleBlockchain initialized (storage: {blockchain_storage})")
        
        # Initialize BigchainDB connection if available and requested
        self.bdb = None
        if self.provider == "bigchaindb" and BIGCHAINDB_AVAILABLE:
            try:
                self.bdb = BigchainDB(self.node_url)
                logger.info(f"BigchainDB also available at {self.node_url}")
            except Exception as e:
                logger.warning(f"BigchainDB connection failed: {e}. Using SimpleBlockchain only.")
    
    async def store_record_hash(
        self,
        record_id: str,
        record_hash: str,
        patient_id: str,
        public_key: str
    ) -> Dict:
        
        asset = {
            "data": {
                "type": "medical_record_hash",
                "record_id": record_id,
                "patient_id": patient_id,
                "hash": record_hash,
                "timestamp": None  # Will be set by BigchainDB
            }
        }
        
        metadata = {
            "operation": "CREATE",
            "record_type": "medical_record"
        }
        
        return await self.create_transaction(
            asset=asset,
            metadata=metadata,
            public_keys=[public_key]
        )
    
    async def store_consent_transaction(
        self,
        consent_id: str,
        patient_id: str,
        provider_id: str,
        record_id: str,
        consent_type: str,
        status: str,
        patient_public_key: str,
        provider_public_key: Optional[str] = None
    ) -> Dict:
        
        asset = {
            "data": {
                "type": "consent",
                "consent_id": consent_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "record_id": record_id,
                "consent_type": consent_type,
                "status": status
            }
        }
        
        metadata = {
            "operation": "CREATE" if status == "granted" else "TRANSFER",
            "consent_action": status
        }
        
        public_keys = [patient_public_key]
        if provider_public_key:
            public_keys.append(provider_public_key)
        
        return await self.create_transaction(
            asset=asset,
            metadata=metadata,
            public_keys=public_keys
        )
    
    async def _create_simple_blockchain_transaction(
        self,
        asset: Dict,
        metadata: Dict,
        public_keys: List[str]
    ) -> Dict:
        
        transaction = {
            "type": asset.get("data", {}).get("type", "transaction"),
            "asset": asset,
            "metadata": metadata,
            "public_keys": public_keys
        }
        
        # Add transaction to blockchain and mine immediately
        result = self.blockchain.add_transaction_and_mine(transaction)
        
        logger.info(f"Transaction stored on blockchain: {result['tx_id']}")
        return result
    
    async def create_transaction(
        self,
        asset: Dict,
        metadata: Dict,
        public_keys: List[str]
    ) -> Dict:
        
        # Always use SimpleBlockchain (primary implementation)
        return await self._create_simple_blockchain_transaction(asset, metadata, public_keys)
    
    async def _create_bigchaindb_transaction(
        self,
        asset: Dict,
        metadata: Dict,
        public_keys: List[str]
    ) -> Dict:
        
        # Use SimpleBlockchain instead (primary implementation)
        # BigchainDB is kept as optional for future use
        return await self._create_simple_blockchain_transaction(asset, metadata, public_keys)
    
    async def _create_multichain_transaction(
        self,
        asset: Dict,
        metadata: Dict,
        public_keys: List[str]
    ) -> Dict:
        
        # TODO: Implement Multichain transaction creation
        return {
            "tx_id": f"mock_tx_{hash(str(asset) + str(metadata))}",
            "status": "pending",
            "mock": True
        }
    
    async def query_transaction(self, tx_id: str) -> Optional[Dict]:
        # Query SimpleBlockchain
        result = self.blockchain.query_transaction(tx_id)
        if result:
            return result
        
        # Fallback to BigchainDB if available
        if BIGCHAINDB_AVAILABLE and self.bdb:
            try:
                if not tx_id.startswith("mock_tx_"):
                    transaction = self.bdb.transactions.retrieve(tx_id)
                    return transaction
            except Exception as e:
                logger.debug(f"BigchainDB query failed: {e}")
        
        return None
    
    async def query_consent(
        self,
        provider_id: str,
        record_id: str
    ) -> Optional[Dict]:
        
        # Query SimpleBlockchain for consent transactions
        consent_transactions = self.blockchain.query_by_type("consent")
        
        # Find matching consent
        for tx_data in consent_transactions:
            tx = tx_data.get("transaction", {})
            asset_data = tx.get("asset", {}).get("data", {})
            
            if (asset_data.get("provider_id") == provider_id and 
                asset_data.get("record_id") == record_id and
                asset_data.get("status") == "granted"):
                return {
                    "consent_id": asset_data.get("consent_id"),
                    "status": asset_data.get("status"),
                    "tx_id": tx_data.get("tx_id"),
                    "block_index": tx_data.get("block_index"),
                    "timestamp": tx_data.get("timestamp")
                }
        
        return None
    
    async def store_tampering_event(
        self,
        record_id: str,
        patient_id: str,
        tampering_type: str,
        original_hash: Optional[str] = None,
        tampered_hash: Optional[str] = None,
        original_tx_id: Optional[str] = None,
        tampered_tx_id: Optional[str] = None,
        detected_by: Optional[str] = None
    ) -> Dict:
        
        asset = {
            "data": {
                "type": "tampering_detection",
                "record_id": record_id,
                "patient_id": patient_id,
                "tampering_type": tampering_type,
                "original_hash": original_hash,
                "tampered_hash": tampered_hash,
                "original_tx_id": original_tx_id,
                "tampered_tx_id": tampered_tx_id,
                "detected_by": detected_by,
                "severity": "high",
                "timestamp": None  # Will be set by blockchain
            }
        }
        
        metadata = {
            "operation": "CREATE",
            "event_type": "security_alert",
            "description": f"Tampering detected: {tampering_type}"
        }
        
        # Use patient's public key if available, otherwise use system key
        try:
            from app.database.db_client import AsyncSessionLocal
            from sqlalchemy import select
            from app.database.models import User
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(User).where(User.user_id == patient_id)
                )
                patient = result.scalar_one_or_none()
                public_key = patient.public_key if patient and patient.public_key else "system"
        except Exception:
            public_key = "system"
        
        return await self.create_transaction(
            asset=asset,
            metadata=metadata,
            public_keys=[public_key]
        )
    
    async def close(self):
        await self.client.aclose()

# Global blockchain client instance
blockchain_client = BlockchainClient()
