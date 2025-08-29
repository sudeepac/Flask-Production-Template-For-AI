```markdown
<!-- ────────────────────────────────────────────────────────────────
AI_INSTRUCTIONS.md
“Flask + ML Project – Consistent, Human-Friendly, Future-Proof”
──────────────────────────────────────────────────────────────── -->
**Keep this file in repo root and commit to git.**  
Every AI agent (Copilot, Cursor, GPT, Claude, LangChain, etc.) must
read this *before* writing or moving a single line of code.  
Humans: skim the **Quickstart** and **Rules** sections; everything
else is for maintainability.

<!-- ────────────────────────────────────────────────────────────────
0.  One-Line Bootstrap (Human or AI)
──────────────────────────────────────────────────────────────── -->
```bash
./scripts/quickstart.sh          # macOS / Linux
.\scripts\quickstart.ps1         # Windows (PowerShell)
```
Does *all* of the following:  
1. Creates `.venv` (Python ≥ 3.10) if missing.  
2. Installs `requirements.txt` + pre-commit hooks.  
3. Runs DB migrations.  
4. Starts the dev server on http://127.0.0.1:5000 with hot-reload.

Nothing else is required to be “up and running”.

<!-- ────────────────────────────────────────────────────────────────
1. Immutable Directory Layout
──────────────────────────────────────────────────────────────── -->
```
your_app/
├── app/
│   ├── __init__.py           # Application factory ONLY
│   ├── config.py             # Central config (Flask, DB, ML, features)
│   ├── urls.py               # EXCLUSIVE source of URL prefixes
│   ├── extensions.py         # db, migrate, jwt, cache, etc.
│   ├── schemas/
│   │   ├── v1/               # Immutable after release
│   │   ├── v2/               # Current active version
│   │   └── __init__.py       # Re-exports “Current*” aliases
│   ├── services/
│   │   └── base.py           # Abstract BaseMLService
│   ├── blueprints/           # One folder per feature
│   ├── utils/                # Pure helpers
│   ├── static/               # JS/CSS/images
│   └── templates/            # Jinja2
├── tests/                    # Mirrors blueprints/ exactly
├── __template__/             # Blueprint cookie-cutter
├── scripts/
│   ├── quickstart.sh
│   ├── quickstart.ps1
│   ├── gen_tests.py
│   └── make_blueprint.py     # Optional CLI helper
├── AI_INSTRUCTIONS.md        # ← THIS FILE
├── .pre-commit-config.yaml
├── pyproject.toml            # Tool configs + naming rules
├── requirements.txt
├── README.md                 # Human onboarding
└── CONTRIBUTING.md           # Deep-dive docs & style guide
```

<!-- ────────────────────────────────────────────────────────────────
2. Creating a New Feature (Deterministic)
──────────────────────────────────────────────────────────────── -->
1. **Scaffold**  
   ```bash
   python scripts/make_blueprint.py <feature_name>
   # or: cp -r __template__/my_blueprint app/blueprints/<feature_name>
   ```

2. **Register URL**  
   Add to `app/urls.py`:  
   ```python
   URL_PREFIX = {..., "<feature_name>": "/<feature_name>"}
   ```

3. **Fill Blueprint Files**  
   `app/blueprints/<feature_name>/`  
   - `models.py` – SQLAlchemy / Pydantic models  
   - `services.py` – MUST inherit from `BaseMLService`; load/serve ML models here  
   - `controllers.py` – Request/response logic  
   - `routes.py` – Flask routes using `URL_PREFIX[<feature_name>]`  
   - `tests/` – auto-generated test stubs via `scripts/gen_tests.py <feature_name>`

4. **Versioned Schemas**  
   Add input/output schemas under the **latest**  
   `app/schemas/v*/<feature_name>.py`  
   Export alias in `app/schemas/__init__.py`.

5. **Commit**  
   Pre-commit hooks enforce style, type checks, docstring coverage, and
   required files.

<!-- ────────────────────────────────────────────────────────────────
3. Non-Negotiable Rules (CI & Pre-commit Enforced)
──────────────────────────────────────────────────────────────── -->
| # | Rule | Why |
|---|------|-----|
|1|One feature ≡ one blueprint folder|Prevents spaghetti code|
|2|All routes import URL prefix from `app.urls.URL_PREFIX`|Single source of truth|
|3|Every service inherits from `BaseMLService` + typed schemas|Guarantees consistent ML interface|
|4|Schema versions are immutable|Safe backwards compatibility|
|5|Test stub required per route|No uncovered endpoints|
|6|Blueprint `__init__.py` import order fixed|Avoids circular imports|
|7|Logger name: `logging.getLogger("app.blueprints.<name>")`|Uniform logs|
|8|Human-centric documentation mandatory|Readable by humans & AIs|

**Docstring coverage ≥ 90 %** – enforced by `docstring-coverage` pre-commit hook.

<!-- ────────────────────────────────────────────────────────────────
4. Docstring & Comment Guidelines (for Humans)
──────────────────────────────────────────────────────────────── -->
- **Every public module, class, and function** must have a Google-style
  docstring explaining **why** it exists and **how to use it**.  
- **Inline comments** must clarify non-obvious logic, edge cases, or
  business rules.  
- **Template reminder** (auto-inserted in stubs):  
  ```python
  """One-sentence summary.

  Extended description for humans:
  - What this does.
  - Non-obvious side effects.
  - One short usage example.

  See CONTRIBUTING.md §5 for style.
  """
  ```

<!-- ────────────────────────────────────────────────────────────────
5. Quick Reference Cheat-Sheet
──────────────────────────────────────────────────────────────── -->
```bash
# 1. Bootstrap entire env
./scripts/quickstart.sh          # macOS / Linux
.\scripts\quickstart.ps1         # Windows

