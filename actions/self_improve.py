# actions/self_improve.py — Autonomous Self-Improvement V2 for EDIT (EDITH)
"""
Provides EDIT with:
1. create_skill: create and permanently register new Python tools/skills ('делать навыки навеки')
2. self_improve: edit codebase, redesign UI ('переделывать интерфейс'), add functions ('добавлять функции возможности')
3. execute_command: run arbitrary system/bash commands or Python code ('полностью что я захочу')

V2 Features:
- Fuzzy matching for edit_file (не нужен 100% exact текст)
- Автоматические бекапы в config/backups/ + rollback
- create_action — создает новый action в actions/ и автоматически регистрирует в main.py
- patch_ui — меняет цвета, стили, добавляет кнопки
- evolution_log — история всех самоулучшений
"""

import os
import sys
import json
import time
import shutil
import difflib
import subprocess
import tempfile
import py_compile
import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CUSTOM_SKILLS_DIR = Path(__file__).resolve().parent / "custom_skills"
REGISTRY_FILE = CUSTOM_SKILLS_DIR / "registry.json"
BACKUP_DIR = BASE_DIR / "config" / "backups"
EVOLUTION_LOG = BASE_DIR / "config" / "evolution_log.json"

# ── helpers ───────────────────────────────────────────────────────────────────

def _ensure_dirs():
    CUSTOM_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_FILE.exists():
        initial_data = {
            "skills": [
                {
                    "name": "crypto_price",
                    "description": "Fetches current cryptocurrency price in USD (e.g. bitcoin, ethereum, solana). Created as a permanent custom skill.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "coin": {
                                "type": "STRING",
                                "description": "Cryptocurrency name (e.g. bitcoin, ethereum)"
                            }
                        },
                        "required": ["coin"]
                    },
                    "file": "crypto_price.py"
                }
            ]
        }
        REGISTRY_FILE.write_text(json.dumps(initial_data, indent=4, ensure_ascii=False), encoding="utf-8")

def _ensure_registry_exists():
    _ensure_dirs()
    if not REGISTRY_FILE.exists():
        _ensure_dirs()

def _log_evolution(action: str, file_path: str, description: str, success: bool):
    try:
        _ensure_dirs()
        log = []
        if EVOLUTION_LOG.exists():
            try:
                log = json.loads(EVOLUTION_LOG.read_text(encoding="utf-8"))
            except Exception:
                log = []
        log.append({
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "file": file_path,
            "description": description,
            "success": success
        })
        # keep last 200 entries
        log = log[-200:]
        EVOLUTION_LOG.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[Evolution] log failed: {e}")

