# Defects

Observed wrong behaviour in henryk-media, with the trail of what was tried against it.

## Authors

- `@kj` Konrad Jelen

## Animation module `ANIM`

The AdvancedLivePortrait keyframe module and its tests

- log: 2026-10-24T22:39:59Z @kj category created

- [x] `DEF-ANIM-1-YAW-TURNS` **yaw turn test unpacks pairs as triples** - MAJOR; make test fails with ValueError: not enough values to unpack (expected 3, got 2); cause: itertools.pairwise yields 2-tuples and the loop names three values; fix: zip three consecutive slices; tests/test_animation.py
  - evidence: make test: 26 passed in 1.65s; make lint: ruff format and check clean
  - repro: make test, read test_yaw_turns_every_1_to_1_5_s_within_its_peak
  - test-tags: UNIT
  - root-cause: 2026-10-24T22:39:59Z @kj itertools.pairwise(yaw[1:]) yields (a, b); the comprehension unpacks (before, here, after)
  - log: 2026-10-24T22:39:59Z @kj added
  - log: 2026-10-24T22:41:52Z @kj closed: fixed: itertools.pairwise replaced by zip of three consecutive slices in tests/test_animation.py
- [-] `DEF-ANIM-3-WALK-GIFT` **man walks and presents the gift in the LTX-2.5 clip** - MAJOR; the man walks instead of standing in place and presents the gift box instead of holding it steady; the Star Colonel said "he is walking, not standing in place, he shows the present he holds in his hand"; cause under investigation
  - repro: open tmp/media/ltx25-i2v/IMG_0020.mp4: the man walks forward and lifts the gift box to show it instead of standing still and holding it steady
  - test-tags: MANUAL
  - log: 2026-10-25T04:45:13Z @kj added
  - log: 2026-10-25T04:45:20Z @kj reported: round-one preview; prompt tmp/workflows/ltx25-preview/prompts/IMG_0020.json; settings LTX-2.5 22B dev, seed 42, 30 steps, euler, cfg 3.0, 768x1024, 150 frames at 30 fps, 5.00 s; full values tmp/workflows/ltx25-preview/render-settings.json
  - log: 2026-10-25T04:48:46Z @kj rejected: Star Colonel confirmed at 05:52 the man walking and showing the gift box is what he wants: "wait I want for man to walk!" and "problem was with the fact that he was NOT walking"; the prompt that told him to stand still was the error, not the clip
- [x] `DEF-ANIM-4-BLANK-DRAWING` **drawing hand scribbles in one spot and the paper stays blank in the LTX-2.5 clip** - MAJOR; the paper stays blank; the raised hand scribbles in one spot at the top of the canvas; the Star Colonel said "nothing appears on the canvas, and his movements of the hand shoild be around drawing big shapes, not scribbling at the top of the canvas"; cause under investigation
  - evidence: /home/lab/workspace/private/henryk/henryk-media/tmp/media/ltx25-i2v/IMG_8076-h3.mp4 - judged good at 2026-10-25 07:00: "h3 made it quite well"
  - repro: open tmp/media/ltx25-i2v/IMG_8076.mp4: the paper stays blank and the raised hand scribbles in one spot at the top of the canvas instead of drawing big shapes
  - test-tags: MANUAL
  - log: 2026-10-25T04:45:16Z @kj added
  - log: 2026-10-25T04:45:20Z @kj reported: round-one preview; prompt tmp/workflows/ltx25-preview/prompts/IMG_8076.json; settings LTX-2.5 22B dev, seed 42, 30 steps, euler, cfg 3.0, 768x1024, 150 frames at 30 fps, 5.00 s; full values tmp/workflows/ltx25-preview/render-settings.json
  - log: 2026-10-25T05:16:52Z @kj attempted: round two tmp/media/ltx25-i2v/IMG_8076-round2.mp4 - the pale mark appeared but the crayon never left the top edge, so he still paints in one place; Star Colonel: "boy still paints in one place while he'd be drawing oval shapes leaving crayon mark (dark) across entire canvas"
  - log: 2026-10-25T06:04:01Z @kj LTX-2.5 did not reach the requirement in three prompt rounds, H3 did; the new people gate found nothing
  - log: 2026-10-25T06:04:01Z @kj closed: H3 clip judged good by the Star Colonel
