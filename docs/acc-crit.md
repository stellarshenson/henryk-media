# Acceptance Criteria

Acceptance criteria for the whole-frame image-to-video campaign: renders of the three birthday photos in notebooks 03 to 05, the shared render pipeline, the release rules and the model-selection record.

## Authors

- `@kj` Konrad Jelen

## Image-to-video renders `VIDEO`

Whole-frame image-to-video renders of the three birthday photos in notebooks 03 to 05

- log: 2026-10-24T22:38:49Z @kj category created

- [x] `ACC-VIDEO-1-LTX25` **LTX-2.5 clips** - HIGH; notebook 04 runs the 3:4 portrait LENGTH 241 single-pass probe with LTX-2.5; production renders the 4:3 set through the two-part chain in tmp/workflows/ltx25-preview/render_ltx_chain_10s.py at 300 frames and 10.00 s, one clip per photo
  - evidence: 8 chained LTX clips at 1024x768, 300 frames, 30 fps, 10.00 s in tmp/media/ltx25-i2v-10s with sidecars; chain dry check exit 0
  - test: run tmp/workflows/ltx25-preview/render_ltx_chain_10s.py --dry-check and one stem end to end; probe 300 frames at 30 fps and 10.00 s; note the notebook's single pass settles
  - test-tags: FUNCTIONAL
  - log: 2026-10-24T22:38:49Z @kj added
  - log: 2026-10-25T00:29:20Z @kj edited text "notebook 03 renders one clip per photo with LTX-2.5, 5 s at 30 fps, from the two-part prompt" -> "notebook 03 renders one clip per photo with LTX-2.5, 10 s at 30 fps (300 frames), from the two-part prompt"; test "run 03-kj-ltx25-i2v.ipynb, ffprobe each clip for 5.0 s and 30 fps" -> "run 03-kj-ltx25-i2v.ipynb, ffprobe each clip for 10.0 s and 300 frames at 30 fps"
  - log: 2026-10-25T00:41:10Z @kj edited text "notebook 03 renders one clip per photo with LTX-2.5, 10 s at 30 fps (300 frames), from the two-part prompt" -> "notebook 03 renders one 4:3 clip per photo with LTX-2.5, 5 s at 30 fps (150 frames), from the two-part prompt"; test "run 03-kj-ltx25-i2v.ipynb, ffprobe each clip for 10.0 s and 300 frames at 30 fps" -> "run 03-kj-ltx25-i2v.ipynb, ffprobe each clip for 5.0 s and 150 frames at 30 fps"
  - log: 2026-10-25T00:45:06Z @kj edited text "notebook 03 renders one 4:3 clip per photo with LTX-2.5, 5 s at 30 fps (150 frames), from the two-part prompt" -> "notebook 04 renders one 4:3 clip per photo with LTX-2.5, 5 s at 30 fps (150 frames), from the two-part prompt"; test "run 03-kj-ltx25-i2v.ipynb, ffprobe each clip for 5.0 s and 150 frames at 30 fps" -> "run 04-kj-ltx25-i2v.ipynb, ffprobe each clip for 5.0 s and 150 frames at 30 fps"
  - log: 2026-10-26T02:29:27Z @kj edited text "notebook 04 renders one 4:3 clip per photo with LTX-2.5, 5 s at 30 fps (150 frames), from the two-part prompt" -> "notebook 04 renders one 4:3 clip per photo with LTX-2.5, 10 s at 30 fps (300 frames), from the two-part prompt; LTX LENGTH is 241 and at 10 s it settles, so production uses the two-part chain"
  - log: 2026-10-26T02:29:58Z @kj edited test "run 04-kj-ltx25-i2v.ipynb, ffprobe each clip for 5.0 s and 150 frames at 30 fps" -> "run 04-kj-ltx25-i2v.ipynb, ffprobe each clip for 10.0 s and 300 frames at 30 fps"
  - log: 2026-10-26T02:49:39Z @kj edited test "run 04-kj-ltx25-i2v.ipynb, ffprobe each clip for 10.0 s and 300 frames at 30 fps" -> "run tmp/workflows/ltx25-preview/render_ltx_chain_10s.py --dry-check and one stem end to end; probe 300 frames at 30 fps and 10.00 s; note the notebook's single pass settles"
  - log: 2026-10-26T03:11:46Z @kj edited text "notebook 04 renders one 4:3 clip per photo with LTX-2.5, 10 s at 30 fps (300 frames), from the two-part prompt; LTX LENGTH is 241 and at 10 s it settles, so production uses the two-part chain" -> "notebook 04 runs the 3:4 portrait LENGTH 241 single-pass probe with LTX-2.5; production renders the 4:3 set through the two-part chain in tmp/workflows/ltx25-preview/render_ltx_chain_10s.py at 300 frames and 10.00 s, one clip per photo"
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-VIDEO-2-MINIMAX` **MiniMax H3 clips** - HIGH; notebook 05 renders one clip per photo with MiniMax H3, 10 s at 30 fps (300 frames), from the two-part prompt; H3 LENGTH is 243 and at 10 s it renders in a single pass
  - evidence: 10 H3 clips at 1024x768, 300 frames, 30 fps, 10.00 s in data/processed/henryk-urodziny-2026/minimax-h3-10s with sidecars
  - test: run 05-kj-minimax-h3.ipynb, ffprobe each clip for 10.0 s and 300 frames at 30 fps
  - test-tags: FUNCTIONAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-25T00:29:23Z @kj edited text "notebook 04 renders one clip per photo with MiniMax H3, 5 s at 30 fps, from the two-part prompt" -> "notebook 04 renders one clip per photo with MiniMax H3, 10 s at 30 fps (300 frames), from the two-part prompt"; test "run 04-kj-minimax-h3.ipynb, ffprobe each clip for 5.0 s and 30 fps" -> "run 04-kj-minimax-h3.ipynb, ffprobe each clip for 10.0 s and 300 frames at 30 fps"
  - log: 2026-10-25T00:38:04Z @kj rejected: deferred by order, later work resumes on the Star Colonel's word; reason: LTX-2.5 only for now (2026-10-25 02:31); the MiniMax H3 weights and its approved 5 s clips stay, and the criterion returns when he revives it
  - log: 2026-10-25T02:04:58Z @kj edited text "notebook 04 renders one clip per photo with MiniMax H3, 10 s at 30 fps (300 frames), from the two-part prompt" -> "notebook 05 renders one clip per photo with MiniMax H3, 5 s at 30 fps (150 frames), from the two-part prompt"; test "run 04-kj-minimax-h3.ipynb, ffprobe each clip for 10.0 s and 300 frames at 30 fps" -> "run 05-kj-minimax-h3.ipynb, ffprobe each clip for 5.0 s and 150 frames at 30 fps"
  - log: 2026-10-25T06:04:13Z @kj reopened: the Star Colonel revived H3 and judged the boy's clip good at 2026-10-25 07:00
  - log: 2026-10-25T06:04:13Z @kj amended text "notebook 05 renders one clip per photo with MiniMax H3, 5 s at 30 fps (150 frames), from the two-part prompt" -> "MiniMax H3 is the model for the boy's photo; notebook 05 renders one clip per photo with MiniMax H3, 5 s at 30 fps (150 frames), from the two-part prompt; the boy's clip is /home/lab/workspace/private/henryk/henryk-media/tmp/media/ltx25-i2v/IMG_8076-h3.mp4, judged good by the Star Colonel at 2026-10-25 07:00"
  - log: 2026-10-26T02:29:29Z @kj edited text "MiniMax H3 is the model for the boy's photo; notebook 05 renders one clip per photo with MiniMax H3, 5 s at 30 fps (150 frames), from the two-part prompt; the boy's clip is /home/lab/workspace/private/henryk/henryk-media/tmp/media/ltx25-i2v/IMG_8076-h3.mp4, judged good by the Star Colonel at 2026-10-25 07:00" -> "notebook 05 renders one clip per photo with MiniMax H3, 10 s at 30 fps (300 frames), from the two-part prompt; H3 LENGTH is 243 and at 10 s it renders in a single pass"
  - log: 2026-10-26T02:29:58Z @kj edited test "run 05-kj-minimax-h3.ipynb, ffprobe each clip for 5.0 s and 150 frames at 30 fps" -> "run 05-kj-minimax-h3.ipynb, ffprobe each clip for 10.0 s and 300 frames at 30 fps"
  - log: 2026-10-26T03:36:53Z @kj closed
- [-] `ACC-VIDEO-3-WAN22` **Wan2.2 clips** - HIGH; a Wan2.2 notebook renders one clip per photo, 5 s at 30 fps, from the two-part prompt; no notebook was written before the model was discarded
  - test: ffprobe each clip for 5.0 s and 30 fps, had the model been kept
  - test-tags: FUNCTIONAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-25T00:19:22Z @kj rejected: the Star Colonel judged the LTX-2.5 and MiniMax H3 renders great on 2026-10-25 and discarded Wan2.2; its weights and smoke setup stay on disk
  - log: 2026-10-25T02:05:02Z @kj edited text "notebook 05 renders one clip per photo with Wan2.2, 5 s at 30 fps, from the two-part prompt" -> "a Wan2.2 notebook renders one clip per photo, 5 s at 30 fps, from the two-part prompt; no notebook was written before the model was discarded"; test "run 05-kj-wan22-i2v.ipynb, ffprobe each clip for 5.0 s and 30 fps" -> "ffprobe each clip for 5.0 s and 30 fps, had the model been kept"
- [x] `ACC-VIDEO-4-CHECK` **Independent check passes** - HIGH; each model's check records pass true after inspecting the rendered frames
  - evidence: independent checks tmp/workflows/image-to-video/verify-10s-h3.json and verify-10s-ltx.json both pass true: 10 and 8 clips, 10.00 s at 30 fps, sidecars, no audio
  - test: read tmp/workflows/image-to-video/verify-<key>-<round>.json, assert pass true for each model
  - test-tags: FUNCTIONAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-26T03:37:51Z @kj closed
- [x] `ACC-VIDEO-5-SIDECAR` **Clip sidecars** - HIGH; every clip has a .md sidecar naming the source photo, model, prompt and settings
  - evidence: 18 mp4 across the two 10 s sets, each with a .md sidecar naming source, model, prompt and settings
  - test: for each mp4 under data/processed/henryk-urodziny-2026, assert a .md sidecar names source, model, prompt and settings
  - test-tags: FUNCTIONAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-VIDEO-6-LATEST` **Only the latest render** - MEDIUM; each model's output folder holds only its latest render; previous clips were moved to the trash
  - evidence: each 10 s folder holds one clip and sidecar per photo with no older render inside it; the 5 s and 6 s sets occupy their own folders by the Star Colonel's order
  - test: list each model output folder, assert one clip per photo and no older render
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-26T03:37:57Z @kj closed
- [x] `ACC-VIDEO-7-PROMPT` **Two-part prompts** - MEDIUM; each notebook shows the Star Colonel's generic sentence verbatim, then the living-photograph style clause, then that photo's static holds
  - evidence: every prompt is the generic sentence plus the living-photograph style clause plus that photo's holds; fixed line read from render_h3_10s.py
  - test: read the prompt cells in notebooks 04 and 05 and their sidecars, assert the generic sentence verbatim, then the style clause, then the photo's static holds
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-25T09:32:39Z @kj amended text "each notebook shows the Star Colonel's generic sentence verbatim, then a part specific to that photo's theme" -> "each notebook shows the Star Colonel's generic sentence verbatim, then the living-photograph style clause, then that photo's static holds"; reason: the Star Colonel set the living-photograph style on 2026-10-25: the prompt's second part is the style clause then the photo's static holds, not a theme part
  - log: 2026-10-25T09:32:39Z @kj edited test "read the prompt cells in each notebook, assert the generic sentence verbatim then the theme part" -> "read the prompt cells in notebooks 04 and 05 and their sidecars, assert the generic sentence verbatim, then the style clause, then the photo's static holds"
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-VIDEO-19-WIDE` **4:3 landscape set** - HIGH; every photo in data/external/henryk-urodziny-2026/images renders in a 4:3 landscape frame at 1024x768, 10 s at 30 fps, without stretching the child; the frame comes from the extender notebook, never from the image-to-video model
  - evidence: all 18 clips are 1024x768 from extended/4x3 frames; every source photo kept its aspect without stretching
  - test: open notebook 04, assert a 4:3 section with every photo; ffprobe 5.0 s, 30 fps, width/height ratio 1.30 to 1.36; match each clip's source to an extender output
  - test-tags: FUNCTIONAL
  - log: 2026-10-25T00:21:17Z @kj added
  - log: 2026-10-25T00:22:59Z @kj amended text "notebooks 03 and 04 add the same three photos rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child" -> "notebooks 03 and 04 add every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child"
  - log: 2026-10-25T00:29:25Z @kj edited text "notebooks 03 and 04 add every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child" -> "notebooks 03 and 04 add every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 10 s at 30 fps, without stretching the child"; test "open notebooks 03 and 04, assert a 4:3 section with 3 clips each; ffprobe 5.0 s, 30 fps, width/height ratio 1.30 to 1.36" -> "open notebooks 03 and 04, assert a 4:3 section with every photo; ffprobe 10.0 s, 30 fps, width/height ratio 1.30 to 1.36"
  - log: 2026-10-25T00:38:08Z @kj edited text "notebooks 03 and 04 add every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 10 s at 30 fps, without stretching the child" -> "notebook 03 adds every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 10 s at 30 fps, without stretching the child"; test "open notebooks 03 and 04, assert a 4:3 section with every photo; ffprobe 10.0 s, 30 fps, width/height ratio 1.30 to 1.36" -> "open notebook 03, assert a 4:3 section with every photo; ffprobe 10.0 s, 30 fps, width/height ratio 1.30 to 1.36"
  - log: 2026-10-25T00:41:13Z @kj edited text "notebook 03 adds every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 10 s at 30 fps, without stretching the child" -> "notebook 03 adds every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child; a photo of another aspect ratio is fitted by extending the scene, never a blurred or mirrored pad"; test "open notebook 03, assert a 4:3 section with every photo; ffprobe 10.0 s, 30 fps, width/height ratio 1.30 to 1.36" -> "open notebook 03, assert a 4:3 section with every photo; ffprobe 5.0 s, 30 fps, width/height ratio 1.30 to 1.36; view the added area and assert it continues the scene"
  - log: 2026-10-25T00:43:55Z @kj edited text "notebook 03 adds every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child; a photo of another aspect ratio is fitted by extending the scene, never a blurred or mirrored pad" -> "notebook 03 adds every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child; the frame comes from the extender notebook, never from the image-to-video model"; test "open notebook 03, assert a 4:3 section with every photo; ffprobe 5.0 s, 30 fps, width/height ratio 1.30 to 1.36; view the added area and assert it continues the scene" -> "open notebook 03, assert a 4:3 section with every photo; ffprobe 5.0 s, 30 fps, width/height ratio 1.30 to 1.36; match each clip's source to an extender output"
  - log: 2026-10-25T00:45:09Z @kj edited text "notebook 03 adds every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child; the frame comes from the extender notebook, never from the image-to-video model" -> "notebook 04 adds every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child; the frame comes from the extender notebook, never from the image-to-video model"; test "open notebook 03, assert a 4:3 section with every photo; ffprobe 5.0 s, 30 fps, width/height ratio 1.30 to 1.36; match each clip's source to an extender output" -> "open notebook 04, assert a 4:3 section with every photo; ffprobe 5.0 s, 30 fps, width/height ratio 1.30 to 1.36; match each clip's source to an extender output"
  - log: 2026-10-26T03:36:52Z @kj edited text "notebook 04 adds every photo in data/external/henryk-urodziny-2026/images rendered in a 4:3 landscape frame, 5 s at 30 fps, without stretching the child; the frame comes from the extender notebook, never from the image-to-video model" -> "every photo in data/external/henryk-urodziny-2026/images renders in a 4:3 landscape frame at 1024x768, 10 s at 30 fps, without stretching the child; the frame comes from the extender notebook, never from the image-to-video model"
  - log: 2026-10-26T03:36:53Z @kj closed
- [-] `ACC-VIDEO-20-NOTALK` **No talking in notebook 04** - HIGH; the MiniMax H3 4:3 clips show the persons not talking: the mouth stays closed and the lips do not move as in speech
  - overridden-by: ACC-VIDEO-31-NO-FAULT
  - test: extract the mouth region from the first, middle and last frames of each 04 4:3 clip, assert the lips stay closed
  - test-tags: MANUAL
  - log: 2026-10-25T00:21:20Z @kj added
  - log: 2026-10-25T00:38:06Z @kj rejected: deferred with notebook 04; reason: notebook 04 is not rendered while MiniMax H3 is deferred (2026-10-25 02:31); the no-talking rule returns with the model
- [x] `ACC-VIDEO-21-EXTENDER` **Extender notebook** - HIGH; notebook 01 compares every viable local extender in one grid at 1280x960 4:3 and 1280x720 16:9; the production run uses flux3-klein, selected by the Star Colonel on 2026-10-25 07:22; the photo is scaled to the frame height and only the sides are generated; upscaling is deferred by the Star Colonel's order of 2026-10-25 06:00; the faces stay unchanged, the added area continues the scene, and no person appears beyond those already in the photo
  - evidence: tmp/workflows/image-extender/all-extend.json: 11 photos at 4:3 and 16:9 with FLUX 3 Klein, 20 frames generated, 2 scaled only, gate passed, 0 strangers, 7 continuations; 22 sidecars; grids grid-4x3.png and grid-16x9.png
  - test: run 01-kj-image-extender.ipynb on IMG_8564, probe both frames for 1280x960 and 1280x720, view the added area for scene continuation and any new person, compare the face boxes, open both grids
  - test-tags: FUNCTIONAL
  - log: 2026-10-25T00:43:51Z @kj added
  - log: 2026-10-25T00:45:12Z @kj edited text "notebook 05 extends a photo to a 4:3 landscape frame and raises its resolution with a local model before any image-to-video render; the faces stay unchanged and the added area continues the scene" -> "notebook 01 extends a photo to a 4:3 landscape frame and raises its resolution with a local model before any image-to-video render; the faces stay unchanged and the added area continues the scene"; test "run 05-kj-image-extender.ipynb on IMG_8564, probe the output for the 4:3 ratio and its pixel size, view the added area beside the source photo, compare the face boxes" -> "run 01-kj-image-extender.ipynb on IMG_8564, probe the output for the 4:3 ratio and its pixel size, view the added area beside the source photo, compare the face boxes"
  - log: 2026-10-25T01:24:39Z @kj edited text "notebook 01 extends a photo to a 4:3 landscape frame and raises its resolution with a local model before any image-to-video render; the faces stay unchanged and the added area continues the scene" -> "notebook 01 extends a photo to a 4:3 and a 16:9 landscape frame with local models and raises the resolution, comparing the models in one grid; the faces stay unchanged and the added area continues the scene"; test "run 01-kj-image-extender.ipynb on IMG_8564, probe the output for the 4:3 ratio and its pixel size, view the added area beside the source photo, compare the face boxes" -> "run 01-kj-image-extender.ipynb on IMG_8564, probe both frames for the ratios and pixel sizes, view the added area beside the source photo, compare the face boxes, and open both grids"
  - log: 2026-10-25T02:04:17Z @kj edited text "notebook 01 extends a photo to a 4:3 and a 16:9 landscape frame with local models and raises the resolution, comparing the models in one grid; the faces stay unchanged and the added area continues the scene" -> "notebook 01 extends a photo to a 4:3 and a 16:9 landscape frame with local models and raises the resolution, comparing the models in one grid; the faces stay unchanged, the added area continues the scene, and no person appears beyond those already in the photo"; test "run 01-kj-image-extender.ipynb on IMG_8564, probe both frames for the ratios and pixel sizes, view the added area beside the source photo, compare the face boxes, and open both grids" -> "run 01-kj-image-extender.ipynb on IMG_8564, probe both frames for the ratios and sizes, view the added area for scene continuation and any new person, compare the face boxes, open both grids"
  - log: 2026-10-25T05:04:45Z @kj amended text "notebook 01 extends a photo to a 4:3 and a 16:9 landscape frame with local models and raises the resolution, comparing the models in one grid; the faces stay unchanged, the added area continues the scene, and no person appears beyond those already in the photo" -> "notebook 01 extends a photo to a 1280x960 4:3 frame and a 1280x720 16:9 frame with local models, comparing them in one grid; the photo is scaled to the frame height and only the sides are generated; upscaling is deferred by the Star Colonel's order of 2026-10-25 06:00; the faces stay unchanged, the added area continues the scene, and no person appears beyond those already in the photo"; reason: Star Colonel order 2026-10-25 06:00: "do 1280x based images; the time for rendering will drop sharply" and "we can upscale them later"; frames are now 1280x960 4:3 and 1280x720 16:9 with only the sides generated, so the criterion no longer claims raised resolution
  - log: 2026-10-25T05:04:47Z @kj edited test "run 01-kj-image-extender.ipynb on IMG_8564, probe both frames for the ratios and sizes, view the added area for scene continuation and any new person, compare the face boxes, open both grids" -> "run 01-kj-image-extender.ipynb on IMG_8564, probe both frames for 1280x960 and 1280x720, view the added area for scene continuation and any new person, compare the face boxes, open both grids"
  - log: 2026-10-25T06:07:25Z @kj at 2026-10-25 07:22 the Star Colonel selected the extender: "across renders flux klein seems to do the best job"
  - log: 2026-10-25T06:07:28Z @kj amended text "notebook 01 extends a photo to a 1280x960 4:3 frame and a 1280x720 16:9 frame with local models, comparing them in one grid; the photo is scaled to the frame height and only the sides are generated; upscaling is deferred by the Star Colonel's order of 2026-10-25 06:00; the faces stay unchanged, the added area continues the scene, and no person appears beyond those already in the photo" -> "notebook 01 compares every viable local extender in one grid at 1280x960 4:3 and 1280x720 16:9; the production run uses flux3-klein, selected by the Star Colonel on 2026-10-25 07:22; the photo is scaled to the frame height and only the sides are generated; upscaling is deferred by the Star Colonel's order of 2026-10-25 06:00; the faces stay unchanged, the added area continues the scene, and no person appears beyond those already in the photo"; reason: keeps the whole criterion: every extender compared in the bench and flux3-klein named for production, plus the unchanged frame and face rules
  - log: 2026-10-25T09:32:58Z @kj closed: production run completed on all photos
- [-] `ACC-VIDEO-23-UPSCALE` **Clip frames upscaled** - HIGH; after the image-to-video render the generated frames are upscaled with the upscaler chosen in notebook 01 to 2048x1536 at 30 fps, and the sidecar records the upscaler, the scale and the seconds per frame
  - test: probe a delivered clip for 2048x1536 at 30 fps, read its sidecar for the upscaler and the scale, and compare a frame against the unscaled render
  - test-tags: FUNCTIONAL
  - log: 2026-10-25T01:22:49Z @kj added
  - log: 2026-10-25T01:23:37Z @kj rejected: deferred as future ambition; reason: the Star Colonel named it on 2026-10-25 as future ambition, not ordered now: upscale the generated clip frames after the image-to-video render
- [x] `ACC-VIDEO-27-BENCH` **Every viable model in the bench** - HIGH; notebook 01 covers every viable local extender, FLUX.1 Fill dev and FLUX 3 Image Klein included; each model either renders or is excluded in bench.json with its reason
  - evidence: bench.json runs FLUX Fill and FLUX 3 Klein and lists every excluded model with its reason, including the licence and ComfyUI route rejections
  - test: read bench.json, assert FLUX.1 Fill, FLUX 3 Klein, Qwen-Image with the InstantX ControlNet, Qwen-Image-Edit 2509 and 2511, SDXL inpainting and OmniGen2 each carry a result or an exclusion reason
  - test-tags: MANUAL
  - log: 2026-10-25T02:04:48Z @kj added
  - log: 2026-10-25T05:04:49Z @kj amended text "notebook 01 covers every viable local extender, FLUX.1 Fill dev and FLUX 3 Image Klein included, and every upscaler; each model either renders or is excluded in bench.json with its reason" -> "notebook 01 covers every viable local extender, FLUX.1 Fill dev and FLUX 3 Image Klein included; each model either renders or is excluded in bench.json with its reason"; reason: Star Colonel order 2026-10-25 06:00: "do 1280x based images; the time for rendering will drop sharply" and "we can upscale them later"; upscaling leaves the bench run, so the bench compares extenders only
  - log: 2026-10-25T06:07:25Z @kj Star Colonel judged the flux3-klein tiles well extended at both frames on 2026-10-25 07:15 and 07:18: 16:9 "well extended", 4:3 "same, well rendered"; the gate had rejected both for the completed face of the girl cut off at the photo's left edge
  - log: 2026-10-26T03:37:51Z @kj closed
- [ ] `ACC-VIDEO-29-LIVING` **Living photograph style** - HIGH; every clip is a living photograph whose motion runs at natural real-time speed, stated in the prompt and measured in the clip; the person shifts posture and makes small movements of ordinary pace; the face keeps exactly the photo's expression, with one natural blink; IMG_0020 keeps its walk
  - test: measure motion per second against the 5 s clip of the same stem; the 6 s clips scored a median 0.82 of the 5 s rate
  - test-tags: MANUAL
  - log: 2026-10-25T09:32:51Z @kj added
  - log: 2026-10-25T20:29:41Z @kj edited text "every clip is a living photograph: the person only shifts posture and makes small slow movements; the face keeps exactly the photo's expression, with one natural blink and at most the eyes softening; IMG_0020 keeps its walk and IMG_7645 already fits" -> "every clip is a living photograph whose motion runs at natural real-time speed, stated in the prompt and measured in the clip; the person shifts posture and makes small movements of ordinary pace; the face keeps exactly the photo's expression, with one natural blink; IMG_0020 keeps its walk"; test "view each clip beside its source photo; assert only a posture shift and small slow movements, one blink, and the photo's expression, with IMG_0020's walk excepted" -> "measure motion per second against the 5 s clip of the same stem; the 6 s clips scored a median 0.82 of the 5 s rate"
  - log: 2026-10-25T20:29:53Z @kj overridden-by DEF-ANIM-8-SLOWMO removed - criterion amended to natural real-time speed instead of overridden
  - log: 2026-10-27T02:48:18Z @kj attempted: pacing fix at 1024x768, 10 s, seed 42; IMG_8564 M1 20.46 and M2 16.84 motion per second against delivered 16.57 and simple control 4.98; IMG_8716 R2 12.84 against delivered 7.03 and control 7.39; the Star Colonel views the clips; tmp/media/h3-confirm-1024/, tmp/media/h3-slowmo-8716/
- [ ] `ACC-VIDEO-30-SCENE` **Still scene** - HIGH; no speaking; nothing is pressed, drawn, lifted, picked up or built; the hands rest where they are, the camera does not move, the room and every prop stay still, and nobody new enters the frame
  - test: view each clip beside its source photo; assert the lips and teeth stay as in the photo and still, the hands do not act, the camera and props do not move, and no new person appears
  - test-tags: MANUAL
  - log: 2026-10-25T09:32:51Z @kj added
  - log: 2026-10-27T02:48:21Z @kj attempted: speech at 1024x768; Chinese stillness S5 3.5648 mouth median and stronger wording T2 3.2561 against same-prompt control 5.7885 (0.62x and 0.56x), ratios 1.42 and 1.30 to LivePortrait baseline 2.5043; none eliminated mouth motion; the Star Colonel views; tmp/media/h3-speech-iter-1024/
- [x] `ACC-VIDEO-31-NO-FAULT` **No speech word in a positive prompt** - HIGH; a positive prompt never names the speech fault: no speak, talk, laugh, word, mouth or jaw wording; every hold is written as the photo's lips and teeth staying still
  - evidence: scan of the ten prompts finds no speak/talk/laugh/word/mouth/jaw; no delivered clip carries an audio stream
  - overrides: ACC-VIDEO-20-NOTALK
  - test: grep the prompt cells and the H3 sidecars for speak, talk, laugh, word, mouth and jaw; assert no hit in a positive prompt and a lips-and-teeth hold where the mouth is held
  - test-tags: MANUAL
  - mechanism: 2026-10-25T09:32:51Z @kj H3 generates audio with the video: node 6 MiniMaxH3ImageToVideo feeds node 13 VAEDecodeAudio and node 14 CreateVideo, so a positive prompt naming speech drives the lips
  - log: 2026-10-25T09:32:51Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-VIDEO-32-H3` **MiniMax H3 chosen** - HIGH; MiniMax H3 is the chosen model for the living-photograph clips; its graph generates video and audio jointly and has no negative conditioning
  - evidence: H3 is the production model, ten 10 s clips delivered; its graph has no negative conditioning
  - test: read tmp/workflows/image-to-video/workflow-api-minimax.json (the graph setup-minimax.json names); assert node 6 MiniMaxH3ImageToVideo feeds nodes 13 and 14, and one BasicGuider with positive conditioning only
  - test-tags: MANUAL
  - log: 2026-10-25T09:32:52Z @kj added
  - log: 2026-10-25T09:33:26Z @kj edited test "read tmp/workflows/image-to-video/setup-minimax.json; assert the MiniMax H3 graph, node 6 feeding nodes 13 and 14, and one BasicGuider with positive conditioning only" -> "read tmp/workflows/image-to-video/workflow-api-minimax.json (the graph setup-minimax.json names); assert node 6 MiniMaxH3ImageToVideo feeds nodes 13 and 14, and one BasicGuider with positive conditioning only"
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-VIDEO-33-LTX-NEG` **LTX-2.5 negative prompt** - MEDIUM; LTX-2.5 is the alternative model and every render applies its explicit negative prompt, which carries the speech ban alongside the camera and face holds
  - evidence: LTX sidecars record the 1372-character negative prompt: 1163 shared plus 207 per stem
  - test: read notebook 04 and one LTX sidecar; assert the negative prompt is filled from references/ltx-negative-prompt.txt and names speech, dialogue and camera movement
  - test-tags: MANUAL
  - log: 2026-10-25T09:32:52Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-VIDEO-34-LIVEPORTRAIT` **LivePortrait pixel-preserving alternative** - MEDIUM; LivePortrait is the pixel-preserving alternative: it warps the photo's own pixels rather than redrawing the frame, so every pixel outside the animated face crop stays the photo's, and it cannot speak
  - evidence: LivePortrait trial tmp/media/liveportrait/IMG_7666.mp4 warps the photo's pixels, 150 frames at 30 fps, no audio
  - test: compare a notebook 03 clip with its source photo outside the face crop; assert only H.264 encode-level change, 0.04-0.06 on the 0-255 scale as notebook 03 measured
  - test-tags: FUNCTIONAL
  - mechanism: 2026-10-25T09:32:52Z @kj the node warps and pastes the photo's own pixels and has no audio branch, so it has no speech to sync
  - log: 2026-10-25T09:32:52Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-VIDEO-36-TEN-SECONDS` **Ten second clips at 30 fps** - HIGH; every production clip is 10.00 s at 30 fps, 300 frames; H3 renders LENGTH 243 single pass and LTX two 121-frame natives chained and interpolated; clips land in minimax-h3-10s/ or ltx25-i2v-10s/ with sidecars
  - evidence: all 18 clips probe 300 frames at 30 fps, 10.00 s; H3 LENGTH 243 single pass, LTX two 121-frame parts chained
  - test: probe the clip for 300 frames at 30 fps and 10.00 s; motion measured per stem against the 5 s clip of the same frame; LTX uses the two-part chain
  - test-tags: FUNCTIONAL, MANUAL
  - log: 2026-10-25T20:29:41Z @kj added
  - log: 2026-10-26T02:29:31Z @kj edited test "probe the clip for 300 frames at 30 fps and 10.00 s; motion per second at or above the 5 s baseline" -> "probe the clip for 300 frames at 30 fps and 10.00 s; motion measured per stem against the 5 s clip of the same frame; LTX uses the two-part chain"
  - log: 2026-10-26T02:29:33Z @kj measured: delivered 10 s motion per second against the 5 s clip, H3 275/221, 35/42, 15/18, 5.0/5.1, 17/26, 7.0/6.2, 9.8/9.5, 21/50, 13/29, 57/31 and LTX 38.6/29.0, 71.1/91.6, 66.9/52.7, 95.8/62.0, 80.0/133.0, 27.1/253.0, 57.3/51.1, 61.5/65.2
  - log: 2026-10-26T02:49:43Z @kj edited text "every production clip is 10.00 s at 30 fps, 300 frames, interpolated at natural speed from a native 24 fps render (H3 LENGTH 243, LTX LENGTH 241); it lands in minimax-h3-10s/ or ltx25-i2v-10s/ with its sidecar" -> "every production clip is 10.00 s at 30 fps, 300 frames; H3 renders LENGTH 243 single pass and LTX two 121-frame natives chained and interpolated; clips land in minimax-h3-10s/ or ltx25-i2v-10s/ with sidecars"
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-VIDEO-37-RATE` **Prompt states the rate** - HIGH; the motion clause states a real-time rate and fills the whole clip; no slow, small, gently or easing wording in the motion clause; the prompt stays under 600 characters
  - evidence: ten prompts carry normal real-time speed and timed beats with no slow/small/gently/easing; measured motion 20.0 to 275.0 per second
  - test: read the prepared prompt; measure the clip motion per second
  - test-tags: MANUAL
  - log: 2026-10-25T20:29:42Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed

