# tc-monitor: design

A four-channel thermocouple monitor for hand reflow (hot air plus bottom preheater).
It shows the package temperature, says which phase you are in (preheat, soak, hot air,
liquid, cooling) and warns before the peak limit. Heaters stay manual. It is a pure
thermocouple monitor: R, C, L and diodes are measured with an external LCR tweezers
meter, and shorts are found with the bench supply and IR (see below).

Status: design, nothing ordered yet (2026-11-10). The schematic is drawn by hand; see
[Plan](#plan). The accuracy figures below are design targets, not measurements.

## Requirements

- 4 type-K thermocouple inputs on miniature (mini-K) sockets, ±1–2 °C at soldering
  temperatures, open-thermocouple detection, about 5 readings/s per channel.
- 2.0" 240×320 colour TFT (ST7789, SPI), used in landscape: a live 8-minute graph with one
  colour per channel.
- USB-C: power and data (CSV stream to the PC viewer in `host/`).
- Speaker with adjustable volume (quiet tones or voice prompts, mute), three buttons, status LED.
- No built-in SMD tester: a ready-made LCR tweezers meter (chosen 2026-11-11, about
  100 zł: R 10 mΩ–10 MΩ, C 1 pF–22 mF, L 1 µH–10 H, own calibration) covers R, C, L and
  diodes.
- No built-in short finder (dropped 2026-11-11). Shorts are found with the programmable
  bench supply and IR: inject current into the shorted rail with the voltage limit at a
  few hundred mV (below the junction thresholds of the parts on the rail, never above the
  rail's own voltage) and the current limit at about 1 A, then look for the hot spot with a thermal camera, a film of IPA (dries first over the short) or rosin
  (melts first). It works through solder mask and also finds a short under a BGA.
- UART on a JST-SH 3-pin (Raspberry Pi debug pinout, for the Debug Probe's UART port); no
  other expansion header. No SSR output: the preheater (YIHUA 853A)
  has its own K-type PID controller, so it stays on its own knob and nothing touches mains.
- Hand-assembled with lead-free paste on a 4-layer JLCPCB board: the board doubles as lead-free practice
  (QFN-56 and TQFN-16 with exposed pads, VSSOP-10, SOT-563, 0402 passives).

## Blocks

```
USB-C ── fuse ── +5V ── TLV62569 ─ +3V3 ──┬── RP2040 + W25Q128 + 12 MHz
  │                                        ├── ferrite ── +3V3A ── 2× ADS1118 ── 4× mini-K
  └── USBLC6 ── D+/D− ── RP2040 USB        ├── TFT header (SPI0)
                                           └── buttons, LED, expansion
                    +5V ── MAX98357A (I2S from RP2040) ── 8 Ω speaker
```

## Parts

Full list with storage codes and LCSC links: [bom.md](bom.md). Most parts come from
storage; LCSC supplies the ADS1118s, the 10 MΩ resistors, the amplifier and the speaker.

| Ref | Part | Notes |
|---|---|---|
| J1 | USB-C 16P, HRO TYPE-C-31-M-12 | from storage, the same part as on MSPC v3 |
| F1 | PTC 1 A, 0603 | |
| U1 | USBLC6-2P6 | ESD on D+/D− |
| U2 | TLV62569DRLR buck (SOT-563), 2.2 µH | as on gpu_card, but feedback 100k/22k (3.33 V); 10 µF 0603 16 V in (0402 keeps only about 3 µF at 5 V), 2× 10 µF 0402 out. Buck rather than LDO: less heat near the cold junction |
| U3 | RP2040 (QFN-56) | |
| U4 | W25Q128JVSIM (SOIC-8 208 mil) | 16 MB QSPI flash |
| Y1 | 12 MHz ECS-120-8-36-CKM-TR3 (2.5×2.0, 8 pF) | 12 pF C0G load caps (8 pF crystal plus about 3 pF stray; 14 pF would load it to about 10 pF), 1 kΩ series on XOUT |
| U5, U6 | ADS1118IDGSR (VSSOP-10) | two differential channels each, internal temperature sensor for the cold junction |
| J2–J5 | miniature type-K PCB socket PCC-SMP-CV-K (horizontal, Omega PCC-SMP clone) | plug blades 7.9 mm apart; PCB legs from the Omega drawing: 4 holes ø1.77 mm, contact legs 13.7 mm apart, bracket legs 15.7 mm apart, rows 13.5 mm apart (check on a delivered socket) |
| J6 | JST SH 8-pin, BM08B-SRSS-TB vertical | TFT cable, pin order of the ARD-TFT200-8P module, MP to GND. Ready-made SH cable (SH crimps cannot be done by hand); the far end is soldered to the module pads |
| R | 105 Ω 0402 + JP1 solder jumper | backlight: GP11 through 105 Ω to BL, JP1 ties BL to +3V3 instead |
| U7 | MAX98357AETE+T (TQFN-16 3×3), I2S class-D amplifier | from +5V, gain 3 dB (100 kΩ GAIN to VDD), SD_MODE on a GPIO to shut it down between sounds |
| LS1 | 8 Ω 0.5 W speaker, 15×6×2.5 mm, spring contacts | pressed onto two bare ENIG pads by the enclosure (not soldered), sound outlet facing away from the PCB, behind a grille; footprint `tc-monitor:Speaker_INGHAi_GSPK1506025TN_15x6mm_SpringContacts` |
| SW1–SW3 | 6×6 THT tact switch | user buttons: mute/acknowledge alarm, start/stop run, menu (alloy, peak limit, volume) |
| SW4 | TS-1088-AR02016, 4×3 mm SMD tact switch (as on MSPC v3) | BOOTSEL: hold while plugging in USB (QSPI_SS through R5 1k to GND). No RESET button: reset via SWD (J8) or USB re-plug; a blank flash boots to USB by itself, later `machine.bootloader()` |
| D1, D2 | LED 0402 | status (GP25), power |
| J7 | JST SH 3-pin, BM03B-SRSS-TB vertical | UART, Raspberry Pi debug connector pinout (target side): 1 RX (GP1), 2 GND, 3 TX (GP0); MP to GND. Straight SH cable to the Debug Probe "U" port |
| J8 | JST SH 3-pin, BM03B-SRSS-TB vertical | SWD, Raspberry Pi debug connector pinout: 1 SWCLK, 2 GND, 3 SWDIO; MP to GND. Takes the Raspberry Pi Debug Probe's JST-SH cable directly |

## Thermocouple input (per channel)

From the ADS1118 datasheet, Figure 50, with larger bias resistors:

- RPU 10 MΩ from AIN+ to +3V3A, RPD 10 MΩ from AIN− to GND. They set the
  common mode and pull an open thermocouple to full scale. TI's 1 MΩ gives
  1.65 µA through the thermocouple; with a thin probe (about 130 Ω loop) that is
  0.2 mV, about 5 °C. 10 MΩ brings it to about 0.5 °C, and an open input still reads
  about 113 mV against the 710 kΩ differential input impedance (normal maximum about
  55 mV), so open detection still works.
- RDIFF 536 Ω in each lead (TI uses 499 Ω and asks for below 1 kΩ; 536 Ω is in
  storage), CDIFF 1 µF across the inputs, CCM 100 nF from each input to GND
  (CDIFF ≥ 10× CCM). Corner about 150 Hz.
- FSR ±0.256 V, single-shot conversions, 128 SPS. The internal temperature sensor
  (TS_MODE=1) is read between thermocouple conversions and gives the cold junction.

ADS1118 pins (VSSOP-10): 1 SCLK, 2 CS, 3 GND, 4 AIN0, 5 AIN1, 6 AIN2, 7 AIN3,
8 VDD, 9 DOUT/DRDY, 10 DIN. SPI mode 1 (CPOL=0, CPHA=1). DOUT is high-impedance
while CS is high, so both converters share SCLK/DIN/DOUT and have separate CS.

With the IR preheater (YIHUA 853A, ceramic IR) an exposed bead absorbs IR directly and
reads high. Tape the bead to the package with Kapton and cover it with a small piece of
aluminium tape.

## Display

ARD-TFT200-8P: 2.0" TFT, 240×320, ST7789V, 4-wire SPI (write only), module
58 × 37 mm with a metal frame. 8-pin header, duplicated on both edges: 1 GND, 2 VCC,
3 SCL, 4 SDA, 5 RES, 6 DC, 7 CS, 8 BL. Supply 3.3–5 V, logic 3.3 V (module spec,
confirmed 2026-11-14). It runs from +3V3: within the spec, and no 5 V pull-up on the module
can reach the RP2040 pins. +5V was considered and dropped (it would need a long route across
the button and UART lines). If the module has an LDO bypass jumper next to its regulator
(often marked J1), bridge it so the panel gets the full 3.3 V.

- Backlight: GP11 → 105 Ω → BL, PWM for brightness. On modules where BL drives a
  transistor this gives full control; if BL feeds the LEDs directly, the backlight is
  only dim, nothing is overloaded. Then close JP1 (BL to +3V3, no dimming). Measure the
  BL current on the module before the PCB order.
- It mounts in the enclosure on a short cable (under 15 cm) to J6. SPI0 starts at
  31.25 MHz; 62.5 MHz only if the cable allows it.
- Any ST7789 240×320 module with the same eight signals fits, including the 2.4" ones.

## RP2040 pins

Assigned on 2026-11-12 by the side of U3 that faces each block on the board (U3 rotated
−90°: GP0–GP11 on the top edge, GP12–GP17 on the left edge toward the island,
GP18–GP29 on the bottom edge toward the amplifier and buttons; the I2S order SD, DIN,
BCLK, LRCLK matches the MAX98357A pins seen from above, so they route on F.Cu without vias). Any GPIO can do PWM; SPI0, SPI1 and
UART0 use their hardware pins; I2S needs LRCLK = BCLK + 1 in MicroPython.

| GPIO | Net (global label) | Function |
|---|---|---|
| GP0, GP1 | UART_TX, UART_RX | UART0 TX/RX on J7 (pins 3 and 1) |
| GP2–GP5 | — | not connected |
| GP6 | TFT_SCK | SPI0 SCK → TFT SCL |
| GP7 | TFT_MOSI | SPI0 TX → TFT SDA |
| GP8 | TFT_RES | TFT RES |
| GP9 | TFT_DC | TFT DC |
| GP10 | TFT_CS | TFT CS |
| GP11 | TFT_BL | TFT backlight (PWM) through R30 |
| GP12 | ADC_MISO | SPI1 RX ← ADS1118 DOUT/DRDY |
| GP13 | ADC1_CS | ADS1118 #1 CS (channels 1, 2) |
| GP14 | ADC_SCK | SPI1 SCK → ADS1118 SCLK |
| GP15 | ADC_MOSI | SPI1 TX → ADS1118 DIN |
| GP16 | ADC2_CS | ADS1118 #2 CS (channels 3, 4) |
| GP17 | — | not connected |
| GP18 | AMP_SD | MAX98357A SD_MODE (low = shutdown, high = left channel) |
| GP19 | I2S_DIN | I2S DIN → MAX98357A |
| GP20 | I2S_BCLK | I2S BCLK → MAX98357A |
| GP21 | I2S_LRCLK | I2S LRCLK → MAX98357A (BCLK + 1) |
| GP22–GP24 | BTN1–BTN3 | buttons 1–3 (to GND, internal pull-ups) |
| GP25 | LED_STATUS | status LED |
| GP26 | — | not connected |
| GP27–GP29 | — | not connected |

J6 is turned 180° on the board, so its pins 8…1 run left to right and line up with
GP11…GP6 without crossings.

## Sound

A buzzer is loud and harsh; a speaker behind an I2S amplifier can play soft tones at
any volume, or short voice prompts ("soak OK, hot air"), which help while your eyes
are on the board. The MAX98357A takes I2S straight from the RP2040 (MicroPython
`machine.I2S`), needs no codec setup and only a supply capacitor.

- Supply from +5V, not +3V3, so speaker current does not modulate the rail that feeds
  the converters. 10 µF (0603, 16 V) + 100 nF at the amplifier.
- The speaker is rated 0.5 W; at 5 V into 8 Ω the amplifier could deliver about
  1.4 W. Lowest gain (3 dB) and a firmware cap on the digital level (about −8 dBFS)
  keep it under the rating.
- SD_MODE is driven low between sounds, so the amplifier draws no current and makes
  no idle hiss.
- Voice prompts: 16 kHz mono samples in flash (the 16 MB W25Q128 holds plenty).

## Layout

### Stackup: JLCPCB 4 layers, JLC04161H-3313, 1.6 mm, ENIG

The same stackup and design rules as the MSPC mainboard (copied into
`hardware/tc-monitor.kicad_pro` and the board file). Check the thicknesses against the
JLCPCB order page; the impedance figures come from their calculator, ±10 %.

| Layer | Copper | Use |
|---|---|---|
| L1 F.Cu | 1 oz | parts, signals, short power runs |
| prepreg 3313 | 0.0994 mm, εr 4.1 | |
| L2 In1.Cu | 0.5 oz | GND, solid, never routed |
| core | 1.265 mm, εr 4.6 | |
| L3 In2.Cu | 0.5 oz | GND, solid (reference for L4) |
| prepreg 3313 | 0.0994 mm, εr 4.1 | |
| L4 B.Cu | 1 oz | signals, power, GND pour |

- Both outer layers sit 0.1 mm above a solid GND, so every trace has its return path
  right under it. Power currents are small (well under 0.5 A), so +5V, +3V3 and +3V3A
  are tracks or local pours on L1/L4; no power plane.
- Net classes (from the mainboard): USB_90R 0.16/0.15 mm (D+/D−, L1 over L2),
  Signal_50R 0.16 mm (QSPI flash, TFT SPI), XOSC, Power_1A (+5V, buck SW node),
  Power_Low (+3V3, +3V3A), GND. Minimum track/space 0.1 mm, vias 0.5/0.3 mm.
- ENIG: flat pads for the QFN and VSSOP, wets well with lead-free paste, and gold for the
  speaker's spring contacts.

### Analog and digital

One GND for everything; the ground planes are not split. A split plane forces return
currents of any signal crossing the gap to take a detour, which is worse than the noise it
was meant to stop (the ADS1118 also has a single GND pin). The separation comes from
placement:

- Analog zone (the island, left): sockets, input filters, both ADS1118 and their
  decoupling. Nothing digital is routed through it, and no island trace leaves it except
  through the neck.
- Only five SPI lines (ADC_SCK, ADC_MOSI, ADC_MISO, ADC1_CS, ADC2_CS) and +3V3A cross into
  the island, through the neck, on L1 over unbroken GND on L2/L3. FB1 sits at the neck on
  the digital side.
- Noisy parts as far from the island as the board allows: buck switch node and L1, the
  class-D amplifier and its speaker traces, USB, RP2040 and crystal.

### Board and floorplan (draft)

The board file `hardware/tc-monitor.kicad_pcb` has the outline, the slots, the zones and
a floorplan sketch on User.Comments. Parts come in with Update PCB from Schematic (F8).

- 68 × 77.9 mm (100 × 80 → 78 × 74 → 68 × 77.9 on 2026-11-12, the right edge trimmed to
  SW3/J1). The four PCC-SMP sockets sit along the left edge at 19.4 mm pitch (y 7.7, 27.2,
  46.6, 66.0), plugs entering from the edge; front
  face 18.3 mm from the contact row. The plugs set the size: Omega's SMPW drawing
  probably gives 16.8 mm as the plug width, so four side by side need about 70 mm. Check
  that two delivered plugs fit next to each other at 19.4 mm before the order. At this
  pitch the 19 mm socket courtyards no longer overlap.
- Isothermal island: the left 33 mm. Two 1.5 mm routed slots (x 33.1–34.6) separate it from
  the rest, leaving a 13 mm neck in the middle (y 30.4–43.4) and two ~3 mm bridges at the
  board edges. The bridges are copper keepouts (FR4 only), so heat crosses only through the
  neck. On the island: copper on all four layers (GND pours on L1/L4 are in the file),
  stitched with GND vias on a 3 mm grid (about 200 on the island), so the sockets and both
  ADS1118 stay at one temperature.
- Digital side, right to left: USB-C on the right edge with ESD and fuse; buck and L1
  bottom right; RP2040 with flash and crystal in the middle; TFT header on the top edge; BOOTSEL button and SWD near the RP2040; amplifier and speaker in the lower middle (away from the display above the top edge); user buttons and
  LEDs along the bottom edge (final position follows the enclosure); J7 (UART) top right.
- Mounting: three M3 holes, H1/H2 on the island next to the slot (x 29.2 y 2.6, x 27.7
  y 72.2) and H3 top right (x 62.3, y 2.4). The lower right corner with SW1–SW3 has no
  screw: the enclosure needs a post under the buttons so pressing them does not bend the
  board. J1's face sits 0.75 mm behind the right edge.
- Short, symmetric input traces from each socket to its RC filter and converter;
  CDIFF right at the converter pins.
- Analog supply +3V3A through FB1 with 1 µF + 100 nF at each ADS1118.
- Amplifier and speaker: short output traces; its +5V and ground return go straight to
  the USB side, not toward the island.
- QFN exposed pads: thermal vias 0.3/0.5 mm are part of the footprints in the project library
  (`*_ThermalVias_D0.3`). RP2040: 9 (five in the paste-free cross, four corners as on MSPC);
  the EP is its only GND pin. MAX98357A: 4.
- Silkscreen (JLCPCB): references only, 1.0 mm high, 0.85 mm glyph width, 0.17 mm stroke,
  placed off pads, holes, slots and other parts' outlines; values on Fab; no labels on H1–H3.
  DRC silk checks are on (warning).
- Speaker LS1: spring contacts (they stick out 0.9 mm below the body) press on two
  2.0 × 1.5 mm pads with no paste, so the ENIG gold stays flat. Nothing else inside its
  courtyard. The enclosure holds it down with the sound outlet facing the grille.

## Firmware

MicroPython runs on a bare RP2040 with W25Q-series flash (the generic RP2040
build). `firmware/reflow.py` (phases, hints, alarms) carries over from the prototype
unchanged; drivers for ADS1118 and ST7789 replace the MAX31856 and SH1106 ones.
A full 320×240 frame at 16 bits is 150 KB, too much for the MicroPython heap, so the
screen is drawn in parts: the graph in a 4-bit framebuffer with a 16-colour palette
(about 24 KB for 320×150) converted line by line to RGB565, and the text fields in small
separate buffers.
The CSV stream gets four temperature columns. Sound goes through `machine.I2S`
with a volume setting (including mute) kept in flash.

Reflow features:

- Time forecast: from the current slope, the time to the next threshold (soak, liquidus,
  peak limit), for example "217 °C in 40 s", so the hot air can come off in time.
- Alloy profiles: SAC305 (217 °C), Sn63Pb37 (183 °C), Sn42Bi58 (138 °C), each a separate
  `reflow.Run` configuration, with soak and peak limits taken from the paste's datasheet.
- Channel difference: shows the spread between connected probes (top against bottom of
  the package, centre against board edge) and warns above a configurable threshold,
  set from measured runs.
- Previous run: runs are saved in flash (about 19 KB for 8 minutes of 4 channels at 5 Hz)
  and the last one is drawn in dimmed colours behind the live graph.

Host feature: `host/tc_overlay.py` renders the graph and temperature from a CSV log as a
video overlay. The tone at the start of a run is the sync mark against the recorded audio.

## Open questions

- Socket footprint: PCC-SMP-CV-K chosen (horizontal, plug through the enclosure wall at
  the board edge). Footprint drawn from the Omega PCC-SMP drawing:
  `hardware/libs/footprints.pretty/Thermocouple_PCC-SMP_Horizontal.kicad_mod`
  (4 holes ø1.77 mm: contact legs 13.7 mm apart, bracket legs 15.7 mm apart, rows
  13.5 mm apart; front face 18.3 mm from the contact row, scaled from the drawing).
  Confirm with calipers on a delivered socket before the PCB order.
- Whether channel 1 is always the package (phase logic) and channels 2–4 are
  display-only, or the active channel is chosen with a button. Firmware only; it does
  not block the schematic.

## Plan

1. Before drawing: PCC-SMP-CV-K sockets ordered (AliExpress); measure one when it
   arrives.
2. Schematic in KiCad in `hardware/` (the video shows the block diagram and the finished
   schematic, not the drawing). Done 2026-11-11, five sheets:
   - root;
   - power (TLV62569, ferrite to +3V3A, power flags);
   - RP2040/USB/flash: the block from mspc `fpga_extension/jtag_programmer`, GPIOs
     relabelled to the nets above, plus RUN pull-up and a small BOOTSEL button (SW4);
   - thermocouple inputs: four channels as in the section above, 2× ADS1118;
   - display/sound/buttons.

   Signals between sheets are global labels named as in the pin map. ERC: one expected
   error, both ADS1118 DOUT pins on ADC_MISO (output to output; high-Z while CS is high),
   and one expected warning, the MAX98357A exposed pad's "unspecified" pin type on GND. The four
   lib-symbol-mismatch warnings come from the mspc copy. Every part has a footprint
   (LS1 added 2026-11-11 from the datasheet pad area).
3. Footprints: done in `hardware/libs/footprints.pretty` (PCC-SMP socket, speaker); the
   rest are KiCad library footprints.
4. Layout: placed and routed, DRC clean with schematic parity (2026-11-14). Review fixes
   on 2026-11-14: C1 and C38 (10 µF on +5V) moved to 0603 16 V, U2 GND pin track widened
   to 0.3 mm, island GND stitching on a 3 mm grid, crystal caps 14 → 12 pF.
   Before the order (blocking): measure a delivered PCC-SMP-CV-K socket against the
   footprint (leg holes and spacing, front face to contact row; pin 1 = +, the alumel −
   contact is magnetic), check that two plugs fit side by side at 19.4 mm, and measure the
   TFT module's BL current (VCC stays on +3V3; bridge the module's LDO bypass jumper if it has
   one). Then order from JLCPCB
   (4 layers, ENIG) with a stencil.
   Order the LCSC parts separately (under €150, VAT at checkout); order the TFT at the
   same time (sockets and thermocouples are ordered already).
5. Assembly with SAC305, in stages, checking each before the next: power rails, then
   RP2040, flash and USB, then converters, then sound and TFT.
6. Firmware: new pin map in `config.py`, ADS1118 driver with NIST type-K linearization
   and cold-junction compensation, ST7789 driver, I2S sound, reflow screen; then alloy
   profiles, time forecast, channel difference and previous run (with tests in `tests/`).
7. `host/tc_plot.py` for four channels, then `host/tc_overlay.py` for the video.
8. Check against references: thermocouples against a known temperature. Replace the
   targets in this document with measured figures.
9. Enclosure in `enclosure/`: TFT window, speaker pocket that presses LS1 onto its pads
   (body 2.5 mm, contacts 0.9 mm below it when free; measure the working stroke on a real
   part) with a grille over the outlet,
   access to the sockets.
10. Video materials in ScriptForge.

The hardware feature set is closed for this revision: no DC voltmeter, no SSR, no
built-in SMD tester, no short finder.

Later ideas, not committed; none of them needs a change to this board (spare GPIOs have no
connector since 2026-11-12, so any wired add-on would need a board revision):

- Suggested YIHUA 853A setting, learned from earlier runs.
- MSL floor-life counter, with the time taken from the PC over USB (no RTC on the board).
- Top-side temperature: an IR camera when needed (the pyrometer port was dropped on
  2026-11-11).
- Separate module: current-limited supply for the board under test.
