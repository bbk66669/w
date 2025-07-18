#!/usr/bin/env python3
import logging
import requests
import json
import os

# TradeLog schema 定义
_SCHEMA = {
  "class": "TradeLog",
  "description": "策略交易与因果日志",
  "properties": [
    {"name": "timestamp",           "dataType": ["number"]},
    {"name": "symbol",              "dataType": ["text"]},
    {"name": "signal",              "dataType": ["text"]},
    {"name": "price",               "dataType": ["number"]},
    {"name": "size",                "dataType": ["number"]},
    {"name": "leverage",            "dataType": ["number"]},
    {"name": "order_id",            "dataType": ["text"]},
    {"name": "status",              "dataType": ["text"]},
    {"name": "prompt",              "dataType": ["text"]},
    {"name": "extra",               "dataType": ["text"]},
    {"name": "pnl_realized",        "dataType": ["number"]},
    {"name": "equity",              "dataType": ["number"]},
    {"name": "trail_sl_pct",        "dataType": ["number"]},
    {"name": "trail_sl_price_init","dataType": ["number"]},
    {"name": "trail_sl_hit",        "dataType": ["text"]}
  ]
}

BASE_URL = os.getenv("WEAVIATE_URL", "http://infra-weaviate-1:8080")

# ---------- 新增：幂等判断 ----------
def class_exists(cls_name: str) -> bool:
    url = f"{BASE_URL}/v1/schema/classes/{cls_name}"
    return requests.get(url, timeout=5).status_code == 200
# ------------------------------------

def get_schema():
    resp = requests.get(f"{BASE_URL}/v1/schema")
    resp.raise_for_status()
    return resp.json()

def create_class():
    if class_exists("TradeLog"):   # 幂等检查
        return
    resp = requests.post(
        f"{BASE_URL}/v1/schema/classes",
        headers={"Content-Type": "application/json"},
        data=json.dumps(_SCHEMA)
    )
    resp.raise_for_status()
    logging.info("Weaviate: created TradeLog class")

def add_property(prop):
    # 如需幂等，可再 GET /schema/TradeLog/properties 检查，这里保持原样
    resp = requests.post(
        f"{BASE_URL}/v1/schema/TradeLog/properties",
        headers={"Content-Type": "application/json"},
        data=json.dumps(prop)
    )
    resp.raise_for_status()
    logging.info(f"Weaviate: added property '{prop['name']}' to TradeLog")

def ensure_schema():
    try:
        schema = get_schema()
        classes = [c["class"] for c in schema.get("classes", [])]
        if "TradeLog" not in classes:
            create_class()
        else:
            existing = {
                p["name"]
                for c in schema["classes"]
                if c["class"] == "TradeLog"
                for p in c.get("properties", [])
            }
            for prop in _SCHEMA["properties"]:
                if prop["name"] not in existing:
                    add_property(prop)
    except Exception as e:
        logging.warning(f"Weaviate schema ensure failed: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_schema()
