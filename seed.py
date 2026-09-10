"""
Seed script for LLM Cost Optimization Gateway.
Populates SQLite database with sample API keys, request logs across 30 days,
budgets, and semantic cache items.
"""
from __future__ import annotations
import asyncio
import random
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func

from models.database import init_db, AsyncSessionLocal
from models.tables import APIKey, RequestLog, Budget, CacheEntry
from models.config import settings
from gateway.middleware.auth import _hash_key
from gateway.cache import get_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

SAMPLE_PROMPTS = [
    "What is quantum computing and how does it work?",
    "Explain the difference between REST APIs and GraphQL.",
    "Write a Python function to sort a binary tree.",
    "Summarize the key principles of machine learning.",
    "How do I optimize SQL queries for large datasets?",
    "Explain microservices architecture pros and cons.",
    "Draft an email requesting project deadline extension.",
    "What are vector embeddings and vector databases?",
    "Compare React vs Vue.js for web development.",
    "How does transformer architecture power modern LLMs?",
]

PROVIDERS_MODELS = [
    ("openai", "gpt-4o-mini", 0.00015, 0.0006),
    ("openai", "gpt-4o", 0.0025, 0.010),
    ("anthropic", "claude-3-5-haiku-20241022", 0.001, 0.005),
    ("anthropic", "claude-3-5-sonnet-20241022", 0.003, 0.015),
    ("gemini", "gemini-1.5-flash", 0.000075, 0.0003),
    ("gemini", "gemini-1.5-pro", 0.00125, 0.005),
    ("mock", "mock-fast", 0.0001, 0.0002),
]


async def seed_database(auto_only_if_empty: bool = False):
    """Seed sample data if DB is empty or explicitly requested."""
    await init_db()

    async with AsyncSessionLocal() as db:
        # Check if logs already exist
        res = await db.execute(select(func.count(RequestLog.id)))
        count = res.scalar() or 0
        if auto_only_if_empty and count > 0:
            logger.info(f"DB already has {count} request logs. Skipping auto-seed.")
            return

        logger.info("🌱 Seeding database with sample analytics and keys...")

        # 1. Create API Keys
        sample_keys = [
            ("llmg-dev-demo-key-12345", "Dev Demo Key", "Engineering", 25.0, 100),
            ("llmg-prod-app-key-67890", "Production Mobile App", "Mobile Team", 100.0, 500),
            ("llmg-analytics-key-99999", "BI & Analytics", "Data Science", 50.0, 200),
        ]

        key_objs: list[APIKey] = []
        for raw_key, name, owner, budget_usd, rpm in sample_keys:
            khash = _hash_key(raw_key)
            existing = await db.execute(select(APIKey).where(APIKey.key_hash == khash))
            kobj = existing.scalar_one_or_none()
            if not kobj:
                kobj = APIKey(
                    key_hash=khash,
                    name=name,
                    owner=owner,
                    monthly_budget_usd=budget_usd,
                    rpm_limit=rpm,
                    is_active=True,
                )
                db.add(kobj)
                await db.flush()

                # Budget
                b = Budget(
                    api_key_id=kobj.id,
                    period="monthly",
                    limit_usd=budget_usd,
                    spent_usd=0.0,
                    reset_at=datetime.now(timezone.utc) + timedelta(days=30),
                )
                db.add(b)
            key_objs.append(kobj)

        await db.commit()

        # 2. Create 30 days of Request Logs
        now = datetime.now(timezone.utc)
        total_seeded_cost = 0.0

        for day_offset in range(30, -1, -1):
            day_time = now - timedelta(days=day_offset)
            # 5 to 15 requests per day
            daily_req_count = random.randint(6, 14)

            for _ in range(daily_req_count):
                provider, model, prompt_rate, comp_rate = random.choice(PROVIDERS_MODELS)
                prompt_tok = random.randint(80, 1200)
                comp_tok = random.randint(150, 800)
                tot_tok = prompt_tok + comp_tok

                raw_cost = (prompt_tok / 1000.0) * prompt_rate + (comp_tok / 1000.0) * comp_rate
                raw_cost = round(raw_cost, 6)

                # ~25% cache hit chance
                is_cached = random.random() < 0.25
                cost_usd = 0.0 if is_cached else raw_cost
                savings_usd = raw_cost if is_cached else 0.0
                latency = random.randint(15, 60) if is_cached else random.randint(120, 650)

                api_key_obj = random.choice(key_objs)
                req_timestamp = day_time + timedelta(minutes=random.randint(0, 1430))

                log = RequestLog(
                    api_key_id=api_key_obj.id,
                    provider=provider,
                    model=model,
                    prompt_tokens=0 if is_cached else prompt_tok,
                    completion_tokens=0 if is_cached else comp_tok,
                    total_tokens=0 if is_cached else tot_tok,
                    cost_usd=cost_usd,
                    cached=is_cached,
                    savings_usd=savings_usd,
                    latency_ms=latency,
                    status="success",
                    created_at=req_timestamp,
                )
                db.add(log)
                total_seeded_cost += cost_usd

        await db.commit()

        # 3. Pre-populate Semantic Cache
        cache = get_cache()
        for p in SAMPLE_PROMPTS[:5]:
            cache.set(
                prompt=p,
                response=f"This is a pre-cached response for: '{p}'",
                model="gpt-4o-mini",
                provider="openai",
                cost_usd=0.0005,
            )

        logger.info(f"✅ Seeding complete! Populated 30 days of data and sample API keys.")
        logger.info("🔑 Sample API Key for testing: llmg-dev-demo-key-12345")


if __name__ == "__main__":
    asyncio.run(seed_database(auto_only_if_empty=False))
