"""Mechanical check that no new face or person appears in the added side panels.

The photo is pasted back before this check, so its own faces and bodies are already unchanged by
construction; only the two added panels can hold a new person. Two detectors run over the whole
composited frame, and every detection is classified:

- a stranger when its box lies wholly inside an added panel and clear of the frame border,
  because the photo shows that person nowhere; a stranger fails the frame,
- a continuation when a face box crosses the photo's edge into a panel, because it is someone the
  photo already shows whose head or body the extension completes; a continuation is recorded and
  does not fail the frame, and
- clipped when the box touches the frame's outer border, because that edge cuts a person off
  exactly as the photo's own edge does; a clipped box is recorded and never fails the frame.

A face wholly within the photo and a person that touches the photo are the photo's own and are
not recorded unless the box touches the frame's outer border, where it is recorded as clipped.
The rules are the Star Colonel's order of 2026-10-25 04:44, refined after he judged the
flux3-klein tiles well extended: their only flagged face was the girl cut off at the photo's
left edge, not a stranger, and the person boxes that failed the tiles sat on the frame border
over an easel leg, a pink cloth and the floor. Both detectors run on the CPU so the render server
keeps the GPU, and one pair of models is loaded once and reused for every tile.
"""

from pathlib import Path

from PIL import Image

FACE_WEIGHTS = "face_yolov8n.pt"  # ultralytics face detector, one class: face
PERSON_WEIGHTS = "yolo11n.pt"  # COCO detector, class 0 is person
CONFIDENCE = 0.25  # a detection below this confidence is ignored
IMAGE_SIZE = 1280  # inference size; the 1280 px frame reaches the detectors at 1:1
PERSON_CLASS = 0  # COCO class index of person
FULLY_INSIDE = 1.0 - 1e-6  # float tolerance for "wholly inside"
BORDER_TOLERANCE = 2.0  # px within which a box counts as touching the frame's outer border
STRANGER = "stranger"  # a person the photo shows nowhere; a violation
CONTINUATION = "continuation"  # a face the photo already shows, completed into a panel
CLIPPED = "clipped"  # a box cut off by the frame's outer border; never a violation


def panels(frame_width: int, photo_left: int, photo_width: int) -> tuple[tuple[int, int], ...]:
    """Return the x ranges of the added panels: left of the photo and right of it.

    The photo is scaled to the frame height, so the panels span the full frame height and only
    their horizontal extent matters.

    Args:
        frame_width: Width of the composited frame in pixels.
        photo_left: x of the photo's left edge in the frame.
        photo_width: Width of the photo in the frame.
    """
    return ((0, photo_left), (photo_left + photo_width, frame_width))


def inside_fraction(
    box: tuple[float, float, float, float], ranges: tuple[tuple[int, int], ...]
) -> float:
    """Return the fraction of a box's width that lies inside the added panels.

    Args:
        box: (x1, y1, x2, y2) of a detection.
        ranges: The added panels' x ranges, as returned by ``panels``.
    """
    x1, _, x2, _ = box
    width = max(x2 - x1, 1e-6)
    inside = sum(max(0.0, min(x2, right) - max(x1, left)) for left, right in ranges)
    return round(min(inside / width, 1.0), 6)


def touches_border(
    box: tuple[float, float, float, float],
    size: tuple[int, int],
    tolerance: float = BORDER_TOLERANCE,
) -> bool:
    """Return whether a box touches the frame's outer border within ``tolerance`` pixels.

    Args:
        box: (x1, y1, x2, y2) of a detection.
        size: (width, height) of the composited frame.
        tolerance: Distance from a border, in pixels, that still counts as touching it.
    """
    x1, y1, x2, y2 = box
    width, height = size
    return (
        x1 <= tolerance or y1 <= tolerance or x2 >= width - tolerance or y2 >= height - tolerance
    )


def detection_kind(detector: str, inside: float, clipped: bool = False) -> str | None:
    """Return a detection's kind: ``stranger``, ``continuation``, ``clipped``, or None.

    A box touching the frame's outer border is clipped: the frame edge, like the photo's own
    edge, cuts the person off, so the tile portrays no one new. Otherwise a box wholly inside a
    panel is a stranger, and a face crossing into the photo is a continuation.

    Args:
        detector: ``face`` or ``person``.
        inside: Fraction of the detection's box inside the added panels.
        clipped: Whether the box touches the frame's outer border.
    """
    if clipped:
        return CLIPPED
    if inside >= FULLY_INSIDE:
        return STRANGER
    if detector == "face" and inside > 0.0:
        return CONTINUATION
    return None


