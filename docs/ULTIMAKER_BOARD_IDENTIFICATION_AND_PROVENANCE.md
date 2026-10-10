# Ultimaker Board Identification, Component Hierarchy, and Provenance

**Target Board:** Ultimaker Ultimainboard v2.1.4  
**Specimen ID:** `bench-ultimaker-01`  
**Dataset Repository:** `https://github.com/TokitoAI/tokito-app-dataset`  
**Branch:** `ultimaker-component-ar`  
**Baseline Commit:** `ab1420fb08e813d4c761c6454fbba16cceaaa5dc`  

---

## 1. Board & Variant Identification

Visual inspection of all available high-resolution photographs (`IMG_20261010_092241.jpg`, `IMG_20261010_092241_1.jpg`, `IMG_20261010_092244.jpg`, `IMG_20261010_092247.jpg`, and the multi-angle `IMG_20261009_222024.jpg`–`222137_1.jpg` series) along with phone video sweeps confirms the following physical characteristics of the board specimen:

- **Silkscreen Identification:** Top-side silkscreen explicitly reads `Ultimainboard rev. 2.1.4`, verifying exact revision match with CAD sources in `data/board-sources/ultimainboard-2.1.4/`.
- **Form Factor & Dimensions:** Rectangular form factor measuring 175.0 mm (width X) × 79.0 mm (height Z) with 1.74 mm board thickness. Four non-plated corner mounting holes (3.2 mm diameter) located symmetrically at outer corners for rigid chassis mounting.
- **Main Microcontroller:** Microchip/Atmel ATmega2560-16AU in a 100-pin TQFP package (`U1`), operating at 16 MHz with dedicated crystal resonator `Y1`.
- **USB-to-UART Interface:** FTDI FT232RL in an SSOP-28 package (`U2`) adjacent to USB Type-B female receptacle `J19` and status LEDs `LED1` (TX) / `LED2` (RX).
- **Stepper Motor Drivers:** Five dedicated stepper channels (`X`, `Y`, `Z`, `E1`, `E2`), implemented with Allegro A4988-compatible drivers in QFN packages (`U6`, `U7`, `U8`, `U9`, `U10`) with adjacent current-sensing shunts and motor headers (`J14`, `J15`, `J16`, `J17`, `J18`).
- **Power Management & Heaters:**
  - `J24`: 2-position 24V screw terminal block for main DC power input.
  - `J21`: Screw terminal block for Heated Bed (HB) power output driven by high-current N-channel MOSFET `T1`.
  - `J8`, `J9`: Screw terminal blocks for Extruder Heaters 1 and 2, driven by MOSFETs `T2` and `T3`.
  - Switching buck regulator (`U3`, LM2576-5.0) generating the system +5V rail from 24V input, backed by toroidal inductor `L1` and electrolytic filtering capacitors.
- **Connectors & Interfaces:**
  - `J22`: 4-pin 2.54mm pitch single-row serial communication header (`SERIAL`), verified pinout: Pin 1 `+5V`, Pin 2 `GND`, Pin 3 `TXD2`, Pin 4 `RXD2`.
  - `J23`: 2×3 pin 2.54mm dual-row auxiliary input/output header (`EXT/IO`), verified pinout: Pin 1 `GND`, Pin 2 `GND`, Pin 3 `+5V`, Pin 4 `+5V`, Pin 5 `PC7`, Pin 6 `PD7`.
  - `J1`: 2×3 pin ICSP header for ATmega2560 (`ICSP1`), verified pinout: Pin 1 `PB3` (MISO), Pin 2 `+5V`, Pin 3 `PB1` (SCK), Pin 4 `PB2` (MOSI), Pin 5 `NRESET`, Pin 6 `GND`.
  - `J2`: 2×3 pin ICSP header for auxiliary controller (`ICSP2`).
  - `J20`: 2-pin keyed header for 19–24V cooling fan (`FAN 19-24V`).
  - `EXP1` / `EXP2`: Dual 2×5 shrouded box headers for LCD/rotary encoder interface.
  - `J4`, `J5`, `J6`, `J7`: 3-pin headers for endstop switches (X-min, Y-min, Z-min, etc.).

---

## 2. Comparison with CAD Source & Community Clone

The official Ultimaker 2 open-source repository design (`data/board-sources/ultimainboard-2.1.4/`) was cross-examined against the photographed specimen:

1. **Revision Coherence:** Both native Altium schematics (`schema1.SchDoc`..`schema5.SchDoc`) and imported KiCad board (`Ultimainboard-2.1.4.imported.kicad_pcb`) explicitly target `Ultimainboard V2.1.4`. Silkscreen legends, component placements, and pin numbering match the physical specimen precisely.
2. **Component Density:** KiCad PCB stats verify 574 total components (39 through-hole, 535 surface-mount) across 13,825 mm² board surface.
3. **Mounting Hole Anchors:** Four 3.2 mm mounting holes positioned at CAD coordinates `(7.5, 7.5)`, `(167.5, 7.5)`, `(167.5, 71.5)`, and `(7.5, 71.5)` mm correspond directly to the visible mechanical features on the photographed board.
4. **Pin 1 Orientation Triangles:** Silkscreen triangles visible in photos adjacent to `J22`, `J23`, `J1`, and `J2` align with Pad 1 in both Altium and KiCad footprints.

---

## 3. Verified Electrical Pinout & Aliases

### J22: 1×4 Serial Header (`SERIAL`)
| Pin Number | Silkscreen Label | Net Name | Schematic Record | Function |
|---|---|---|---|---|
| `1` | Triangle | `+5V` | schema3:1184 | +5V Logic Supply |
| `2` | — | `GND` | schema3:1187 | Ground Reference |
| `3` | `TXD` | `TXD2` | schema3:1190 | USART2 Transmit |
| `4` | `RXD` | `RXD2` | schema3:1193 | USART2 Receive |

### J23: 2×3 Auxiliary Header (`EXT/IO`)
| Pin Number | Position | Net Name | Schematic Record | Function |
|---|---|---|---|---|
| `1` | Lower-Left | `GND` | schema3:1215 | Ground Reference |
| `2` | Upper-Left | `GND` | schema3:1218 | Ground Reference |
| `3` | Lower-Mid | `+5V` | schema3:1221 | +5V Logic Supply |
| `4` | Upper-Mid | `+5V` | schema3:1224 | +5V Logic Supply |
| `5` | Lower-Right | `PC7` | schema3:1227 | ATmega2560 Port C7 |
| `6` | Upper-Right | `PD7` | schema3:1230 | ATmega2560 Port D7 |

### J1: 2×3 ICSP Header (`ICSP1`)
| Pin Number | Position | Net Name | Schematic Record | Function |
|---|---|---|---|---|
| `1` | Lower-Left | `PB3` | schema1:510 | ATmega2560 MISO |
| `2` | Upper-Left | `+5V` | schema1:513 | +5V Target Supply |
| `3` | Lower-Mid | `PB1` | schema1:516 | ATmega2560 SCK |
| `4` | Upper-Mid | `PB2` | schema1:519 | ATmega2560 MOSI |
| `5` | Lower-Right | `NRESET` | schema1:522 | MCU Active-Low Reset |
| `6` | Upper-Right | `GND` | schema1:525 | Ground Reference |

---

## 4. Multi-View AR Alignment & Traceability

All component coordinates in the digital twin and calibration landmarks use metric units (metres), a right-handed Y-up orientation, and origin centered on the PCB substrate. This structure ensures full compatibility with Tokito's AR alignment pipeline and automated node audits.