## Render pipeline `PIPE`

Shared code that submits a render to ComfyUI and converts the result to 30 fps

- log: 2026-10-24T22:38:56Z @kj category created

- [x] `ACC-PIPE-8-CLIENT` **Client submits a render** - HIGH; one module client submits an image-to-video graph to a ComfyUI server and saves the returned clip
  - evidence: render_h3_10s.py and render_ltx_chain_10s.py submitted graphs to ComfyUI and wrote readable clips; 18 delivered
  - test: submit one graph to a running ComfyUI server, assert a readable clip is written
  - test-tags: FUNCTIONAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-PIPE-9-FPS` **30 fps interpolation** - HIGH; every clip is converted to 30 fps with learned frame interpolation, never duplicated or blended frames
  - evidence: every delivered clip probes 300 frames at 30 fps; frame_interpolation.schedule maps each output moment to the same native moment, no duplicates
  - test: ffprobe each clip for 30 fps and inspect frames for duplicates or blends
  - test-tags: FUNCTIONAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-PIPE-10-TESTS` **Unit tests green** - HIGH; the module helpers that need no GPU are covered by pytest and the suite passes
  - evidence: make test in the project root: 73 passed in 2.39s on 2026-10-25; tests/test_animation.py and tests/test_image_to_video.py at 100 percent
  - test: make test green
  - test-tags: UNIT
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-25T09:32:58Z @kj closed: make test green after the review fixes
- [x] `ACC-PIPE-11-LINT` **Lint green** - MEDIUM; ruff reports no violation and formatting is clean
  - evidence: make lint in the project root: ruff format --check 25 files already formatted, ruff check All checks passed
  - test: make lint green
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-25T09:32:58Z @kj closed: make lint green after the review fixes
- [x] `ACC-PIPE-35-SHIP` **Adversarial review to SHIP** - HIGH; the imaging and animation code reaches verdict SHIP from the adversarial review, with no open must after three rounds and four edits
  - evidence: tmp/workflows/review/ship-report.md: round 3 verdict SHIP after three musts in round 1 and one label must in round 2; make test 73 passed in 2.39s; make lint clean
  - test: read tmp/workflows/review/ship-report.md; assert the round-3 verdict SHIP and no open must
  - test-tags: MANUAL
  - log: 2026-10-25T09:32:58Z @kj added
  - log: 2026-10-25T09:32:58Z @kj closed: review reached SHIP

