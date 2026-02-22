# FoldIt Robot - Full-Scale Prototype Design Document

**Project:** FoldIt Clothes-Folding Robot
**Revision:** 1.0
**Date:** 2026-02-22
**Scale:** Full-size (1:1), upgraded from 1:4 tabletop prototype

---

## 1. Overview

This document describes the design path from the current 1:4 scale 3D-printed prototype to a full-size clothes-folding robot capable of handling real garments. The full-scale robot retains the same Raspberry Pi + PCA9685 control architecture and software stack, upgrading only the mechanical structure and actuators.

---

## 2. Frame

### Material: 2020 Aluminum Extrusion (T-Slot)

- **Type:** 20mm x 20mm T-slot aluminum extrusion (V-slot or standard T-slot)
- **Dimensions:** 24" x 30" (610mm x 762mm) base frame, rectangular
- **Corner joints:** 3D-printed corner brackets or cast aluminum L-brackets with M5 T-nuts
- **Advantages over 3D-printed frame:**
  - Rigid, vibration-resistant structure
  - Easy to cut, assemble, and reconfigure
  - T-slot channels accept standard M5 hardware for mounting servos, camera gantry, and electronics
  - Widely available (OpenBuilds, Misumi, 80/20 brand)

### Frame Layout

```
          30" (762mm)
    ┌──────────────────────┐
    │                      │
    │   2020 extrusion     │  24" (610mm)
    │   perimeter frame    │
    │                      │
    │   ┌──────────────┐   │
    │   │  Folding      │   │
    │   │  Surface      │   │
    │   │  (panels sit  │   │
    │   │   inside)     │   │
    │   └──────────────┘   │
    │                      │
    └──────────────────────┘
         ▲
    4x 2020 extrusion uprights
    for camera gantry (~18")
```

### 3D-Printed Joints

- Corner brackets, servo mount adapters, and hinge rail clips printed in PETG or ABS for heat resistance
- Designed to slide into T-slot channels and clamp with M5 T-nuts
- STL/SCAD files to be added to `hardware_files/full_scale/`

---

## 3. Folding Panels

### Material Options

| Option | Thickness | Weight | Cost | Notes |
|--------|-----------|--------|------|-------|
| **6mm plywood (birch)** | 6mm | ~800g/panel | $5-8/panel | Easy to cut, strong, good for prototyping |
| 3mm acrylic (cast) | 3mm | ~500g/panel | $8-12/panel | Lighter, more rigid, cracks under impact |
| 3mm aluminum sheet | 3mm | ~600g/panel | $10-15/panel | Durable, overkill for prototype |

### Recommended: 6mm Birch Plywood

- Cut to panel dimensions matching the 1:4 prototype scaled up (roughly 10" x 22" for side panels, 18" x 10" for bottom panel)
- Sand edges smooth to avoid snagging garments
- Apply fabric or silicone covering for garment grip (prevents slipping during fold)

### Surface Covering

- **Silicone shelf liner:** Inexpensive, grippy, easy to attach with spray adhesive. ~$6/roll.
- **Neoprene sheet (1-2mm):** Better grip, cushioned, professional feel. ~$10/panel.
- The covering prevents garments from sliding off during the fold motion, a critical issue at full scale where garment weight creates momentum.

### Hinge System

- **Aluminum hinge rails:** Piano hinges (continuous hinges) along each panel edge, 24" or 30" as needed
- Piano hinges provide uniform support along the full edge, unlike point hinges which create stress concentrations
- Mount with M4 flat-head screws countersunk into the panel surface
- Alternatively: printed hinge clips that slide into the T-slot extrusion channels

---

## 4. Servos / Actuators

### Servo Selection

| Servo | Torque | Voltage | Stall Current | Weight | Cost | Notes |
|-------|--------|---------|---------------|--------|------|-------|
| MG996R (current) | 10 kg-cm | 6V | 2.5A | 55g | $8 | Not sufficient for full-scale panels |
| **DS3225 (recommended)** | 25 kg-cm | 6.8V | 3A | 60g | $15-20 | Metal gear, waterproof, popular upgrade |
| RDS3235 | 35 kg-cm | 7.4V | 4A | 80g | $20-25 | Higher torque for heavier panels or garments |

### Recommended: DS3225 (25 kg-cm)

- 2.5x the torque of MG996R, sufficient for full-size plywood panels with garments
- Same standard servo footprint and PWM interface
- Compatible with PCA9685 driver (no software changes)
- Available from Amazon/AliExpress in quantity

### Linkage Design

At full scale, direct-drive servo horns may not provide enough mechanical advantage. A horn-and-pushrod linkage amplifies force:

```
    Servo Mount (fixed to frame)
    ┌─────────┐
    │  SERVO  │
    │  ┌──┐   │
    │  │()│──── Servo Horn (25mm arm)
    │  └──┘   │       │
    └─────────┘       │
                      │  Pushrod (M3 threaded rod + ball links)
                      │
                      ▼
              Panel Hinge Edge
              ┌─────────────────
              │  PANEL
              │
```

