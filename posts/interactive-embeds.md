---
title: interactive embeds
date: 2026-08-30
category: Meta
tags: [meta]
excerpt: the blog can now embed interactive apps — starting with a leader election simulator
---
# why
I want to start writing about the internals of distributed systems (airflow, kubernetes, consensus protocols, etc), and those
systems read much better when you can actually poke them. So the build system now supports embedding interactive apps
directly inside posts.

# how
Each app is a single self-contained html file under `apps/`, embedded with one directive in the markdown source:

```markdown
<!-- app: leader-election height=400 caption="kill a node and watch re-election" -->
```

The directive renders the app below in a lazy iframe that auto-resizes via postMessage, so it stays mobile friendly.
Apps get the site's light/dark scheme for free by keeping a transparent background and `color-scheme: light dark`.

# the demo
A leader election sim. The leader pulses heartbeats to every follower; killing the leader starts a timed election
race (randomized timeouts, first candidate to gather a majority wins). Click a node to kill or revive it, or drag the
election timeout below the heartbeat interval to watch the cluster flap.

<!-- app: leader-election height=400 caption="leader election — click a node to kill or revive it" -->

# notes
External embeds work too with `<!-- embed: <url> -->`. Scratch or draft posts named with a leading underscore
(`_draft.md`) are skipped by the builder.
