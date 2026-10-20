# Run Brief: hub-img-sizes

## Ask
"take the hub items" (the two hub issues filed 2026-10-19 evening, #248 and #249; the third hub task, the GSC recheck, is dated Nov 1 and out of scope), then "unattended please".

## Source
- **Kind:** issue list
- **Location:** 626Labs-LLC/626Labs-LLC.github.io#248, #249; dashboard tasks task-1792462985402-b6ng54vqw and task-1792462985403-rptuwsszf

## Intent
Every generated product page reserves its images' boxes so nothing jumps as captures load, and the Sanduhr page test pins its gallery instead of flooring it.

## Done when
- Every `<img>` a generated product page emits for a local file carries `width` and `height`; all 14 pages re-render and `--check` is clean; a test holds the rule.
- The Sanduhr page test asserts each gallery and showcase item in its pageSpec renders exactly once; the platforms-block test comment says what is true.

## Out of scope
- The GSC recheck task (dated 2026-11-01).
- Images in hand-authored pages, the home page, plugin pages: the issue names the product-page renderer only.
- Any change to the CSS that sizes images (`width:100%; height:auto` stays; the attributes only reserve the ratio).

## Inferred
- Remote or missing image files get no attributes rather than a fetch at render time (from: the renderer never touches the network; `shots` already emits sizes only when the uploader metadata has them).
- The hero app icon gets the attributes too, though CSS fixes it at 128px (from: the issue says every img; harmless).
- #249's second half is stale: `content/site.json` line 2551 gives `rororo` a `platforms` block, so the block is live-rendered (from: grep at planning).
- Base is `origin/main`, checkout 0 behind (from: `git rev-list`).

## Mode
- **Mode:** Unattended
- **Triggered by:** builder confirmed the late-window recommendation (21:43 local, 2 items): "unattended please"
