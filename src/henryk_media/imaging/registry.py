"""The bench's models: what each graph loads, the licence, and the settings it runs with.

One entry per model, so the notebook iterates this data instead of repeating a graph name, a
licence or a file per cell. ``settings`` holds every graph marker in lower case; the render
functions fill ``{{KEY}}`` from it, so the recorded settings cannot drift from what ran.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Extender:
    """One outpainting model.

    Attributes:
        name: Folder name and checkpoint name.
        label: Label of the tile in the contact sheet.
        graph: Graph template name under ``graphs/``.
        file: Diffusion weight file the graph loads, empty when the graph hardcodes it.
        model: Human description recorded in the sidecar.
        weights: Repositories, files and byte counts.
        licence: Licence of the weights.
        settings: Graph marker values, including steps and sampler settings.
        notes: Documented limits recorded with every image.
    """

    name: str
    label: str
    graph: str
    file: str
    model: str
    weights: str
    licence: str
    settings: dict[str, object] = field(default_factory=dict)
    notes: str = ""


@dataclass(frozen=True)
class Upscaler:
    """One upscaling model.

    Attributes:
        name: Folder name and checkpoint name.
        label: Label of the tile in the contact sheet.
        graph: Graph template name under ``graphs/``.
        file: Weight file the graph loads, empty when the graph hardcodes it.
        model: Human description recorded in the sidecar.
        weights: Repositories, files and byte counts.
        licence: Licence of the weights.
        scale: Factor the model applies to its input.
        prompt: Prompt the model takes, empty when it takes none.
        settings: Graph marker values, including steps and sampler settings.
        notes: Documented limits recorded with every image.
    """

    name: str
    label: str
    graph: str
    file: str
    model: str
    weights: str
    licence: str
    scale: float = 2.0
    prompt: str = ""
    settings: dict[str, object] = field(default_factory=dict)
    notes: str = ""


QWEN_WEIGHTS = (
    "Comfy-Org/Qwen-Image: qwen_image_bf16.safetensors 40,861,031,488 B, "
    "qwen_2.5_vl_7b.safetensors 16,584,415,576 B, qwen_image_vae.safetensors 253,806,246 B"
)

EXTENDERS: tuple[Extender, ...] = (
    Extender(
        name="qwen-inpainting",
        label="Qwen-Image + InstantX Inpainting",
        graph="qwen_inpainting",
        file="",
        model="Qwen-Image 20B bf16 with the InstantX Qwen-Image Inpainting ControlNet",
        weights=QWEN_WEIGHTS + "; Comfy-Org/Qwen-Image-InstantX-ControlNets: "
        "Qwen-Image-InstantX-ControlNet-Inpainting.safetensors 4,234,599,432 B",
        licence="Apache-2.0 (Qwen-Image and the InstantX ControlNet)",
        settings={
            "steps": 20,
            "cfg": 2.5,
            "sampler": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "shift": 3.1,
        },
        notes="True mask: only the two side panels are generated; the photo is composited back.",
    ),
    Extender(
        name="qwen-edit-2509",
        label="Qwen-Image-Edit 2509",
        graph="qwen_edit",
        file="qwen_image_edit_2509_bf16.safetensors",
        model="Qwen-Image-Edit 2509 20B bf16",
        weights=QWEN_WEIGHTS
        + "; Comfy-Org/Qwen-Image-Edit_ComfyUI: qwen_image_edit_2509_bf16.safetensors "
        "40,861,031,488 B",
        licence="Apache-2.0 (Qwen-Image-Edit)",
        settings={
            "steps": 20,
            "cfg": 2.5,
            "sampler": "euler",
            "scheduler": "simple",
            "shift": 3.0,
        },
        notes="No mask: the whole canvas is re-rendered from the grey-padded input, then the "
        "photo is composited back. Superseded by 2511 for outpainting reliability.",
    ),
    Extender(
        name="qwen-edit-2511",
        label="Qwen-Image-Edit 2511",
        graph="qwen_edit",
        file="qwen_image_edit_2511_bf16.safetensors",
        model="Qwen-Image-Edit 2511 20B bf16",
        weights=QWEN_WEIGHTS
        + "; Comfy-Org/Qwen-Image-Edit_ComfyUI: qwen_image_edit_2511_bf16.safetensors "
        "40,861,031,560 B",
        licence="Apache-2.0 (Qwen-Image-Edit)",
        settings={
            "steps": 40,
            "cfg": 3.0,
            "sampler": "euler",
            "scheduler": "simple",
            "shift": 3.1,
        },
        notes="No mask: the whole canvas is re-rendered from the grey-padded input, then the "
        "photo is composited back. Best identity consistency in the Qwen line per the research.",
    ),
    Extender(
        name="omnigen2",
        label="OmniGen2",
        graph="omnigen2",
        file="omnigen2_fp16.safetensors",
        model="OmniGen2 7B fp16 with its Qwen 2.5 VL 3B text encoder",
        weights="Comfy-Org/OmniGen-2: omnigen2_fp16.safetensors 7,934,384,176 B, "
        "qwen_2.5_vl_fp16.safetensors 7,509,337,224 B, ae.safetensors 335,304,388 B",
        licence="Apache-2.0 (OmniGen2, Qwen 2.5 VL text encoder)",
        settings={"steps": 20, "cfg": 5.0, "sampler": "euler", "scheduler": "simple"},
        notes="No mask: prompt-based editor. Documented working cap about 2 MP, so a larger "
        "canvas is rendered at its cap and resized.",
    ),
    Extender(
        name="flux-fill",
        label="FLUX.1 Fill dev",
        graph="flux_fill",
        file="",
        model="FLUX.1 Fill dev 12B bf16",
        weights="black-forest-labs/FLUX.1-Fill-dev: flux1-fill-dev.safetensors "
        "23,804,922,408 B, ae.safetensors 335,304,388 B; comfyanonymous/flux_text_encoders: "
        "clip_l.safetensors 246,144,152 B, t5xxl_fp16.safetensors 9,787,841,024 B",
        licence="FLUX.1 [dev] Non-Commercial License v1.1.1; private home use permitted",
        settings={
            "steps": 30,
            "cfg": 1.0,
            "sampler": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
            "flux_guidance": 30.0,
        },
        notes="True mask through Flux Fill: only the two side panels are generated; the photo "
        "is composited back. CFG is 1, so the negative prompt is encoded but does not influence "
        "the fill. Known VAE colour shift and seams, corrected by the tone match.",
    ),
    Extender(
        name="sdxl-inpainting",
        label="SDXL Inpainting 0.1",
        graph="sdxl_inpainting",
        file="",
        model="SDXL Inpainting 0.1 fp16, 9-channel inpainting UNet",
        weights="diffusers/stable-diffusion-xl-1.0-inpainting-0.1: UNet fp16 5,135,178,560 B, "
        "CLIP-L 246,144,867 B, CLIP-G 1,389,382,884 B, VAE 167,335,338 B",
        licence="CreativeML Open RAIL++-M; the model card states a research intent, private "
        "home use is not forbidden",
        settings={
            "steps": 30,
            "cfg": 5.0,
            "sampler": "euler",
            "scheduler": "normal",
            "denoise": 1.0,
        },
        notes="True mask through the 9-channel inpainting UNet; the photo is composited back. "
        "Trained at 1024 px, so its detail is below the 2026 models, and its own card warns of "
        "malformed faces; it is the low-VRAM baseline.",
    ),
    Extender(
        name="flux-kontext",
        label="FLUX.1 Kontext dev",
        graph="flux_kontext",
        file="",
        model="FLUX.1 Kontext dev 12B bf16",
        weights="black-forest-labs/FLUX.1-Kontext-dev: flux1-kontext-dev.safetensors "
        "23,802,947,360 B, ae.safetensors 335,304,388 B; comfyanonymous/flux_text_encoders: "
        "clip_l.safetensors 246,144,152 B, t5xxl_fp16.safetensors 9,787,841,024 B",
        licence="FLUX.1 [dev] Non-Commercial License v1.1.1; private home use permitted",
        settings={
            "steps": 20,
            "cfg": 1.0,
            "sampler": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "flux_guidance": 2.5,
        },
        notes="No mask: the grey-padded canvas is a reference latent and the instruction edit "
        "fills it; the photo is composited back. Rendered at the full frame size, above the "
        "template's 1 MP working scale, so 16:9 is the harder case.",
    ),
    Extender(
        name="flux3-klein",
        label="FLUX 3 Image Klein + Outpaint LoRA",
        graph="flux3_klein",
        file="flux3-image-klein-bf16.safetensors",
        model="FLUX 3 Image Klein 5.6B bf16 distilled with the ausboss Outpaint LoRA",
        weights="black-forest-labs/flux-3-image-klein: model.safetensors 11,097,404,512 B, "
        "ae.safetensors 336,211,292 B, text encoder shards 4,967,229,296 + 3,908,490,048 B "
        "merged; ausboss/FLUX-3-Image-Klein-Outpaint-LoRA: "
        "flux-3-image-klein-outpaint.safetensors 160,697,104 B",
        licence="FLUX Kommunity License v1.0; private non-commercial use permitted, commercial "
        "output allowed below the licence revenue threshold",
        settings={
            "steps": 16,
            "cfg": 1.0,
            "sampler": "euler",
            "scheduler": "simple",
            "denoise": 1.0,
            "lora_strength": 1.5,
        },
        notes="No mask: the grey-padded frame is the reference latent and the LoRA at strength "
        "1.5 paints the panels; the photo is composited back. The LoRA was trained at 0.94 to "
        "1.96 MP, so both frames are above its tested range; faces are its documented weak area "
        "and it does not sharpen.",
    ),
)

SEEDVR2_WEIGHTS = "Comfy-Org/SeedVR2: seedvr2_ema_vae_fp16.safetensors 501,324,814 B"

UPSCALERS: tuple[Upscaler, ...] = (
    Upscaler(
        name="seedvr2-3b",
        label="SeedVR2 3B",
        graph="seedvr2",
        file="seedvr2_3b_fp16.safetensors",
        model="SeedVR2 3B fp16, non-sharp, with its EMA VAE",
        weights=SEEDVR2_WEIGHTS + "; seedvr2_3b_fp16.safetensors 6,784,268,336 B",
        licence="Apache-2.0",
        scale=2.0,
        settings={"tile": 512, "overlap": 128},
        notes="One-step diffusion restoration; can over-generate on lightly degraded inputs.",
    ),
    Upscaler(
        name="seedvr2-7b",
        label="SeedVR2 7B",
        graph="seedvr2",
        file="seedvr2_7b_fp16.safetensors",
        model="SeedVR2 7B fp16, non-sharp, with its EMA VAE",
        weights=SEEDVR2_WEIGHTS + "; seedvr2_7b_fp16.safetensors 16,480,583,960 B",
        licence="Apache-2.0",
        scale=2.0,
        settings={"tile": 512, "overlap": 128},
        notes="One-step diffusion restoration; the sharp 7B variant is not used on a child's face.",
    ),
    Upscaler(
        name="hypir",
        label="HYPIR",
        graph="hypir",
        file="",
        model="HYPIR-SD2, one step from the SD2.1 base",
        weights="lxq007/HYPIR: HYPIR_sd2.pth 1,038,090,392 B, sd2_denoise_ae_encoder.pth "
        "136,688,930 B; EricRollei/SAI-SD2.1-for-HYPIR: unet 3,463,726,498 B, text encoder "
        "1,361,597,018 B, VAE 334,643,276 B",
        licence="Non-commercial proprietary (SupPixel); private home use permitted",
        scale=2.0,
        prompt="a sharp, detailed, natural photograph",
        settings={},
        notes="Most conservative generative pass by the research ranking.",
    ),
    Upscaler(
        name="ccsr",
        label="CCSR",
        graph="ccsr",
        file="",
        model="CCSR v1 fp16, tiled mixdiff",
        weights="Kijai/ccsr-safetensors: real-world_ccsr-fp16.safetensors 3,437,051,694 B",
        licence="Apache-2.0 weights; the kijai node repository carries no licence file",
        scale=2.0,
        settings={
            "steps": 45,
            "sampling_method": "ccsr_tiled_mixdiff",
            "tile_size": 512,
            "tile_stride": 256,
            "color_fix_type": "adain",
        },
        notes="Faithful and deterministic first pass; soft.",
    ),
    Upscaler(
        name="hat",
        label="HAT",
        graph="spandrel",
        file="Real_HAT_GAN_sharper.pth",
        model="HAT, Real_HAT_GAN_sharper, x4 through spandrel",
        weights="Acly/hat: Real_HAT_GAN_sharper.pth 170,277,017 B",
        licence="Apache-2.0",
        scale=4.0,
        settings={},
        notes="Regressive transformer: sharpens without inventing detail; rendered at 4x, "
        "then scaled to the target.",
    ),
    Upscaler(
        name="swinir",
        label="SwinIR",
        graph="spandrel",
        file="SwinIR-L_x4_GAN.pth",
        model="SwinIR-L x4 GAN, through spandrel",
        weights="JingyunLiang/SwinIR release v0.0: "
        "003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth 142,473,939 B",
        licence="Apache-2.0",
        scale=4.0,
        settings={},
        notes="Regressive baseline: sharpens without inventing detail; rendered at 4x, then "
        "scaled to the target.",
    ),
    Upscaler(
        name="supir",
        label="SUPIR",
        graph="supir",
        file="",
        model="SUPIR v0Q fp16 over SDXL base 1.0",
        weights="Kijai/SUPIR_pruned: SUPIR-v0Q_fp16.safetensors 2,664,858,464 B; "
        "stabilityai/stable-diffusion-xl-base-1.0: sd_xl_base_1.0.safetensors 6,938,078,334 B",
        licence="Non-commercial proprietary (SupPixel); private home use permitted",
        scale=1.0,  # the graph pre-scales to the target, as SUPIR's own pipeline does
        prompt="a sharp, highly detailed, natural photograph",
        settings={"steps": 50, "cfg": 4.0, "sampler": "euler", "scheduler": "simple"},
        notes="Highest texture gain, highest identity risk; the photo is composited back.",
    ),
    Upscaler(
        name="invsr",
        label="InvSR",
        graph="invsr",
        file="",
        model="InvSR with SD-Turbo, one step",
        weights="OAOA/InvSR: noise_predictor_sd_turbo_v5.pth 135,417,810 B; "
        "stabilityai/sd-turbo: fp16 components",
        licence="S-Lab License 1.0, non-commercial; private home use permitted",
        scale=4.0,
        settings={"steps": 1, "cfg": 1.0, "chopping_size": 256, "color_fix": "wavelet"},
        notes="Always runs at 4x, then scaled to the target; the research rejects it for faces, "
        "which the composite protects.",
    ),
    Upscaler(
        name="real-esrgan",
        label="Real-ESRGAN",
        graph="spandrel",
        file="RealESRGAN_x2plus.pth",
        model="Real-ESRGAN x2plus, through spandrel",
        weights="xinntao/Real-ESRGAN release v0.2.1: RealESRGAN_x2plus.pth 67,061,725 B",
        licence="BSD-3-Clause",
        scale=2.0,
        settings={},
        notes="Fast GAN baseline; not a final portrait upscaler.",
    ),
    Upscaler(
        name="remacri",
        label="4x Remacri",
        graph="spandrel",
        file="4x_foolhardy_Remacri.pth",
        model="4x_foolhardy_Remacri, x4 through spandrel",
        weights="uwg/upscaler: ESRGAN/4x_foolhardy_Remacri.pth 67,025,055 B",
        licence="No licence stated on the mirror; private use unproblematic",
        scale=4.0,
        settings={},
        notes="ESRGAN-family baseline, the least damaging of the community 4x files for skin "
        "by the research ranking; rendered at 4x, then scaled to the target.",
    ),
)


def extender(name: str) -> Extender:
    """Return the extender with ``name``.

    Raises:
        KeyError: If no extender has that name.
    """
    return next(item for item in EXTENDERS if item.name == name)


def upscaler(name: str) -> Upscaler:
    """Return the upscaler with ``name``.

    Raises:
        KeyError: If no upscaler has that name.
    """
    return next(item for item in UPSCALERS if item.name == name)
