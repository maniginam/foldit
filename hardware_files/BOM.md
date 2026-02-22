# FoldIt Clothes-Folding Robot -- Bill of Materials (BOM)

**Project:** FoldIt Tabletop Clothes Folder Prototype
**Revision:** 1.0
**Date:** 2026-02-22
**Full-scale base plate:** ~24" x 30"
**Prototype scale:** 1:4 (3D-printed)

---

## 1. Electronics

| # | Item | Qty | Unit Cost | Total | Source | Notes |
|---|------|-----|-----------|-------|--------|-------|
| 1.1 | Raspberry Pi 4 Model B (4GB) | 1 | $55.00 | $55.00 | Adafruit / PiShop | 4GB recommended; 2GB workable but tight for OpenCV. 8GB unnecessary for this use case. |
| 1.2 | Pi Camera Module v2 (8MP) | 1 | $25.00 | $25.00 | Adafruit / Amazon | Sony IMX219 sensor. NoIR variant available if low-light operation needed. |
| 1.3 | MG996R Servo Motor | 3 | $8.00 | $24.00 | Amazon | 10 kg-cm torque, metal gear. One per folding panel (left, right, bottom). Comes with servo horns and mounting screws. |
| 1.4 | PCA9685 16-Channel PWM Servo Driver | 1 | $6.00 | $6.00 | Adafruit / Amazon | I2C interface (SDA/SCL). Offloads PWM generation from Pi GPIO. Adafruit #815 is the reference design; clones work fine. |
| 1.5 | 5V 3A USB-C Power Supply (for Pi) | 1 | $8.00 | $8.00 | Adafruit / CanaKit | Official Raspberry Pi PSU recommended. Must be USB-C, 5.1V/3A for stable operation. |
| 1.6 | 6V 4A DC Power Supply (for servos) | 1 | $12.00 | $12.00 | Amazon / DigiKey | Dedicated servo power. 3x MG996R at stall can draw ~2.5A each; 4A handles typical loads with headroom. Do NOT power servos from Pi. |
| 1.7 | LM2596 DC-DC Buck Converter | 1 | $3.00 | $3.00 | Amazon | Adjustable step-down. Useful if using a single 12V supply split to 5V (Pi) and 6V (servos). Not needed if using two separate supplies. |
| 1.8 | MicroSD Card (32GB, Class 10 / A1) | 1 | $8.00 | $8.00 | Amazon | SanDisk Ultra or Samsung EVO recommended. 32GB sufficient; 64GB if storing garment image datasets locally. |
| 1.9 | Solderless Breadboard (830 tie-points) | 1 | $5.00 | $5.00 | Amazon / Adafruit | Full-size breadboard for prototyping. Upgrade to proto/perf board for permanent build. |
| 1.10 | Jumper Wire Kit (M-F, M-M, F-F) | 1 | $7.00 | $7.00 | Amazon | 120-piece assorted kit. Need M-F for Pi GPIO to PCA9685; M-M for breadboard. |
| 1.11 | Camera Ribbon Cable (300mm or 610mm) | 1 | $4.00 | $4.00 | Adafruit / Amazon | Stock cable is 150mm. Longer cable needed if camera gantry is elevated above base. 300mm usually sufficient for prototype. |
| 1.12 | 5mm LED (green) + 220 Ohm Resistor | 2 | $0.50 | $1.00 | Amazon / DigiKey | Optional status indicator. Green = ready, red = error. Can substitute with NeoPixel for multi-color on one GPIO pin. |
| 1.13 | Capacitor 1000uF 10V (electrolytic) | 1 | $0.50 | $0.50 | DigiKey / Amazon | Place across servo power rail on PCA9685 to absorb voltage spikes during servo startup. Strongly recommended. |

**Electronics Subtotal: $158.50**

---

## 2. Mechanical Hardware

| # | Item | Qty | Unit Cost | Total | Source | Notes |
|---|------|-----|-----------|-------|--------|-------|
| 2.1 | M3 x 8mm Socket Head Cap Screws | 20 | $0.10 | $2.00 | Amazon / McMaster-Carr | For general panel-to-bracket and bracket-to-frame fastening. Hex socket preferred for tight spaces. |
| 2.2 | M3 x 12mm Socket Head Cap Screws | 10 | $0.10 | $1.00 | Amazon / McMaster-Carr | For servo mount attachment through thicker printed parts. |
| 2.3 | M3 x 16mm Socket Head Cap Screws | 6 | $0.10 | $0.60 | Amazon / McMaster-Carr | For securing hinge brackets through base plate where extra thread engagement is needed. |
| 2.4 | M3 Hex Nuts | 30 | $0.05 | $1.50 | Amazon / McMaster-Carr | Match with M3 screws above. Nyloc (lock nuts) recommended for vibration-prone joints. |
| 2.5 | M3 Flat Washers | 20 | $0.03 | $0.60 | Amazon / McMaster-Carr | Distribute load on 3D-printed surfaces to prevent cracking. |
| 2.6 | M2.5 x 6mm Screws + Nuts | 4 | $0.10 | $0.40 | Amazon / McMaster-Carr | For Raspberry Pi mounting to base plate. Pi mounting holes are M2.5 spaced. Nylon screws are a safe alternative. |
| 2.7 | M2 x 5mm Screws + Nuts | 4 | $0.10 | $0.40 | Amazon / McMaster-Carr | For Pi Camera Module v2 mounting to gantry. Camera board holes are M2. |
| 2.8 | 3mm Diameter Steel Rod (100mm length) | 3 | $1.00 | $3.00 | Amazon / hobby shop | Cut to length for panel hinge pins. Stainless steel or music wire. Each hinge needs ~30-40mm; one rod per panel. |
| 2.9 | Rubber Feet (self-adhesive, 10mm) | 4 | $0.50 | $2.00 | Amazon | Stick to bottom of base plate. Prevents sliding and dampens vibration during folding. |
| 2.10 | Nylon Standoffs M2.5 x 11mm | 4 | $0.25 | $1.00 | Amazon / Adafruit | Elevate Pi off base plate for airflow and to prevent shorts against screw heads. Male-female style. |
| 2.11 | Servo Horns (single-arm and cross-style) | -- | $0.00 | $0.00 | (included with MG996R) | MG996R ships with horn assortment. Use single-arm horn connected to hinge bracket via linkage or direct drive. |