## Release and privacy `RELE`

Rules that keep a child's media out of the repository and generated files distinguishable

- log: 2026-10-24T22:38:56Z @kj category created

- [x] `ACC-RELE-12-NOCHILD` **No child media in notebooks** - CRITICAL; no notebook holds image or video data of a child; photos and clips appear only as links
  - evidence: 10 notebooks scanned (checkpoints excluded): 0 base64 image or video payloads; photos appear only as Image(url=...) links
  - test: grep notebooks for image/png, image/jpeg and video/mp4 payloads, assert none
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-26T03:36:52Z @kj closed
- [x] `ACC-RELE-13-OUTPUTS` **Notebooks committed without outputs** - CRITICAL; every notebook in the repository has all outputs and execution counts cleared
  - evidence: all 9 notebooks outside .ipynb_checkpoints have outputs [] and execution_count null; 03 was cleared at 04:44
  - test: open each notebook, assert no cell outputs and no execution counts
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-RELE-14-HOOK` **Commit hook rejects outputs** - HIGH; the pre-commit hook rejects a commit that stages a notebook with outputs
  - evidence: core.hooksPath=.githooks; a staged notebook with an output was rejected (exit 1) and a clean notebook committed (exit 0) in scratch repo /tmp/hooktest.4zqkEr
  - test: stage a notebook with an output, run git commit, assert the hook rejects it
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:56Z @kj added
  - log: 2026-10-24T22:43:44Z @kj closed: retested the commit hook
- [x] `ACC-RELE-15-ORIGINALS` **Originals unchanged** - HIGH; no file under data/raw/ or data/external/henryk-urodziny-2026/images/ is modified
  - evidence: find data/raw data/external/henryk-urodziny-2026/images -newermt '2026-10-24 18:32' returns no file
  - test: find those paths -newermt '2026-10-24 18:32', assert no file changed
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:57Z @kj added
  - log: 2026-10-24T22:43:44Z @kj closed: checked the originals
- [ ] `ACC-RELE-16-DATA` **Only metadata staged under data** - MEDIUM; a commit stages only .md files under data/, never a photo, clip or weight
  - test: git diff --cached --name-only, assert only .md files under data/
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:57Z @kj added
- [x] `ACC-RELE-28-OUTPUT-LOCATION` **Output location** - HIGH; only a production run writes into data/; bench and test renders write under tmp/media/, every output carries its sidecar, and notebooks link media by relative path
  - evidence: notebook 04 writes tmp/media/ltx25-i2v-probe; data/processed holds only the production H3 10 s run with sidecars
  - test: run notebook 01 and one test render, assert their outputs land under tmp/media and nothing new appears under data/; git status shows no media staged
  - test-tags: MANUAL
  - log: 2026-10-25T02:13:02Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed

## Model selection record `DOCS`

The written record of the model choice for the image-to-video test

- log: 2026-10-24T22:38:57Z @kj category created

- [x] `ACC-DOCS-17-RESEARCH` **Photo animation research** - MEDIUM; the research document ranks purpose-built candidates and cites a source for each claim
  - evidence: docs/model-selection/photo-animation.md holds 66 source URLs and ranks LivePortrait, FantasyPortrait and FlashPortrait with per-claim sources
  - test: read docs/model-selection/photo-animation.md, assert each ranked candidate cites a source
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:57Z @kj added
  - log: 2026-10-24T22:43:44Z @kj closed: verified the research document
- [x] `ACC-DOCS-18-CHOICE` **Image-to-video choice** - MEDIUM; the choice document states the model for notebook 03, the Wan2.2 files and settings, and whether Seedance has downloadable weights
  - evidence: tmp/workflows/image-to-video/choose.md line 3 names LTX-2.5 for notebook 03 and the Wan2.2-I2V-A14B files; the Seedance section states no version has downloadable weights
  - test: read tmp/workflows/image-to-video/choose.md, assert all three parts
  - test-tags: MANUAL
  - log: 2026-10-24T22:38:57Z @kj added
  - log: 2026-10-24T22:43:44Z @kj closed: verified the choice document
- [x] `ACC-DOCS-22-EXTENDER` **Extender model research** - MEDIUM; the research document ranks outpainting and upscaling models that run locally, cites a source for each claim, and the choice names the weights, the licence and the VRAM need
  - evidence: docs/model-selection/image-extender.md ranks local extenders with a source per claim and names weights, licence and VRAM need
  - test: read docs/model-selection/image-extender.md, assert each ranked candidate cites a source and the choice states weights, licence and VRAM
  - test-tags: MANUAL
  - log: 2026-10-25T00:43:53Z @kj added
  - log: 2026-10-26T03:36:53Z @kj closed
- [x] `ACC-DOCS-26-FUNCRAFT` **Funcraft model research** - LOW; the research names every model Funcraft uses, by role, with a source for each claim, its open-weights status, its licence, and whether it is already in our stack
  - evidence: docs/model-selection/funcraft.md identifies Funcraft as the efecte8/funcraft AI photo editor, names its two models (SDXL 1.0 base, LCM-LoRA SDXL) with a source URL, open-weights status and licence each, and maps local equivalents.
  - test: read tmp/workflows/model-research/funcraft.md, assert each named model carries a source URL and a licence note
  - test-tags: MANUAL
  - log: 2026-10-25T02:04:40Z @kj added
  - log: 2026-10-26T03:46:57Z @kj closed

## Model store `STORE`

Model weights kept on the NAS so they are available locally

- log: 2026-10-25T02:04:34Z @kj category created

- [x] `ACC-STORE-24-LOCAL` **Models stored on the NAS** - HIGH; every bench weight, Qwen 3.8 Flash and DeepSeek 4.1 Flash sit under /mnt/nas-shared/models/<Org>--<Model>/ with a sidecar naming repository, byte sizes, sha256 and licence
  - evidence: copy report complete with 0 issues, all 22 copied folders sha256-verified, 16 superseded folders in /mnt/nas-shared/.nas-trash/2026-10-26-models, INDEX.md rebuilt with 12 rows
  - test: ls /mnt/nas-shared/models, assert a folder and a sidecar for every model named in bench.json and resolve.json, and compare sha256
  - test-tags: MANUAL
  - log: 2026-10-25T02:04:34Z @kj added
  - log: 2026-10-26T10:01:05Z @kj partial: all 22 folders and sidecars exist; 15 of 22 models sha256-verified; unmatched on Comfy-Org--Qwen-Image, Comfy-Org--Qwen-Image-Edit_ComfyUI, Comfy-Org--OmniGen-2, black-forest-labs--FLUX.1-Fill-dev, black-forest-labs--FLUX.1-Kontext-dev, comfyanonymous--flux_text_encoders and black-forest-labs--flux-3-image-klein; the two Qwen-Image files are being rewritten in place; NAS reads at 3-5 MB/s
  - log: 2026-10-26T20:32:49Z @kj root cause: one full-file NFS COMMIT exceeds the soft mount 15 s timeout, so the tail is lost; per-chunk fsync keeps each COMMIT at 16 MiB; probe: 1420 fsync calls, sha256 matched and replaced flux1-kontext-dev.safetensors at 23,802,947,360 B in 278 s
  - log: 2026-10-26T22:24:45Z @kj copy verified, 16 superseded image folders moved to /mnt/nas-shared/.nas-trash/2026-10-26-models, index rebuilt to 12 rows
  - log: 2026-10-26T22:24:47Z @kj closed
- [x] `ACC-STORE-25-INDEX` **NAS model index** - MEDIUM; the index lists every model directory with its file count, total size, licence, date added and sidecar, and is rebuilt after every copy
  - evidence: /mnt/nas-shared/models/INDEX.md has 28 rows; all 22 folders copied by the extender run appear with file count, size, licence and newest-file date; rebuilt with python3 -I /home/lab/workspace/private/henryk/henryk-media/tmp/workflows/nas-llm/nas_index.py
  - test: read /mnt/nas-shared/models/INDEX.md, assert one row per model directory, the store total, and that a newly copied model appears
  - test-tags: MANUAL
  - log: 2026-10-25T02:04:37Z @kj added
  - log: 2026-10-26T10:01:08Z @kj closed

