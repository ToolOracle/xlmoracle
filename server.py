#!/usr/bin/env python3
"""XLMOracle MCP Server v1.0.0 — Port 11301
Stellar Network Intelligence for AI Agents.
Payment corridor analysis, tokenized asset checks, issuer trust,
anchor compliance, DEX liquidity, stablecoin monitoring, cross-border
payment intelligence. Evidence-grade data for institutional payments
and tokenized finance on Stellar.
"""
import os, sys, json, logging, aiohttp, asyncio
from datetime import datetime, timezone

sys.path.insert(0, "/root/whitelabel")
from shared.utils.mcp_base import WhitelabelMCPServer

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [XLMOracle] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("/root/whitelabel/logs/xlmoracle.log", mode="a")])
logger = logging.getLogger("XLMOracle")

PRODUCT_NAME = "XLMOracle"
VERSION      = "1.0.0"
PORT_MCP     = 11301
PORT_HEALTH  = 11302

HORIZON  = "https://horizon.stellar.org"
LLAMA    = "https://api.llama.fi"
CG       = "https://api.coingecko.com/api/v3"
HEADERS  = {"User-Agent": "XLMOracle-ToolOracle/1.0", "Accept": "application/json"}

def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

async def get(url, params=None, timeout=15):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, headers=HEADERS,
                             timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                if r.status == 200:
                    return await r.json(content_type=None)
                return {"error": f"HTTP {r.status}"}
    except Exception as e:
        return {"error": str(e)}

def risk_grade(score):
    if score >= 80: return "A"
    if score >= 60: return "B"
    if score >= 40: return "C"
    if score >= 20: return "D"
    return "F"

# Known Stellar anchors/issuers for RWA
KNOWN_ANCHORS = {
    "circle":    {"name": "Circle (USDC)", "asset": "USDC", "type": "stablecoin", "regulated": True},
    "ultrastellar": {"name": "Ultra Stellar", "asset": "USDC", "type": "stablecoin", "regulated": True},
    "moneygram": {"name": "MoneyGram", "type": "anchor", "regulated": True},
    "cowrie":    {"name": "Cowrie", "type": "anchor", "regulated": False},
    "anclax":    {"name": "Anclax", "type": "anchor", "regulated": False},
}

async def handle_overview(args):
    """Stellar network overview: XLM price, network stats, ledger info"""
    price_task = get(f"{CG}/simple/price", {
        "ids": "stellar", "vs_currencies": "usd,eur",
        "include_24hr_change": "true", "include_market_cap": "true", "include_24hr_vol": "true"
    })
    ledger_task = get(f"{HORIZON}/ledgers", {"order": "desc", "limit": "1"})
    fee_task = get(f"{HORIZON}/fee_stats")

    price_data, ledger_data, fee_data = await asyncio.gather(price_task, ledger_task, fee_task)

    xlm = price_data.get("stellar", {}) if isinstance(price_data, dict) else {}

    ledgers = ledger_data.get("_embedded", {}).get("records", [{}]) if isinstance(ledger_data, dict) else [{}]
    latest = ledgers[0] if ledgers else {}

    fees = fee_data if isinstance(fee_data, dict) else {}
    last_ledger_base_fee = fees.get("last_ledger_base_fee", "100")

    return {
        "chain": "Stellar",
        "network": "mainnet",
        "timestamp": ts(),
        "price": {
            "usd": xlm.get("usd"),
            "eur": xlm.get("eur"),
            "change_24h": xlm.get("usd_24h_change"),
            "market_cap_usd": xlm.get("usd_market_cap"),
            "volume_24h_usd": xlm.get("usd_24h_vol")
        },
        "network": {
            "latest_ledger": latest.get("sequence"),
            "closed_at": latest.get("closed_at"),
            "transaction_count": latest.get("transaction_count"),
            "operation_count": latest.get("operation_count"),
            "base_fee_stroops": last_ledger_base_fee,
            "base_fee_xlm": round(int(last_ledger_base_fee or 100) / 1e7, 7)
        },
        "source": "CoinGecko + Stellar Horizon"
    }