**Mechanical Hardware Subtotal: $12.50**

---

## 3. 3D-Printed Parts (PLA)

All parts printed at 1:4 scale for prototyping. Estimated print times and filament usage assume 0.2mm layer height, 20% infill, PLA filament at ~$20/kg.

| # | Part | Qty | Filament (g) | Print Time (est.) | Cost | Notes |
|---|------|-----|-------------|-------------------|------|-------|
| 3.1 | Base Plate | 1 | 120g | 6 hrs | $2.40 | Full-scale: 24" x 30". At 1:4 scale: ~6" x 7.5". Print flat. 3-4 perimeters for rigidity. |
| 3.2 | Left Folding Panel | 1 | 40g | 2 hrs | $0.80 | Hinges along left edge of base plate. Thin profile (~3mm wall) to reduce weight. |
| 3.3 | Right Folding Panel | 1 | 40g | 2 hrs | $0.80 | Mirror of left panel. Same dimensions and hinge design. |
| 3.4 | Bottom Folding Panel | 1 | 50g | 2.5 hrs | $1.00 | Folds upward from bottom edge. Slightly wider than side panels. |
| 3.5 | Hinge Brackets | 6 | 10g each (60g) | 3 hrs total | $1.20 | 2 per panel. Accepts 3mm steel rod. Print in strongest orientation (load path along layer lines). |
| 3.6 | Servo Mounts | 3 | 15g each (45g) | 2 hrs total | $0.90 | Designed to cradle MG996R body. Bolt to base plate with M3 hardware. |
| 3.7 | Camera Gantry / Arm | 1 | 35g | 1.5 hrs | $0.70 | Elevates camera ~12" above folding surface (3" at 1:4 scale). Must be rigid to avoid vibration blur. Consider bracing. |
| 3.8 | PLA Filament (1kg spool) | 1 | -- | -- | $20.00 | 1kg spool covers all parts above (~390g total) with ample margin for test prints and reprints. |

**3D Printing Subtotal: $27.80**
*(Filament cost only. Assumes access to a 3D printer. If outsourcing, budget $50-80 for a print service.)*

---

## 4. Optional / Recommended Accessories

| # | Item | Qty | Unit Cost | Total | Source | Notes |
|---|------|-----|-----------|-------|--------|-------|
| 4.1 | Heat Shrink Tubing Assortment | 1 kit | $6.00 | $6.00 | Amazon | For insulating solder joints and bundling wires cleanly. |
| 4.2 | Cable Ties / Zip Ties (100-pack, small) | 1 | $4.00 | $4.00 | Amazon | Cable management along frame and gantry. |
| 4.3 | Servo Extension Cables (300mm) | 3 | $2.00 | $6.00 | Amazon | If stock MG996R leads are too short to reach PCA9685 board. JR-style 3-pin connectors. |
| 4.4 | Silicone Grip Mat (12" x 12") | 1 | $8.00 | $8.00 | Amazon | Placed on base plate surface to prevent garment slipping during fold operations. Cut to size. |
| 4.5 | Raspberry Pi Case (open-frame) | 1 | $8.00 | $8.00 | Amazon / Adafruit | Optional. Protects Pi. Use open-frame or mount direct to base plate with standoffs. |
| 4.6 | MicroHDMI to HDMI Cable | 1 | $8.00 | $8.00 | Amazon | For initial Pi setup and debugging. Not needed once headless SSH is configured. |
| 4.7 | USB Keyboard + Mouse (for setup) | 1 | $0.00 | $0.00 | (use existing) | Only needed during initial Raspberry Pi OS setup. |

**Optional Accessories Subtotal: $40.00**

---

## Cost Summary

| Category | Subtotal |
|----------|----------|
| 1. Electronics | $158.50 |
| 2. Mechanical Hardware | $12.50 |
| 3. 3D-Printed Parts (filament) | $27.80 |
| 4. Optional / Recommended | $40.00 |
| **Estimated Total** | **$238.80** |

> **Notes:**
> - Prices are estimates as of February 2026 and may vary by supplier and region.
> - Buying hardware (screws, nuts, washers) in assortment kits is often cheaper than individual quantities. A typical M2/M2.5/M3 kit runs $12-15 and covers all needs above.
> - The PCA9685 board is strongly recommended over bit-banged GPIO PWM. Software PWM on the Pi introduces jitter that causes servo twitching.
> - The total assumes access to a 3D printer. If outsourcing prints, add $50-80 to the total.
> - Budget an additional $10-20 for miscellaneous items (solder, electrical tape, spare wires, etc.).
