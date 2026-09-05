# test_tacho.py
import lgpio
import time

TACHO_GPIO = 18
pulse_count = 0

def callback(chip, gpio, level, timestamp):
    global pulse_count
    pulse_count += 1

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_input(h, TACHO_GPIO)
cb = lgpio.callback(h, TACHO_GPIO, lgpio.RISING_EDGE, callback)

print("Measuring fan RPM for 5 seconds...")
time.sleep(5)

rpm = (pulse_count / 5) * 30  # 2 pulses per revolution
print(f"Pulses: {pulse_count}, RPM: {rpm}")

lgpio.callback_cancel(cb)
lgpio.gpiochip_close(h)
