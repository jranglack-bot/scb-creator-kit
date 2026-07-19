---
name: video-model-prompting
description: Deep, model-specific prompt-engineering guidance for AI video generation with Seedance 2.0, Kling 3.0, Google Veo 3.1, and Gemini Omni Flash — the models exposed via the higgsfield-generate skill. Use this whenever the user asks for a video prompt, wants to generate/edit a video with one of these models, asks "what's the best way to prompt X for video", is unhappy with a video generation result and wants to improve the prompt, or needs help picking between these models. Trigger even if the user doesn't name the model explicitly but describes a video generation task (Reel, ad, UGC clip, product video) that will route through higgsfield-generate — load this skill BEFORE writing the prompt, not after a bad result. Each model has real, documented quirks (e.g. Seedance jitters on the word "fast") that a generic video prompt will trip over.
---

# Video Model Prompting

Each AI video model has its own prompting dialect. A prompt tuned for one model can under-perform or actively misfire on another — Seedance 2.0 jitters on the word "fast"; Veo 3.1 expects a fixed five-part formula; Kling 3.0 has no confirmed official guide at all. Guessing a shared "generic video prompt" style wastes the generation (time + credits) and produces mediocre output. This skill exists so you don't have to relearn these quirks by trial and error each time.

**Relationship to `higgsfield-generate`:** that skill handles model selection, the CLI mechanics, and generic Higgsfield-wide prompting basics (`references/prompt-engineering.md` there). This skill is the deep layer — model-specific prompt *wording* rules for the four models below. Consult both: pick the model with `higgsfield-generate`, then write the actual prompt text using this skill.

## Step 1 — identify the model, then read its reference file

Do not try to hold all four models' rules in your head at once — read only the file for the model in play. This keeps you from cross-contaminating Seedance rules into a Kling prompt or vice versa.

| Model | When it's the pick | Reference file |
|---|---|---|
| **Seedance 2.0** | Default for serious motion, multi-shot, cinematic, image-to-video | `references/seedance-2.0.md` |
| **Veo 3.1** | Cinematic quality, native audio, scene extension, frame-exact reference control | `references/veo-and-omni.md` |
| **Gemini Omni Flash** | Conversational iterative editing of an *existing* clip, no timeline/masking | `references/veo-and-omni.md` |
| **Kling 3.0** | Cheaper Seedance substitute, single-plane scenes without heavy motion | `references/kling-3.0.md` |

If the user says "Google", "Omni", or "Gemini" without specifying which, don't guess — `references/veo-and-omni.md` opens with exactly this disambiguation (they are two separate models with different jobs), read it before asking or assuming.

## Step 2 — apply the model's rules, don't paraphrase them away

Each reference file gives concrete phrasing rules (not vague advice like "be descriptive"). Follow them literally — they come from verified vendor documentation or, where marked, from adversarially-verified secondary sources. Where a reference file says a claim was **checked and rejected** during verification, do not reintroduce it — those are listed precisely so you don't repeat a plausible-sounding but false "best practice" picked up from a stray blog post.

## Step 3 — flag confidence honestly

The three models are not equally well-documented (see the confidence markers inside each reference file). When you write a prompt for a model with confirmed official guidance (Seedance 2.0, Veo 3.1, Gemini Omni Flash), state your prompt choices with normal confidence. When you write a prompt for **Kling 3.0**, say plainly that no official prompting guide exists and that you're applying generic video-prompt principles rather than Kling-specific ones — then treat the first generation as a test, and suggest a quick iteration rather than promising it'll be optimal on the first try.

## Step 4 — after generation, close the loop

If the user reports the result was off (wrong pacing, jitter, flat delivery, lost lip-sync), check the relevant reference file's "Common mistakes" section before proposing a fix — the failure is often a named, already-documented quirk (e.g. Seedance + "fast") rather than something to guess at freshly.

## Research provenance

This skill's Seedance 2.0 and Veo 3.1 / Gemini Omni Flash content comes from a 104-agent deep-research pass (July 2026) that fetched 22 sources and adversarially verified 25 extracted claims (3-vote confirm/refute per claim). Kling 3.0 content is explicitly a documented gap — see `references/kling-3.0.md` for what was checked and rejected. If Kuaishou publishes official Kling 3.0 prompting documentation later, that reference file should be the first thing updated.