async def handle_account_intel(args):
    """Stellar account intelligence: balances, trust lines, flags"""
    account_id = args.get("account_id", "").strip()
    if not account_id:
        return {"error": "account_id required (Stellar public key G...)"}

    data = await get(f"{HORIZON}/accounts/{account_id}")
    if isinstance(data, dict) and "error" in data:
        return {"error": f"Account not found: {account_id}"}

    balances = data.get("balances", [])
    xlm_bal = next((b for b in balances if b.get("asset_type") == "native"), {})
    token_bals = [b for b in balances if b.get("asset_type") != "native"]

    flags = data.get("flags", {})
    score = 60
    if flags.get("auth_required"): score += 10
    if flags.get("auth_revocable"): score -= 5
    if len(token_bals) > 20: score -= 10

    return {
        "account_id": account_id,
        "xlm_balance": xlm_bal.get("balance"),
        "xlm_reserve_locked": str(round((2 + len(balances)) * 0.5, 1)),
        "token_trust_lines": len(token_bals),
        "tokens": [{"asset": f"{b.get('asset_code')}/{b.get('asset_issuer', '')[:8]}...",
                    "balance": b.get("balance"), "limit": b.get("limit")}
                   for b in token_bals[:10]],
        "flags": flags,
        "sequence": data.get("sequence"),
        "signers": len(data.get("signers", [])),
        "risk_score": score,
        "risk_grade": risk_grade(score),
        "timestamp": ts(),
        "source": "Stellar Horizon"
    }

async def handle_asset_check(args):
    """Stellar asset (token) analysis: issuer trust, holders, trading volume"""
    code = args.get("asset_code", "USDC").upper()
    issuer = args.get("asset_issuer", "")

    if not issuer:
        KNOWN = {
            "USDC": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
            "AQUA": "GBNZILSTVQZ4R7IKQDGHYGY2QXL5QOFJYQMXPKWRRM5PAV7Y4M67AQUA",
            "yXLM": "GARDNV3Q7YGT4AKSDF25LT32YSCCW4EV22Y2TV3I2PU2MMXJTEDL5T55",
            "SHx":  "BNSH2JQQA5JHXPDL2DYBUYZNWCJKGSCFWZJ5DFBCDOEIIT5AJDX2CZBR",
        }
        issuer = KNOWN.get(code, "")

    if not issuer:
        return {"error": f"No known issuer for {code}. Provide asset_issuer."}

    asset_data, trades = await asyncio.gather(
        get(f"{HORIZON}/assets", {"asset_code": code, "asset_issuer": issuer}),
        get(f"{HORIZON}/trade_aggregations",
            {"base_asset_type": "credit_alphanum4", "base_asset_code": code,
             "base_asset_issuer": issuer, "counter_asset_type": "native",
             "resolution": "86400000", "limit": "7", "order": "desc"})
    )

    records = asset_data.get("_embedded", {}).get("records", [{}]) if isinstance(asset_data, dict) else [{}]
    asset = records[0] if records else {}

    trade_records = trades.get("_embedded", {}).get("records", []) if isinstance(trades, dict) else []
    avg_vol = sum(float(t.get("base_volume", 0)) for t in trade_records) / max(len(trade_records), 1)

    score = 50
    accounts = int(asset.get("accounts", {}).get("authorized", 0))
    if accounts > 10000: score += 20
    elif accounts > 1000: score += 10
    if asset.get("flags", {}).get("auth_required"): score += 10

    return {
        "asset_code": code,
        "asset_issuer": issuer,
        "issuer_short": issuer[:12] + "...",
        "authorized_accounts": accounts,
        "claimable_balances": asset.get("claimable_balances_amount"),
        "liquidity_pools": asset.get("liquidity_pools_amount"),
        "supply": asset.get("amount"),
        "flags": asset.get("flags", {}),
        "avg_daily_volume_7d": round(avg_vol, 2),
        "trade_days_data": len(trade_records),
        "risk_score": score,
        "risk_grade": risk_grade(score),
        "timestamp": ts(),
        "source": "Stellar Horizon"
    }

