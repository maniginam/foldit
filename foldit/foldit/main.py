"""Main robot control loop."""


class FoldItRobot:
    """Orchestrates the garment detection and folding pipeline."""

    def __init__(self, camera, preprocessor, classifier, sequencer):
        self._camera = camera
        self._preprocessor = preprocessor
        self._classifier = classifier
        self._sequencer = sequencer

    def process_one(self):
        frame = self._camera.capture_frame()
        gray = self._preprocessor.to_grayscale(frame)
        binary = self._preprocessor.threshold(gray)
        contour = self._preprocessor.find_largest_contour(binary)

        if contour is None:
            return None

        garment_type = self._classifier.classify(contour)
        self._sequencer.fold(garment_type)
        return garment_type

    def run(self, max_items=None):
        self._camera.start()
        folded = []
        try:
            count = 0
            while max_items is None or count < max_items:
                result = self.process_one()
                if result is not None:
                    folded.append(result)
                    count += 1
        finally:
            self._camera.stop()
        return folded
