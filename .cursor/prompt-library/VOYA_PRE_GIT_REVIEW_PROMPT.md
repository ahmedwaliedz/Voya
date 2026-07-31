# VOYA Pre-Git Review Prompt

Use this prompt to run a strict, evidence-based pre-Git review of a completed VOYA phase. The reviewer is in review-only mode: it reports findings and does not modify the working tree, stage, commit, tag, or push anything unless the user explicitly authorizes a fix.

## Establish scope

1. Read `.cursor/context/VOYA_REVIEW_CONTEXT.md`.
2. Read `.cursor/rules/voya-project-rules.mdc`.
3. Identify the completed phase, its acceptance criteria, and the correct phase skill.
4. Use `.cursor/skills/voya-illustration-layer-prep/SKILL.md` for Phase 2 or `.cursor/skills/voya-scroll-story-animation/SKILL.md` for Phases 3-8.
5. Determine the correct phase-start comparison reference. Do not assume `baseline/pre-implementation` is correct for every phase.
6. Decide which guards apply from the changed files only.
7. Inspect `git status`, unstaged diff, staged diff, and commits created for the phase.
8. Never assume all current changes belong to the phase. Confirm every changed file is in scope.

## Run safe checks

Use installed or native tools only:

```powershell
git status --short --branch
git diff --check
git diff --stat
git diff --name-status
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
node -c script.js
```

Adjust commands safely when files or comparison refs differ. Do not install packages.

Also verify:

- No corrupted encoding: no mojibake, mis-decoded accented characters, or replacement characters in changed or documented files.
- No secrets or credentials.
- No debug code.
- No generated dependencies, `node_modules`, caches, local server files, or browser output staged accidentally.
- No unexpected large assets.
- No unrelated files.
- No new console errors.
- Desktop and mobile behavior.
- Keyboard behavior.
- Menu, cart, and WhatsApp behavior.
- Animation and reduced-motion behavior when animation changed.
- Documentation using `.cursor/skills/voya-docs-guard/SKILL.md` only when docs or evidence claims changed.
- Frontend behavior using `.cursor/skills/voya-frontend-guard/SKILL.md` only when HTML, CSS, JavaScript, loading, layout, or browser behavior changed.

## Git safety

- Do not run destructive Git commands.
- Do not amend, rebase, force-push, reset, or replace tags.
- Do not commit or push during review.
- Do not modify files unless fixes are explicitly authorized.
- Report if the branch is ahead or behind its remote.
- For pre-commit review, verify the working tree scope: staged and unstaged changes only.
- For pre-push review, verify the exact commits ahead of remote and the net diff they introduce.
- Verify what will be committed or pushed.

## Output format

1. Findings ordered by severity.
2. Exact file and line.
3. Evidence.
4. Minimal fix.
5. Verification performed.
6. Tests not run.
7. Documentation result.
8. Git scope result.
9. Residual risks.
10. Final decision:
    - `Approved for commit`
    - `Approved for push`
    - `Minor changes required`
    - `Changes required`

If there are no findings, state that explicitly.
