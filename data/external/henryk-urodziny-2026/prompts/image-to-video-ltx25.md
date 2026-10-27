# Image-to-video with LTX-2.5

| Setting | Value |
|---|---|
| Model | LTX-2.5 |
| Checkpoint | Lightricks 22B dev checkpoint bf16 |
| Short name | `ltx25-i2v` |
| Revision | `49b093a39c19169a8a81721dcc541e07e945232f` |
| Weights | `ltx-2.5-22b-dev-transformer-bf16`, `gemma4-12b-with-proj-ltx-2.5-bf16`, `ltx-2.5-video-vae-bf16`, `ltx-2.5-audio-vae-bf16` |
| GPU | `GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5` |
| nvidia-smi index | 1 |
| GPU model | RTX PRO 6000 96 GB |
| Port | 8190 |
| Canvas | 1024 x 768 |
| `LENGTH` | 121 per part |
| Parts | two, joined at frame 120 |
| Seed | 42 |
| Steps | 30 |
| Sampler | `euler` |
| Scheduler | `LTXVScheduler max_shift 2.05 base_shift 0.95 stretch terminal 0.1` |
| `cfg_video` | 3.0 |
| `cfg_audio` | 7.0 |
| `stg_scale` | 1.0 |
| `stg_blocks` | 28 |
| `modality_scale` | 3.0 |
| `image_strength` | 1.0 |
| Output | 300 frames at 30 fps after FILM fp16 interpolation |

Sources: `tmp/workflows/ltx25-preview/render-settings.json`, `tmp/workflows/ltx25-preview/chain-ltx-10s.json`, `tmp/workflows/image-to-video/setup-chosen.json`

## Generic sentence

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live;
```

## Negative prompt

```
blurry, out of focus, overexposed, underexposed, low contrast, washed out colors, excessive noise, grainy texture, poor lighting, flickering, motion blur, distorted proportions, unnatural skin tones, deformed facial features, asymmetrical face, missing facial features, extra limbs, disfigured hands, wrong hand count, artifacts around text, inconsistent perspective, camera shake, incorrect depth of field, background too sharp, background clutter, distracting reflections, harsh shadows, inconsistent lighting direction, color banding, cartoonish rendering, 3D CGI look, unrealistic materials, uncanny valley effect, incorrect ethnicity, wrong gender, exaggerated expressions, wrong gaze direction, mismatched lip sync, silent or muted audio, distorted voice, robotic voice, echo, background noise, off-sync audio, incorrect dialogue, added dialogue, repetitive speech, jittery movement, awkward pauses, incorrect timing, unnatural transitions, inconsistent framing, tilted camera, flat lighting, inconsistent tone, cinematic oversaturation, stylized filters, or AI artifacts. camera movement, zoom, changing face, morphing, distorted hands, extra fingers, text
```

Each stem appends its `negative_extra` to this negative prompt, separated by `, `.

## IMG_7666

Sources: `tmp/workflows/ltx25-preview/prompts/user/IMG_7666.json`, `tmp/workflows/ltx25-preview/prompts/IMG_7666-ltx.json`

**Prompt**

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live; a living photograph, like a moving picture in a newspaper: he moves at normal real-time speed and keeps moving through the whole clip; in the first two seconds he turns his head slightly toward the camera; by four seconds his smile opens and closes; around six seconds he blinks; in the last three seconds he settles his shoulders; his right hand stays flat on the cardboard tortoise and his left on his knee, and the child behind him is removed from the image; the camera holds still and nobody new enters
```

**Negative extra**

```
speech, talking, lip sync, mouthing words, laughing, a new person, someone entering the frame, an extra person, a duplicated person, a background person changing size or place, camera movement, zoom, shaking
```

## IMG_7667

Sources: `tmp/workflows/ltx25-preview/prompts/user/IMG_7667.json`, `tmp/workflows/ltx25-preview/prompts/IMG_7667-ltx.json`

**Prompt**

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live; a living photograph, like a moving picture in a newspaper: he moves at normal real-time speed and keeps moving through the whole clip; in the first two seconds he tilts his head slightly; by four seconds his open grin widens; around six seconds he blinks; in the last three seconds he shifts his weight; his left hand stays on the ship's red edge and his right hand loosely curled at chest height; the camera holds still and nobody new enters
```

**Negative extra**

```
speech, talking, lip sync, mouthing words, laughing, a new person, someone entering the frame, an extra person, a duplicated person, a background person changing size or place, camera movement, zoom, shaking
```

## IMG_8564

Sources: `tmp/workflows/ltx25-preview/prompts/user/IMG_8564.json`, `tmp/workflows/ltx25-preview/prompts/IMG_8564-ltx.json`

**Prompt**

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live; a living photograph, like a moving picture in a newspaper: he moves at normal real-time speed and keeps moving through the whole clip; in the first two seconds he turns his head slightly to his left and looks back at the camera; by four seconds his open grin widens; around six seconds he blinks; in the last three seconds he shifts his weight; he holds the closed book flat in both hands at waist height, the four girls keep their poses and hands as in the photo, and the children cut by the edges stay cut; the camera holds still and nobody new enters
```

