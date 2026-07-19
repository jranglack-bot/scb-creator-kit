# Kling 3.0 (Kuaishou) — Prompting Guide

Confidence: **low / honest gap**. Say so to the user when writing a Kling 3.0 prompt — don't present the guidance below as confirmed Kling-specific best practice.

## What the July 2026 research found

A 104-agent deep-research pass specifically looked for Kuaishou's own official Kling 3.0 prompting documentation and could not find or verify any. Two plausible-sounding claims were tested and both were **rejected** during adversarial verification:

- ❌ "Kling 3.0's recommended prompt structure follows a fixed narrative order: setting/subject → action/movement → camera/lighting → style/mood." — the only source (a third-party blog, seavidgen.com) failed verification (0-vote-confirm, 3-vote-refute).
- ❌ "Kling 3.0 has an explicit 0–3 motion-intensity parameter that must be set deliberately or it defaults to slow-motion." — same source, same rejection.

**Do not repeat either of these as fact.** If you've seen them elsewhere (blog posts, community guides), treat them as unverified until a primary Kuaishou source turns up.

## What's actually confirmed (technical parameters, not prompt wording)

From Higgsfield's own model catalog — this is real and usable, just not about prompt *phrasing*:

- Kling 3.0 is positioned as the **cheaper Seedance 2.0 substitute** for single-plane scenes that don't need heavy motion
- Supports multi-shot, audio sync, motion transfer
- Aspect ratios: `16:9`, `9:16`, `1:1`
- Duration: 3–15s
- Modes: `pro` / `std`
- Sound: `on` / `off`
- Media roles: `start_image`, `end_image`

For the current live values (these can drift), run `higgsfield model get kling3_0`.

## Working approach until Kuaishou publishes real guidance

Fall back to general, model-agnostic video-prompt principles rather than inventing Kling-specific rules:

- Name the subject, setting, and action in clear, concrete language — avoid vague mood-only adjectives
- Describe camera position/movement explicitly if it matters (Kling doesn't have confirmed camera-terminology docs, so plain language like "camera stays still, low angle" is safer than assuming it recognizes the same vocabulary Veo or Seedance do)
- Keep the prompt reasonably short and sensory rather than long and abstract
- Since it's positioned for **low-dynamics, single-plane scenes**, don't ask it for heavy multi-shot action the way you might with Seedance — pick Kling for the calmer end of a brief, not the complex end

## Set expectations honestly

Tell the user plainly, in the moment: *"Für Kling 3.0 gibt es keine offizielle Kuaishou-Prompt-Dokumentation, die ich verifizieren konnte — ich wende generische Videoprompt-Prinzipien an. Der erste Versuch ist eher ein Test; wir iterieren nach dem Ergebnis."* Then treat the first generation as a calibration run rather than promising it will land the first time — that's a materially different commitment than what you'd say for Seedance or Veo 3.1, where the guidance is confirmed.

If you or the user later find Kuaishou's own documentation (official developer portal, model card, or similar primary source), this file should be the first thing updated — replace this whole "gap" framing with the confirmed rules.
