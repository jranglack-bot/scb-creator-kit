# Beispiel: Schreibtisch bei Nacht

Der Test vom 17.09.2026, vollständig. Motiv passend zu „KI-Content ohne
Gesicht": ein Schreibtisch bei Nacht, in der Mitte ein Handy, über dem Herzen und
Benachrichtigungen aufsteigen. Ohne Personen, ohne Schrift, Format 9:16.

Ergebnis: Papierbild und Storyboard auf Anhieb sauber, beide in 752 × 1344.
Kling lief durch (17,5 Credits). Seedance blockte zweimal, solange das Papierbild
als zweite Referenz dabei war, und lief dann mit dem Storyboard allein durch
(45 Credits). Bei jedem Prompt steht, was davon wörtlich getestet ist.

## Schritt 1: Papierbild

Die Szene ist wörtlich aus dem Test. Der Satz zum Bildaufbau und der Stilblock
sind die Fassungen aus SKILL.md; der Test lief mit einem Stilblock gleichen
Inhalts aus einem fremden Prompt-Paket und noch ohne den Bildaufbau-Satz. Den
braucht es: Im Test stand der Handyständer knapp im unteren Fünftel, Lampe und
Tasse lagen rechts unter Instagrams Knöpfen. Nebensachen dürfen dort liegen, das
Hauptmotiv nicht.

```
A vertical 9:16 illustration of a cozy creator desk at night, as a handcrafted torn-paper collage. In the background a large window shows a deep muted navy night sky with a pale crescent moon, a few tiny stars and a distant city skyline of dark blue building silhouettes with small warm lit windows; the wall around the window is dark slate blue. The lower third is a warm muted wooden desk surface. On the desk: a small potted plant with rounded green leaves at the far left, an open laptop angled on the left with a softly glowing pale blue blank screen, a desk lamp on the right casting a warm amber cone of light, and a white coffee mug next to the lamp. The hero in the center foreground is a smartphone standing upright in a small stand, its screen glowing soft cornflower blue with one large white heart icon in the middle. Rising above the phone into the upper middle of the frame float three rounded cornflower-blue notification bubbles, each holding a single white icon (a heart, a small shopping bag, a speech bubble), surrounded by a few small muted coral paper hearts. No people. Keep the main subject and every important detail inside the central area of the frame: nothing important in the top seventh, in the bottom fifth or along the right edge. Handmade torn-paper collage look. Each element is a separate flat piece of paper, cut or torn by hand, with ragged white-fibred edges and a small hard shadow where it lies on the layer below. Paper grain is visible on every surface. Thin gaps of white paper show between neighbouring pieces. Colours are muted and slightly faded like matte craft paper, lit by soft light from one side. No gradients, no clean vector shapes, no glossy or plastic 3D surfaces. No text, no letters, no numbers, no logos anywhere.
```

## Schritt 2: Storyboard

Wörtlich aus dem Test, mit dem Papierbild als `--image`:

```
A clean storyboard sheet: a 3x3 grid of 9 sequential vertical panels with thin white borders, read left to right and top to bottom, showing the scene from the reference image assembling itself piece by piece out of torn paper, always with the same fixed framing. Panel 1: a near-empty frame of plain paper, only the first dark slate blue wall pieces sliding in from the top corners as torn paper. Panel 2: the deep navy night-sky window panes and the window frame slide in from the top and sides. Panel 3: the pale crescent moon and tiny stars drop into the sky while the dark blue city skyline with small warm lit windows rises up inside the window. Panel 4: the warm wooden desk surface slides up from below in layered torn strips. Panel 5: the potted plant, the open laptop with its pale blue screen, and the dark desk lamp slide in from the left and right sides. Panel 6: the warm amber cone of lamp light and the white coffee mug settle into place. Panel 7: the phone stand drops onto the center of the desk and the phone body slides into it, its screen still empty and dark. Panel 8: the cornflower-blue screen and the white heart icon press into the phone, and the first notification bubble with the heart drops in above it. Panel 9: the complete finished composition exactly matching the reference image, with all three notification bubbles (heart, shopping bag, speech bubble) and the small coral paper hearts in place. Every panel keeps the same handcrafted paper-cut look: rough torn edges, visible paper grain, hard shadows, rough white negative-space slivers, and the same muted navy, wood brown, amber and cornflower-blue palette. Absolutely no text, no labels, no captions, no frame numbers and no writing in any panel.
```

