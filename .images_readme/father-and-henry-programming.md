# father-and-henry-programming.webp

Generated drawing, not a photograph or a recording. An illustration made by FLUX 3 Klein from a text prompt and three reference images.

## References

- Image 1, the father: drawn from IMG_0020, the Star Colonel's own photo, used with his authorisation
- Image 2, the boy: drawn from Henry in IMG_8840 at the Star Colonel's request; the girl in that photo is excluded from the crop
- Image 3, the monitor picture: drawn from a frame of the IMG_8840 MiniMax H3 clip at 4.0 s; the girl is excluded from the crop

Generated locally on the workstation GPU through a ComfyUI server bound to 127.0.0.1. No photo is in the repository, and no photo was sent to an external service.

## Settings

- Source candidate: `/home/lab/workspace/private/henryk/henryk-media/tmp/media/readme-drawings/ref/father-and-henry-programming-s42.png`
- Model: `flux3-image-klein-bf16.safetensors`, registry entry `flux3-klein`, without the outpaint LoRA
- Graph: `/home/lab/workspace/private/henryk/henryk-media/tmp/workflows/readme-drawings/flux3_klein_ref.json` (ReferenceMultiLatent, references resized to 1.0 MP)
- Seed: 42
- Steps 16, cfg 1.0, sampler euler, scheduler simple, denoise 1.0
- Size: 1792x1024, empty latent
- GPU: `GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5`
- Render seconds: 34.6
- Conversion: PNG to WebP, quality 90, full size, with Pillow

## Gate result

- Result: pass (two_people yes, no_girl yes, drawn yes, father_likeness yes, screen_frame yes, scene_match yes, anatomy yes, no_text_banner yes)
- Gate note: boy points at the screen; the father types with one visible hand; the screen shows code beside a single drawn smiling curly-haired boy; the father has spiky dark hair with faded sides and a short stubble beard as in IMG_0020

## Prompt

```
Create a hand-drawn illustration in coloured pencil and ink on warm cream paper, loose sketch lines and soft cross-hatching, muted warm palette of sepia, terracotta, soft blue and orange, a light watercolour wash in the background, storybook feel. The father is the man from image 1, with his face, hair and beard, wearing a blue shirt with rolled sleeves. His son is the boy from image 2, with his face and hair, wearing an orange t-shirt. The father and his son sit side by side at a wooden desk in a cosy home study, programming together on a computer. The father types on the keyboard while the boy points at the large monitor, which shows colourful lines of code beside a picture of the boy from image 3 drawn in the same coloured-pencil style. Both look at the screen, focused and smiling. A bookshelf in the background, a mug of pencils on the desk, warm lamp light. Only these two people are in the room.
```
