# FoldIt v2 — Intelligent Separation & Classification

## Overview
Five improvements to make the folding robot handle real-world garments: conveyor-based separation, ML classification, adaptive thresholding, wrinkle handling, and multi-item detection.

## 1. Conveyor Feed System
A small conveyor belt upstream of the folding platform. Garments are placed at the feed end, belt moves them single-file into the fold zone. An ultrasonic sensor (HC-SR04) detects when a garment enters the zone and stops the belt. After folding completes, the belt advances the next item.

**New hardware:** DC motor + belt kit, HC-SR04 ultrasonic sensor, motor driver (L298N)
**New software:** ConveyorController, GarmentDetector (ultrasonic-based)

## 2. ML-Based Classification (MobileNetV2 + TFLite)
Replace aspect-ratio heuristics with a fine-tuned MobileNetV2 running via TensorFlow Lite on RPi. Classifies into 5 categories: shirt, pants, towel, small, unknown. Falls back to heuristic classifier if ML confidence < threshold (0.7).

**New deps:** tflite-runtime, training script (runs on desktop, exports .tflite model)
**Architecture:** MLClassifier wraps TFLite inference, implements same interface as GarmentClassifier. HybridClassifier tries ML first, falls back to heuristic.

## 3. Adaptive Thresholding
Replace fixed threshold (>127) with:
- Background subtraction: capture empty platform on startup, subtract from each frame
- Adaptive Gaussian thresholding for varying lighting conditions
- Handles dark garments on dark surfaces and vice versa

## 4. Wrinkle Handling (Pre-Flatten)
Before classification, compute garment "flatness" via solidity (contour area / convex hull area). If solidity < 0.75, the garment is bunched up. Execute a pre-flatten sequence (fold_left → home → fold_right → home) to spread the fabric, then re-capture and classify.

## 5. Multi-Item Detection
After finding the largest contour, scan for additional contours above a minimum area threshold. If multiple garments are detected on the platform simultaneously, pause and either:
- Advance the conveyor to push extras off
- Alert the operator
