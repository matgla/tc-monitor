# BOM: one board

Storage stock from the ESU inventory cache (synced 2026-11-10); LCSC stock and prices
read 2026-11-11. Counts match the schematic draft in `hardware/` (BOM export 2026-11-11);
RP2040 decoupling follows the minimal design: one 100 nF per IOVDD, USB_VDD and ADC_AVDD
pin (8), one per DVDD pin (2), 1 µF on VREG_IN and on VREG_VOUT, plus 100 nF on the flash
(the extra DVDD cap, the VBUS cap and the TFT-header cap were removed on 2026-11-12). Every storage line covers the quantity needed. "Order" includes spares
for rework practice.

## Shopping list

### Now (needed for footprints, enclosure and testing)

| Item | Qty | Where | Notes |
|---|---|---|---|
| Miniature type-K PCB socket, horizontal, PCC-SMP-CV-K (Omega PCC-SMP clone, K-alloy contacts) | 5 (4 + 1 spare) | AliExpress, 46.49 zł per 5 | plug enters parallel to the board, through the enclosure wall at the board edge. Footprint from the PCC-SMP drawing (4 holes ø1.77 mm: contact legs 13.7 mm apart, bracket legs 15.7 mm; the plug blades are 7.9 mm apart); measure one on arrival before the PCB order. Fallback: RS PRO 381-7564 / Labfacility IM-K-PCB (different footprint) |
| TFT 2.0" 240×320 ST7789V, SPI 8-pin, ARD-TFT200-8P | 1 | Allegro | 58 × 37 mm. On arrival, measure the BL pin current and the mounting holes. Any ST7789 240×320 module with the same 8 pins fits |
| Type-K thermocouple, thin wire, exposed junction, miniature plug | 2 (board + package; channels 3–4 later) | Allegro, BGA-station type: PFA, 0.25 mm wire, 0.8 mm bead, 1 m, ±2.5 °C / 0.75 %, yellow ANSI mini plug | insulation rated 300 °C: keep the lead out of the hot-air jet and wrap the first 2–3 cm at the bead in Kapton. Mini plug fits the IEC socket (same pins, only colour differs). Omega 5SRTC-GG-K-30-36 (glass fibre) dropped at about $100 per 5 |
| LCR tweezers meter (R 10 mΩ–10 MΩ, C 1 pF–22 mF, L 1 µH–10 H, own calibration) | 1 | about 100 zł | external tool for R, C, L and diodes; not part of the board |

### With the board (after the layout)

Separate LCSC order (it does not ship with JLCPCB). Keep it under €150: LCSC then
charges the 23 % Polish VAT at checkout (IOSS); check the checkout for any EU small-parcel
duty. Above €150 the courier adds duty and a clearance fee. The same parts from DigiKey PL
cost about 210 zł net (ADS1118 21.30 zł each) (checked 2026-11-11).

