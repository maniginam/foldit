# FoldIt Robot - Wiring Diagram & Electrical Schematic

**Project:** FoldIt Tabletop Clothes Folder Prototype
**Revision:** 1.0
**Date:** 2026-02-22

---

## 1. ASCII Wiring Diagram

```
                        ╔══════════════════════════════════════════════╗
                        ║          RASPBERRY PI 4 MODEL B             ║
                        ║                                              ║
     USB-C 5V/3A ──────║──► PWR IN                                    ║
     Power Supply       ║                                              ║
                        ║   GPIO HEADER (selected pins)                ║
                        ║   ┌─────────────────────────────────┐        ║
                        ║   │ Pin 1  [3.3V] ──────────┐       │        ║
                        ║   │ Pin 3  [GPIO2/SDA1] ──┐ │       │        ║
                        ║   │ Pin 5  [GPIO3/SCL1] ┐ │ │       │        ║
                        ║   │ Pin 6  [GND] ─────┐ │ │ │       │        ║
                        ║   │ Pin 18 [GPIO24] ─┐ │ │ │ │       │        ║
                        ║   │ Pin 14 [GND] ──┐ │ │ │ │ │       │        ║
                        ║   └────────────────│─│─│─│─│─│───────┘        ║
                        ║                    │ │ │ │ │ │                ║
                        ║   CSI CAMERA PORT  │ │ │ │ │ │                ║
                        ║   ┌──────────┐     │ │ │ │ │ │                ║
                        ║   │ ▓▓▓▓▓▓▓▓ │     │ │ │ │ │ │                ║
                        ║   └────┬─────┘     │ │ │ │ │ │                ║
                        ╚════════│═══════════│═│═│═│═│═│════════════════╝
                                 │           │ │ │ │ │ │
              ┌──────────────────┘           │ │ │ │ │ │
              │  Ribbon Cable (300mm)        │ │ │ │ │ │
              │                              │ │ │ │ │ │
     ┌────────▼────────┐                     │ │ │ │ │ │
     │  PI CAMERA v2   │                     │ │ │ │ │ │
     │  (8MP IMX219)   │                     │ │ │ │ │ │
     │  Mounted on     │                     │ │ │ │ │ │
     │  camera gantry  │                     │ │ │ │ │ │
     └─────────────────┘                     │ │ │ │ │ │
                                             │ │ │ │ │ │
          STATUS LED                         │ │ │ │ │ │
          ┌─────┐                            │ │ │ │ │ │
 GND(14)──│─[K] │◄── 330Ω ◄─────────────────│─┘ │ │ │ │
          │ LED │              GPIO24 ───────┘   │ │ │ │
          └─────┘                                │ │ │ │
                                                 │ │ │ │
    ┌─────────────────────────────────────────────│─│─│─│──────────────┐
    │                                            │ │ │ │              │
    │  GND(6) ───────────────────────────────────┘ │ │ │              │
    │  SCL ────────────────────────────────────────┘ │ │              │
    │  SDA ──────────────────────────────────────────┘ │              │
    │  VCC (3.3V) ─────────────────────────────────────┘              │
    │                                                                  │
    │         ╔═══════════════════════════════════════╗                │
    │         ║       PCA9685 16-CH PWM DRIVER        ║                │
    │         ║                                        ║                │
    │    ┌────║── VCC  (3.3V logic power)              ║                │
    │    │    ║── GND  (logic ground)                   ║                │
    │    │    ║── SCL  (I2C clock)                      ║                │
    │    │    ║── SDA  (I2C data)                       ║                │
    │    │    ║                                         ║                │
    │    │    ║   SERVO OUTPUT CHANNELS                 ║                │
    │    │    ║   ┌─────┬─────┬─────┐                  ║                │
    │    │    ║   │CH 0 │CH 1 │CH 2 │  CH3-15 unused   ║                │
    │    │    ║   │ S G V│ S G V│ S G V│                ║                │
    │    │    ║   └──┬──┘└──┬──┘└──┬──┘                 ║                │
    │    │    ║      │      │      │                    ║                │
    │    │    ║   V+ TERMINAL ──────────┐               ║                │
    │    │    ║   GND TERMINAL ───────┐ │               ║                │
    │    │    ║                        │ │               ║                │
    │    │    ╚════════════════════════│═│═══════════════╝                │
    │    │                            │ │                                │
    │    │    1000uF 10V Cap          │ │                                │
    │    │    ┌──┤├──┐                │ │                                │
    │    │    │  (+)  │               │ │                                │
    │    │    │       │               │ │                                │
    │    │    └───┬───┘               │ │                                │
    │    │        │                   │ │                                │
    │    │        ▼                   │ │                                │
    │    │   ─────────── Common GND ──┘ │                                │
    │    │                              │                                │
    │    │              ┌───────────────┘                                │
    │    │              │                                                │
    │    │    ┌─────────▼─────────┐                                     │
    │    │    │   6V / 5A DC PSU  │                                     │
    │    │    │   (Servo Power)   │                                     │
    │    │    │   V+ ─────────────┼──► To PCA9685 V+ terminal          │
    │    │    │   GND ────────────┼──► Common GND bus                   │
    │    │    └───────────────────┘                                     │
    │    │                                                              │
    └────│──────────────────────────────────────────────────────────────┘
         │
         ▼
    SERVO CONNECTIONS (via PCA9685 channels)

    CH 0 ──► LEFT PANEL SERVO (MG996R)
             Signal (orange/white) ← CH0 S
             Power  (red)          ← V+ rail
             Ground (brown/black)  ← GND rail

    CH 1 ──► RIGHT PANEL SERVO (MG996R)
             Signal (orange/white) ← CH1 S
             Power  (red)          ← V+ rail
             Ground (brown/black)  ← GND rail

    CH 2 ──► BOTTOM PANEL SERVO (MG996R)
             Signal (orange/white) ← CH2 S
             Power  (red)          ← V+ rail
             Ground (brown/black)  ← GND rail
```