- **Servo horn:** Single-arm, 25mm radius. Provides ~25mm lever arm.
- **Pushrod:** M3 threaded rod with adjustable ball-link ends. Length depends on mounting geometry (~80-120mm).
- **Ball links:** Allow angular misalignment during the fold arc. M3 ball link sets available from RC hobby suppliers (~$5/set).
- **Mechanical advantage:** With a 25mm horn and ~50mm attachment point on the panel, the effective torque at the panel is roughly doubled.

---

## 5. Camera

### Pi Camera v2 (Retained)

- Same Sony IMX219 8MP sensor
- Mounted on a taller gantry to cover the full 24" x 30" folding surface
- **Gantry height:** ~18" (457mm) above the folding surface
  - At 18", the Camera v2 with its 62.2-degree horizontal FOV covers approximately 20" width
  - 30" base width requires the camera at roughly 24" height, or use the wide-angle lens attachment

### Gantry Construction

- Two vertical 2020 extrusion uprights (~18-24") mounted to the rear of the base frame
- One horizontal 2020 crossbar connecting the uprights
- 3D-printed camera mount plate bolted to the center of the crossbar
- Add diagonal braces (printed or extrusion) to prevent camera sway during folding vibration

### Lens Considerations

- The stock Pi Camera v2 lens may have insufficient FOV at practical gantry heights
- **Option A:** Raise gantry to ~24" for full coverage with stock lens
- **Option B:** Use an aftermarket wide-angle lens (120-degree FOV, ~$10) for lower gantry height
- Either option requires recalibrating the vision pipeline's perspective transform

---

## 6. Power System

### Architecture: Single 12V Input with Buck Converters

```
    ┌─────────────────┐
    │ 12V / 10A DC PSU│    (120W, AC-DC switching supply)
    │ (Mean Well or   │
    │  equivalent)    │
    └───────┬─────────┘
            │ 12V main bus
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
 ┌────────┐   ┌────────┐
 │ Buck #1│   │ Buck #2│
 │ 12V→5V │   │12V→6.8V│    (LM2596 or XL4015 module)
 │  3A    │   │  5A    │
 └───┬────┘   └───┬────┘
     │             │
     ▼             ▼
  Raspberry Pi   PCA9685 V+ terminal
  (5V USB-C      (servo power rail)
   via buck or
   micro-USB)
```

### Power Specifications

| Rail | Voltage | Current | Module | Notes |
|------|---------|---------|--------|-------|
| Main input | 12V DC | 10A | Mean Well LRS-100-12 or similar | Single point of power entry |
| Pi supply | 5V | 3A | LM2596 buck converter | Feed via USB-C breakout or GPIO pins 2+4 (5V) |
| Servo supply | 6.8V | 5A | XL4015 5A buck converter | Adjustable output, set to match DS3225 spec |

### Advantages Over Dual-PSU Prototype

- Single AC outlet, single power cord
- Cleaner installation, no separate wall warts
- Common ground is inherent (shared 12V supply ground)
- Mean Well supplies are reliable, UL-listed, and well-suited for 24/7 operation

---

## 7. Controller

### Raspberry Pi 4 (Retained)

- Same RPi 4 Model B (4GB)
- Same PCA9685 16-channel PWM driver on I2C
- **No software changes required** — the servos respond to the same PWM signals regardless of physical size
- The `fold_sequences.py` step timings may need adjustment for larger panel inertia (slower, smoother ramps)

### Software Adjustments

| Parameter | Prototype Value | Full-Scale Value | Reason |
|-----------|----------------|-----------------|--------|
| Servo min/max pulse | 150-600 (PCA9685 ticks) | Recalibrate per DS3225 | Different servo model |
| Fold speed (step delay) | 15ms per degree | 25-30ms per degree | Larger panels need slower motion to avoid overshoot |
| Camera resolution | 640x480 | 1280x720 or 1920x1080 | Larger surface needs more pixels for garment detection |
| Camera height calibration | 3" gantry | 18-24" gantry | Perspective transform recalibration |

---

## 8. Design Challenges

### Fabric Grip
- Garments tend to slide during folding, especially synthetic fabrics
- **Mitigation:** Silicone or neoprene panel surface; optional vacuum holes with small suction pump

### Wrinkle Detection
- The current vision pipeline detects garment outline but not wrinkles
- Full-scale wrinkle detection requires higher-resolution imaging and potentially ML-based analysis
- **Mitigation:** Higher camera resolution; future ML model for wrinkle mapping

### Varying Garment Sizes
- T-shirts, pants, towels, and dress shirts have very different dimensions and fold sequences
- The prototype's garment classifier handles basic categories but may need expansion
- **Mitigation:** Expand `garment_classifier.py` heuristics; add size estimation based on detected contour area

### Cycle Speed
- Full-scale folds take longer due to panel inertia and required care with garments
- Target: < 30 seconds per garment for a basic fold
- **Mitigation:** Optimize fold sequence timing; use faster servos; overlap panel motions where safe

### Noise Reduction
- Larger servos under load produce more noise (gear whine, frame vibration)
- **Mitigation:** Rubber servo mount dampeners; frame vibration isolation feet; slower acceleration ramps

---

## 9. Estimated Full-Scale BOM

| # | Item | Qty | Unit Cost | Total | Notes |
|---|------|-----|-----------|-------|-------|
| 1 | 2020 Aluminum Extrusion (1m lengths) | 6 | $5 | $30 | Base frame + gantry uprights + crossbar |
| 2 | Cast aluminum corner brackets | 12 | $2 | $24 | 90-degree L-brackets with M5 hardware |
| 3 | M5 T-nuts and bolts kit | 1 | $15 | $15 | 50-piece kit for frame assembly |
| 4 | 6mm birch plywood panels (pre-cut) | 3 | $8 | $24 | Left, right, bottom folding panels |
| 5 | Piano hinges (continuous, 24") | 2 | $6 | $12 | Left and right panel hinges |
| 6 | Piano hinge (continuous, 30") | 1 | $8 | $8 | Bottom panel hinge |
| 7 | Silicone shelf liner (roll) | 1 | $8 | $8 | Panel surface grip covering |
| 8 | DS3225 25kg servo | 3 | $18 | $54 | Panel actuators |
| 9 | M3 pushrod + ball link sets | 3 | $5 | $15 | Servo-to-panel linkages |
| 10 | Raspberry Pi 4 (4GB) | 1 | $55 | $55 | Controller (reuse from prototype) |
| 11 | PCA9685 PWM driver | 1 | $6 | $6 | I2C servo driver (reuse from prototype) |
| 12 | Pi Camera v2 | 1 | $25 | $25 | Vision system (reuse from prototype) |
| 13 | 12V/10A switching power supply | 1 | $25 | $25 | Main power input |
| 14 | LM2596 buck converter (5V out) | 1 | $3 | $3 | Pi power |
| 15 | XL4015 buck converter (6.8V out) | 1 | $5 | $5 | Servo power |
| 16 | Wiring, connectors, misc hardware | 1 | $20 | $20 | Terminals, wire, heat shrink, zip ties |
| 17 | 3D-printed brackets and adapters | -- | $10 | $10 | PETG filament for custom joints |
| 18 | Rubber feet / vibration dampeners | 4 | $2 | $8 | Frame feet |
| 19 | Camera ribbon cable (610mm) | 1 | $5 | $5 | Extended length for tall gantry |
| 20 | Wide-angle lens for Pi Camera (optional) | 1 | $10 | $10 | Better FOV coverage |
| | | | | | |
| | **Estimated Total** | | | **$382** | |

> **Cost range: ~$380-$550** depending on supplier, shipping, and optional upgrades (35kg servos, aluminum panels, additional cameras). Reusing the Pi, PCA9685, and camera from the prototype saves ~$86.

---

## 10. Future Enhancements

### Conveyor Feed System
- Add a motorized belt or roller system to feed garments onto the folding surface automatically
- Enables continuous batch folding without manual garment placement
- Requires an additional stepper motor, driver (e.g., A4988), and belt mechanism
- Estimated addition: $40-60

### Second Camera for Edge Detection
- Mount a side-angle or low-angle camera to detect garment edges and thickness
- Improves fold accuracy by detecting fabric drape and overhang
- Could use a second Pi Camera v2 or a USB webcam
- PCA9685 has unused channels; Pi has additional CSI/USB ports
- Estimated addition: $25-35

### ML-Based Classification Upgrade
- Replace heuristic-based `garment_classifier.py` with a trained ML model
- Use TensorFlow Lite or ONNX runtime on the Pi for inference
- Train on a garment dataset (top-down images of T-shirts, pants, towels, etc.)
- Enables recognition of garment type, size, orientation, and fold strategy
- Can run on existing Pi 4 hardware with Coral USB accelerator (~$60) for real-time inference
- Estimated addition: $0 (software) to $60 (with Coral accelerator)

### Multi-Garment Stacking
- After folding, use the bottom panel or a secondary mechanism to stack folded garments
- Requires a shelf/tray system and additional actuator
- Estimated addition: $30-50

### Remote Monitoring / Web Interface
- Add a Flask or FastAPI web server on the Pi for remote monitoring
- Live camera feed, fold status, garment count, error alerts
- Control via smartphone or tablet on local network
- Estimated addition: $0 (software only)

### Enclosure
- Build an outer enclosure from 2020 extrusion and acrylic panels
- Provides safety (keeps hands away from moving panels), noise dampening, and a finished appearance
- Estimated addition: $50-80
