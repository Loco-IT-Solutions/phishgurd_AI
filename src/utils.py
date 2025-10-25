# src/utils.py
import json
from typing import Dict

def json_response(obj: Dict, status:int=200):
    return json.dumps(obj), status, {"Content-Type":"application/json"}
