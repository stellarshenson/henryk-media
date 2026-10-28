# father-and-henry-watching.webp

Generated drawing, not a photograph or a recording. An illustration made by FLUX 3 Klein in two renders: the scene from a text prompt and three reference images, and the picture on the monitor screen from a text prompt and two reference images, composited into the display.

## Scene references

- Image 1, the father: drawn from IMG_0020, the Star Colonel's own photo, used with his authorisation
- Image 2, the boy: drawn from Henry in IMG_8840 at the Star Colonel's request; the girl in that photo is excluded from the crop
- Image 3 of the scene render was the cat in the birthday video at 129.5 s, crop box [0, 253, 434, 768]; no person is in the crop (0 faces, the person box outside it); the screen picture it produced is fully covered by the composite below

## Screen picture references

- Image 1: a frame of the birthday video the Star Colonel supplied on 2026-10-28, showing only the cat and him
- Image 2, the man: drawn from IMG_0020, the Star Colonel's own photo, used with his authorisation
- At his request the man is moved to the right of his place in the frame, so more of his face shows beside the cat

Generated locally on the workstation GPU through a ComfyUI server bound to 127.0.0.1. No photo of Henry is in the repository, and no photo was sent to an external service.

## Scene settings

- Scene render: `/home/lab/workspace/private/henryk/henryk-media/tmp/media/readme-drawings/watch/father-and-henry-watching-s42.png`
- Model: `flux3-image-klein-bf16.safetensors`, registry entry `flux3-klein`, without the outpaint LoRA
- Graph: `/home/lab/workspace/private/henryk/henryk-media/tmp/workflows/readme-drawings/flux3_klein_ref.json` (ReferenceMultiLatent, references resized to 1.0 MP)
- Seed: 42
- Steps 16, cfg 1.0, sampler euler, scheduler simple, denoise 1.0
- Size: 1792x1024, empty latent
- GPU: `GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5`
- Render seconds: 34.1

## Screen picture settings

- Screen render: `/home/lab/workspace/private/henryk/henryk-media/tmp/media/readme-drawings/screen/screen-s42.png`
- Model: `flux3-image-klein-bf16.safetensors`, registry entry `flux3-klein`, without the outpaint LoRA
- Graph: `/home/lab/workspace/private/henryk/henryk-media/tmp/workflows/readme-drawings/flux3_klein_ref.json` (ReferenceMultiLatent, references resized to 1.0 MP), with the third LoadImage node removed
- Seed: 42
- Steps 16, cfg 1.0, sampler euler, scheduler simple, denoise 1.0
- Size: 992x1008, empty latent
- GPU: `GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5`
- Render seconds: 36.2

## Composite

- Composite: `/home/lab/workspace/private/henryk/henryk-media/tmp/media/readme-drawings/screen/father-and-henry-watching-s42.png`
- Script: `/home/lab/workspace/private/henryk/henryk-media/tmp/workflows/readme-drawings/composite_screen.py`
- The screen picture is shrunk with PIL LANCZOS to 362x406, then put into the display quad (TL, TR, BR, BL) [[141.7, 349.9], [501.4, 382.0], [537.0, 704.6], [185.8, 752.7]] by a perspective warp (cv2.warpPerspective INTER_LANCZOS4, BORDER_REPLICATE), with a 1.5 px blend at the display edge
- The rest of the drawing is unchanged: every pixel more than 3 px outside the display equals the scene render (max difference 0)
- Conversion: PNG to WebP, quality 90, full size, with Pillow
- Trim: the published WebP is the composite of the screen picture cropped to box (left, upper, right, lower) [0, 18, 992, 997] by `/home/lab/workspace/private/henryk/henryk-media/tmp/workflows/readme-drawings/trim_screen.py`, removing the pale paper rows at its top and bottom, composited with the same script and quad to `/home/lab/workspace/private/henryk/henryk-media/tmp/media/readme-drawings/screen/father-and-henry-watching-s42-trim.png`

## Gate result

- Scene: pass (two_people yes, no_extra_person yes, drawn yes, father_likeness yes, screen_faces_them yes, cat_on_screen yes, anatomy yes, no_text_banner yes)
- Composite: pass (scene_unchanged yes, screen_shows_frame yes, father_face_visible yes, drawn yes, no_extra_person yes, fits_screen yes, anatomy yes, no_text_banner yes)
- Gate note: cat's right ear hides his right eye; his left eye, nose, smile and stubble are visible; more of his face than in screen-frame.png, where the ear hides the mouth. Blank cream paper band across the full width: top 1.6% and bottom 0.4% of the picture height. Figurine, curtain and window as in the frame; no text.

## Scene prompt

```
Create a hand-drawn illustration in coloured pencil and ink on warm cream paper, loose sketch lines and soft cross-hatching, muted warm palette of sepia, terracotta, soft blue and orange, a light watercolour wash in the background, storybook feel. The father is the man from image 1, with his face, hair and beard, wearing a blue shirt with rolled sleeves. His son is the boy from image 2, with his face and hair, wearing an orange t-shirt. Later the same evening the father and his son sit together on a sofa in a cosy room, seen from the side at a three-quarter angle. A computer monitor stands on a low table in front of the sofa, turned toward them, so its screen faces the father and son and is seen at an angle. On the screen is the cat from image 3, drawn in the same coloured-pencil style. The father and son look at the screen; the boy points at the cat and smiles with wonder, the father has his arm around him and smiles. Warm lamp light. Only these two people are in the room.
```

## Screen picture prompt

```
Create a hand-drawn illustration in coloured pencil and ink on warm cream paper, loose sketch lines and soft cross-hatching, muted warm palette of sepia, terracotta, soft blue and orange, storybook feel. Draw the scene of image 1 as one still frame. A grey British shorthair cat's face in close-up fills the left and centre of the picture, with large round orange eyes and a small open mouth, looking straight out; behind it a warm room with a curtain, a window and a small wooden figurine on a shelf. Behind the cat on the right is the man from image 2, with his face, spiky dark hair and grey-flecked stubble, in a dark top; he is further to the right than in image 1, so his whole face is visible beside the cat's ear, and he smiles. Only the cat and this one man are in the picture. No text.
```
