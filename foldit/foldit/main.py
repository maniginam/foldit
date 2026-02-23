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
        except Exception:
            pass
        finally:
            self._camera.stop()
        return folded


class FoldItRobotV2:
    """V2 pipeline: conveyor -> detect -> multi-check -> flatten -> classify -> fold."""

    def __init__(self, camera, preprocessor, classifier, sequencer,
                 conveyor, item_detector, flatness_checker, platform=None):
        self._camera = camera
        self._preprocessor = preprocessor
        self._classifier = classifier
        self._sequencer = sequencer
        self._conveyor = conveyor
        self._detector = item_detector
        self._flatness = flatness_checker
        self._platform = platform

    def process_one(self):
        if not self._conveyor.advance_to_fold_zone():
            return None

        frame = self._camera.capture_frame()
        gray = self._preprocessor.to_grayscale(frame)
        binary = self._preprocessor.threshold(gray)

        detection = self._detector.detect(binary)
        if not detection.is_single:
            return None

        contour = detection.largest
        if not self._flatness.is_flat(contour) and self._platform:
            self._platform.fold_left()
            self._platform.home()
            self._platform.fold_right()
            self._platform.home()
            frame = self._camera.capture_frame()
            gray = self._preprocessor.to_grayscale(frame)
            binary = self._preprocessor.threshold(gray)
            detection = self._detector.detect(binary)
            contour = detection.largest

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
        except Exception:
            pass
        finally:
            self._camera.stop()
        return folded


def main():
    import argparse
    parser = argparse.ArgumentParser(description="FoldIt Robot Controller")
    parser.add_argument("--simulate", action="store_true", help="Run in simulator mode without hardware")
    parser.add_argument("--items", type=int, default=1, help="Number of items to process in simulate mode")
    args = parser.parse_args()

    if args.simulate:
        from foldit.simulator import create_simulated_robot_v3
        import time
        robot, ctx = create_simulated_robot_v3()
        for i in range(args.items):
            start = time.monotonic()
            result = robot.process_one()
            elapsed = time.monotonic() - start
            if result:
                ctx["metrics"].record_fold(result, success=True, cycle_sec=elapsed)
                ctx["logger"].log_event("fold_complete", garment=result, cycle_sec=round(elapsed, 2))
        print(ctx["metrics"].snapshot())


if __name__ == "__main__":
    main()