| Ref | Part | LCSC | Qty | Order | Unit price | Line |
|---|---|---|---|---|---|---|
| U5, U6 | ADS1118IDGSR, VSSOP-10 | [C55347](https://www.lcsc.com/product-detail/C55347.html) | 2 | 4 | $1.73 | $6.93 |
| R | 10 MΩ 1 % 0402, 0402WGF1005TCE (thermocouple bias) | [C26082](https://www.lcsc.com/product-detail/C26082.html) | 8 | 100 (min.) | $0.0012 | $0.12 |
| U7 | MAX98357AETE+T, I2S amplifier, TQFN-16 3×3 | [C910544](https://www.lcsc.com/product-detail/C910544.html) | 1 | 3 | $1.32 | $3.96 |
| LS1 | INGHAi GSPK1506025TN-8R0.5W-1, 8 Ω 0.5 W, 15×6×2.5 mm, spring contacts (pressure mount) | [C46961944](https://www.lcsc.com/product-detail/C46961944.html) | 1 | 2 | $0.80 | $1.61 |
| J6 | JST SH 8-pin header, vertical, BM08B-SRSS-TB(LF)(SN) (TFT) | [C160394](https://www.lcsc.com/product-detail/C160394.html) | 1 | 2 | $0.44 | $0.88 |
| J7, J8 | JST SH 3-pin header, vertical, BM03B-SRSS-TB(LF)(SN) (UART and SWD, Raspberry Pi debug connector) | [C160389](https://www.lcsc.com/product-detail/C160389.html) | 2 | 5 (min.) | $0.28 | $1.39 |

LCSC total about $14.90 plus shipping.

| Item | Qty | Where |
|---|---|---|
| PCB, 4 layers JLC04161H-3313, 1.6 mm, 68 × 77.9 mm, ENIG, with stencil | 5 | [JLCPCB](https://jlcpcb.com) |

### Consumables not tracked in storage (check the workshop)

Lead-free paste SAC305, flux, Kapton tape, aluminium tape (for the thermocouple beads
under IR).

## Full BOM

**storage** = take from storage (code, stock); **ORDER** = in the shopping list above.

| Ref | Part | Qty | Source | Code | Stock |
|---|---|---|---|---|---|
| U1 | USBLC6-2P6, SOT-666 | 1 | storage | `USBLC6-2P6` | 9 |
| U2 | TLV62569DRLR buck, SOT-563 | 1 | storage | `TLV62569DRLR` | 9 |
| U3 | RP2040, QFN-56 | 1 | storage | `RP2040` | 12 |
| U4 | W25Q128JVSIM, SOIC-8 208 mil | 1 | storage | `W25Q128JVSIM` | 10 |
| U5, U6 | ADS1118IDGSR, VSSOP-10 | 2 | **ORDER** LCSC | C55347 | |
| U7 | MAX98357AETE+T, TQFN-16 | 1 | **ORDER** LCSC | C910544 | |
| D1 | LED 0402 yellow-green (status) | 1 | storage | `SZYY0402YG` | 50 |
| D2 | LED 0402 red (power) | 1 | storage | `F.0402.00003` | 100 |
| L1 | 2.2 µH LQM21PN2R2NGCD, 0805 | 1 | storage | `LQM21PN2R2NGCD` | 19 |
| FB1 | ferrite BLM21PG600SN1D, 0805 | 1 | storage | `BLM21PG600SN1D` | 28 |
| F1 | PTC 1 A BSMD0603-SS1.0 | 1 | storage | `BSMD0603-SS1.0` | 20 |
| Y1 | 12 MHz ECS-120-8-36-CKM-TR3, 2.5×2.0 | 1 | storage | `ECS-120-8-36-CKM-TR3` | 29 |
| LS1 | speaker INGHAi GSPK1506025TN, 8 Ω 0.5 W, spring contacts | 1 | **ORDER** LCSC | C46961944 | |
| SW1–SW3 | tact switch 6×6 THT (user buttons) | 3 | storage | `TCTSW66` | 41 |
| SW4 | tactile switch 4×3 mm SMD, TS-1088-AR02016 (BOOTSEL, as on MSPC v3) | 1 | storage | `TS-1088-AR02016` | 20 |
| J1 | USB-C 16-pin, HRO TYPE-C-31-M-12 (as on MSPC v3) | 1 | storage | `USB-C16PINH` | 10 |
| J2–J5 | miniature type-K PCB socket PCC-SMP-CV-K (horizontal) | 4 | **ORDER** AliExpress | | |
| J8 | JST SH 3-pin BM03B-SRSS-TB (SWD) | 1 | **ORDER** LCSC | C160389 | |
| J6 | JST SH 8-pin header BM08B-SRSS-TB (TFT) | 1 | **ORDER** LCSC | C160394 | |
| J7 | JST SH 3-pin BM03B-SRSS-TB (UART) | 1 | **ORDER** LCSC | C160389 | |
| — | TFT module 2.0" ST7789V, ARD-TFT200-8P | 1 | **ORDER** | | |
| — | TFT cable: ready-made JST SH 1.0 mm 8-pin cable (pre-crimped, about 15 cm), one end cut off and soldered straight to the module pads | 1 | **ORDER** AliExpress | | |
| R | 105 Ω 0402 (TFT backlight series) | 1 | storage | `RC0402FR-07105RL` | 99 |
| JP1 | solder jumper (BL to +3V3), PCB only | — | — | | |
| R | 5.1 kΩ 0402 (USB CC) | 2 | storage | `RC0402FR-075K1L` | 48 |
| R | 27.4 Ω 0402 (USB D±) | 2 | storage | `RC0402FR-0727R4L` | 96 |
| R | 1 kΩ 0402 (XOUT, BOOTSEL, LEDs) | 4 | storage | `RC0402FR-071KL` | 95 |
| R | 10 kΩ 0402 (RUN, flash CS pull-ups) | 2 | storage | `RC0402FR-0710KL` | 83 |
| R | 100 kΩ 0402 (buck feedback top, amplifier GAIN to VDD) | 2 | storage | `RC0402FR-07100KL` | 97 |
| R | 22 kΩ 0402 (buck feedback bottom, 3.33 V) | 1 | storage | `RC0402FR-0722KL` | 98 |
| R | 536 Ω 0402 (thermocouple filter) | 8 | storage | `RC0402FR-07536RL` | 97 |
| R | 10 MΩ 0402 (thermocouple bias) | 8 | **ORDER** LCSC | C26082 | |
| C | 100 nF 0402 (decoupling, common-mode filter) | 22 | storage | `CC0402KRX7R6BB104` | 190 |
| C | 1 µF 0402 (VREG, differential filter, analog) | 8 | storage | `GRM155R61E105KA12D` | 118 |
| C | 10 µF 0402 (2× buck out) | 2 | storage | `CL05A106MP5NUNC` | 49 |
| C | 10 µF 0603 16 V X6S, CL10X106MO8NRNC (buck in, amplifier) | 2 | storage | `CC60310u` | 8 |
| C | 12 pF 0402 C0G (crystal) | 2 | storage | `UMK105CG120JVHF` | 23 |
| C | 6.8 pF 0402 (buck feed-forward, DNP footprint) | 0 (1) | storage | `CC4026p8` | 299 |
| — | M3 screws for mounting | 3 | storage | `M3x10P` | 14 |

Notes:

- 536 Ω instead of TI's 499 Ω only moves the thermocouple filter corner from 160 Hz to
  150 Hz.
- The buck feedback 100k/22k gives 3.33 V.
