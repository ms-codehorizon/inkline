# Stage 05: Post

**Job:** thumbnail and post text for the approved video.

## Inputs

| Source | File/Location | Why |
|---|---|---|
| Approved video | `../04-render/output/` | What is being posted |
| Style | `../../../../_config/style.md` | Thumbnail look |

## Process

1. From the factory root run `python3 engine/thumb.py <slug>` and pick the strongest frame with the author.
2. Draft the post: short, simple words, human, no em dashes, no hashtag pile.
3. Say plainly that it is a fictional sketch. If the post mentions ICM, describe only what this workspace really does.

## Audit

- [ ] Post reads like a person wrote it
- [ ] No claim the video or workspace does not back up
- [ ] Nothing published automatically

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Thumbnail | `output/thumbnail.png` | 1920x1080 PNG |
| Post text | `output/post.md` | Markdown |

## Completion

The author approves and posts it. STOP.
