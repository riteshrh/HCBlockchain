
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.db_client import get_db
from app.middleware.auth_middleware import get_current_user, require_role
from app.blockchain.client import blockchain_client

router = APIRouter()

@router.get("/info")
async def get_blockchain_info(
    current_user: dict = Depends(get_current_user)
):
    
    info = blockchain_client.blockchain.get_chain_info()
    return {
        "chain_length": info["chain_length"],
        "pending_transactions": info["pending_transactions"],
        "difficulty": info["difficulty"],
        "is_valid": info["is_valid"],
        "latest_block_hash": info["latest_block_hash"]
    }

@router.get("/blocks")
async def get_all_blocks(
    current_user: dict = Depends(get_current_user),
    limit: Optional[int] = 50
):
    
    blocks = blockchain_client.blockchain.chain[-limit:] if limit else blockchain_client.blockchain.chain
    return {
        "total_blocks": len(blockchain_client.blockchain.chain),
        "blocks": [block.to_dict() for block in reversed(blocks)]  # Most recent first
    }

@router.get("/blocks/{block_index}")
async def get_block_by_index(
    block_index: int,
    current_user: dict = Depends(get_current_user)
):
    
    if block_index < 0 or block_index >= len(blockchain_client.blockchain.chain):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Block {block_index} not found"
        )
    
    block = blockchain_client.blockchain.chain[block_index]
    return block.to_dict()

@router.get("/transactions")
async def get_all_transactions(
    current_user: dict = Depends(get_current_user),
    transaction_type: Optional[str] = None,
    limit: Optional[int] = 100
):
    
    all_transactions = []
    
    # Get transactions from all blocks
    for block in blockchain_client.blockchain.chain:
        for tx in block.transactions:
            if not transaction_type or tx.get("type") == transaction_type:
                all_transactions.append({
                    "tx_id": tx.get("tx_id"),
                    "type": tx.get("type"),
                    "block_index": block.index,
                    "block_hash": block.hash,
                    "timestamp": block.timestamp,
                    "transaction": tx
                })
    
    # Sort by timestamp (most recent first) and limit
    all_transactions.sort(key=lambda x: x["timestamp"], reverse=True)
    return {
        "total_transactions": len(all_transactions),
        "transactions": all_transactions[:limit]
    }

@router.get("/transactions/{tx_id}")
async def get_transaction_by_id(
    tx_id: str,
    current_user: dict = Depends(get_current_user)
):
    
    result = blockchain_client.blockchain.query_transaction(tx_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return result

@router.get("/transactions/type/{transaction_type}")
async def get_transactions_by_type(
    transaction_type: str,
    current_user: dict = Depends(get_current_user)
):
    
    transactions = blockchain_client.blockchain.query_by_type(transaction_type)
    return {
        "transaction_type": transaction_type,
        "count": len(transactions),
        "transactions": transactions
    }

@router.get("/tampering-events")
async def get_tampering_events(
    current_user: dict = Depends(get_current_user),
    limit: Optional[int] = 50
):
    
    tampering_events = blockchain_client.blockchain.query_by_type("tampering_detection")
    
    # Sort by timestamp (most recent first) and limit
    tampering_events.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    return {
        "total_events": len(tampering_events),
        "events": tampering_events[:limit]
    }

@router.get("/validate")
async def validate_blockchain(
    current_user: dict = Depends(require_role(["admin"]))
):
    
    is_valid = blockchain_client.blockchain.is_chain_valid()
    return {
        "is_valid": is_valid,
        "chain_length": len(blockchain_client.blockchain.chain),
        "message": "Blockchain is valid" if is_valid else "Blockchain validation failed"
    }