# 2. New ML feature
python scripts/make_blueprint.py fraud_detector
#   → folder created, URL registered, stubs generated

# 3. Add schemas
touch app/schemas/v2/fraud_detector.py

# 4. Generate / refresh tests
python scripts/gen_tests.py fraud_detector

# 5. Lint & type check
pre-commit run --all-files

# 6. Run tests
pytest tests/fraud_detector/
```

<!-- ────────────────────────────────────────────────────────────────
6. Documentation Map (Robust & Discoverable)
──────────────────────────────────────────────────────────────── -->
| File | Audience | Purpose |
|------|----------|---------|
| `README.md` | New humans | One-screen setup, quickstart link |
| `CONTRIBUTING.md` | All devs | Deep style guide, architecture, FAQ |
| `AI_INSTRUCTIONS.md` | AI agents | Zero-ambiguity rules & templates |
| `docs/` (optional) | End users | API docs, tutorials, changelogs |
| `docs/arch/` | Maintainers | ADRs, decision logs |

<!-- ────────────────────────────────────────────────────────────────
7. Scripts (place in /scripts)
──────────────────────────────────────────────────────────────── -->
**scripts/quickstart.sh**
```bash
#!/usr/bin/env bash
set -euo pipefail
echo "🚀 Bootstrapping Flask + ML project …"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt
pre-commit install
flask db upgrade
echo "✅ Ready. Starting dev server http://127.0.0.1:5000"
exec flask run --host=0.0.0.0 --port=5000 --reload
```

**scripts/quickstart.ps1**
```powershell
#Requires -Version 5.1
Write-Host "🚀 Bootstrapping Flask + ML project …" -ForegroundColor Green
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip wheel
pip install -r requirements.txt
pre-commit install
flask db upgrade
Write-Host "✅ Ready. Starting dev server http://127.0.0.1:5000" -ForegroundColor Green
flask run --host=0.0.0.0 --port=5000 --reload
```

Make them executable:  
```bash
chmod +x scripts/quickstart.sh
# Windows:  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

<!-- ────────────────────────────────────────────────────────────────
End of AI_INSTRUCTIONS.md
──────────────────────────────────────────────────────────────── -->
```