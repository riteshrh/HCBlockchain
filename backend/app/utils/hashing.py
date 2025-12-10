
import hashlib
from typing import Union

def generate_hash(data: Union[str, bytes]) -> str:
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hash_object = hashlib.sha256(data)
    return hash_object.hexdigest()

def verify_hash(data: Union[str, bytes], hash_value: str) -> bool:
    computed_hash = generate_hash(data)
    return computed_hash == hash_value.lower()
