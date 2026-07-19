# Seedance 2.0 (ByteDance) — Prompting Guide

Confidence: **high**. Rules below are confirmed by ByteDance's own site and/or two-plus independent hosting-partner docs (Replicate, fal.ai, BytePlus ModelArk), each cross-checked in adversarial verification.

## Core rule: specificity over mood-words

Seedance's own guidance is blunt: *"Be specific — describe camera movements, lighting, mood, and specific actions for best results."* Vague adjectives ("epic", "beautiful", "cinematic") without a concrete camera/light/action anchor under-perform. Every prompt should name:

- **Camera movement** — e.g. "slow dolly-in", "handheld tracking shot", "rack focus from foreground to subject"
- **Lighting** — e.g. "golden-hour rim light", "cold blue window light", "practical neon glow"
- **Mood** — one clear adjective, not a pile of them
- **Specific action** — what the subject is doing, not just what the subject is

Example:
> Bad: "a man in a kitchen, cinematic, moody"
> Good: "handheld tracking shot follows a man chopping vegetables in a dim kitchen, single warm pendant light overhead, focused and quiet mood"

## Known quirk: avoid the word "fast"

Documented directly in Seedance's own prompt-guide docs: the word **"fast"** in a prompt causes visible jitter/instability in the output. If tempo matters, describe **one element** as fast rather than pushing the whole scene:

> Instead of: "the car speeds fast down the fast highway"
> Use: "the car accelerates hard, tires screeching, down the highway" (motion conveyed through verb choice, not the word "fast")

## Dialogue and lip-sync

For any spoken line, wrap it in double quotes inside the prompt — Seedance generates matching lip movement and voice from it:

> `The man stopped and said: "Remember this moment."`

Practical constraints that make lip-sync land well:
- Keep spoken lines short — **5–10 words**. Longer lines degrade sync accuracy.
- Use a **medium close-up**, roughly static camera, **frontal angle** on the speaking subject. Heavy camera movement or side angles during dialogue reduce lip-sync reliability.

## Multi-shot sequences within one clip

Seedance 2.0 can generate what reads as a cut sequence — multiple shots with natural transitions — inside a single up-to-15s clip. To signal a cut, use the literal phrase **"Cut scene to..."**:

> "Wide shot of the storefront at dusk. Cut scene to a close-up of hands unlocking the door."

This is stronger than just describing two things happening — it's the documented trigger phrase for a clean transition rather than a blended/morphed one.

## Multi-reference input (@-labeled references)

Seedance 2.0 accepts multiple reference media in one generation, referenced by label inside the prompt text:

> "The character from [Image1] performs the dance from [Video1]"

Confirmed capability from ByteDance's own site. Use this when the brief needs a specific character/product (image reference) combined with specific motion (video reference) or specific dialogue timing (audio reference).

## Strength: complex camera work

Seedance 2.0 is comparatively strong (medium-confidence, hosting-partner-sourced) at dolly-zooms, rack-focus, tracking shots, and POV changes — lean into named camera moves rather than simple static framing when the brief calls for production polish.

## Claims checked and rejected — do not use these

These looked plausible but failed adversarial verification (2-vote-refute or worse) during the July 2026 research pass. Do not present them as fact:

- ❌ A fixed "Subject + Action + Camera + Scene/Lighting + Style" formula with an ideal 50–150 word length — **not confirmed**, treat prompt length as flexible and driven by what the shot actually needs.
- ❌ A hard requirement to use square-bracket notation for every reference (`[Image1]` etc.) — the @/bracket labeling exists (see above) but no confirmed rule makes it *mandatory* for all reference use.
- ❌ Specific resolution/duration/aspect-ratio claims from third-party blog posts — for exact current values, check the live schema instead: `higgsfield model get seedance_2_0`.
- ❌ Blanket claims about physics realism (fabric tearing, fight-scene realism) — unconfirmed, don't promise this to the user as a guaranteed strength.