- [x] `DEF-ANIM-6-SPEECH-CHILD` **IMG_7666 clip speaks and redraws the background child** - MAJOR; Henry's mouth moves as if speaking, and the background child is redrawn standing forward with a ball, larger than in the source, so she reads as another child
  - evidence: the Star Colonel viewed the new clips on 2026-10-25 and both pass - H3 data/processed/henryk-urodziny-2026/minimax-h3/IMG_7666.mp4 and LTX tmp/media/ltx25-i2v/IMG_7666.mp4; the prompt holds the photo's face, the lips and teeth, and names no speech
  - repro: open data/processed/henryk-urodziny-2026/minimax-h3/IMG_7666.mp4, 1024x768, 150 frames, beside data/processed/henryk-urodziny-2026/extended/4x3/IMG_7666.png: at frame 75 Henry's mouth is open with teeth showing and the background child stands forward on the mat holding a black ball with both hands, larger and closer to the centre than in the source
  - test-tags: MANUAL
  - log: 2026-10-25T07:37:01Z @kj added
  - log: 2026-10-25T08:11:02Z @kj attempted: the 09:00 style render still animated the jaw; the prompt asked the smile to soften and return, which invites mouth motion; the fix pins the face to the photo with only the eyes softening
  - log: 2026-10-25T08:18:34Z @kj root cause: H3 generates audio jointly with the video and the positive prompts named the fault; fix: no speech word in a positive prompt, holds written as lips and teeth
  - log: 2026-10-25T14:57:26Z @kj closed: closed on the Star Colonel's 2026-10-25 verdict
- [x] `DEF-ANIM-7-SPEECH-GRIN` **IMG_7667 clip speaks** - MAJOR; Henry's open grin is animated into speech, the jaw moving as if talking; the source is a single still grin and the clip has no audio track
  - evidence: the Star Colonel viewed both new 7667 clips on 2026-10-25 and both pass - data/processed/henryk-urodziny-2026/minimax-h3/IMG_7667.mp4 and tmp/media/ltx25-i2v/IMG_7667.mp4
  - related: DEF-ANIM-6-SPEECH-CHILD
  - repro: the clip path data/processed/henryk-urodziny-2026/minimax-h3/IMG_7667.mp4, 1024x768, 150 frames, beside data/processed/henryk-urodziny-2026/extended/4x3/IMG_7667.png
  - test-tags: MANUAL
  - log: 2026-10-25T07:44:27Z @kj added
  - log: 2026-10-25T14:57:23Z @kj root cause: H3 generates audio jointly with the video and the positive prompt named the fault; the fix removed every speech word and pinned the lips and teeth
  - log: 2026-10-25T14:57:32Z @kj closed: on the Star Colonel's 2026-10-25 verdict
