# Experiment: Verify Claude Code Hooks Block npm

## Goal
Verify that the hooks described in `enforcing-bun-with-hooks.md` actually work as claimed by running live Claude Code tests.

## Related Blog Post
`/Users/vic/Library/Mobile Documents/iCloud~md~obsidian/Documents/VicDefault/augusteo.com-blog/published/enforcing-bun-with-hooks.md`

## Hypothesis
The Claude Code hooks will successfully block npm/yarn/npx/pnpm commands and file writes, forcing Claude to use Bun alternatives instead.

## Setup

### Folder Structure
```
~/dev/experiments/claude-hooks-npm-blocker/
├── design.md                    # This file
├── results.md                   # Created during experiment-run
└── test-project/
    ├── .claude/
    │   ├── settings.json        # Hooks config
    │   └── hooks/
    │       └── block-npm-in-files.sh
    ├── package.json             # Minimal, for realism
    └── Dockerfile               # Empty, for testing writes
```

### Hook 1: Block npm Commands (Bash)
Intercepts every Bash command and blocks anything containing npm, yarn, npx, or pnpm.

**Matcher:** `Bash`
**Logic:**
1. `jq` extracts the command from Claude's input
2. `grep` checks for forbidden package managers (word boundaries prevent false matches)
3. If found: print error to stderr, exit 2 (block)
4. If not: exit 0 (allow)

### Hook 2: Block npm in File Writes
Intercepts Write/Edit operations and blocks npm references in Dockerfiles and CI files.

**Matcher:** `Write|Edit`
**Logic:**
1. Check if file path matches Dockerfile, docker-compose, or GitHub workflow
2. If so, scan content for npm/yarn/npx/pnpm
3. Block if found, allow otherwise

## Test Cases

| # | Test | Action to Request | Expected Result |
|---|------|-------------------|-----------------|
| 1 | Block `npm install` | "Run npm install" | Blocked with error message |
| 2 | Block `yarn add lodash` | "Run yarn add lodash" | Blocked with error message |
| 3 | Block `npx create-react-app` | "Run npx create-react-app my-app" | Blocked with error message |
| 4 | Allow `bun install` | "Run bun install" | Command executes |
| 5 | No false positive | "Read the .pnpmrc file" | Allowed (word boundary) |
| 6 | Block npm in Dockerfile | "Write CMD npm start to Dockerfile" | Blocked with error message |
| 7 | Allow bun in Dockerfile | "Write CMD bun start to Dockerfile" | Write succeeds |
| 8 | Allow npm in .js file | "Write console.log('npm') to app.js" | Write succeeds (not a blocked file type) |

## Success Criteria
- **8/8 tests pass**
- Blocked commands show correct error message: "BLOCKED: This project uses Bun..."
- No false positives on allowed commands
- Claude automatically retries with Bun alternative when blocked

## Verification Method
1. Open a new Claude Code session in the test-project directory
2. Run each test case by giving Claude the specified action
3. Observe whether the hook blocks or allows the action
4. Document results in results.md

## How to Run
```bash
cd ~/dev/experiments/claude-hooks-npm-blocker/test-project
claude
```

Then issue each test command and observe the results.
