"""Tests for fold sequence engine."""


class FakePlatform:
    def __init__(self):
        self.actions = []

    def home(self):
        self.actions.append("home")

    def fold_left(self):
        self.actions.append("fold_left")

    def fold_right(self):
        self.actions.append("fold_right")

    def fold_bottom(self):
        self.actions.append("fold_bottom")


class TestFoldSequencer:
    def test_shirt_fold_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("shirt")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_right", "home",
            "fold_bottom", "home"
        ]

    def test_pants_fold_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("pants")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_bottom", "home"
        ]

    def test_towel_fold_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("towel")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_bottom", "home"
        ]

    def test_small_fold_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("small")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_bottom", "home"
        ]

    def test_unknown_fold_uses_basic_sequence(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("unknown")
        assert platform.actions == [
            "home", "fold_left", "home", "fold_right", "home",
            "fold_bottom", "home"
        ]

    def test_fold_returns_garment_type(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        result = sequencer.fold("shirt")
        assert result == "shirt"


class FakeTimingPlatform:
    def __init__(self):
        self.actions = []
        self.delays = []

    def home(self):
        self.actions.append("home")

    def fold_left(self, delay_factor=1.0):
        self.actions.append("fold_left")
        self.delays.append(delay_factor)

    def fold_right(self, delay_factor=1.0):
        self.actions.append("fold_right")
        self.delays.append(delay_factor)

    def fold_bottom(self, delay_factor=1.0):
        self.actions.append("fold_bottom")
        self.delays.append(delay_factor)


class TestFoldSequencerSpeedFactor:
    def test_fold_with_speed_factor_passes_to_steps(self):
        from foldit.folder import FoldSequencer
        platform = FakeTimingPlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("shirt", speed_factor=1.5)
        assert all(d == 1.5 for d in platform.delays)

    def test_fold_default_speed_factor_is_one(self):
        from foldit.folder import FoldSequencer
        platform = FakeTimingPlatform()
        sequencer = FoldSequencer(platform)
        sequencer.fold("pants", speed_factor=1.0)
        assert all(d == 1.0 for d in platform.delays)

    def test_fold_without_speed_factor_still_works(self):
        from foldit.folder import FoldSequencer
        platform = FakePlatform()
        sequencer = FoldSequencer(platform)
        result = sequencer.fold("shirt")
        assert result == "shirt"