- [x] `DEF-ANIM-8-SLOWMO` **every 6 s clip plays in slow motion** - MAJOR; all 6 s clips move in slow motion and look unnatural, H3 and LTX alike; the Star Colonel named data/processed/henryk-urodziny-2026/minimax-h3-6s/IMG_8564.mp4 and IMG_8716.mp4; cause under investigation; data/processed/henryk-urodziny-2026/minimax-h3-6s/ and tmp/media/ltx25-i2v-6s/
  - evidence: measured 2026-10-26: H3 10 s IMG_0020 motion_per_second 275 vs 221 at 5 s, IMG_8840 57 vs 31; LTX chain 38.62 vs 9.14 single-pass, near-duplicate 15.4% vs 86.3%, join ratio 1.10; tmp/media/slowmo-probe-beats and chain-spike
  - root-cause: 2026-10-25T20:24:40Z @kj Longer native render, not retiming: H3 158 frames at 24 fps (6.58 s) against 124 (5.17 s), LTX 145 against 121, spreads the same action over 27% (H3) or 20% (LTX) more seconds; H3 stalls: IMG_8564 near-duplicate frames 0.1141 -> 0.6927 (ratio 0.4516), IMG_7666 0.4228 -> 0.8994 (0.4614).
  - repro: play data/processed/henryk-urodziny-2026/minimax-h3-6s/IMG_8564.mp4 and IMG_8716.mp4 at normal speed; the motion reads as slow motion
  - test-tags: FUNCTIONAL, MANUAL
  - log: 2026-10-25T20:17:43Z @kj added
  - log: 2026-10-25T20:24:44Z @kj measured: 9 of 12 5 s/6 s pairs move less per second at 6 s (median ratio 0.8192, mean 0.8727); H3 IMG_8564 25.6787 -> 11.5962 (ratio 0.4516), H3 IMG_7666 18.1879 -> 8.392 (0.4614), LTX IMG_7666 28.9996 -> 23.2949 (0.8033), LTX IMG_7667 91.6357 -> 76.5242 (0.8351)
  - log: 2026-10-25T20:24:46Z @kj ruled out: interpolation maps every output moment to the same native moment, so it does not retime; playback is constant 30 fps
  - log: 2026-10-25T20:29:53Z @kj overrides ACC-VIDEO-29-LIVING removed - criterion amended to natural real-time speed instead of overridden
  - log: 2026-10-25T20:49:45Z @kj attempted: 10 s H3 probe IMG_8564, rate prompt only, 243 frames, 20 steps - did NOT fix: motion_per_second 5.43 against 11.60 at 6 s and 25.68 at 5 s, 99.3% near-duplicate frames, plateau 0.156 after 4 s; peak 64.70 GB; tmp/media/slowmo-probe/IMG_8564.mp4
  - log: 2026-10-25T20:49:46Z @kj attempted: 10 s H3 probe with timed beats filling the whole clip, running since 21:48:21, pid 113531, output tmp/media/slowmo-probe-beats
  - log: 2026-10-25T21:08:16Z @kj attempted: 10 s H3 probe with timed beats - WORKED: motion_per_second 20.01 against 5.43 rate-only, 11.60 at 6 s and 25.68 at 5 s; near-duplicate frames 34.1% against 99.3% rate-only; two-second windows 0.656, 0.793, 0.561, 0.710, no late freeze; peak 64.74 GB; tmp/media/slowmo-probe-beats/IMG_8564.mp4
  - log: 2026-10-25T21:35:23Z @kj first 10 s clips: H3 IMG_0020 motion_per_second 275.0, 0.0% near-duplicate, windows 8.95/10.72/8.56/8.65 - works; LTX IMG_7666 9.14, 86.3% near-duplicate, windows 0.066/0.166/0.159/0.514 - 30 steps still settles
  - log: 2026-10-25T22:24:24Z @kj LTX 10 s at 60 steps: motion_per_second 9.60 against 9.14 at 30 steps, 86.6% near-duplicate, same window shape - steps are not the lever; LTX settles with duration alone
  - log: 2026-10-25T22:58:10Z @kj chaining two 5 s LTX renders WORKED: 10 s chained motion_per_second 38.62 against 9.14 single-pass, near-duplicate 15.4% against 86.3%, join ratio 1.10 (no seam), part A 5 s control 44.65; tmp/workflows/ltx25-preview/chain-spike/IMG_7666-chained.mp4
  - log: 2026-10-26T01:00:30Z @kj H3 10 s set done 01:59, 10 of 10 at 300 frames: motion_per_second against 5 s - 0020 275/221, 7645 35/42, 7666 15/18, 7667 5.0/5.1, 8564 17/26, 8716 7.0/6.2, 8732 9.8/9.5, 8779 21/50, 8828 13/29, 8840 57/31
  - log: 2026-10-26T01:52:12Z @kj LTX chained 10 s set done 02:51, 8 of 8: motion_per_second against 5 s - 7666 38.6/29.0, 7667 71.1/91.6, 8564 66.9/52.7, 8716 95.8/62.0, 8732 80.0/133.0, 8779 27.1/253.0, 8828 57.3/51.1, 8840 61.5/65.2; near-duplicate 0.7-22%
  - log: 2026-10-26T01:59:58Z @kj closed: fixed: 10 s method ships beats in the prompt and a chained render for LTX; the 6 s set is superseded
  - log: 2026-10-26T02:29:38Z @kj residual motion figures lower than the 5 s baseline on part of the delivered 10 s set, no late freeze in any clip; the Star Colonel's view pending
  - log: 2026-10-26T03:13:53Z @kj note: the LTX closure figures came from the pre-split chain clips; the current chain script splits prompts per 5 s part, so a future chain run re-renders those eight and its motion must be re-measured
  - log: 2026-10-26T14:37:01Z @kj regressed as DEF-ANIM-8-SLOWMO-1