def _box(box: tuple[float, float, float, float]) -> list[float]:
    """Return a detection box rounded for a sidecar or a checkpoint."""
    return [round(value, 1) for value in box]


def detection_text(item: dict[str, object]) -> str:
    """Return one recorded detection as a sidecar phrase, such as ``face 0.74 box (...)``.

    Args:
        item: A detection record with detector, confidence, box and inside.
    """
    x1, y1, x2, y2 = item["box"]
    return (
        f"{item['detector']} {item['confidence']:.2f} box "
        f"({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}) inside {item['inside']:.2f}"
    )


class PersonGate:
    """The face and person detectors, loaded once and run over every rendered tile.

    Args:
        weights_dir: Folder holding ``face_yolov8n.pt`` and ``yolo11n.pt``.
        confidence: Lowest detection confidence that counts.
        image_size: Inference size passed to both detectors.
        device: Torch device; ``cpu`` leaves the GPUs to the render server.

    Raises:
        FileNotFoundError: If a detector's weights are missing when first used.
    """

    def __init__(
        self,
        weights_dir: Path,
        confidence: float = CONFIDENCE,
        image_size: int = IMAGE_SIZE,
        device: str = "cpu",
    ) -> None:
        self.weights_dir = Path(weights_dir)
        self.confidence = confidence
        self.image_size = image_size
        self.device = device
        self._models: dict[str, object] = {}
        self._version = ""

    def _load(self, detector: str):
        """Return the loaded detector, importing ultralytics on first use."""
        if not self._models:
            import ultralytics

            self._version = ultralytics.__version__
        if detector not in self._models:
            from ultralytics import YOLO

            name = FACE_WEIGHTS if detector == "face" else PERSON_WEIGHTS
            weights = self.weights_dir / name
            if not weights.exists():
                raise FileNotFoundError(f"{weights} is missing; the no-new-people gate cannot run")
            self._models[detector] = YOLO(str(weights))
        return self._models[detector]

    def signatures(self) -> dict[str, str]:
        """Return each detector's weights, library version and settings for the record."""
        self._load("face")
        self._load("person")
        shared = f"ultralytics {self._version}, conf {self.confidence}, imgsz {self.image_size}"
        return {
            "face": f"{FACE_WEIGHTS}, {shared}",
            "person": f"{PERSON_WEIGHTS} class {PERSON_CLASS} person, {shared}",
        }

    def check(self, frame: Image.Image, photo_left: int, photo_width: int) -> dict[str, object]:
        """Return the gate verdict for one composited frame.

        Args:
            frame: The composited frame, RGB, with the photo already pasted back.
            photo_left: x of the photo's left edge in the frame.
            photo_width: Width of the photo in the frame.

        Returns:
            A JSON-ready record with ``passed``, the panel x ranges, the rule text, the stranger
            ``violations``, the face ``continuations`` and the ``clipped`` detections; no
            violation means the frame passed.
        """
        ranges = panels(frame.width, photo_left, photo_width)
        strangers: list[dict[str, object]] = []
        continuations: list[dict[str, object]] = []
        clipped: list[dict[str, object]] = []
        groups = {STRANGER: strangers, CONTINUATION: continuations, CLIPPED: clipped}
        for detector in ("face", "person"):
            result = self._load(detector).predict(
                frame,
                imgsz=self.image_size,
                conf=self.confidence,
                device=self.device,
                verbose=False,
            )[0]
            for box, confidence, label in zip(
                result.boxes.xyxy, result.boxes.conf, result.boxes.cls, strict=True
            ):
                if detector == "person" and int(label) != PERSON_CLASS:
                    continue
                coordinates = tuple(float(value) for value in box)
                inside = inside_fraction(coordinates, ranges)
                kind = detection_kind(detector, inside, touches_border(coordinates, frame.size))
                if kind is None:
                    continue
                record: dict[str, object] = {
                    "detector": detector,
                    "label": result.names[int(label)],
                    "confidence": round(float(confidence), 3),
                    "box": _box(coordinates),
                    "inside": inside,
                    "kind": kind,
                }
                groups[kind].append(record)
        return {
            "passed": not strangers,
            "panels": [list(pair) for pair in ranges],
            "rule": (
                "stranger: a face or person box wholly inside an added panel and clear of the "
                "frame border; continuation: a face crossing into the photo, recorded and not a "
                f"violation; clipped: a box touching the frame's outer border within "
                f"{BORDER_TOLERANCE:g} px, recorded and not a violation"
            ),
            "violations": strangers,
            "continuations": continuations,
            "clipped": clipped,
        }
