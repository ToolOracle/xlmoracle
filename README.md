# ✦ xlmOracle

**Stellar Network Intelligence MCP Server** — 7 tools | Part of [ToolOracle](https://tooloracle.io)

![Tools](https://img.shields.io/badge/MCP_Tools-7-10B898?style=flat-square)
![Status](https://img.shields.io/badge/Status-Live-00C853?style=flat-square)
![Chain](https://img.shields.io/badge/Chain-Stellar-3E1BDB?style=flat-square)
![Tier](https://img.shields.io/badge/Tier-Free-2196F3?style=flat-square)

Payment corridor analysis, tokenized asset checks, issuer trust, anchor SEP compliance, DEX liquidity, stablecoin monitoring, RWA on Stellar. Evidence-grade data for institutional cross-border payments and tokenized finance.

## Quick Connect

```bash
npx -y mcp-remote https://feedoracle.io/mcp/xlmoracle/
```

```json
{
  "mcpServers": {
    "xlmoracle": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://feedoracle.io/mcp/xlmoracle/"]
    }
  }
}
```

## Tools (7)

| Tool | Description |
|------|-------------|
| `xlm_overview` | Stellar network overview: XLM price, ledger stats, throughput, fees |
| `xlm_account_intel` | Account intelligence: XLM balance, trust lines, authorized accounts, flags |
| `xlm_asset_check` | Asset analysis: issuer trust, 2M+ authorized accounts, trading volume |
| `xlm_payment_corridor` | Cross-border payment corridor: path payments, routing, settlement speed |
| `xlm_anchor_check` | Anchor intelligence: SEP-24/31/38 compliance, KYC/AML, fiat on/off ramps |
| `xlm_dex_liquidity` | Stellar AMM pool intelligence: reserves, trading pairs, liquidity |
| `xlm_rwa_assets` | RWA on Stellar: Franklin Templeton BENJI, tokenized bonds, treasuries |

## Use Cases

- **Payment intelligence**: Cross-border corridor analysis, ODL routing, settlement
- **Anchor compliance**: SEP protocol verification for regulated fiat gateways
- **Asset risk**: Issuer trust scoring, authorized account concentration
- **RWA monitoring**: Tokenized money market funds and bonds on Stellar

## Part of FeedOracle / ToolOracle

**Blockchain Oracle Suite:**
- [ethOracle](https://github.com/tooloracle/ethoracle) — Ethereum
- [xlmOracle](https://github.com/tooloracle/xlmoracle) — Stellar (this repo)
- [xrplOracle](https://github.com/tooloracle/xrploracle) — XRP Ledger
- [bnbOracle](https://github.com/tooloracle/bnboracle) — BNB Chain
- [aptOracle](https://github.com/tooloracle/aptoracle) — Aptos
- [baseOracle](https://github.com/tooloracle/baseoracle) — Base L2

## Links

- 🌐 Live: `https://feedoracle.io/mcp/xlmoracle/`
- 🏠 Platform: [feedoracle.io](https://feedoracle.io)

---
*Built by [FeedOracle](https://feedoracle.io) — Evidence by Design*
