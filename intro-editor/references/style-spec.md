# Style Spec — Samin's Intro Editing Grammar

Extracted from the reference video (YouTube `lH5wrfNwL3k`, indexed in Jockey knowledge store
`ks_019f8be4-fe4c-70d3-a16e-78afc77b70ea` as item `ksi_019f8be7-8aab-7880-8e93-63e6e955bc69`).
Timestamps below are from that video — re-extract frames with ffmpeg if you need to see any of them again.

## The two layers

- **Audio spine:** the talking-head take's voice runs continuously. Inserts never bring their own audio (screen recordings are muted or ducked to silence).
- **Visual layer:** alternates between the camera and full-screen inserts. During almost every full-screen insert, a small rounded-corner PiP bubble of the speaker sits in a bottom corner (usually bottom-right, ~12–15% of frame width) so the viewer never loses the person.

## Cold open formula (0:00–0:14 in reference)

Before any talking-head shot: a rapid montage of *proof* — the end result of what the video teaches.
Reference sequence: animated performance chart with profit callouts (+15.5% / +34.8% / +$9,650) → brand icon beat → dark product dashboard screen recording → light-UI setup form screen recording. Cuts every ~2 s, PiP present. The opening VO lines play underneath.

Verified via Jockey: those proof visuals are harvested from much later in the same video — the 8:11–8:46 order confirmation, 20:37–21:30 and 24:28–24:56 strategy-beats-S&P graphs, 34:06–35:05 automation demo. When editing a new video, search the full footage for equivalent "it works" moments and pull them forward.

Cold-open VO structure (0:00–0:15): bold claim ("Claude just changed how we trade stocks forever") → what it concretely does ("access live market data, track what whales and politicians are buying... automatically") → credibility ("I've been using this for the past couple of weeks"). First full-screen camera shot appears only after the montage (~0:14).

## Verified intro anatomy (from Jockey beat map)

- 0:00–0:14 — cold open proof montage over hook VO
- 0:14–0:21 — first camera appearance: personal result claim + "three levels" promise
- 0:21–0:47 — roadmap on agenda cards (1 Setup / 2 Copy-trading bot / 3 Options), each card holds ~5–9 s while that level is described
- 0:47–0:56 — camera: accessibility claim ("beginners can do this, it's just talking to Claude") + transition
- 0:56–2:39 — "Why this matters" context block: story-dense, alternates illustration ↔ camera
- 2:39–2:41 — "LEVEL 1: SETUP" title card; intro ends at "All right, let's build this thing" (~2:41)

## The story rhythm (illustration ↔ camera punchline)

Consistent pattern in the context block: a story beat plays over an illustration (~6–11 s), then the video cuts BACK to full-screen camera for the conclusion/punchline of that story ("You would never sit at a table like that", "Wall Street avoids that problem"). Emotional peaks land on the speaker's face, not on b-roll. Claims that follow stories stay on camera; the next story starts the next illustration.

## Insert taxonomy (with reference timestamps)

| Treatment | When the speech... | Looks like | Ref examples |
|---|---|---|---|
| `screen-rec` | names a tool, shows a result, "I built/ran/got..." | real product UI, cursor visible, muted; full-screen with PiP | 0:04–0:12 dashboards; 1:58 Claude prompt; 2:14 order confirmation; 2:38 Alpaca form |
| `stat-graphic` | states a number, comparison, or abstract claim | motion graphic on white grid-paper background: big number bubbles ("$50M single trade"), simple line/pie charts, hand-drawn-style icon clusters, orange/blue accent | 0:00 chart; 1:12–1:16; 2:20; 2:44–2:52 icon sequences |
| `illustration` | tells a story or paints a scene ("when I was at...", "brokers used to...") | AI-generated scene matching the story's era/mood. Styles rotate: pixel-art (poker game 1:18–1:26, restaurant 2:04, retro terminal 3:56), comic/cartoon (trading floor 1:34–1:46, office 2:24), sepia vintage (phone broker 2:58–3:04), realistic-painterly (JPMorgan office 1:04–1:10). Often carries a caption of the key sentence | see timestamps |
| `agenda-card` | lays out what's coming ("first..., then..., finally...") | numbered cards on grid paper: big blue circled number + label + device mockup screenshot of that section ("1 Setup", "2 Building a copy trading bot", "3 Options"), 0:20–0:48 | |
| `title-card` | poses a question or opens a section | big text on white/grid ("Why this matters?" 0:56) or huge outlined numerals ("LEVEL 1: SETUP" 2:54) | |
| `camera-punch` | emphasis, punchlines, direct address | same take cropped ~15–25% tighter (jump-cut zoom); also used to break up long camera stretches | throughout |
| `overlay-only` | a key phrase worth reinforcing while staying on camera | small graphic or numbered bubble popped near the speaker's gesture (yellow "1" bubble 3:40); caption text | |

## Pacing rules

- Insert lengths: graphics 2–4 s, screen recordings and illustrations 4–8 s.
- Camera holds: typically 6–15 s between inserts; hard ceiling ~20 s. After ~3 min the density relaxes (main content begins) — intros are the dense zone.
- Cut *on* the sentence: an insert starts within ~0.5 s of the phrase that motivates it and ends when the thought ends. The visual must literally match the sentence under it.
- Return to camera between insert clusters — don't chain 4+ inserts without showing the speaker full-screen, except in the cold open.
- Vary punch-in level on consecutive camera segments (wide → tight → wide) to hide jump cuts.

## Text & captions

- Key quotable sentences appear as caption text on inserts (white, sentence case, centered low or contextual).
- Section questions get their own title cards rather than captions.
- Numbers on stat graphics are big and few — one figure per graphic beat.

## Asset generation prompts

When generating illustrations, match one of the rotating styles and describe the *story beat*, not the topic:
- Pixel-art: "16-bit pixel art, warm palette, [scene: man checking a stock app over dinner in a cozy restaurant]"
- Comic: "flat comic illustration, muted colors, [scene: analysts pointing at charts on a night trading floor]"
- Sepia vintage: "1960s sepia office illustration, [scene: broker taking orders on a rotary phone at a paper-covered desk]"
Stat graphics live on a white grid-paper (graph paper) background with blue/orange accents and hand-drawn-style icons.

## PiP bubble spec

Rounded-rect (near-squircle) crop of the live camera take, ~200–260 px wide at 1080p, bottom-right with ~24 px margin (bottom-left if the insert's focal content is right-heavy). Present on all full-screen inserts including title cards; absent only on full-screen camera.
