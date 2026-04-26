# claude-busy-monitor

List active Claude sessions for the current user with their state.

> Polished README pending in [TODO #3](TODO.md). What follows is the minimum needed to develop the project.

## Develop

Prerequisite: [`uv`](https://github.com/astral-sh/uv) on your `PATH` (one-line install: `pipx install uv` or follow the upstream installer).

```bash
make venv-activate
make help
```

`make venv-activate` creates `.venv`, syncs dependencies, and drops you into an activated shell. `make help` lists every available target. Tooling targets (`lint`, `format`, `test`, `build`) work outside the shell too — they run via `uv run`, which handles syncing implicitly.
