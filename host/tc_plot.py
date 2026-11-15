#!/usr/bin/env python3
"""Live plot of the thermocouple monitor over USB; every run is saved as CSV.

    uv run --with pyserial --with pyqtgraph --with PySide6 host/tc_plot.py
"""
import argparse
import csv
import sys
import time
from pathlib import Path

import pyqtgraph as pg
import serial
from serial.tools import list_ports
from pyqtgraph.Qt import QtCore, QtWidgets

FIELDS = ["t_ms", "temp_c", "cj_c", "fault", "state", "tal_s", "ramp_cps",
          "phase", "soak_s", "msg"]


def find_port():
    for p in list_ports.comports():
        if p.vid == 0x2E8A:          # Raspberry Pi (Pico, MicroPython)
            return p.device
    sys.exit("No Pico found; give --port")


class Plot(QtWidgets.QWidget):
    def __init__(self, port, out_dir, peak, liquidus, window_s):
        super().__init__()
        self.ser = serial.Serial(port, 115200, timeout=0)
        self.out_dir = Path(out_dir).expanduser()
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.window = window_s
        self.buf = b""
        self.t, self.v = [], []
        self.log = None
        self.state = "IDLE"

        self.setWindowTitle(f"TC monitor - {port}")
        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("--")
        self.label.setStyleSheet("font-size: 28px; font-weight: 600;")
        layout.addWidget(self.label)
        self.pw = pg.PlotWidget()
        self.pw.showGrid(x=True, y=True, alpha=0.3)
        self.pw.setLabel("bottom", "czas", "s")
        self.pw.setLabel("left", "temperatura", "°C")
        self.pw.addItem(pg.InfiniteLine(liquidus, angle=0,
                                        pen=pg.mkPen("#e90", style=QtCore.Qt.DashLine)))
        self.peak_line = pg.InfiniteLine(peak, angle=0,
                                         pen=pg.mkPen("#e33", style=QtCore.Qt.DashLine))
        self.pw.addItem(self.peak_line)
        self.curve = self.pw.plot(pen=pg.mkPen("w", width=2))
        layout.addWidget(self.pw)
        self.peak = peak

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.poll)
        timer.start(100)

    def start_log(self):
        name = self.out_dir / time.strftime("tc_%Y%m%d_%H%M%S.csv")
        self.log_file = open(name, "w", newline="")
        self.log = csv.writer(self.log_file)
        self.log.writerow(FIELDS)
        self.t, self.v = [], []
        print("logging to", name)

    def stop_log(self):
        if self.log:
            self.log_file.close()
            self.log = None

    def poll(self):
        self.buf += self.ser.read(4096)
        *lines, self.buf = self.buf.split(b"\n")
        for raw in lines:
            row = raw.decode(errors="replace").strip().split(",")
            if len(row) != len(FIELDS) or not row[0].isdigit():
                continue
            t_ms, temp, cj, fault, state, tal, ramp, phase, soak, msg = row
            if state == "RUN" and self.state != "RUN":
                self.start_log()
            if self.log:
                self.log.writerow(row)
            if self.state == "RUN" and state != "RUN":
                self.stop_log()
            self.state = state
            if temp:
                self.t.append(int(t_ms) / 1000)
                self.v.append(float(temp))
            text = f"{temp or 'TC fault'} °C   {state}"
            if state == "RUN":
                text += (f"   {msg}   {float(ramp):+.1f} °C/s   soak {float(soak):.0f} s"
                         f"   TAL {float(tal):.0f} s")
            self.label.setText(text)
            hot = temp and float(temp) >= self.peak
            self.label.setStyleSheet("font-size: 28px; font-weight: 600;"
                                     + ("background: #a00;" if hot else ""))
        if len(self.t) > 20000:
            del self.t[:-20000], self.v[:-20000]
        if self.t:
            self.curve.setData(self.t, self.v)
            self.pw.setXRange(max(self.t[0], self.t[-1] - self.window), self.t[-1] + 2,
                              padding=0)

    def closeEvent(self, ev):
        self.stop_log()
        super().closeEvent(ev)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port")
    ap.add_argument("--out", default="~/tc_logs")
    ap.add_argument("--peak", type=float, default=245.0)
    ap.add_argument("--liquidus", type=float, default=217.0)
    ap.add_argument("--window", type=float, default=480.0, help="seconds shown")
    args = ap.parse_args()
    app = pg.mkQApp("TC monitor")
    w = Plot(args.port or find_port(), args.out, args.peak, args.liquidus, args.window)
    w.resize(1100, 650)
    w.show()
    app.exec()


if __name__ == "__main__":
    main()
