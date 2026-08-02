"""
Social OSINT — мощный инструмент для поиска людей в соцсетях.

Работает в OSINT-режиме (osint_mode = true).
Поддерживает: VK, Telegram, Instagram, Facebook, X/Twitter, LinkedIn, TikTok и др.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from actions.web_search import web_search as _web_search

BASE_DIR = Path(__file__).resolve().parent.parent
API_FILE = BASE_DIR / "config" / "api_keys.json"


def _load_config() -> dict:
    try:
        return json.loads(API_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _is_osint_mode() -> bool:
    return bool(_load_config().get("osint_mode", False))


def social_osint(parameters: dict, player=None, speak=None) -> str:
    """
    parameters:
        action     : search | deep | connections | recent (default: search)
        query      : имя, username, телефон, email
        platforms  : список платформ (vk, tg, instagram, facebook, x, linkedin, tiktok)
        limit      : сколько результатов (default: 10)
        deep       : делать ли глубокий поиск (true/false)
    """
    if not _is_osint_mode():
        return "OSINT Mode выключен. Включи 🕵️ OSINT MODE в настройках для использования этого инструмента."

    p = parameters or {}
    action = p.get("action", "search").lower()
    query = (p.get("query") or p.get("name") or "").strip()
    platforms = p.get("platforms", ["vk", "instagram", "telegram", "facebook", "x"])
    limit = int(p.get("limit", 10))
    deep = bool(p.get("deep", False))

    if not query:
        return "Укажи query (имя, username, телефон или email)."

    results = []

    if action == "search":
        results = _basic_search(query, platforms, limit)
    elif action == "deep":
        results = _deep_search(query, platforms, limit)
    elif action == "connections":
        results = _find_connections(query, platforms)
    elif action == "recent":
        results = _recent_activity(query, platforms, limit)
    else:
        return f"Неизвестное действие: {action}. Используй search, deep, connections, recent."

    if not results:
        return f"Ничего не найдено по запросу «{query}»."

    # Форматируем красивый вывод
    output = f"🕵️ OSINT — {query}\n"
    output += "=" * 50 + "\n"

    for i, r in enumerate(results[:limit], 1):
        output += f"\n{i}. {r.get('platform', 'Unknown').upper()}\n"
        output += f"   {r.get('title', '')}\n"
        if r.get("url"):
            output += f"   🔗 {r['url']}\n"
        if r.get("snippet"):
            output += f"   {r['snippet'][:180]}...\n"

    if player:
        player.show_content(f"OSINT — {query}", output)

    return output


def _basic_search(query: str, platforms: List[str], limit: int) -> List[Dict]:
    """Быстрый поиск по соцсетям через web_search."""
    results = []

    platform_queries = {
        "vk": f"site:vk.com {query}",
        "instagram": f"site:instagram.com {query}",
        "telegram": f"site:t.me {query} OR telegram {query}",
        "facebook": f"site:facebook.com {query}",
        "x": f"site:x.com {query} OR site:twitter.com {query}",
        "linkedin": f"site:linkedin.com {query}",
        "tiktok": f"site:tiktok.com {query}",
    }

    for platform in platforms:
        q = platform_queries.get(platform, f"{query} {platform}")
        try:
            res = _web_search({"query": q, "mode": "search"}, player=None)
            if res and not res.startswith("No results"):
                results.append({
                    "platform": platform,
                    "title": f"Результаты по {platform}",
                    "snippet": res[:300],
                    "url": ""
                })
        except Exception:
            continue

    return results


def _deep_search(query: str, platforms: List[str], limit: int) -> List[Dict]:
    """Глубокий OSINT-поиск (имя + город + возраст + фото и т.д.)."""
    enhanced_query = f'"{query}" (профиль OR аккаунт OR vk OR instagram OR telegram)'

    try:
        res = _web_search({
            "query": enhanced_query,
            "mode": "research"
        }, player=None)
        return [{
            "platform": "web",
            "title": f"Глубокий поиск: {query}",
            "snippet": res[:500] if res else "Результаты не найдены",
            "url": ""
        }]
    except Exception:
        return []


def _find_connections(query: str, platforms: List[str]) -> List[Dict]:
    """Поиск связей (друзья, подписчики, упоминания)."""
    conn_query = f'"{query}" (друг OR подписчик OR упоминание OR связан)'

    try:
        res = _web_search({"query": conn_query, "mode": "search"}, player=None)
        return [{
            "platform": "connections",
            "title": f"Связи: {query}",
            "snippet": res[:400] if res else "",
            "url": ""
        }]
    except Exception:
        return []


def _recent_activity(query: str, platforms: List[str], limit: int) -> List[Dict]:
    """Последняя активность."""
    recent_q = f'"{query}" after:2024 (пост OR фото OR видео)'

    try:
        res = _web_search({"query": recent_q, "mode": "news"}, player=None)
        return [{
            "platform": "recent",
            "title": f"Недавняя активность: {query}",
            "snippet": res[:400] if res else "",
            "url": ""
        }]
    except Exception:
        return []