- [-] `DEF-ANIM-8-SLOWMO-1` **every 6 s clip plays in slow motion** - MAJOR; all 6 s clips move in slow motion and look unnatural, H3 and LTX alike; the Star Colonel named data/processed/henryk-urodziny-2026/minimax-h3-6s/IMG_8564.mp4 and IMG_8716.mp4; cause under investigation; data/processed/henryk-urodziny-2026/minimax-h3-6s/ and tmp/media/ltx25-i2v-6s/
  - test-tags: FUNCTIONAL, MANUAL
  - related: ACC-VIDEO-29-LIVING
  - repro: play data/processed/henryk-urodziny-2026/minimax-h3-10s/IMG_8716.mp4 and IMG_8564.mp4 at normal speed; the motion reads as slow motion
  - log: 2026-10-26T14:37:01Z @kj regression of DEF-ANIM-8-SLOWMO: regressed: the Star Colonel reported data/processed/henryk-urodziny-2026/minimax-h3-10s/IMG_8716.mp4 and IMG_8564.mp4 as slow motion on 2026-10-26
  - log: 2026-10-26T14:37:06Z @kj edited repro added "play data/processed/henryk-urodziny-2026/minimax-h3-10s/IMG_8716.mp4 and IMG_8564.mp4 at normal speed; the motion reads as slow motion"
  - log: 2026-10-26T14:37:06Z @kj measured: IMG_8564 motion_per_second 16.572 at 10 s against 25.6787 at 5 s, ratio 0.6454; IMG_8716 7.0287 against 6.2229, ratio 1.1295; longest plateau 0 s in both clips; IMG_8716 near-duplicate fraction 0.9532 against 0.953
  - log: 2026-10-26T14:37:40Z @kj edited test-tags added "FUNCTIONAL, MANUAL"
  - log: 2026-10-26T17:36:31Z @kj attempted: simple official-grammar prompts; motion_per_second new/delivered - IMG_8564 4.9773/16.572, IMG_8716 7.3901/7.0287, IMG_7667 6.3338/4.9644, IMG_8779 16.3322/20.7143; near-duplicate fraction new/delivered - 0.9967/0.4816, 0.903/0.9532, 0.9732/0.9933, 0.5351/0.4314; the Star Colonel views; tmp/media/h3-simple-prompts/
  - log: 2026-10-26T22:16:17Z @kj attempted: 4 prompts on IMG_8564; motion per second (ratio to M0) and near-duplicate: M1 rate sentence 22.7819 (0.96x), 0.2575; M2 larger action 21.7818 (0.92x), 0.2642; M3 continuous motion 24.5455 (1.03x), 0.2308; M0 23.7881, 0.2441; the Star Colonel views; tmp/media/h3-speech-slowmo/
  - log: 2026-10-27T00:00:32Z @kj attempted: M1, M2, M3 at 1024x768; motion per second 20.4553/16.8435/33.0849 against the 1024 control 4.9773 and the delivered clip 16.572; near-duplicate 0.2776/0.5217/0.0435 against 0.9967 and 0.4816; the Star Colonel views; tmp/media/h3-confirm-1024/
  - log: 2026-10-27T02:43:55Z @kj attempted: IMG_8716 pacing variants at 10 s; motion per second and near-duplicate - R1 9.735/0.8361, R2 12.8441/0.6555 against the simple control 7.3901/0.903 and the delivered 7.0287/0.9532; both stems now have a measured pacing variant; the Star Colonel views; tmp/media/h3-slowmo-8716/
  - log: 2026-10-28T12:46:27Z @kj rejected: rejected by the Star Colonel 2026-10-28: the clip campaign is finished, he has all the clips he needs; no fix is claimed
