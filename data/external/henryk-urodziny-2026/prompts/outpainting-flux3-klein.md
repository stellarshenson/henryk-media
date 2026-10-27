# Outpainting with FLUX 3 Klein

Model `black-forest-labs/flux-3-image-klein` (`flux3-image-klein-bf16.safetensors`, 5.6B bf16 distilled) with LoRA `ausboss/FLUX-3-Image-Klein-Outpaint-LoRA` (`flux-3-image-klein-outpaint.safetensors`, strength 1.5 through `LoraLoaderModelOnly`).

Source: `.agents/skills/image-outpainting/references/extender-recipe.md`

## Positive prompt

```
Outpaint the image: replace the solid grey areas with an empty continuation of the same room and scene beyond the frame, keeping the existing picture unchanged. Continue the same floor, the same wall and background and the same soft indoor daylight as the photo, at the same perspective, scale and brightness. The added area holds no person, no child, no face, no hands and no figure; keep every person already in the photo exactly as they are, with the same faces, expressions, hair and clothes.
```

## Negative prompt

```
person, child, man, woman, crowd, face, hands, portrait, new person, extra person, second child, mirrored child, reflected child, reflection of a person, different face, changed expression, deformed, distorted, blurry, low quality, text, watermark
```

The negative prompt is inert at cfg 1.0; the graph conditions on the positive prompt only.

## Settings

| Setting | Value |
|---|---|
| steps | 16 |
| cfg | 1.0 |
| sampler | euler |
| scheduler | simple |
| denoise | 1.0 |
| LoRA strength | 1.5 |
| render scale | 1.0 (retry 0.71, then 0.5) |
| seed | 42-47 (six attempts, first passing frame kept) |
