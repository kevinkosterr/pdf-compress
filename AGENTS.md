# AGENTS.md

AI agent instructions for repo. Skills in `.agents/skills/` (mirrored `.claude/skills/`).

## Skills

| When | Skill |
| --- | --- |
| Every request | `caveman` |
| Every code request (write, fix, refactor) | `ponytail` |
| FastAPI code (e.g. `main.py`) | `fastapi` |
| Commit messages | `caveman-commit` |
| Any code review | `caveman-review` |

- **caveman**: always on. Terse, keep all technical facts.
- **ponytail**: on top of `caveman` for code. Smallest change fully solving task.
- **fastapi**: load before changing FastAPI app, route, dependency, Pydantic model.
- **caveman-commit**: every commit message. Follow convention below.
- **caveman-review**: every review (PRs, diffs, files).

## Commit convention

[Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`.

- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `build`, `ci`, `style`.
- Scope optional, names area, e.g. `compress`, `api`, `ui`, `ai`.
- History examples: `feat(api): add FastAPI app with compress endpoint`, `docs: add README with usage instructions`.

## Code search

Default: semble. Local semantic + lexical search (tree-sitter chunks, Model2Vec embeddings + BM25). Natural language or symbol query → relevant snippets w/ file path + line range. No full-file reads, far fewer tokens than grep+read. CPU, no API keys.

Use precise tooling (`grep`/`rg`, symbol lookup, direct read) only for exact matches (every occurrence, rename, regex) or when semble insufficient.

### CLI

```bash
# Search current repo (index built + cached on first run, auto-refreshed on file change)
semble search "how is PDF compressed" .

# Search by symbol name
semble search "compress_pdf" .

# Limit results
semble search "upload endpoint" . --top-k 5

# Search docs/config instead of code
semble search "usage instructions" . --content docs   # or: config, all

# Find code similar to known location (file + line)
semble find-related compress.py 69 .

# Trim snippets (0 = path/line range only)
semble search "image downsampling" . --max-snippet-lines 10
```

- `path` default current dir. Git URLs OK.
- `--content`: `code` (default), `docs`, `config`, `all`.
- `--format`: `json` (default) or `text`.
- Not on `$PATH`? Use `uvx --from "semble[mcp]" semble` instead of `semble`.
- Not installed? `uv tool install semble`.

### MCP

Semble MCP server available → prefer its tools over CLI:

| Tool | Use |
| --- | --- |
| `search` | Query codebase. `repo` = local path or https git URL (or list). `content` = `code` (default), `docs`, `config`, `all`. |
| `find_related` | File path + line number → semantically similar chunks. |

### Tips

- Natural-language ("where are uploads validated") and symbol queries (`compress_pdf`, `UploadFile`) both work. Symbol queries rank definitions above references.
- Tests + example code ranked lower. Search explicitly if needed.
- Respects `.gitignore` + `.sembleignore`. Skips `.venv/`, `node_modules/`, `__pycache__/`, files > 1 MB.
- Use `find-related` from good hit to explore nearby/similar code, not whole-file reads.