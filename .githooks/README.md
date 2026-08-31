# Git push guard

## Automatic GitHub check

`.github/workflows/chat-api-url.yml` runs the same validator on pushes, pull
requests, and merge queues, without any per-clone setup. The check is named
**Validate production chat API URL**. Commit both `.github/` and `.githooks/`.

For enforcement, after the workflow has run, configure a GitHub branch rule for
the production branch (Settings → Rules → Rulesets): require a pull request and
require this status check to pass. Set the rule to Active and do not grant bypass
access if it should apply to everyone. This is a one-time repository setting,
not a setting each clone needs. The workflow alone reports failures after push;
it does not reject pushes or stop independent Pages/Vercel deployments. Requiring
the check before merging keeps invalid changes off the protected production branch.

## Optional local early warning

The pre-push hook checks `chat/static/chat.js` in each branch/tag tip being pushed,
not the working copy. It blocks localhost, loopback, private-network addresses,
and unrecognizable URL assignments. Commented-out `//` alternatives are ignored.
Keep `CHAT_API_URL` as one plain, single-line quoted HTTP(S) URL.

Requires Node.js. Enable once in each clone, from the repository root:

```sh
git config --local core.hooksPath .githooks
```

Local, uncommitted API URL changes are fine. Before pushing, commit the deployed
API URL. The hook checks final snapshots, not every intermediate commit.

This is an accidental-push safeguard, not a GitHub-enforced security boundary:
Git hooks are local and can be bypassed with `--no-verify`. New clones must enable
the hook themselves. Check for existing hooks before changing `core.hooksPath`.
