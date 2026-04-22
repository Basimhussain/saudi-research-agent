# Saudi Business Research Agent

![Demo Screenshot](demo.png)

A simple script that hits a few APIs (Tavily, Yahoo Finance, OpenAI/Claude) to answer questions about Saudi companies and markets. Built to help with quick business research in both English and Arabic.

---

## What it does

- **Web Search**: Uses Tavily to pull recent news and info.
- **Finance Calc**: Unified tool for VAT (ZATCA 15%), Tadawul quotes (`yfinance`), and SAMA policy rates.
- **CR Lookup**: Ministry of Commerce Commercial Registration records (10-digit CR) — Arabic/English legal name, status, capital, ISIC codes.
- **Vision 2030 Alignment**: Scores a business activity against the 3 Vision 2030 pillars and 8 flagship programs (NEOM, Red Sea, Qiddiya, ROSHN, Saudi Green Initiative, FSDP, NIDLP, HCDP).

Conversation memory persists to **SQLite** for local dev or **PostgreSQL** for deployment — configurable via `DB_TYPE`.

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup your keys
cp .env.example .env
# Edit .env and drop in your OPENAI_API_KEY and TAVILY_API_KEY

# 3. Run it
python main.py                                      # starts chat
python main.py "What is Aramco's current P/E?"      # single question
python main.py "ما هو سعر سهم سابك اليوم؟"           # supports Arabic!
```

### Getting API keys

- **OpenAI**: https://platform.openai.com/ (Or Anthropic if you prefer)
- **Tavily**: https://tavily.com (gives you 1,000 free searches a month)

---

## Example Queries

**1. Stock info and news**
```bash
python main.py "What is Aramco's current P/E and latest earnings news?"
```
*Output snippet:*
```json
{
  "summary": "Saudi Aramco's current P/E ratio is 18.93, with a market cap of approximately 6.59 trillion SAR. Recent earnings news highlights their robust quarterly dividends despite fluctuations in oil prices...",
  "caveats": ["Stock data may be delayed by 15 mins", "Earnings news based on recent web search"]
}
```

**2. Arabic questions**
```bash
python main.py "قارن بين أرامكو وسابك من حيث القيمة السوقية"
```
*Output snippet:*
```json
{
  "summary": "القيمة السوقية لشركة أرامكو السعودية تبلغ حوالي 6.59 تريليون ريال سعودي، بينما تبلغ القيمة السوقية لشركة سابك حوالي 240 مليار ريال سعودي...",
  "caveats": ["تعتمد البيانات على أحدث إغلاق للسوق"]
}
```

**3. VAT Calc**
```bash
python main.py "If I sell a service for 10,000 SAR, what's the VAT-inclusive price?"
```
*Output snippet:*
```json
{
  "summary": "For a net amount of 10,000 SAR, the 15% VAT is 1,500 SAR. The total VAT-inclusive price is 11,500 SAR.",
  "caveats": []
}
```

---

## How it works under the hood

The `main.py` file starts a basic shell. It talks to the LLM, giving it tools like `tadawul_lookup` and `web_search`. The LLM runs whatever tools it needs, gathers the data, and returns a JSON report at the end. History is saved to `agent_memory.db`.

To add a new tool, just make a new python file in `tools/` and register it in `main.py`.

### Tests

```bash
python -m pytest tests/ -q
```
Runs basic checks against the tools.

---

## Deploying with Postgres

The memory layer supports two backends. SQLite is the default for local dev. For anything shared or long-lived, set `DB_TYPE=postgres`.

### Docker Compose

```bash
cp .env.example .env
docker compose up -d postgres
docker compose run --rm agent --healthcheck
docker compose run --rm agent "Check CR 1010000001 and its Vision 2030 alignment"
```

The `postgres:16-alpine` container uses a named volume (`saudi-agent-pgdata`) and the init script at `deploy/postgres/init.sql` (which just enables `pgcrypto` + `pg_stat_statements`). The agent service waits on `pg_isready`.

### Managed Postgres (RDS / Cloud SQL / Neon / ...)

```bash
export DB_TYPE=postgres
export DATABASE_URL=postgresql://user:pass@host:5432/saudi_agent
export DB_SSLMODE=require
export DB_POOL_MIN=2 DB_POOL_MAX=20
python main.py --migrate
python main.py --healthcheck
python main.py "Check CR 1010000001"
```

### Env vars

| Var | Default | Notes |
| --- | --- | --- |
| `DATABASE_URL` | required | libpq DSN |
| `DB_POOL_MIN` / `DB_POOL_MAX` | 1 / 10 | pool sizing |
| `DB_CONNECT_TIMEOUT` | 5 | seconds |
| `DB_STATEMENT_TIMEOUT_MS` | 30000 | server-side statement timeout |
| `DB_RETRY_ATTEMPTS` | 5 | retries on OperationalError/InterfaceError |
| `DB_RETRY_BASE_DELAY` | 0.5 | first retry delay, doubles each attempt |
| `DB_SSLMODE` | prefer | disable / prefer / require / verify-ca / verify-full |
| `DB_APPLICATION_NAME` | saudi-research-agent | shows up in `pg_stat_activity` |

### Migrations

`memory/migrations.py` keeps the schema versioned in a `schema_version` table. On startup anything unapplied runs in a single transaction.

- v1 — `conversations` + `messages` with `TIMESTAMPTZ`, `JSONB`, FK cascade.
- v2 — composite index on `(conversation_id, created_at)` + GIN index on `content_json`.

### Health

`python main.py --healthcheck` prints JSON with `ok`, latency, server version, schema version, and pool sizing. Exit code 0/1. The Dockerfile's `HEALTHCHECK` calls the same path.

---

## Known issues

- Tadawul quotes have a ~15-minute delay via yfinance.
- `cr_lookup` runs off a small fixture set. Swap it for the real MoC API once you have accredited credentials.

---

## License

MIT. Feel free to use.
