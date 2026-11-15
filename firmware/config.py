# Pins (GPx numbers) and reflow limits. Copied to the Pico with the other files.

# MAX31856 on SPI0
SPI_ID = 0
PIN_SCK = 18
PIN_MOSI = 19   # board SDI
PIN_MISO = 16   # board SDO
PIN_CS = 17
TC_TYPE = "K"
MAINS_HZ = 50

# SH1106 1.3" OLED on I2C1
I2C_ID = 1
PIN_SDA = 14
PIN_SCL = 15
OLED_ADDR = 0x3C
OLED_ROTATE180 = False

PIN_BUZZER = 12     # through an NPN transistor, active buzzer
PIN_BUTTON = 13     # to GND, internal pull-up

SAMPLE_MS = 200

# Reflow limits (SAC305, JEDEC J-STD-020 package limits). Check the FPGA's
# packaging guide; a long press on the button cycles PEAK_LIMITS.
LIQUIDUS = 217.0
PEAK_LIMITS = (245.0, 250.0, 260.0)
APPROACH = 10.0     # beep this far below the peak limit
RAMP_MAX = 3.0      # C/s
TAL_MIN = 60.0      # s above liquidus: enough wetting
TAL_MAX = 120.0     # s above liquidus: start alarming
START_T = 100.0     # a run starts when the package passes this
DONE_T = 150.0      # after the peak, the run ends below this
# Soak on the preheater before hot air. If the preheater cannot bring the
# package to SOAK_LO, lower the window (e.g. 130-180).
SOAK_LO = 150.0
SOAK_HI = 200.0
SOAK_MIN = 60.0     # s in the window before hot air goes on
SOAK_MAX = 120.0    # s; longer soaks dry out the flux
COOL_MAX = 6.0      # C/s
SOLID_SAFE = 200.0  # do not move the board until the package is below this

# Wi-Fi (Pico W only). With WIFI_SSID set it joins that network; otherwise it
# starts its own access point.
WIFI_SSID = ""
WIFI_PASS = ""
AP_SSID = "TC-Monitor"
AP_PASS = "lutowanie"   # at least 8 characters
