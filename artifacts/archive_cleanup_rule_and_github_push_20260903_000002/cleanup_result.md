# cleanup_result.md — archive_cleanup_rule_and_github_push_20260903_000002

status: completed
authorized_by: user
rule_files:
  - artifacts/runtime/common.md
  - artifacts/runtime/orchestrator.md
remote: https://github.com/13229226903/web-test
branch: main
pushed_commit: f46aea7

## Rule change

- Archive confirmation now triggers archive-cleanup.
- Unreferenced screenshots, snapshots, and temporary downloads are removed after a manifest is generated.
- Referenced evidence and versioned formal artifacts remain protected.
- Cleanup manifest / result and progress / journal records are required.

## Push exclusions

- Explicit backup directory is ignored and not pushed:
  - artifacts/framework_playwright_mcp_explore_20260901_111335/backups/
- Generated heavy outputs are also ignored:
  - reports/
  - data/screenshots/
  - .playwright-mcp/
  - debug.log
- Secrets remain ignored:
  - .env

## Verification

- Backup staged/tracked file count: 0
- reports/ staged/tracked file count: 0
- data/screenshots/ staged/tracked file count: 0
- .env staged/tracked file count: 0
- Initial project push succeeded.