async def handle_payment_corridor(args):
    """Cross-border payment corridor intelligence on Stellar"""
    from_asset = args.get("from_asset", "USD").upper()
    to_asset   = args.get("to_asset", "EUR").upper()
    amount     = args.get("amount", 1000)

    # Stellar Path Payment finding
    ASSET_ISSUERS = {
        "USDC": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN",
        "EURC": "GDHU6WRG4IEQXM5NZ4BMPKOXHW76MZM4Y2IEMFDVXBSDP6SJY4ITNPP",
        "XLM":  None,
    }

    src_issuer = ASSET_ISSUERS.get(from_asset)
    dst_issuer = ASSET_ISSUERS.get(to_asset)

    paths = await get(f"{HORIZON}/paths/strict-send", {
        "source_asset_type": "native" if from_asset == "XLM" else "credit_alphanum4",
        "source_asset_code": from_asset if from_asset != "XLM" else "",
        "source_asset_issuer": src_issuer or "",
        "source_amount": str(amount),
        "destination_asset_type": "native" if to_asset == "XLM" else "credit_alphanum4",
        "destination_asset_code": to_asset if to_asset != "XLM" else "",
        "destination_asset_issuer": dst_issuer or "",
    })

    records = paths.get("_embedded", {}).get("records", []) if isinstance(paths, dict) else []
    routes = []
    for r in records[:5]:
        routes.append({
            "destination_amount": r.get("destination_amount"),
            "path_length": len(r.get("path", [])),
            "path": [p.get("asset_code", "XLM") for p in r.get("path", [])]
        })

    return {
        "corridor": f"{from_asset} → {to_asset}",
        "send_amount": amount,
        "routes_found": len(routes),
        "best_routes": routes,
        "settlement": "Stellar (3-5 seconds)",
        "fee_xlm": "0.00001 per operation",
        "timestamp": ts(),
        "note": "Stellar enables atomic cross-border settlement via path payments",
        "source": "Stellar Horizon Path API"
    }

async def handle_anchor_check(args):
    """Stellar anchor intelligence: SEP compliance, fiat on/off ramps"""
    anchor = args.get("anchor", "").lower()
    if anchor in KNOWN_ANCHORS:
        info = KNOWN_ANCHORS[anchor]
        return {
            "anchor": anchor,
            "name": info["name"],
            "asset": info.get("asset"),
            "type": info["type"],
            "regulated": info["regulated"],
            "sep_standards": ["SEP-24", "SEP-31", "SEP-12"] if info["regulated"] else ["SEP-24"],
            "risk_score": 80 if info["regulated"] else 40,
            "risk_grade": risk_grade(80 if info["regulated"] else 40),
            "timestamp": ts(),
            "note": "Stellar Anchor provides fiat on/off ramp via SEP protocols"
        }

    return {
        "known_anchors": list(KNOWN_ANCHORS.keys()),
        "message": "Provide an anchor name or query known anchors",
        "sep_standards": {
            "SEP-24": "Interactive deposit/withdrawal",
            "SEP-31": "Direct payment (institutional)",
            "SEP-12": "KYC/AML compliance",
            "SEP-38": "Quotes and conversion"
        },
        "timestamp": ts()
    }

async def handle_dex_liquidity(args):
    """Stellar DEX liquidity pools and order book intelligence"""
    pools = await get(f"{HORIZON}/liquidity_pools",
                      {"order": "desc", "limit": "20", "reserves": ""})

    records = pools.get("_embedded", {}).get("records", []) if isinstance(pools, dict) else []
    result = []
    for p in records:
        reserves = p.get("reserves", [])
        if len(reserves) == 2:
            result.append({
                "pool_id": p.get("id", "")[:16] + "...",
                "asset_a": reserves[0].get("asset"),
                "asset_b": reserves[1].get("asset"),
                "amount_a": reserves[0].get("amount"),
                "amount_b": reserves[1].get("amount"),
                "total_shares": p.get("total_shares"),
                "total_trustlines": p.get("total_trustlines"),
                "fee_bp": p.get("fee_bp")
            })

    return {
        "top_liquidity_pools": result,
        "count": len(result),
        "timestamp": ts(),
        "note": "Stellar AMM pools with constant-product formula",
        "source": "Stellar Horizon"
    }

