# FoldIt — Tabletop Clothes Folding Robot

## Overview
A tabletop robot that takes a pile of clean clothes, identifies garment type via camera, and folds them using motorized hinged plates. Runs on Raspberry Pi 4 with Python.

## Software Architecture (`foldit/`)
Python package with modules:
- **classifier.py** — Garment identification (shirt/pants/towel/socks) via OpenCV shape/size heuristics
- **folder.py** — Fold sequence engine with per-garment-type fold patterns
- **motor_controller.py** — Servo control abstraction via RPi GPIO
- **camera.py** — Camera capture and image preprocessing
- **main.py** — Main loop: detect → classify → fold
- **config.py** — Pin mappings, motor calibration, camera settings

## Hardware Design (`hardware_files/`)
Tabletop folding platform with:
- Base plate (~24" x 30")
- 3 hinged folding panels (left, right, bottom)
- Servo motor mounts for each panel
- Camera gantry/mount above the platform
- Hinge mechanisms for panel rotation

## Target Specs
- Garment size: up to 20" x 30"
- 3 folding axes (left, right, bottom)
- Pi Camera v2 for vision
- Raspberry Pi 4 controller
- MG996R servos (or equivalent high-torque)

## Form Factor
Tabletop folder — flat surface with folding arms/plates that flip clothes. Simplest to 3D print and prototype.