- [-] `DEF-ANIM-9-CHILD-DRIFT` **background child walks off and loses the ball in the IMG_7666 clip** - MAJOR; the small child behind Henry leaves the photo's pose, walks left and no longer holds the black-and-white ball; the source has her standing still with the ball at the chest; found by the 10 s no-talk gate at frame 82; data/processed/henryk-urodziny-2026/minimax-h3-10s/IMG_7666.mp4
  - repro: play IMG_7666.mp4 from frame 82; the background child walks left without the ball
  - test-tags: FUNCTIONAL, MANUAL
  - log: 2026-10-26T01:10:56Z @kj added
  - log: 2026-10-26T02:00:18Z @kj rejected: not a defect: the Star Colonel's own saved prompt of 2026-10-25 21:14 asks 'the child behind him is removed from the image'; the clip follows that instruction and she walks out of frame; prompts/user-2026-10-25T2208/IMG_7666.json holds the text
- [-] `DEF-ANIM-10-TALKING10S` **ten second H3 clips animate the mouth as speech** - MAJOR; many clips show Henry's mouth moving as if talking; the Star Colonel said "many movies have Henry talking"; the highest mouth-screen ratios are IMG_7667 1.99 and IMG_8779 1.94 against the 2.0 flag; cause under investigation
  - related: ACC-VIDEO-30-SCENE
  - related: DEF-ANIM-7-SPEECH-GRIN
  - root-cause: 2026-10-26T14:37:31Z @kj the ten second beat shape names smile and grin shape changes; H3 generates audio jointly and renders the shape change as speech; the 5 s fix pinned the lips and teeth, the 10 s beats reintroduced the change
  - repro: play data/processed/henryk-urodziny-2026/minimax-h3-10s/IMG_7667.mp4 and IMG_8779.mp4; Henry's mouth moves as if talking
  - test-tags: MANUAL
  - log: 2026-10-26T14:37:28Z @kj added
  - log: 2026-10-26T15:38:53Z @kj attempted: custom CFGGuider with a negative speech prompt, cfg 2.0, on IMG_7667; mouth ratio 2.121 against 1.99 delivered; motion_per_second 5.9343 against 4.9644; 0 new persons; the Star Colonel views
  - log: 2026-10-26T17:36:34Z @kj attempted: simple official-grammar prompts; mouth median new/delivered - IMG_8564 0.1522/1.5161, IMG_8716 1.2281/1.1654, IMG_7667 5.7885/5.1028, IMG_8779 4.3718/4.9574; ratio to baseline 2.5043 new/delivered - 0.061/0.605, 0.49/0.465, 2.311/2.038, 1.746/1.98; persons: IMG_8779 3 new detections max conf 0.2626, others 0; the Star Colonel views
  - log: 2026-10-26T22:16:13Z @kj attempted: 8 prompts on IMG_7667; mouth median ratio to S0 (3.3812): S1 stillness 0.12x, S2 sound design 0.19x, S3 stillness+sound 0.24x, S4 CFG negative 0.73x, S5 Chinese stillness 0.02x, S6 Chinese soundscape 0.15x, S7 both Chinese 0.14x; the Star Colonel views; tmp/media/h3-speech-slowmo/
  - log: 2026-10-27T00:00:30Z @kj attempted: Chinese stillness S5 at 1024x768; mouth median new/control/delivered 3.5648/5.7885/5.1028, ratio to baseline 1.423; the 480x320 0.02x lead did not hold; the Star Colonel views; tmp/media/h3-confirm-1024/IMG_7667-S5.mp4
  - log: 2026-10-27T01:13:46Z @kj attempted: 3 prompts on IMG_7667 at 1024x768; mouth median and ratio to S5 3.5648 / control 5.7885 - T1 4.2228 1.1846/0.7295, T2 3.2561 0.9134/0.5625, T3 6.3584 1.7837/1.0985; T3 changes head action to a very slight tilt, so its figures measure that package; the Star Colonel views; tmp/media/h3-speech-iter-1024/
  - log: 2026-10-27T13:15:41Z @kj attempted: IMG_7667 U1 N/A/N/A and U2 fields omitted at 1024x768; native audio not silent - U1 mean -47.8 max -37.6 dB, U2 mean -42.5 max -29.2 dB against -50; mouth median U1 3.2781, U2 3.4573 against T2 3.2561 and control 5.7885; the Star Colonel views
  - log: 2026-10-28T12:46:27Z @kj rejected: rejected by the Star Colonel 2026-10-28: the clip campaign is finished, he has all the clips he needs; no fix is claimed

## Image extender `EXTEND`