async def handle_rwa_assets(args):
    """Real-world asset tokenization on Stellar: tokenized bonds, funds, commodities"""
    # Known RWA issuers/projects on Stellar
    RWA_STELLAR = [
        {"name": "Franklin Templeton BENJI", "asset": "BENJI", "type": "money_market_fund",
         "issuer": "GBZH3S5JQTSO3OOPKQGFMFEZ4N5PQFANFQNQHFKFTSW4FQQERMXHZXQ",
         "regulated": True, "jurisdiction": "US"},
        {"name": "WisdomTree Prime", "asset": "WTGOLD", "type": "tokenized_commodity",
         "regulated": True, "jurisdiction": "US"},
        {"name": "Arca US Treasury", "asset": "ArCoin", "type": "tokenized_treasury",
         "regulated": True, "jurisdiction": "US"},
        {"name": "Bitbond Token Platform", "type": "tokenized_bonds",
         "regulated": True, "jurisdiction": "DE"},
    ]

    category = args.get("category", "").lower()
    filtered = [r for r in RWA_STELLAR
                if not category or category in r.get("type", "").lower()]

    return {
        "rwa_on_stellar": filtered,
        "total": len(filtered),
        "categories": ["money_market_fund", "tokenized_bonds", "tokenized_commodity", "tokenized_treasury"],
        "stellar_advantages": [
            "5-second settlement finality",
            "Native DEX for tokenized assets",
            "Built-in compliance via auth_required flag",
            "Clawback capability for regulated assets",
            "SEP-31 for institutional direct payments"
        ],
        "timestamp": ts(),
        "source": "ToolOracle RWA Registry"
    }



def build_server():
    server = WhitelabelMCPServer(
        product_name=PRODUCT_NAME,
        product_slug="xlmoracle",
        version=VERSION,
        port_mcp=PORT_MCP,
        port_health=PORT_HEALTH,
    )
    server.register_tool("xlm_overview",
        "Stellar network overview: XLM price, ledger stats, transaction throughput, fees",
        {"type": "object", "properties": {}, "required": []}, handle_overview)
    server.register_tool("xlm_account_intel",
        "Stellar account intelligence: XLM balance, token trust lines, account flags",
        {"type": "object", "properties": {"account_id": {"type": "string", "description": "Stellar public key (G...)"}}, "required": ["account_id"]}, handle_account_intel)
    server.register_tool("xlm_asset_check",
        "Stellar asset analysis: issuer trust, authorized accounts, trading volume",
        {"type": "object", "properties": {"asset_code": {"type": "string"}, "asset_issuer": {"type": "string"}}, "required": []}, handle_asset_check)
    server.register_tool("xlm_payment_corridor",
        "Cross-border payment corridor analysis on Stellar: routing, settlement speed, path payments",
        {"type": "object", "properties": {"from_asset": {"type": "string", "default": "USDC"}, "to_asset": {"type": "string", "default": "EURC"}, "amount": {"type": "number", "default": 1000}}, "required": []}, handle_payment_corridor)
    server.register_tool("xlm_anchor_check",
        "Stellar anchor intelligence: SEP compliance, fiat on/off ramps, KYC/AML",
        {"type": "object", "properties": {"anchor": {"type": "string"}}, "required": []}, handle_anchor_check)
    server.register_tool("xlm_dex_liquidity",
        "Stellar DEX liquidity pools: top AMM pools, reserves, trading pairs",
        {"type": "object", "properties": {}, "required": []}, handle_dex_liquidity)
    server.register_tool("xlm_rwa_assets",
        "Real-world asset tokenization on Stellar: tokenized bonds, funds, treasuries, commodities",
        {"type": "object", "properties": {"category": {"type": "string"}}, "required": []}, handle_rwa_assets)
    return server

if __name__ == "__main__":
    srv = build_server()
    srv.run()