### Simplified Block Diagram

```
  ┌──────────────┐    USB-C     ┌──────────────────┐
  │  5V/3A PSU   │────────────►│   Raspberry Pi 4  │
  └──────────────┘              │                    │
                                │  GPIO2 (SDA) ──────┼──┐
                                │  GPIO3 (SCL) ──────┼──┼──┐
                                │  3.3V ─────────────┼──┼──┼──┐
                                │  GND ──────────────┼──┼──┼──┼──┐
                                │  GPIO24 ───────────┼──┼──┼──┼──┼──► 330Ω ──► LED ──► GND
                                │  CSI port ─────────┼──┼──┼──┼──┘
                                └────────────────────┘  │  │  │
                                       │ ribbon         │  │  │
                                ┌──────▼──────┐         │  │  │
                                │ Pi Camera v2│         │  │  │
                                └─────────────┘         │  │  │
                                                        │  │  │
  ┌──────────────┐              ┌───────────────────┐   │  │  │
  │  6V/5A PSU   │──► V+ ──────│   PCA9685 Driver  │◄──┘  │  │
  │ (servo pwr)  │──► GND ─┬───│   I2C: 0x40       │◄─────┘  │
  └──────────────┘         │   │                    │◄────────┘
                           │   │  CH0 ──► Servo L   │
     Common GND ◄──────────┘   │  CH1 ──► Servo R   │
     (Pi GND + PSU GND         │  CH2 ──► Servo B   │
      + PCA9685 GND)           └────────────────────┘
                                        │
                                   1000uF cap
                                   across V+/GND
```

---

## 2. Connection Table

| Component | Pin / Port | Connects To | Wire Color | Notes |
|-----------|-----------|-------------|------------|-------|
| **Raspberry Pi 4** | Pin 1 (3.3V) | PCA9685 VCC | Red | Logic power for PCA9685 (NOT servo power) |
| Raspberry Pi 4 | Pin 3 (GPIO2 / SDA1) | PCA9685 SDA | Blue | I2C data line |
| Raspberry Pi 4 | Pin 5 (GPIO3 / SCL1) | PCA9685 SCL | Yellow | I2C clock line |
| Raspberry Pi 4 | Pin 6 (GND) | PCA9685 GND | Black | Shared logic ground |
| Raspberry Pi 4 | Pin 6 (GND) | Common GND bus | Black | Bridge to servo PSU ground |
| Raspberry Pi 4 | Pin 18 (GPIO24) | 330 ohm resistor | Green | Status LED signal |
| Raspberry Pi 4 | Pin 14 (GND) | LED cathode | Black | LED return path |
| Raspberry Pi 4 | CSI port | Pi Camera v2 ribbon | Ribbon | 300mm FFC ribbon cable |
| Raspberry Pi 4 | USB-C | 5V/3A PSU | -- | Dedicated Pi power supply |
| **PCA9685** | VCC | Pi Pin 1 (3.3V) | Red | 3.3V logic supply |
| PCA9685 | GND | Pi Pin 6 (GND) | Black | Logic ground |
| PCA9685 | SDA | Pi Pin 3 (GPIO2) | Blue | I2C data, addr 0x40 default |
| PCA9685 | SCL | Pi Pin 5 (GPIO3) | Yellow | I2C clock, 100/400 kHz |
| PCA9685 | V+ terminal | 6V/5A PSU (+) | Red (thick) | Servo power input, min 16 AWG |
| PCA9685 | GND terminal | 6V/5A PSU (-) | Black (thick) | Servo power ground, min 16 AWG |
| PCA9685 | CH0 (signal) | Left servo signal | Orange | PWM signal wire |
| PCA9685 | CH1 (signal) | Right servo signal | Orange | PWM signal wire |
| PCA9685 | CH2 (signal) | Bottom servo signal | Orange | PWM signal wire |
| **Left Servo** (MG996R) | Signal (orange) | PCA9685 CH0 S | Orange | PWM input |
| Left Servo | Power (red) | PCA9685 V+ rail | Red | 6V from servo PSU |
| Left Servo | Ground (brown) | PCA9685 GND rail | Brown | Common ground |
| **Right Servo** (MG996R) | Signal (orange) | PCA9685 CH1 S | Orange | PWM input |
| Right Servo | Power (red) | PCA9685 V+ rail | Red | 6V from servo PSU |
| Right Servo | Ground (brown) | PCA9685 GND rail | Brown | Common ground |
| **Bottom Servo** (MG996R) | Signal (orange) | PCA9685 CH2 S | Orange | PWM input |
| Bottom Servo | Power (red) | PCA9685 V+ rail | Red | 6V from servo PSU |
| Bottom Servo | Ground (brown) | PCA9685 GND rail | Brown | Common ground |
| **Pi Camera v2** | Ribbon connector | Pi CSI port | Ribbon | 15-pin FFC, 300mm length |
| **Status LED** | Anode (+) | 330 ohm resistor | Green | Resistor connects to GPIO24 |
| Status LED | Cathode (-) | Pi Pin 14 (GND) | Black | Return to ground |
| **1000uF Cap** | (+) | PCA9685 V+ rail | -- | Spike absorption, observe polarity |
| 1000uF Cap | (-) | PCA9685 GND rail | -- | Must be rated >= 10V |
| **6V/5A PSU** | V+ | PCA9685 V+ terminal | Red (thick) | Dedicated servo power |
| 6V/5A PSU | GND | Common GND bus | Black (thick) | MUST tie to Pi GND |

