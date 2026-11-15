# Reflow run tracking: phase, ramp, soak time, time above liquidus, hints and
# alarm events. The heaters stay manual; this only says what to do next.
# Plain Python, so it also runs (and is tested) on a PC.


def slope(points):
    """Least-squares slope in C/s of [(ms, temp), ...]."""
    n = len(points)
    if n < 3:
        return 0.0
    mt = sum(p[0] for p in points) / n
    mv = sum(p[1] for p in points) / n
    num = sum((p[0] - mt) * (p[1] - mv) for p in points)
    den = sum((p[0] - mt) ** 2 for p in points)
    return num / den * 1000 if den else 0.0


class Run:
    def __init__(self, cfg):
        self.c = cfg
        self.peak_i = 0
        self.last = None        # summary of the last finished run
        self.reset()

    @property
    def peak(self):
        return self.c.PEAK_LIMITS[self.peak_i]

    def next_peak(self):
        self.peak_i = (self.peak_i + 1) % len(self.c.PEAK_LIMITS)
        return self.peak

    def reset(self):
        # Keeps the peak limit and the last summary.
        self.state = "IDLE"
        self.t0 = None
        self.prev_ms = None
        self.max_t = None
        self.tal = 0.0
        self.ramp = 0.0
        self.max_ramp = 0.0
        self.recent = []
        self.fired = set()
        self.ramp_high = False
        self.cool_fast = False
        self.alarm = False
        self.muted = False
        self.phase = ""
        self.soak = 0.0
        self.early = False      # hot air went on before the soak was long enough

    def elapsed(self, ms):
        return 0.0 if self.t0 is None else (ms - self.t0) / 1000

    def summary(self):
        return {"peak": self.max_t, "tal": self.tal, "max_ramp": self.max_ramp,
                "soak": self.soak}

    def clear(self):
        self.reset()
        self.last = None

    def mute(self):
        self.muted = True

    def _once(self, name, cond, events):
        if cond and name not in self.fired:
            self.fired.add(name)
            events.append(name)

    def update(self, ms, temp):
        """Feed one sample. Returns events: start, soak_ok, soak_long, early,
        approach, tal_ok, ramp, cool_fast, done. self.alarm stays True while
        over the peak limit or past TAL_MAX."""
        c = self.c
        events = []
        self.recent.append((ms, temp))
        while self.recent[0][0] < ms - 3000:
            self.recent.pop(0)
        self.ramp = slope(self.recent)
        dt = 0.0 if self.prev_ms is None else (ms - self.prev_ms) / 1000
        self.prev_ms = ms

        if self.state == "IDLE":
            if temp >= c.START_T:
                self.state = "RUN"
                self.t0 = ms
                events.append("start")
        elif self.state == "DONE":
            if temp < c.START_T - 20:
                self.state = "IDLE"
        if self.state != "RUN":
            self.alarm = False
            return events

        self.max_t = temp if self.max_t is None else max(self.max_t, temp)
        reflowed = self.max_t >= c.LIQUIDUS
        if reflowed and temp < c.LIQUIDUS:
            phase = "COOL"
        elif temp >= c.LIQUIDUS:
            phase = "REFLOW"
        elif temp > c.SOAK_HI:
            phase = "RAMP"
        elif temp >= c.SOAK_LO:
            phase = "SOAK"
        else:
            phase = "PREHEAT"
        if phase == "RAMP" and self.phase != "RAMP" and self.soak < c.SOAK_MIN:
            self.early = True
            self._once("early", True, events)
        self.phase = phase

        if phase == "SOAK" and not reflowed:
            self.soak += dt
        if self.soak >= c.SOAK_MIN:
            self.early = False
        if temp >= c.LIQUIDUS:
            self.tal += dt
        if not reflowed:
            self.max_ramp = max(self.max_ramp, self.ramp)
        self._once("soak_ok", self.soak >= c.SOAK_MIN, events)
        self._once("soak_long", self.soak >= c.SOAK_MAX, events)
        self._once("approach", temp >= self.peak - c.APPROACH, events)
        self._once("tal_ok", self.tal >= c.TAL_MIN, events)
        if self.ramp > c.RAMP_MAX and not self.ramp_high:
            self.ramp_high = True
            events.append("ramp")
        elif self.ramp < c.RAMP_MAX - 0.5:
            self.ramp_high = False
        if phase == "COOL" and self.ramp < -c.COOL_MAX and not self.cool_fast:
            self.cool_fast = True
            events.append("cool_fast")
        elif self.ramp > -c.COOL_MAX + 0.5:
            self.cool_fast = False

        over = temp >= self.peak or self.tal >= c.TAL_MAX
        if not over:
            self.muted = False
        self.alarm = over and not self.muted

        if reflowed and temp < c.DONE_T:
            self.last = self.summary()
            self.reset()
            self.state = "DONE"
            events.append("done")
        elif not reflowed and temp < c.START_T - 10:
            self.reset()
        return events

    def message(self, temp):
        """What to do now: (text of at most 16 ASCII chars, is_warning), or None
        outside a run."""
        c = self.c
        if self.state != "RUN" or temp is None:
            return None
        if temp >= self.peak:
            return "LIMIT! ZDEJMIJ", True
        if self.tal >= c.TAL_MAX:
            return "TAL ZA DLUGI!", True
        if self.ramp_high:
            return "ZA SZYBKO!", True
        if self.cool_fast:
            return "CHLODZ WOLNIEJ", True
        p = self.phase
        if p == "PREHEAT":
            return "PREHEAT ->%d" % c.SOAK_LO, False
        if p == "SOAK":
            if self.soak >= c.SOAK_MAX:
                return "SOAK ZA DLUGI", True
            if self.soak >= c.SOAK_MIN:
                return "SOAK OK:HOT AIR", False
            return "SOAK %d/%ds" % (self.soak, c.SOAK_MIN), False
        if p == "RAMP":
            if self.early:
                return "ZA WCZESNIE!", True
            return "HOT AIR ->%d" % c.LIQUIDUS, False
        if p == "REFLOW":
            if temp >= self.peak - c.APPROACH:
                return "BLISKO LIMITU!", True
            if self.tal >= c.TAL_MIN:
                return "TAL OK: ZDEJMIJ", False
            return "LUT PLYNNY %ds" % self.tal, False
        return ("NIE RUSZAJ" if temp > c.SOLID_SAFE else "CHLODZENIE"), False
