"""The studio: one local page that outpaints a photo and animates an image on one selected GPU.

``cli`` serves ``web.handler`` on 127.0.0.1 in front of one ``app.Studio``, which queues the jobs
and runs them one at a time through the ``generators`` on one ComfyUI server (``comfy``) pinned to
the GPU the user picked from ``gpus``. ``prompts`` holds the preset texts and the H3 grammar.
"""
