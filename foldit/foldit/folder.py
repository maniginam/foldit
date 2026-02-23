"""Fold sequence engine for different garment types."""
from foldit.config import GarmentType


FOLD_SEQUENCES = {
    GarmentType.SHIRT: ["fold_left", "fold_right", "fold_bottom"],
    GarmentType.PANTS: ["fold_left", "fold_bottom"],
    GarmentType.TOWEL: ["fold_left", "fold_bottom"],
    GarmentType.SMALL: ["fold_left", "fold_bottom"],
    GarmentType.UNKNOWN: ["fold_left", "fold_right", "fold_bottom"],
}


class FoldSequencer:
    """Executes fold sequences on the platform for each garment type."""

    def __init__(self, platform):
        self._platform = platform

    def fold(self, garment_type, speed_factor=1.0):
        steps = FOLD_SEQUENCES.get(
            garment_type, FOLD_SEQUENCES[GarmentType.UNKNOWN]
        )
        self._platform.home()
        for step in steps:
            method = getattr(self._platform, step)
            try:
                method(delay_factor=speed_factor)
            except TypeError:
                method()
            self._platform.home()
        return garment_type