**Negative extra**

```
speech, talking, lip sync, mouthing words, laughing, a new person, someone entering the frame, an extra person, a duplicated person, a background person changing size or place, camera movement, zoom, shaking
```

## IMG_8716

Sources: `tmp/workflows/ltx25-preview/prompts/user/IMG_8716.json`, `tmp/workflows/ltx25-preview/prompts/IMG_8716-ltx.json`

**Prompt**

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live; a living photograph, like a moving picture in a newspaper: he moves at normal real-time speed and keeps moving through the whole clip; in the first two seconds he turns his head slightly toward Santa; by four seconds his closed smile warms; around six seconds he blinks; in the last three seconds his hands settle on the bag handles; his hands stay closed around the white gift bag's handles and Santa stays seated and still; the camera holds still and nobody new enters
```

**Negative extra**

```
speech, talking, lip sync, mouthing words, laughing, a new person, someone entering the frame, an extra person, a duplicated person, a background person changing size or place, camera movement, zoom, shaking
```

## IMG_8732

Sources: `tmp/workflows/ltx25-preview/prompts/user/IMG_8732.json`, `tmp/workflows/ltx25-preview/prompts/IMG_8732-ltx.json`

**Prompt**

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live; a living photograph, like a moving picture in a newspaper: he moves at normal real-time speed and keeps moving through the whole clip; in the first two seconds he bows his head a little more over the table; by four seconds his eyes move from the paper to the pencil; around six seconds he blinks; in the last three seconds his shoulders settle; the blue pencil stays raised just off the paper in his right hand and his left hand a loose fist on the table, and he does not draw; the camera holds still and nobody new enters
```

**Negative extra**

```
speech, talking, lip sync, mouthing words, laughing, a new person, someone entering the frame, an extra person, a duplicated person, a background person changing size or place, camera movement, zoom, shaking
```

## IMG_8779

Sources: `tmp/workflows/ltx25-preview/prompts/user/IMG_8779.json`, `tmp/workflows/ltx25-preview/prompts/IMG_8779-ltx.json`

**Prompt**

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live; a living photograph, like a moving picture in a newspaper: he moves at normal real-time speed and keeps moving through the whole clip; in the first two seconds he turns his head a little more over his shoulder; by four seconds his closed smile warms; around six seconds he blinks; in the last three seconds he settles his weight in the sand; his gloved left hand rests on the sand beside the upright sand toy, and the child cut off at the left edge stays cut, with no face forming; the camera holds still and nobody new enters
```

**Negative extra**

```
speech, talking, lip sync, mouthing words, laughing, a new person, someone entering the frame, an extra person, a duplicated person, a background person changing size or place, camera movement, zoom, shaking
```

## IMG_8828

Sources: `tmp/workflows/ltx25-preview/prompts/user/IMG_8828.json`, `tmp/workflows/ltx25-preview/prompts/IMG_8828-ltx.json`

**Prompt**

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live; a living photograph, like a moving picture in a newspaper: he moves at normal real-time speed and keeps moving through the whole clip; in the first two seconds he lifts his head slightly; by four seconds his closed smile warms; around six seconds he blinks; in the last three seconds his raised palm turns a little; the blue glue stick stays flat on the paper in his right hand, his left palm raised open toward the camera, and he does not spread glue; the camera holds still and nobody new enters
```

**Negative extra**

```
speech, talking, lip sync, mouthing words, laughing, a new person, someone entering the frame, an extra person, a duplicated person, a background person changing size or place, camera movement, zoom, shaking
```

## IMG_8840

Sources: `tmp/workflows/ltx25-preview/prompts/user/IMG_8840.json`, `tmp/workflows/ltx25-preview/prompts/IMG_8840-ltx.json`

**Prompt**

```
take the photo and make a small 5-10s animated clip out of this, essentially making the image live; a living photograph, like a moving picture in a newspaper: he moves at normal real-time speed and keeps moving through the whole clip; in the first two seconds he lifts the jar a little; by four seconds his open grin widens; around six seconds he blinks; in the last three seconds he lowers the jar back to the same height; the jar stays upright with its lid level, his left hand keeps the white star card at the bottom-left edge, and the girl on the right keeps her fist under her chin; the camera holds still and nobody new enters
```

**Negative extra**

```
speech, talking, lip sync, mouthing words, laughing, a new person, someone entering the frame, an extra person, a duplicated person, a background person changing size or place, camera movement, zoom, shaking
```