---

## 3. Power Budget

### Per-Component Current Draw

| Component | Voltage | Idle Current | Active Current | Peak / Stall | Notes |
|-----------|---------|-------------|----------------|-------------|-------|
| Raspberry Pi 4 (4GB) | 5V | 600 mA | 900 mA | 1200 mA | With camera active, no USB peripherals |
| Pi Camera v2 | 3.3V (via Pi) | 0 mA | 250 mA | 250 mA | Powered through CSI, included in Pi draw |
| PCA9685 driver | 3.3V logic | 10 mA | 10 mA | 10 mA | Logic power only; servo power separate |
| MG996R servo x1 | 6V | 10 mA | 500 mA | 2500 mA | Stall current per servo |
| MG996R servo x3 | 6V | 30 mA | 1500 mA | 7500 mA | All 3 servos worst case |
| Status LED | 3.3V | 0 mA | 10 mA | 10 mA | Via 330 ohm resistor |

### Power Supply Requirements

| Supply | Voltage | Min Capacity | Recommended | Rationale |
|--------|---------|-------------|-------------|-----------|
| Pi Power Supply | 5V USB-C | 2.5A | **3A** | Pi + camera + GPIO load. Official RPi PSU recommended. |
| Servo Power Supply | 6V DC | 3A | **5A** | 3 servos active simultaneously draw ~1.5A typical. 5A provides headroom for stall/startup transients. |

### Total System Power

| Rail | Typical Draw | Peak Draw |
|------|-------------|-----------|
| 5V (Pi) rail | ~1.0A (5W) | ~1.2A (6W) |
| 6V (Servo) rail | ~1.5A (9W) | ~7.5A (45W) |
| **System total** | **~14W typical** | **~51W peak** |

> **Note:** Peak draw occurs only if all three servos stall simultaneously, which should not happen during normal operation. The 1000uF capacitor on the servo rail handles brief current spikes during servo startup.

---

## 4. Safety Notes

### Capacitor on Servo Rail (Required)
- Place a **1000uF 10V electrolytic capacitor** directly across the V+ and GND terminals on the PCA9685 board
- Observe polarity: (+) stripe to V+, (-) stripe to GND
- Absorbs voltage spikes when servos start/stop, protecting both the PCA9685 and the servos
- Use a cap rated at least 10V (the 6V servo supply needs headroom)

### Reverse Polarity Protection
- Double-check polarity on the 6V servo power supply before connecting
- If using barrel jack connectors, verify center-positive vs center-negative
- Consider adding an inline Schottky diode (e.g., 1N5822) on the V+ line for protection, accepting ~0.3V drop
- The PCA9685 has no built-in reverse polarity protection and will be destroyed by reversed power

### Never Power Servos from Pi 5V
- The Pi's 5V rail can supply at most ~1A total to peripherals
- A single MG996R can draw up to 2.5A at stall
- Powering servos from the Pi will cause brownouts, SD card corruption, or permanent Pi damage
- **Always** use a separate dedicated power supply for the servo rail

### Common Ground (Critical)
- The Pi GND, PCA9685 GND, and servo power supply GND **must** all be connected together
- Without a common ground, I2C communication will be unreliable and PWM signals will not reference correctly
- Use a GND bus or star-ground topology from a single point

### General Electrical Safety
- Keep servo power wiring (16-18 AWG) separate from signal wiring where possible
- Secure all connections; loose jumper wires on a breadboard can cause intermittent faults
- Do not exceed 3.3V on any Pi GPIO pin; the Pi has no overvoltage protection on GPIO
- Disconnect power before making wiring changes
- When using a breadboard, ensure power rails are continuous (some boards have split rails)
- For a permanent build, migrate from breadboard to soldered proto-board or PCB