The photo extender notebook and its module under src/henryk_media/imaging/

- log: 2026-10-25T03:49:02Z @kj category created

- [x] `DEF-EXTEND-2-NEW-PEOPLE` **Outpainting invents people in the added panels** - MAJOR; the first bench tiles add a person who is not in the photo: FLUX Fill puts a girl in a white floral top and yellow skirt in the right panel, and Qwen inpainting gives the girl cut off at the left edge a face the photo never shows
  - test-tags: UNIT, MANUAL
  - evidence: person gate src/henryk_media/imaging/gate.py splits a stranger wholly inside a panel from a continuation crossing the photo edge; tests/test_imaging.py and tests/test_gate.py cover stranger, continuation and clipped boxes, make test 73 passed; production 11 photos, 22 frames: 0 strangers, 7 continuations, tmp/workflows/image-extender/all-extend.json
  - repro: open tmp/media/extended/4x3/flux-fill/IMG_8564.png and tmp/media/extended/4x3/qwen-inpainting/IMG_8564.png beside data/interim/henryk-urodziny-2026/IMG_8564.png
  - root-cause: 2026-10-25T03:49:02Z @kj FLUX Fill runs at CFG 1 so the negative prompt is encoded but inert, and the positive no-people clause loses to a scene full of children; nothing checked the added panels for faces before the tile was accepted
  - log: 2026-10-25T03:49:02Z @kj added
  - log: 2026-10-25T07:33:28Z @kj root cause: no check on the added panels; fix: the person gate plus its stranger/continuation rule split
  - log: 2026-10-25T07:33:31Z @kj closed: fixed: person gate rejects strangers wholly inside the added panels and records continuations
  - log: 2026-10-25T20:29:57Z @kj edited test-tags added "UNIT, MANUAL"
- [-] `DEF-EXTEND-5-ROOM-GEOMETRY` **flux-kontext 16:9 extension breaks the room geometry** - MAJOR; the wooden table and stool legs merge and one ends in mid-air, the window and balcony run at angles the room does not have, the floor edge breaks at the seam, and a wall corner floats over the carpet
  - repro: open /home/lab/workspace/private/henryk/henryk-media/tmp/media/extended/16x9/flux-kontext/IMG_8564.png, 1280x720, photo x 369 to 911, seed 47
  - test-tags: MANUAL
  - log: 2026-10-25T06:07:19Z @kj added
  - log: 2026-10-25T14:57:35Z @kj rejected: flux-kontext is a bench variant, not the production extender; FLUX 3 Klein produced the 16:9 IMG_8564 frame and it passed the gate and the Star Colonel's view

## Studio server `STUDIO`

Defects of the local studio server

- log: 2026-10-27T21:55:58Z @kj category created

- [x] `DEF-STUDIO-11-H3-CROP` **H3 crops a wide source to 4:3** - MAJOR; a 16:9 outpaint result animated at 1024x768 loses the outpainted panels: the MiniMax H3 node cover-crops the input to the canvas (comfy_extras/nodes_minimax_h3.py _resize center), and the studio sizes the video at 4:3 or 3:2 whatever the source aspect
  - evidence: live pipeline frame 20261028-145745-dc5f64 (1920x1080) fed to H3 job 20261028-145745-e48830: clip 1280x720, aspect_ok true, frame0_mad [10.22, 10.536, 10.345], horizontal scale scan best 1.0; tests/test_studio_frames.py::test_frame_fed_to_h3_keeps_its_aspect and ::test_clip_renders_on_the_32_step_and_crops_to_the_preset green; reshoot-live.json
  - related: ACC-STUDIO-58-VID-OPTIONS
  - repro: live run: outpaint IMG_0020 to 16:9 at 1280x720, animate the result at 1024x768; the clip shows the centre 4:3 only
  - root-cause: 2026-10-28T12:47:39Z @kj the MiniMax H3 node stretches the input to the canvas (nodes_minimax_h3.py first_frame resize, not the AddGuide crop); the studio sized every clip 4:3 or 3:2; the first fix (video_size keeping the source aspect, short side rounded to 32) still stretched 3 of 8 aspect and size pairs, 16:9 at 480x320 by 5.5 percent; fixed by rendering at the preset size rounded up to the 32-pixel step from the frame scaled to cover it, then centre-cropping the clip to the exact preset size
  - root-cause: 2026-10-27T21:55:58Z @kj video size taken from the preset (1024x768 or 480x320) and the source orientation only, never from the source aspect; the H3 node centre-crops to that size
  - log: 2026-10-27T21:55:58Z @kj added
  - log: 2026-10-28T12:47:39Z @kj root-cause overridden; reason: records the disproved first fix and the final fix together, so the stretch is not re-diagnosed as a crop
  - log: 2026-10-28T15:22:19Z @kj closed
