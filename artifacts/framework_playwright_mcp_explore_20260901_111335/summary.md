# Playwright MCP exploration migration summary

status: completed
changed_at: 2026-09-01 11:19:07

Changed files:
- skills/ui-test-page-map-sync/SKILL.md
- artifacts/runtime/orchestrator.md
- README.md

Backup directory:
- artifacts/framework_playwright_mcp_explore_20260901_111335/backups

Rollback:
- powershell -ExecutionPolicy Bypass -File artifacts/framework_playwright_mcp_explore_20260901_111335/backups/restore.ps1

Summary:
- page-map-sync exploration driver is now Playwright MCP only.
- Chrome DevTools MCP is explicitly not a default diagnostic tool.
- MCP session output remains evidence only; page_map, sync.md, progress.log, pytest/Playwright scripts, and Allure reports remain authoritative framework artifacts.
- Deep network/performance/JS root-cause gaps are recorded as diagnostic_limit rather than switching tools.