Im Ergebnis lagen die senkrechten Trennlinien oben bei 263 px, in den beiden
unteren Zeilen bei 238 px. Genau dafür sucht `feld_ausschneiden.py` die Spalten
je Zeile getrennt.

## Schritt 3a: Kling

Wörtlich aus dem Test. Startbild war Feld 1 (dunkle Wand mit zwei gerissenen
Stücken oben), Endbild das Papierbild, `--mode std --sound on`:

```
Handcrafted stop-motion paper collage animation, the camera stays completely still. Starting from the dark blue paper wall, the scene builds itself piece by piece out of flat torn paper cutouts that slide and drop in from outside the frame in choppy stop-motion steps: first the navy night-sky window and its frame drop in from above, then the pale crescent moon, tiny stars and the dark blue city skyline with small lit windows appear inside the window, then the wooden desk slides up from below in layered torn strips, then the potted plant and the open laptop slide in from the left and the dark desk lamp swings in from the right, then the amber lamp light and the white coffee mug settle in, then the phone stand drops onto the desk and the phone drops into it, its blue screen and white heart icon settling on, and finally three blue notification bubbles and small coral paper hearts drop in above the phone. Every piece is a rigid flat paper cutout with rough white torn edges, visible paper grain and a crisp drop shadow, arriving one after another with tiny misalignments and staggered timing. No morphing, no cross-fade, no dissolve, no folding, no smooth digital motion. Sound: quiet paper foley only, soft paper slides, taps and drops, no music, no voice.
```

## Schritt 3b: Seedance

Einleitung und Aufbau wörtlich aus dem Lauf, der durchging. Der Satz nach
„no camera movement" und alles ab „At the end" sind die Fassungen aus SKILL.md;
der Test lief dort mit gleichbedeutenden Sätzen aus dem fremden Prompt-Paket.

```
[Image1] is a 3x3 storyboard sheet: use its nine panels, read left to right and top to bottom, only as the order of the assembly; never show the grid, the borders or several panels at once, the video is one single continuous full-frame shot. Its last panel is the finished scene the video must end on. Static locked-off camera, no camera movement. Handcrafted stop-motion paper collage animation: the scene builds itself piece by piece out of flat torn paper cutouts that slide and drop in from outside the frame in choppy stop-motion steps. The frame starts on plain paper. The dark slate blue wall slides in from the top corners and the sides as overlapping torn paper panels. The deep navy window panes and the window frame drop in from above. The pale crescent moon and tiny paper stars drop into the sky while the dark blue city skyline with small lit windows rises from below inside the window. The wooden desk surface slides up from below in layered torn paper strips. The potted plant and the open laptop with its pale blue screen slide in from the left, and the dark desk lamp swings in from the right, each with a crisp paper drop shadow beneath it. The amber cone of lamp light drops into place and the white coffee mug slides in from the right. The phone assembles last in the center, piece by piece: the dark stand drops onto the desk, the phone drops into its stand, the cornflower-blue screen piece settles onto the phone, then the white heart icon settles onto the screen. Above the phone the three cornflower-blue notification bubbles drop in from above one after another, the heart bubble first, then the shopping bag bubble, then the speech bubble, followed by the small coral paper hearts. At the end every piece settles into place with small, slightly uneven nudges. Every piece is a rigid flat paper cutout with rough white torn edges, visible paper grain and a crisp drop shadow, arriving one after another with tiny misalignments and staggered timing. No morphing, no cross-fade, no dissolve, no folding, no smooth digital motion. Sound: quiet paper foley only, soft paper slides, taps and drops, no music, no voice.
```
