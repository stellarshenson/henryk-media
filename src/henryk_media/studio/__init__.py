"""The studio: one local page that outpaints a photo and animates an image on a GPU the studio
chooses per job.

``cli`` serves ``web.handler`` on 127.0.0.1 in front of one ``app.Studio``, which queues the jobs
and runs them one at a time through the ``generators`` on one ComfyUI server (``comfy``) pinned to
the GPU ``gpus.choose`` returns. ``prompts`` holds the preset texts and the H3 grammar.
"""
