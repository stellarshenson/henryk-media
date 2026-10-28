---
name: comfyui-workflow-templates
description: Official ComfyUI template JSONs ship inside the ComfyUI venv package; a template's real nodes sit under definitions.subgraphs[0]
metadata:
  type: reference
---

Official ComfyUI workflow templates are installed in the ComfyUI checkout at
`.venv/lib/python3.13/site-packages/comfyui_workflow_templates_json/templates/<name>.json`
(preview images sit in the sibling `comfyui_workflow_templates_media_assets_01` package).

**Why:** a template often wraps its pipeline in a subgraph. The top level then holds only
`LoadImage`, `SaveVideo`, notes and one node whose `type` is a UUID; the real nodes, links and
widget values live under `definitions.subgraphs[0]`. Reading only the top level makes the
template look nearly empty.

**How to apply:** parse `definitions.subgraphs[0]` for node types, links and `widgets_values`,
map widgets to input names with the running server's `/object_info/<class>`, and confirm every
combo option (sampler, clip type, file list) before submitting. A template's widget values are
positional and include link-driven values, so never assume the order.