- [x] `DEF-STUDIO-12-PROGRESS-STAGES` **Progress skips decoding and interpolating** - MEDIUM; during a live job the stages decoding and interpolating never appear; the bar stays at sampling 88 until done (outpaint 7 s, video 42 s)
  - evidence: live H3 job 20261028-145745-e48830: decoding at 2026-10-28T15:05:43, interpolating at 15:06:06, done at 15:06:23; tests/test_studio_jobs.py::test_graph_is_queued_with_the_listener_client_id green; reshoot-live.json
  - related: ACC-STUDIO-64-PROGRESS
  - repro: live run: watch the job endpoint during the H3 job; no decoding or interpolating stage is reported
  - root-cause: 2026-10-27T21:55:58Z @kj prompts are queued without a client_id, so ComfyUI sends executing and progress events for later nodes only to that client; the interpolating stage, run by the studio itself, is not set before FILM starts
  - log: 2026-10-27T21:55:58Z @kj added
  - log: 2026-10-28T15:22:19Z @kj closed
- [-] `DEF-STUDIO-13-H3-PEAK` **H3 memory need recorded too low** - MEDIUM; the memory table assumes 66.156 GB for H3 1024x768 5 s; the live job peaked at 74.43 GB after an outpaint in the same ComfyUI process, so a GPU with 66.2 to 74.4 GB free is admitted and then runs out of memory
  - related: ACC-STUDIO-43-GPU-FIT
  - repro: live run sidecar tmp/media/studio-live/state/jobs/20261027-223015-d78a61/IMG_0020.md peak 74.43 GB against the table value 66.156 GB
  - root-cause: 2026-10-27T21:55:58Z @kj the table value comes from a fresh-process production run; a warm process holding the Klein model adds the difference
  - log: 2026-10-27T21:55:58Z @kj added
  - log: 2026-10-28T12:47:39Z @kj rejected: rejected by the Star Colonel 2026-10-28: the 74.43 GB peak was read in a ComfyUI process that still held the Klein model, which ComfyUI frees on demand, so it shows no H3 need above the recorded 66.156 GB (review round 1 ruling)
- [x] `DEF-STUDIO-14-KLEIN-PEAK` **Klein memory estimate ignores the frame size** - MAJOR; The studio's fit check uses one FLUX 3 Klein peak (OUTPAINT_GB = 21.317 GB in src/henryk_media/studio/gpus.py) for every outpaint frame size; larger frames need more memory, so a frame job can be admitted on a GPU it does not fit and run out of memory
  - evidence: tests/test_studio_gpus.py::test_klein_estimate_meets_every_recorded_row and ::test_klein_frame_fit_follows_the_frame_size pass (UHD 4K frame refused on GPU 0 25.7 GB at 27.48 GB, Full HD admitted at 22.054 GB, a 2880x2160 crop admitted without a fit); patch tmp/workflows/studio/patches/owner/5.patch; live rows from tmp/workflows/studio/reshoot-live.json: 21.43 GB at 1080x1080, 22.08 GB at 1920x1080, 27.48 GB at 3840x2160
  - repro: a UHD 4K frame job on GPU 0 (25.7 GB): the fit check admits it at 21.317 GB; the live UHD job peaked at 27.48 GB (reshoot-live.json uhd_frame)
  - test-tags: UNIT
  - root-cause: 2026-10-28T13:40:31Z @kj one recorded row at 1280x960 is used for every frame size; Klein's peak grows with the frame's pixel count (21.43 GB at 1080x1080, 22.08 GB at 1920x1080, 27.48 GB at 3840x2160)
  - log: 2026-10-28T13:40:31Z @kj added
  - log: 2026-10-28T13:43:48Z @kj closed: fixed

