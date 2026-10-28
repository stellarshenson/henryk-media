# father-and-henry-watching.webp

Generated drawing, not a photograph or a recording. An illustration made by FLUX 3 Klein from a text prompt and three reference images.

## References

- Image 1, the father: drawn from IMG_0020, the Star Colonel's own photo, used with his authorisation
- Image 2, the boy: drawn from Henry in IMG_8840 at the Star Colonel's request; the girl in that photo is excluded from the crop
- Image 3, the screen picture: drawn from the cat in the birthday video at 129.5 s, crop box [0, 253, 434, 768]; no person is in the crop (0 faces, the person box outside it)

Generated locally on the workstation GPU through a ComfyUI server bound to 127.0.0.1. No photo is in the repository, and no photo was sent to an external service.

## Settings

- Source candidate: `/home/lab/workspace/private/henryk/henryk-media/tmp/media/readme-drawings/watch/father-and-henry-watching-s42.png`
- Model: `flux3-image-klein-bf16.safetensors`, registry entry `flux3-klein`, without the outpaint LoRA
- Graph: `/home/lab/workspace/private/henryk/henryk-media/tmp/workflows/readme-drawings/flux3_klein_ref.json` (ReferenceMultiLatent, references resized to 1.0 MP)
- Seed: 42
- Steps 16, cfg 1.0, sampler euler, scheduler simple, denoise 1.0
- Size: 1792x1024, empty latent
- GPU: `GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5`
- Render seconds: 34.1
- Conversion: PNG to WebP, quality 90, full size, with Pillow

## Gate result

- Result: pass (two_people yes, no_extra_person yes, drawn yes, father_likeness yes, screen_faces_them yes, cat_on_screen yes, anatomy yes, no_text_banner yes)
- Gate note: Monitor on the left, turned toward the pair: left edge nearer and taller, left side panel visible, stand behind the screen. Spiky top, faded sides, grey-flecked stubble match father.png. Hands checked at full size: five-digit grip on the boy's arm, normal pointing hand

## Prompt

```
Create a hand-drawn illustration in coloured pencil and ink on warm cream paper, loose sketch lines and soft cross-hatching, muted warm palette of sepia, terracotta, soft blue and orange, a light watercolour wash in the background, storybook feel. The father is the man from image 1, with his face, hair and beard, wearing a blue shirt with rolled sleeves. His son is the boy from image 2, with his face and hair, wearing an orange t-shirt. Later the same evening the father and his son sit together on a sofa in a cosy room, seen from the side at a three-quarter angle. A computer monitor stands on a low table in front of the sofa, turned toward them, so its screen faces the father and son and is seen at an angle. On the screen is the cat from image 3, drawn in the same coloured-pencil style. The father and son look at the screen; the boy points at the cat and smiles with wonder, the father has his arm around him and smiles. Warm lamp light. Only these two people are in the room.
```
