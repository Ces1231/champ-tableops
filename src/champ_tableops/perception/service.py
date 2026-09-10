from dataclasses import dataclass


@dataclass(frozen=True)
class SceneObject:
    name: str
    object_type: str
    x: float
    y: float
    z: float


def observe_scene() -> list[SceneObject]:
    # Adapter placeholder for simulator/vision scene observations.
    return []