def _backup_file(target: Path) -> Path | None:
    """Create timestamped backup before modification."""
    try:
        _ensure_dirs()
        if not target.exists() or not target.is_file():
            return None
        ts = time.strftime("%Y%m%d_%H%M%S")
        safe_name = f"{target.name}.{ts}.bak"
        # keep folder structure flattened but with parent prefix
        parent_prefix = target.parent.name
        backup_name = f"{parent_prefix}_{safe_name}" if parent_prefix else safe_name
        dst = BACKUP_DIR / backup_name
        shutil.copy2(target, dst)
        # keep only last 20 backups per file stem
        all_b = sorted(BACKUP_DIR.glob(f"*{target.name}*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in all_b[20:]:
            try:
                old.unlink()
            except Exception:
                pass
        return dst
    except Exception as e:
        print(f"[Evolution] backup failed for {target}: {e}")
        return None

def _fuzzy_find(haystack: str, needle: str, threshold: float = 0.85) -> str | None:
    """Try exact match, then fuzzy line-based search. Returns best matching substring."""
    if needle in haystack:
        return needle
    # Normalize whitespace for comparison
    needle_stripped = needle.strip()
    if needle_stripped in haystack:
        return needle_stripped
    # Line-level fuzzy: find block of lines in haystack that best matches needle
    hay_lines = haystack.splitlines()
    need_lines = needle_stripped.splitlines()
    if not need_lines:
        return None
    # If single line, find best single-line fuzzy match
    if len(need_lines) == 1:
        best_ratio = 0
        best_line = None
        for hl in hay_lines:
            r = difflib.SequenceMatcher(None, hl.strip(), need_lines[0].strip()).ratio()
            if r > best_ratio:
                best_ratio = r
                best_line = hl
        if best_ratio >= threshold and best_line is not None:
            return best_line
        return None
    # Multi-line: sliding window
    best_ratio = 0
    best_start = -1
    n_len = len(need_lines)
    for i in range(len(hay_lines) - n_len + 1):
        window = hay_lines[i:i+n_len]
        # compare joined strings
        r = difflib.SequenceMatcher(None, "\n".join(window), "\n".join(need_lines)).ratio()
        if r > best_ratio:
            best_ratio = r
            best_start = i
    if best_ratio >= threshold and best_start != -1:
        return "\n".join(hay_lines[best_start:best_start+n_len])
    return None

def _validate_python_syntax(code_text: str) -> tuple[bool, str]:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tf:
            tf.write(code_text)
            tf_path = tf.name
        py_compile.compile(tf_path, doraise=True)
        os.unlink(tf_path)
        return True, ""
    except py_compile.PyCompileError as ce:
        try:
            if os.path.exists(tf_path):
                os.unlink(tf_path)
        except Exception:
            pass
        return False, str(ce)
    except Exception as e:
        return False, str(e)


# ── Custom Skills registry ────────────────────────────────────────────────────

def get_custom_tool_declarations() -> list[dict]:
    _ensure_registry_exists()
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        skills = data.get("skills", [])
        decls = []
        for s in skills:
            name = s.get("name")
            if not name:
                continue
            decls.append({
                "name": name,
                "description": s.get("description", f"Custom skill: {name}"),
                "parameters": s.get("parameters", {"type": "OBJECT", "properties": {}})
            })
        return decls
    except Exception as e:
        print(f"[SelfImprove] Error loading custom skill declarations: {e}")
        return []

def is_custom_skill(name: str) -> bool:
    _ensure_registry_exists()
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        return any(s.get("name") == name for s in data.get("skills", []))
    except Exception:
        return False

def run_custom_skill(skill_name: str, parameters: dict, player=None) -> str:
    _ensure_registry_exists()
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        skill_entry = next((s for s in data.get("skills", []) if s.get("name") == skill_name), None)
        if not skill_entry:
            return f"Error: Custom skill '{skill_name}' not found in registry."
        file_name = skill_entry.get("file", f"{skill_name}.py")
        file_path = CUSTOM_SKILLS_DIR / file_name
        if not file_path.exists():
            return f"Error: Skill file {file_path} does not exist on disk."
        spec = importlib.util.spec_from_file_location(f"custom_skill_{skill_name}", str(file_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "run_skill"):
            return str(mod.run_skill(parameters, player=player))
        elif hasattr(mod, "main"):
            return str(mod.main(parameters))
        else:
            return f"Error: Skill '{skill_name}' does not define 'def run_skill(args, player=None)'."
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[SelfImprove] ❌ Error executing custom skill '{skill_name}': {e}\n{tb}")
        return f"Execution error in custom skill '{skill_name}': {e}"

def create_skill(parameters: dict, player=None, speak=None) -> str:
    """Create, list, test, or remove permanent custom skills — 'делать навыки навеки'."""
    _ensure_registry_exists()
    action = parameters.get("action", "create").lower().strip()
    skill_name = parameters.get("skill_name", "").strip()

    if action == "list":
        try:
            data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
            skills = data.get("skills", [])
            if not skills:
                return "No custom skills created yet. Используй create_skill чтобы создать первый навык навсегда."
            lines = ["🔧 Постоянно установленные навыки (навеки):"]
            for s in skills:
                lines.append(f" • {s.get('name')}: {s.get('description')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error listing skills: {e}"

    if action in ("remove", "delete"):
        if not skill_name:
            return "Please provide 'skill_name' to remove."
        try:
            data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
            skills = data.get("skills", [])
            new_skills = [s for s in skills if s.get("name") != skill_name]
            if len(new_skills) == len(skills):
                return f"Skill '{skill_name}' was not found."
            data["skills"] = new_skills
            REGISTRY_FILE.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
            skill_file = CUSTOM_SKILLS_DIR / f"{skill_name}.py"
            if skill_file.exists():
                _backup_file(skill_file)
                skill_file.unlink()
            if player:
                player.write_log(f"SYS: Skill removed — {skill_name}")
            _log_evolution("remove_skill", skill_name, f"removed {skill_name}", True)
            return f"Skill '{skill_name}' has been permanently removed."
        except Exception as e:
            return f"Error removing skill: {e}"

    if action == "test":
        if not skill_name:
            return "Please provide 'skill_name' to test."
        # pass remaining args as skill args
        test_args = {k: v for k, v in parameters.items() if k not in ("action", "skill_name", "description", "parameters_schema", "python_code")}
        return run_custom_skill(skill_name, test_args, player=player)

    # action == "create"
    if not skill_name:
        return "Please provide a valid unique 'skill_name' (snake_case, например: my_feature)."

    description = parameters.get("description", f"Custom skill {skill_name}")
    python_code = parameters.get("python_code", "")
    raw_schema = parameters.get("parameters_schema", '{"type": "OBJECT", "properties": {}}')

    if not python_code.strip():
        return "Please provide complete 'python_code' implementing def run_skill(args, player=None)."

    if isinstance(raw_schema, str):
        try:
            parameters_schema = json.loads(raw_schema)
        except Exception:
            parameters_schema = {"type": "OBJECT", "properties": {}}
    elif isinstance(raw_schema, dict):
        parameters_schema = raw_schema
    else:
        parameters_schema = {"type": "OBJECT", "properties": {}}

    skill_file = CUSTOM_SKILLS_DIR / f"{skill_name}.py"
    ok, err = _validate_python_syntax(python_code)
    if not ok:
        return f"SyntaxError in custom skill code for '{skill_name}': {err}. Исправь синтаксис."

    try:
        _backup_file(skill_file) if skill_file.exists() else None
        skill_file.write_text(python_code, encoding="utf-8")
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        skills = [s for s in data.get("skills", []) if s.get("name") != skill_name]
        skills.append({
            "name": skill_name,
            "description": description,
            "parameters": parameters_schema,
            "file": f"{skill_name}.py"
        })
        data["skills"] = skills
        REGISTRY_FILE.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
        if player:
            player.write_log(f"SYS: Навык создан навеки — {skill_name}")
        _log_evolution("create_skill", skill_name, description, True)
        print(f"[SelfImprove] ✅ Skill created: {skill_name} -> {skill_file}")
        return f"✅ Успех! Навык '{skill_name}' создан и сохранён НАВЕКИ. Он теперь доступен как инструмент навсегда. Перезапусти сессию чтобы увидеть его в списке tools."
    except Exception as e:
        _log_evolution("create_skill", skill_name, description, False)
        return f"Failed to save custom skill '{skill_name}': {e}"


# ── Self-Improvement Engine ───────────────────────────────────────────────────

def self_improve(parameters: dict, player=None, speak=None) -> str:
    """
    Autonomous self-improvement: edit code, redesign UI, add features.
    Триггеры: 'переделывать интерфейс', 'добавлять функции', 'улучшать себя'
    """
    action = parameters.get("action", "").lower().strip()
    file_path_str = parameters.get("file_path", "").strip()
    old_text = parameters.get("old_text", "")
    new_text = parameters.get("new_text", "")
    content = parameters.get("content", "")
    description = parameters.get("description", "self-improvement")

    target_path = BASE_DIR / file_path_str if file_path_str else BASE_DIR

    # ── READ ────────────────────────────────────────────────────────────────
    if action == "read_file":
        if not file_path_str:
            return "Укажи 'file_path' относительно корня проекта. Например: ui.py, actions/web_search.py"
        if not target_path.exists():
            return f"File not found: {file_path_str}. Используй list_files чтобы посмотреть что есть."
        try:
            txt = target_path.read_text(encoding="utf-8")
            lines = txt.splitlines()
            if len(lines) > 200:
                head = "\n".join(lines[:160])
                tail = "\n".join(lines[-40:])
                return (f"📄 File {file_path_str} ({len(lines)} lines, showing first 160 + last 40):\n"
                        f"{head}\n\n... [{len(lines)-200} lines omitted] ...\n\n{tail}")
            return txt
        except Exception as e:
            return f"Error reading file: {e}"

    # ── LIST ────────────────────────────────────────────────────────────────
    elif action == "list_files":
        try:
            p = target_path if target_path.exists() else BASE_DIR
            if p.is_file():
                p = p.parent
            files = []
            for item in sorted(p.iterdir()):
                if item.name.startswith(".") or item.name in ("__pycache__", "build", "dist", "node_modules"):
                    continue
                kind = "DIR " if item.is_dir() else "FILE"
                size = f"{item.stat().st_size//1024}KB" if item.is_file() else ""
                files.append(f"{kind}  {item.name:<30} {size}")
            return "\n".join(files) if files else "Empty dir"
        except Exception as e:
            return f"Error listing files: {e}"

    # ── EDIT (with fuzzy + backup) ──────────────────────────────────────────
    elif action == "edit_file":
        if not file_path_str:
            return "Specify 'file_path' to edit."
        if not target_path.exists():
            return f"File not found: {file_path_str}"
        if not old_text:
            return "Specify 'old_text' to replace. Если хочешь заменить весь файл — используй write_file."
        try:
            txt = target_path.read_text(encoding="utf-8")
            # Try fuzzy find if exact not found
            needle = old_text
            found = old_text if old_text in txt else _fuzzy_find(txt, old_text)
            if not found:
                # Show similar lines hint
                sample = "\n".join(txt.splitlines()[:20])
                return (f"❌ Could not find 'old_text' in {file_path_str} даже fuzzy поиском.\n"
                        f"Первые 20 строк файла для подсказки:\n{sample}\n\n"
                        f"Совет: скопируй точный кусок через read_file.")
            backup = _backup_file(target_path)
            new_content = txt.replace(found, new_text, 1)
            if str(target_path).endswith(".py"):
                ok, err = _validate_python_syntax(new_content)
                if not ok:
                    return f"SyntaxError after replacement in {file_path_str}: {err}. Edit aborted, backup saved: {backup}"
            target_path.write_text(new_content, encoding="utf-8")
            if player:
                player.write_log(f"SYS: Code improved — {file_path_str} (backup: {backup.name if backup else 'none'})")
            _log_evolution("edit_file", file_path_str, description, True)
            return f"✅ Successfully edited {file_path_str} ({description}). Backup: {backup}"
        except Exception as e:
            _log_evolution("edit_file", file_path_str, description, False)
            return f"Error editing file: {e}"

    # ── WRITE ────────────────────────────────────────────────────────────────
    elif action == "write_file":
        if not file_path_str:
            return "Specify 'file_path' to write. Например: actions/my_new_tool.py"
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                _backup_file(target_path)
            if str(target_path).endswith(".py"):
                ok, err = _validate_python_syntax(content)
                if not ok:
                    return f"SyntaxError in new code for {file_path_str}: {err}. Write aborted."
            target_path.write_text(content, encoding="utf-8")
            if player:
                player.write_log(f"SYS: File written — {file_path_str}")
            _log_evolution("write_file", file_path_str, description, True)
            return f"✅ Successfully wrote {file_path_str} ({description}). Размер: {len(content)} chars."
        except Exception as e:
            _log_evolution("write_file", file_path_str, description, False)
            return f"Error writing file: {e}"

    # ── REDESIGN UI ─────────────────────────────────────────────────────────
    elif action == "redesign_ui":
        cfg_path = BASE_DIR / "config" / "api_keys.json"
        try:
            cfg = {}
            if cfg_path.exists():
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

            # 1) Color change via ui_color param
            color = parameters.get("ui_color") or parameters.get("new_text") or parameters.get("content")
            if color:
                color = color.strip()
                if color.startswith("#") and len(color) in (4, 7):
                    cfg["ui_color"] = color
                    cfg_path.write_text(json.dumps(cfg, indent=4, ensure_ascii=False), encoding="utf-8")
                    if player and hasattr(player, "_apply_name_update"):
                        try:
                            asst_name = cfg.get("assistant_name", "EDIT")
                            player._apply_name_update(asst_name, cfg.get("user_name",""), color)
                        except Exception:
                            pass
                    _log_evolution("redesign_ui", "config/api_keys.json", f"color {color}", True)
                    return f"🎨 UI color changed to {color} — применился мгновенно!"

            # 2) Full UI file edit via old_text/new_text
            if old_text and new_text:
                ui_file = BASE_DIR / (file_path_str or "ui.py")
                if not ui_file.exists():
                    return f"UI file not found: {ui_file}"
                _backup_file(ui_file)
                txt = ui_file.read_text(encoding="utf-8")
                found = old_text if old_text in txt else _fuzzy_find(txt, old_text)
                if not found:
                    return f"Could not find old_text in {ui_file.name} для редизайна."
                new_content = txt.replace(found, new_text, 1)
                ok, err = _validate_python_syntax(new_content)
                if not ok:
                    return f"SyntaxError после редизайна {ui_file.name}: {err}"
                ui_file.write_text(new_content, encoding="utf-8")
                if player:
                    player.write_log(f"SYS: EDIT UI redesigned — {description}")
                _log_evolution("redesign_ui", str(ui_file), description, True)
                return f"✅ UI redesign applied to {ui_file.name}: {description}. Перезапусти приложение чтобы увидеть."

            # 3) Just description without file edit — save theme preference
            if description and description != "self-improvement":
                _log_evolution("redesign_ui", "ui.py", description, True)
                return f"🎨 UI redesign logged: {description}. Чтобы реально поменять код — передай old_text/new_text или ui_color."

            return "Укажи ui_color (#RRGGBB) или old_text/new_text для правки ui.py/hub.py"
        except Exception as e:
            _log_evolution("redesign_ui", file_path_str or "ui.py", description, False)
            return f"Error redesigning UI: {e}"

    # ── ADD FEATURE ─────────────────────────────────────────────────────────
    elif action == "add_feature":
        if not file_path_str:
            return "Укажи file_path куда добавить фичу. Например: actions/my_feature.py"
        if not content:
            return "Укажи content — полный код новой фичи."
        # If action file, also try to auto-register
        result = self_improve({
            "action": "write_file",
            "file_path": file_path_str,
            "content": content,
            "description": f"Added feature: {description}"
        }, player=player)
        # If it's in actions/, suggest import in main.py if needed
        if file_path_str.startswith("actions/") and file_path_str.endswith(".py"):
            mod_name = Path(file_path_str).stem
            _log_evolution("add_feature", file_path_str, description, True)
            return result + f"\n\n💡 Чтобы использовать: добавь импорт в main.py: from actions.{mod_name} import ..."
        return result

    # ── CREATE ACTION (new autonomous action) ───────────────────────────────
    elif action == "create_action":
        # More structured than add_feature — creates proper action with run function
        if not file_path_str:
            file_path_str = f"actions/{parameters.get('skill_name','my_action')}.py"
        if not content:
            return "Для create_action нужен content — Python код action'а."
        result = self_improve({
            "action": "write_file",
            "file_path": file_path_str,
            "content": content,
            "description": f"Created action: {description}"
        }, player=player)
        return result + "\n\nТеперь можешь вызывать через create_skill или напрямую через execute_command для теста."

    # ── INSPECT ─────────────────────────────────────────────────────────────
    elif action == "inspect_code":
        query = parameters.get("old_text", "") or parameters.get("description", "") or content
        if not query or query == "self-improvement":
            return "Укажи old_text или description как поисковый запрос. Например: 'class HudCanvas'"
        try:
            res = subprocess.run(
                ["grep", "-rn", query, str(BASE_DIR / "actions"), str(BASE_DIR / "core"), str(BASE_DIR / "ui.py"), str(BASE_DIR / "main.py")],
                capture_output=True, text=True, timeout=10
            )
            out = res.stdout.strip()
            if not out:
                return f"No matches found for '{query}' в actions/, core/, ui.py, main.py."
            lines = out.splitlines()
            if len(lines) > 40:
                return f"Found {len(lines)} matches. First 40:\n" + "\n".join(lines[:40])
            return out
        except Exception as e:
            return f"Error inspecting code: {e}"

    # ── BACKUP / ROLLBACK / LOG ─────────────────────────────────────────────
    elif action == "backup":
        if not file_path_str:
            # backup all important
            backed = []
            for p in [BASE_DIR / "ui.py", BASE_DIR / "main.py", BASE_DIR / "actions" / "self_improve.py"]:
                if p.exists():
                    b = _backup_file(p)
                    if b:
                        backed.append(str(b))
            return f"Backups created: {backed}"
        else:
            if not target_path.exists():
                return f"File not found: {file_path_str}"
            b = _backup_file(target_path)
            return f"Backup created: {b}" if b else "Backup failed"

    elif action == "rollback":
        # list backups or restore
        try:
            bname = parameters.get("old_text", "").strip()  # backup filename
            if bname:
                src = BACKUP_DIR / bname
                if not src.exists():
                    return f"Backup file not found: {bname}. Use list_backups."
                # Determine original: strip timestamp
                # backup format: {parent}_{orig}.YYYYMMDD_HHMMSS.bak
                orig_guess = bname.split(".")[0]  # heuristic
                # Find target by searching for orig name in backup name
                # Better: use file_path_str as restore destination
                if file_path_str:
                    dst = BASE_DIR / file_path_str
                else:
                    # try to infer from backup name
                    # e.g. actions_my_tool.py.20240101_120000.bak -> actions/my_tool.py
                    # simplified: remove timestamp
                    clean = bname.split(".20")[0]  # before .2024...
                    # parent_name + "_" + filename
                    if "_" in clean:
                        parts = clean.split("_", 1)
                        if "/" not in parts[1] and "\\" not in parts[1]:
                            # assume actions/ or root
                            # try actions first
                            candidate = BASE_DIR / "actions" / parts[1]
                            if candidate.exists() or "actions" in bname:
                                dst = candidate
                            else:
                                dst = BASE_DIR / parts[1]
                        else:
                            dst = BASE_DIR / parts[1]
                    else:
                        dst = BASE_DIR / clean
                shutil.copy2(src, dst)
                _log_evolution("rollback", str(dst), f"restored from {bname}", True)
                return f"✅ Rolled back {dst} from backup {bname}"
            else:
                # list backups
                backs = sorted(BACKUP_DIR.glob("*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)[:30]
                if not backs:
                    return "No backups found in config/backups/"
                lines = ["📦 Recent backups (укажи old_text=имя_файла для отката):"]
                for b in backs:
                    mt = time.strftime("%Y-%m-%d %H:%M", time.localtime(b.stat().st_mtime))
                    lines.append(f" • {b.name}  ({mt})")
                return "\n".join(lines)
        except Exception as e:
            return f"Rollback error: {e}"

    elif action == "list_backups":
        try:
            backs = sorted(BACKUP_DIR.glob("*.bak"), key=lambda p: p.stat().st_mtime, reverse=True)
            if not backs:
                return "No backups"
            return "\n".join([f"{b.name} - {time.strftime('%Y-%m-%d %H:%M', time.localtime(b.stat().st_mtime))}" for b in backs[:50]])
        except Exception as e:
            return f"Error: {e}"

    elif action == "evolution_log":
        try:
            if not EVOLUTION_LOG.exists():
                return "Лог эволюции пуст — ещё не было самоулучшений."
            data = json.loads(EVOLUTION_LOG.read_text(encoding="utf-8"))
            if not data:
                return "Лог пуст"
            lines = ["🧬 История эволюции EDIT (последние 20):"]
            for entry in data[-20:]:
                status = "✅" if entry.get("success") else "❌"
                lines.append(f"{status} {entry.get('ts')} | {entry.get('action')} | {entry.get('file')} | {entry.get('description')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading log: {e}"

    return ("Unknown action for self_improve. Доступные:\n"
            " • read_file | list_files | edit_file | write_file\n"
            " • redesign_ui | add_feature | create_action\n"
            " • inspect_code | backup | rollback | list_backups | evolution_log\n"
            "Примеры: переделать интерфейс -> redesign_ui с ui_color, добавить функцию -> add_feature / create_action")


def execute_command(parameters: dict, player=None, speak=None) -> str:
    """Execute arbitrary system/bash command or Python code — 'полностью что я захочу'."""
    cmd = parameters.get("command", "").strip()
    mode = parameters.get("mode", "bash").lower().strip()
    timeout = int(parameters.get("timeout", 30))

    if not cmd:
        return "Please specify a 'command' to execute."

    if mode == "python":
        try:
            import io
            from contextlib import redirect_stdout, redirect_stderr
            stdout_buf = io.StringIO()
            stderr_buf = io.StringIO()
            globals_dict = {
                "__name__": "__main__",
                "BASE_DIR": BASE_DIR,
                "CUSTOM_SKILLS_DIR": CUSTOM_SKILLS_DIR,
                "BACKUP_DIR": BACKUP_DIR,
                "player": player,
                "os": os,
                "sys": sys,
                "json": json,
                "subprocess": subprocess,
                "Path": Path,
                "time": time,
            }
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                try:
                    exec(compile(cmd, "<execute_command_python>", "exec"), globals_dict)
                except Exception as e:
                    import traceback
                    traceback.print_exc()

            out = stdout_buf.getvalue() + stderr_buf.getvalue()
            if not out.strip():
                return "Python code executed successfully (no printed output)."
            # truncate if too large
            if len(out) > 8000:
                out = out[:8000] + "\n... [truncated]"
            return f"Python output:\n{out.strip()}"
        except Exception as e:
            return f"Error executing Python code: {e}"

    # Bash / Shell mode — enhanced
    try:
        # Block dangerous destructive commands unless user explicitly wants
        dangerous = ["rm -rf /", "mkfs", ":(){:|:&};:", "dd if="]
        if any(d in cmd for d in dangerous) and "--force" not in cmd:
            return f"⛔ Blocked potentially destructive command: {cmd}. Add --force if you really mean it."

        res = subprocess.run(
            cmd,
            shell=True,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        out = (res.stdout or "") + (res.stderr or "")
        out = out.strip()
        if len(out) > 10000:
            out = out[:10000] + "\n... [truncated, full output >10KB]"
        if res.returncode == 0:
            _log_evolution("execute_command", "bash", cmd[:120], True)
            return f"✅ Command succeeded:\n{out}" if out else "✅ Command executed successfully (no output)."
        else:
            _log_evolution("execute_command", "bash", cmd[:120], False)
            return f"❌ Command exited with status {res.returncode}:\n{out}"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Error executing command: {e}"
