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


class FoldItRobotV3:
    """V3 pipeline: full V2 pipeline + orientation, size, verification, error recovery, metrics."""

    def __init__(self, camera, preprocessor, classifier, sequencer,
                 conveyor, item_detector, flatness_checker,
                 orientation, size_estimator, fold_verifier,
                 error_recovery, metrics, logger, data_collector,
                 frame_quality, alerter, platform=None):
        self._camera = camera
        self._preprocessor = preprocessor
        self._classifier = classifier
        self._sequencer = sequencer
        self._conveyor = conveyor
        self._detector = item_detector
        self._flatness = flatness_checker
        self._platform = platform
        self._orientation = orientation
        self._size_estimator = size_estimator
        self._verifier = fold_verifier
        self._recovery = error_recovery
        self._metrics = metrics
        self._logger = logger
        self._data_collector = data_collector
        self._frame_quality = frame_quality
        self._alerter = alerter
        self._stop_requested = False
        self._last_orientation = None
        self._last_size = None

    def process_one(self):
        import time
        start = time.monotonic()

        if not self._recovery.safe_advance(self._conveyor):
            return None

        frame = self._recovery.safe_capture(self._camera)
        if frame is None:
            return None

        quality = self._frame_quality.check(frame)
        if not quality.acceptable:
            frame = self._recovery.safe_capture(self._camera)
            if frame is None:
                return None

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
            frame = self._recovery.safe_capture(self._camera)
            if frame is None:
                return None
            gray = self._preprocessor.to_grayscale(frame)
            binary = self._preprocessor.threshold(gray)
            detection = self._detector.detect(binary)
            contour = detection.largest

        if contour is None:
            return None

        self._last_orientation = self._orientation.detect(contour)
        self._last_size = self._size_estimator.estimate(contour)

        garment_type = self._classifier.classify(contour, frame=frame)
        self._data_collector.save(frame, garment_type)

        self._sequencer.fold(garment_type, speed_factor=self._last_size.speed_factor)

        verify_result = self._verifier.verify(garment_type)
        if not verify_result.success:
            self._sequencer.fold(garment_type, speed_factor=self._last_size.speed_factor)
            verify_result = self._verifier.verify(garment_type)

        elapsed = time.monotonic() - start
        self._metrics.record_fold(garment_type, success=verify_result.success, cycle_sec=elapsed)
        self._logger.log_event(
            "fold_complete", garment=garment_type,
            cycle_sec=round(elapsed, 2), verified=verify_result.success,
            compactness=round(verify_result.compactness, 3),
        )
        self._alerter.check(garment_type, success=verify_result.success)

        return garment_type

    def run(self, max_items=None):
        self._camera.start()
        folded = []
        try:
            count = 0
            while (max_items is None or count < max_items) and not self._stop_requested:
                result = self.process_one()
                if result is not None:
                    folded.append(result)
                    count += 1
        except Exception:
            pass
        finally:
            self._camera.stop()
        return folded

    def stop(self):
        self._stop_requested = True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="FoldIt Robot Controller")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the robot")
    run_parser.add_argument("--simulate", action="store_true", help="Run in simulator mode")
    run_parser.add_argument("--items", type=int, default=1, help="Number of items to process")

    subparsers.add_parser("dashboard", help="Start the web dashboard")
    subparsers.add_parser("calibrate", help="Run auto-calibration")

    train_parser = subparsers.add_parser("train", help="Train ML classifier")
    train_parser.add_argument("--csv", required=False, help="Path to labels.csv")
    train_parser.add_argument("--output", default="models", help="Output directory")

    args = parser.parse_args()

    if args.command == "run" or args.command is None:
        simulate = getattr(args, "simulate", False)
        items = getattr(args, "items", 1)
        if simulate:
            from foldit.simulator import create_simulated_robot_v3
            robot = create_simulated_robot_v3()
            folded = robot.run(max_items=items)
            print(f"Folded {len(folded)} items: {folded}")
            print(f"Metrics: {robot._metrics.snapshot()}")
    elif args.command == "dashboard":
        from foldit.dashboard import create_app
        from foldit.robot_logger import MetricsCollector
        from foldit.error_recovery import RobotState
        metrics = MetricsCollector()
        state = {"state": RobotState.IDLE, "uptime_sec": 0}
        app = create_app(metrics, state)
        app.run(port=5000)
    elif args.command == "calibrate":
        print("Place reference object (credit card) on belt and press Enter...")
    elif args.command == "train":
        from training.train import train
        if args.csv:
            train(args.csv, args.output)
        else:
            print("Usage: foldit train --csv path/to/labels.csv")


if __name__ == "__main__":
    main()
