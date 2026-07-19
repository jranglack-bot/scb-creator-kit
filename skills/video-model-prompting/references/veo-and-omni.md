# Google Video Models: Gemini Omni Flash vs. Veo 3.1 — Prompting Guide

Confidence: **high** for the model split and the Veo 3.1 formula (Google's own docs, cross-checked 3x). **Medium** for the Gemini Omni Flash usage characterization (partly Higgsfield-blog-sourced).

## First: which model is "Omni"?

If a user says "Google Omni" or just "Omni", they almost always mean **Gemini Omni Flash** — a standalone Google DeepMind model launched May 2026 (Google I/O), **separate from Veo 3.1**, not an alternate name for it. Google's own API docs explicitly recommend Gemini Omni Flash as the *default* model for video generation, reserving Veo 3.1 for cases that need its specific strengths (below). Higgsfield lists both as distinct models in its catalog — don't conflate them.

**Quick disambiguation when unsure:** ask what the task actually needs.
- Generating a new clip fast, or iteratively editing/tweaking an existing clip via natural-language instructions → **Gemini Omni Flash**
- Cinematic single-shot quality, native audio, scene extension, or frame-exact first/last-frame control → **Veo 3.1**

## Veo 3.1 — the five-part formula

Google's official Veo 3.1 prompting guide (Google Cloud blog) specifies a fixed five-part structure, in this order:

```
[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
```

Example:
> "Slow dolly-in, shallow depth of field. A barista steams milk behind a chrome espresso machine. Steam curls upward as she taps the pitcher twice. Warm, softly lit café interior, morning light through a front window. Muted color grade, quiet documentary-style ambiance."

### Camera terminology categories (use these vocabularies explicitly)

- **Camera movement:** dolly, tracking, crane, aerial, slow pan, POV
- **Composition:** wide shot, close-up, extreme close-up, low angle, two-shot
- **Lens/focus:** shallow depth of field, wide-angle lens, soft focus, macro lens, deep focus

Naming the category explicitly (not just "nice camera work") is what the official guide models — pick one term from each relevant category rather than inventing loose descriptive language.

### Multi-shot in one generation: timestamp prompting

Veo 3.1 supports timestamp-based prompting to control a multi-shot sequence with exact timing inside a single generation call:

```
[00:00-00:02] Medium shot, barista steaming milk, dolly-in.
[00:02-00:05] Cut to close-up of hands pouring latte art.
[00:05-00:08] Wide shot, customer takes the cup, warm smile.
```

Use this instead of chaining separate generations when the brief needs precise pacing across several beats within one clip.

### When to pick Veo 3.1 specifically

- Native audio generation is required
- The brief needs scene/video **extension** of existing footage
- Frame-exact control matters — first/last-frame anchoring, up to 3 reference images
- Top-tier cinematic single-shot fidelity is the priority over speed/iteration

## Gemini Omni Flash — conversational, iterative editing

Gemini Omni Flash is best understood as a multimodal, **conversational** editing system rather than a one-shot generation model. Its core strength is iterating on an *existing* clip via natural-language instructions — no timeline, no masking, just describing the change:

> "Make the lighting warmer and have her smile at the end instead."

It maintains scene consistency across a short run of sequential edits. In Higgsfield's own Interactions API this held up for roughly 3 sequential edits with session context before context degradation was observed — so treat a long chain of successive tweaks with some caution; if the 4th or 5th edit starts drifting from earlier ones, consider starting a fresh generation from a clear composite prompt instead of continuing to patch.

### When to pick Gemini Omni Flash specifically

- The user has a clip and wants to *change* something about it via description, not re-generate from scratch
- Fast, low-friction generation is more important than cinematic polish
- Google's own docs position it as the default video model — reach for it first for straightforward video generation asks, and reserve Veo 3.1 for the specific needs listed above

## Practical takeaway for prompt-writing

- Writing a **new Veo 3.1** prompt → use the 5-part formula and named camera-terminology categories above.
- Writing a **new Gemini Omni Flash** prompt → plain natural-language description is fine; it doesn't need Veo's rigid formula.
- **Editing an existing clip** → Gemini Omni Flash, phrased as a direct instruction/change request, not a from-scratch scene description.
