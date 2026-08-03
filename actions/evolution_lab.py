# actions/evolution_lab.py — Evolution Laboratory for EDIT
# Демо-модуль показывающий как EDIT может сам себя переделывать
# Вызывается через self_improve или как отдельный tool если зарегистрировать

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
BACKUP_DIR = BASE_DIR / "config" / "backups"
LOG_PATH = BASE_DIR / "config" / "evolution_log.json"

def evolution_lab(parameters: dict, player=None, speak=None) -> str:
    """
    Лаборатория эволюции — показывает текущее состояние самоулучшений,
    позволяет тестировать идеи.
    
    Триггеры: "лаборатория эволюции", "покажи эволюции", "evolution lab"
    """
    action = parameters.get("action", "status").lower()

    if action == "status":
        lines = ["🧬 EVOLUTION LAB — статус саморазвития EDIT:\n"]
        
        # Skills
        try:
            reg = BASE_DIR / "actions" / "custom_skills" / "registry.json"
            if reg.exists():
                data = json.loads(reg.read_text(encoding="utf-8"))
                skills = data.get("skills", [])
                lines.append(f"📦 Навыков навеки: {len(skills)}")
                for s in skills[-5:]:
                    lines.append(f"   • {s['name']}: {s['description'][:60]}")
            else:
                lines.append("📦 Навыков: 0")
        except Exception as e:
            lines.append(f"📦 Ошибка чтения навыков: {e}")

        lines.append("")
        
        # Backups
        try:
            if BACKUP_DIR.exists():
                backs = list(BACKUP_DIR.glob("*.bak"))
                lines.append(f"💾 Бекапов: {len(backs)} в config/backups/")
                for b in sorted(backs, key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
                    lines.append(f"   • {b.name}")
            else:
                lines.append("💾 Бекапов: 0")
        except Exception as e:
            lines.append(f"💾 Бекап ошибка: {e}")

        lines.append("")

        # Evolution log
        try:
            if LOG_PATH.exists():
                log = json.loads(LOG_PATH.read_text(encoding="utf-8"))
                lines.append(f"🧠 Эволюций в истории: {len(log)}")
                for entry in log[-5:]:
                    status = "✅" if entry.get("success") else "❌"
                    lines.append(f"   {status} {entry.get('ts')} {entry.get('action')} {entry.get('file')}")
            else:
                lines.append("🧠 История эволюции пуста — стань первым мутацией!")
        except Exception as e:
            lines.append(f"🧠 Лог ошибка: {e}")

        lines.append("")
        lines.append("💡 Что можно попросить:")
        lines.append(" • 'Сделай интерфейс красным' → redesign_ui")
        lines.append(" • 'Добавь навык переводчика навеки' → create_skill")
        lines.append(" • 'Добавь функцию которая...' → add_feature")
        lines.append(" • 'Сделай бекап ui.py' → backup")
        lines.append(" • 'Покажи историю эволюции' → evolution_log")

        result = "\n".join(lines)
        if player:
            player.write_log(result)
        return result

    elif action == "demo_ui":
        # Demo: меняет цвет на случайный неоновый и показывает как это работает
        import random
        neon_colors = ["#ff0066", "#00ff88", "#00d4ff", "#ffcc00", "#cc44ff", "#ff6b00"]
        color = random.choice(neon_colors)
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg["ui_color"] = color
            CONFIG_PATH.write_text(json.dumps(cfg, indent=4, ensure_ascii=False), encoding="utf-8")
            if player and hasattr(player, "_apply_name_update"):
                try:
                    player._apply_name_update(cfg.get("assistant_name","EDIT"), cfg.get("user_name",""), color)
                except Exception:
                    pass
            return f"🎨 Demo UI: цвет изменён на {color} — смотри как весь интерфейс перекрасился мгновенно! Это и есть 'переделывать интерфейс'."
        except Exception as e:
            return f"Demo UI error: {e}"

    elif action == "demo_skill":
        # Demo: создает тестовый навык joke
        from .self_improve import create_skill as _create
        code = '''
def run_skill(args, player=None):
    import random
    jokes = [
        "Почему программисты не любят природу? Слишком много багов!",
        "— Эдит, переделай интерфейс! — Уже, сэр, он теперь ещё красивее.",
        "Какой любимый язык у EDIT? Python, конечно!",
        "Почему ИИ не играет в прятки? Потому что всегда найдёт себя в коде!"
    ]
    return random.choice(jokes)
'''
        res = _create({
            "action": "create",
            "skill_name": "demo_joke",
            "description": "Demo навык который рассказывает шутки про EDIT — создан лабораторией эволюции",
            "parameters_schema": '{"type":"OBJECT","properties":{}}',
            "python_code": code
        }, player=player)
        return f"🧪 Demo skill создан: {res}"

    else:
        return f"Unknown lab action: {action}. Try: status | demo_ui | demo_skill"
