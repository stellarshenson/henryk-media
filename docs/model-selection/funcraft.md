# Henryk Media - Funcraft model research v1

Status: RESEARCH NOTE, 2026-10-26. The order named Funcraft without a URL; the identification is unconfirmed.

## Contents

- [1. Subject](#1.-Subject)
- [2. Models](#2.-Models)
- [3. Local equivalents](#3.-Local-equivalents)
- [4. Name disambiguation](#4.-Name-disambiguation)
- [5. Evidence gaps](#5.-Evidence-gaps)
- [6. Sources](#6.-Sources)

## 1. Subject

This section identifies the product named Funcraft and states what it does.

- The order of 2026-10-25 named "funcraft" with no URL, company or product type [1]
- The only AI photo-editing project indexed under the name is the GitHub repository `efecte8/funcraft` [2]
- The repository describes Funcraft as "a free generative AI photo editing tool" that "uses SDXL 1.0 model" [2]
- Funcraft is an open-source desktop GUI with a Google Colab backend; the documented setup runs the model in Colab and reaches it through an ngrok URL [3]
- The GUI offers three pipelines: text-to-image, image-to-image and inpainting [3]
- The repository code is Apache-2.0 [4]
- The repository was created on 2023-07-19 and last pushed on 2024-11-12; it has 6 stars, no releases and no homepage [5]
- Funcraft edits still images and names no photo-animation, video or audio model [3][6]
- The identification is unconfirmed: the name has several unrelated uses (section 4), and no hosted AI photo service named Funcraft is indexed (section 5)

## 2. Models

This section lists every model the Funcraft notebook loads and states the licence recorded for each.

| Role | Model | Exact identifier | Weights | Licence | Source |
|---|---|---|---|---|---|
| Base image model | Stable Diffusion XL 1.0 | `stabilityai/stable-diffusion-xl-base-1.0`, fp16 variant | Open weights, not gated | CreativeML Open RAIL++-M (`openrail++`) | [7] |
| Sampling accelerator | LCM-LoRA for SDXL | `latent-consistency/lcm-lora-sdxl` | Open weights, not gated; 197M parameters; 393,855,224 B | `openrail++` as stated on the model card | [8] |

- The notebook loads exactly these two identifiers [6]
- The notebook sets the scheduler to `LCMScheduler`, loads the LoRA as adapter `lcm` and fuses it into the base pipeline [6]
- Text-to-image uses the base pipeline; image-to-image and inpainting are derived from it with `AutoPipelineForImage2Image.from_pipe` and `AutoPipelineForInpainting.from_pipe` [6]
- No second checkpoint is loaded [6]
- The default sampling is 4 steps with `guidance_scale` 1.0; image-to-image uses strength 0.8 and inpainting strength 0.7 [6]
- The README states an average of about 5 seconds per image on a free Colab T4 [3]
- The LCM-LoRA card states a reduction to 2 to 8 inference steps [8]
- The notebook and README name no separate VAE, refiner, ControlNet, adapter, safety classifier or upscaler [3][6]
- The README names no video model [3]

## 3. Local equivalents

This section maps each Funcraft component to the project's local weights and records what is missing.

| Funcraft component | Local counterpart | Licence | Location | Status |
|---|---|---|---|---|
| SDXL 1.0 base | `sd_xl_base_1.0.safetensors` | CreativeML Open RAIL++-M [7] | `models/photo-animation/ComfyUI/models/checkpoints/` | Present; 6,938,078,334 B; sha256 matches the Hugging Face file; registered in the imaging registry [9] |
| LCM-LoRA SDXL | None | - | `models/photo-animation/ComfyUI/models/loras/` | Not present [9] |
| Text-to-image | SDXL 1.0 base | CreativeML Open RAIL++-M [7] | ComfyUI checkpoints | Present; no recorded project run uses it for text-to-image [9] |
| Image-to-image | SDXL 1.0 base | CreativeML Open RAIL++-M [7] | ComfyUI checkpoints | Present; no recorded project run uses it for image-to-image [9] |
| Image editing | Qwen-Image-Edit-2511 | Apache-2.0 [10][13] | ComfyUI diffusion models | Present as `qwen_image_edit_2511_bf16.safetensors`, 40,861,031,560 B [9] |
| Inpainting | FLUX.1 Fill dev | FLUX.1 [dev] Non-Commercial v1.1.1 [10][11] | ComfyUI diffusion models | Present; the research first choice [10] |
| Inpainting alternative | Qwen-Image-ControlNet-Inpainting | Apache-2.0 [10][12] | ComfyUI diffusion models | Present; first alternative [10] |
| 4-step sampling | None | - | - | No LCM or Lightning LoRA for SDXL is installed [9] |

- The local SDXL checkpoint is byte-identical to the Hugging Face file: same 6,938,078,334 B and same sha256 `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b` [7][9]
- FLUX.1 Fill dev is licensed FLUX.1 [dev] Non-Commercial v1.1.1 [10][11]
- Qwen-Image-ControlNet-Inpainting and Qwen-Image-Edit-2511 are Apache-2.0 [10][12][13]
- The project has local inpainting models; it has no LCM LoRA for SDXL [9][10]
- The documented Funcraft setup sends the image to Google Colab; the same SDXL checkpoint is available locally for ComfyUI [3][9]

## 4. Name disambiguation

This section lists the other products and projects that use the name, so the identification can be checked.

| Name | What it is | Source |
|---|---|---|
| Alibaba Cloud Funcraft | Serverless command-line tool for Function Compute, superseded by Serverless Devs | [14] |
| FunCraft, Inc. | San Francisco studio making daily word and puzzle games, at funcraft.com | [15] |
| FunCraft Minecraft server | French Minecraft mini-game server, at funcraft.net | [16] |
| FUNCRAFT Android games | Crafting and survival games published by Topandev, Apidev and Keisyadev | [17] |
| FunCraft Photo Editor | Android Minecraft-style sticker editor by Klimov Inc. | [18] |
| Funcraft yacht | Dutch motor yacht brand | [19] |
| `stellarshenson/funcraft` | Blender animation repository with downloaded 3D meshes; not a photo editor; whether the order meant this repository is unconfirmed | [20] |

## 5. Evidence gaps

This section states what could not be confirmed and what was checked without a result.

- No source URL was supplied with the order, so the link between the order and `efecte8/funcraft` is unconfirmed [1]
- No hosted Funcraft AI photo or video service is indexed on 2026-10-26; a private or unindexed service cannot be ruled out [21]
- The Hugging Face model and space search APIs return no result for Funcraft [21]
- The Civitai model search returns no result for Funcraft [21]
- The US App Store search API returns FunCraft word games and no Funcraft AI photo app [21]
- Google Play returns only FUNCRAFT crafting games for "funcraft ai" [17]
- Product Hunt returns FanCraft, a different product, and no Funcraft [21]
- The commit author domain `nomorefun.ai` has no DNS record on 2026-10-26 [5][22]
- The domains funcraft.ai, funcraft.app, funcraft.co, funcraft.video, funcraft.studio, funcraft.xyz, funcraft.dev, funcraft.art and funcraft.media did not resolve on 2026-10-26 [22]
- funcraft.io and funcraft.pl are offered for sale, and funcraft.org is a parking page [22]
- The repository has 6 stars and its last push was 2024-11-12 [5]

## 6. Sources

1. Order and tracker wording - `tmp/workflows/model-research/funcraft.js`, `docs/acc-crit.md` (ACC-DOCS-26-FUNCRAFT)
2. efecte8/funcraft repository landing page - https://github.com/efecte8/funcraft
3. efecte8/funcraft README - https://github.com/efecte8/funcraft/blob/main/README.md
4. efecte8/funcraft licence - https://github.com/efecte8/funcraft/blob/main/LICENSE
5. efecte8/funcraft repository metadata - https://api.github.com/repos/efecte8/funcraft
6. efecte8/funcraft backend notebook - https://github.com/efecte8/funcraft/blob/main/funcraft_backend_3_1_sdxl_lcm_lora.ipynb
7. SDXL 1.0 base: model card, licence and file tree - https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 , https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md , https://huggingface.co/api/models/stabilityai/stable-diffusion-xl-base-1.0/tree/main?expand=true
8. LCM-LoRA SDXL: model card and file tree - https://huggingface.co/latent-consistency/lcm-lora-sdxl , https://huggingface.co/api/models/latent-consistency/lcm-lora-sdxl/tree/main
9. Local model store and registry - `models/photo-animation/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors`, `models/photo-animation/ComfyUI/models/loras/`, `models/photo-animation/ComfyUI/models/diffusion_models/`, `src/henryk_media/imaging/registry.py`
10. Project extender decision record - `docs/model-selection/image-extender.md`
11. FLUX.1 Fill dev model card - https://huggingface.co/black-forest-labs/FLUX.1-Fill-dev
12. Qwen-Image-ControlNet-Inpainting model card - https://huggingface.co/InstantX/Qwen-Image-ControlNet-Inpainting
13. Qwen-Image-Edit-2511 model card - https://huggingface.co/Qwen/Qwen-Image-Edit-2511
14. Alibaba Cloud Funcraft - https://github.com/alibaba/funcraft , https://www.alibabacloud.com/help/en/functioncompute/use-funcraft-to-manage-functions
15. FunCraft, Inc. - https://www.funcraft.com/
16. FunCraft Minecraft server - https://www.funcraft.net/
17. FUNCRAFT Android games and Google Play search - https://play.google.com/store/apps/details?id=com.topandev.oneblocksurvival , https://play.google.com/store/search?q=funcraft%20ai&c=apps&hl=en
18. FunCraft Photo Editor - https://funcraft-photo-editor.soft112.com/ , https://apprecs.com/android/com.klimovinc.funcraft/funcraft-photo-editor
19. Funcraft yacht - https://www.theyachtmarket.com/en/boats-for-sale/funcraft/
20. stellarshenson/funcraft - https://github.com/stellarshenson/funcraft , https://github.com/stellarshenson/funcraft/blob/main/README.md
21. Negative searches - https://huggingface.co/api/models?search=funcraft , https://huggingface.co/api/spaces?search=funcraft , https://civitai.com/api/v1/models?query=funcraft , https://itunes.apple.com/search?term=funcraft&entity=software&country=us , https://www.producthunt.com/search?q=funcraft
22. Domain checks - https://funcraft.ai , https://funcraft.app , https://funcraft.co , https://funcraft.video , https://funcraft.studio , https://funcraft.xyz , https://funcraft.dev , https://funcraft.art , https://funcraft.media , https://funcraft.io , https://funcraft.pl , https://funcraft.org

<!-- complete -->
