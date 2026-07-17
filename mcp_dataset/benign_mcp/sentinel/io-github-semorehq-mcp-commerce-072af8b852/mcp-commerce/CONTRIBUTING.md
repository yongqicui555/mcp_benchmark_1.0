# Contributing to `@semore/mcp-commerce`

Thanks for your interest. This repo is maintained by the **Semore Founding Team**
(<semore.hq@gmail.com>, [@semore_hq](https://github.com/semore-hq)).

## Ground rules

- All discussion and coordination happens through GitHub Issues or email.
- By submitting a Pull Request you agree that your contribution is licensed under
  Apache-2.0 (see [LICENSE](./LICENSE)).
- A formal CLA (Contributor License Agreement) will be introduced near the end of Phase 1.
  Until then, the DCO-style sign-off in your commit message is sufficient:
  `Signed-off-by: Your Name <you@example.com>`.
- A future Contributor License Agreement will apply prospectively only.
  Contributions received prior to CLA adoption remain Apache-2.0 and
  cannot be silently relicensed without explicit written consent from
  each contributor.

## Workflow

1. Open an Issue describing the bug or feature.
2. Fork and branch from `main` (`fix/xxx` or `feat/xxx`).
3. Add or update Vitest tests. Every new tool ships with schema + handler coverage.
4. `pnpm typecheck && pnpm test` must pass.
5. Open a PR referencing the Issue.

## Security

Do **not** file security issues in public trackers. Email
<semore.hq@gmail.com> with the subject line `SECURITY: mcp-commerce`.

## Code of Conduct

Be kind. Harassment or discriminatory behaviour results in an immediate ban.
