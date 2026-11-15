# tc-monitor

Four-channel thermocouple monitor for hand reflow with hot air and a preheater:
live temperature and graph on a 2.0" colour TFT, phase hints (preheat, soak, hot air,
liquid, cooling), peak-limit and ramp alarms, CSV over USB.

| directory | contents |
|---|---|
| `docs/design.md` | requirements, parts, RP2040 pin map, layout rules |
| `hardware/` | KiCad 10 project: schematic (5 sheets, ERC without errors); `libs/` holds the PCC-SMP footprint and the crystal symbol |
| `firmware/` | MicroPython: `reflow.py` (phase logic), `config.py`, `main.py` (still for the prototype's MAX31856/SH1106, to be ported) |
| `host/tc_plot.py` | live plot over USB, saves every run as CSV |
| `tests/` | pytest for the phase logic |

```sh
python -m pytest -q tests
uv run --with pyserial --with pyqtgraph --with PySide6 host/tc_plot.py
```
