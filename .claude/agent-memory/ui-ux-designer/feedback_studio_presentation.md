---
name: studio-presentation-preferences
description: The Star Colonel's presentation bar for the henryk-media studio page - local short times, file names not paths, no stale progress, GalaxaLabs design language
metadata:
  type: feedback
---

On 2026-10-28 the Star Colonel judged the studio page "terrible terrible ux, even date time presentation is just sloppy". He wants times as "27 Oct 2026, 22:30" in local time (no ISO text, no seconds, no offset), photos named by file name only (never a job folder path), no progress bar or "Stage: done" on finished jobs, results at one fixed height, and links as design-language buttons.

**Why:** the Jobs panel showed every setting as one bold sentence, raw paths, ISO timestamps and a 100 % bar on done jobs; he read this as sloppy.

**How to apply:** for any studio UI work, follow the GalaxaLabs design language (tokens summarised in tmp/workflows/studio/design-tokens.md) and the spec tmp/workflows/studio/ux-spec.md. Where the DL conflicts with his explicit order (the DL wants relative times), his order wins. Labels must be literal, because he reads every word literally. See [[live-photo-believability-bar]] for the media side.
