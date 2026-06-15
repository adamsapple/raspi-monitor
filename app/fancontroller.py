#!/usr/bin/env python3
import time
from gpiozero import PWMOutputDevice
#from gpiozero.pins.pigpio import PiGPIOFactory

# --- Configuration ---
GPIO_PWM = 18             # BCM pin (physical pin 8)
# Noctua's spec is ~25 kHz, but hardware PWM at that rate was unresponsive with the
# fan tested here. The previous time.sleep-based PWM nominally targeted 25 kHz but
# in practice ran at sub-kHz due to scheduler granularity, which is what the fan
# was implicitly tuned for. Drop to 100 if a winding whine becomes audible.
PWM_FREQ_HZ    = 25000/4
TEMP_FILE_PATH = "/sys/block/nvme0n1/device/hwmon1/temp1_input"
READ_INTERVAL  = 1        # seconds
OPERATION_INTERVAL = 10   # seconds between fan speed updates
LOWER_TEMP     = 40       # degrees Celsius
UPPER_TEMP     = 65       # degrees Celsius
MIN_FAN_SPEED  = 20       # percent
MAX_FAN_SPEED  = 100      # percent

##
#
#
class FanController:
    def __init__(self, gpio_pinid : int = GPIO_PWM, frequency_hz: int = PWM_FREQ_HZ):
        self.set_fan_pwm(gpio_pinid, frequency_hz)

        self.temp_path         = TEMP_FILE_PATH
        self.next_read_at      = 0
        self.next_operation_at = 0
        self.target_temp       = self._read_temp()
        self._speed_rate       = 0
    
    ##
    # Stops the fan.
    #
    def stop(self) -> None:
        if self.fan is not None:
            self.fan_speed = 0
            self.fan.off()

    ##
    # Closes the fan controller.
    #
    def close(self) -> None:
        self.fan.stop()
        if self.fan is not None:
            self.fan.close()

    def set_fan_pwm(self, gpio_pinid : int = GPIO_PWM, frequency_hz: int = PWM_FREQ_HZ, isHW = False) -> None:
        if gpio_pinid >= 0:
            if isHW:
                factory = PiGPIOFactory()
            else:
                factory = None
            self.fan = PWMOutputDevice(gpio_pinid, frequency=frequency_hz, initial_value=0, pin_factory=factory)
        else:
            self.fan = None

    ##
    #
    #
    @property
    def temp(self) -> float:
        return self.target_temp

    ##
    #
    #
    @property
    def fan_speed(self) -> int:
        return self._speed_rate
                
    
    @fan_speed.setter
    def fan_speed(self, speed_percent: int):
        value = speed_percent
        if value < MIN_FAN_SPEED:
            value = 0
        
        self._speed_rate = value
        if self.fan is not None:
            self.fan.value = max(0, min(100, self._speed_rate)) * 0.01
        

    ##
    # 
    #
    def _read_temp(self) -> float:
        try:
            with open(self.temp_path) as f:
                return int(f.read().strip()) / 1000.0
        except FileNotFoundError:
            print(f"Error: Temperature file not found at {self.temp_path}")
            return 0
        except (OSError, ValueError) as e:
            print(f"Error reading temperature: {e}")
            return 0


    ##
    # 
    #
    def _calculate_fan_speed(self, temp: float | None) -> int:
        if temp is None:
            return 0
        if temp < LOWER_TEMP:
            return 0
        if temp >= UPPER_TEMP:
            return MAX_FAN_SPEED
        span = (temp - LOWER_TEMP) / (UPPER_TEMP - LOWER_TEMP)
        return int(MIN_FAN_SPEED + span * (MAX_FAN_SPEED - MIN_FAN_SPEED))


    ##
    # Updates the fan speed based on the current temperature.
    #
    def update(self) -> None:
        now = time.time()

        if now >= self.next_read_at:
            self.target_temp = self._read_temp()
            self.next_read_at = now + READ_INTERVAL
        
        if self.target_temp is None:
            return
        
        if now >= self.next_operation_at:
            self.fan_speed         = self._calculate_fan_speed(self.target_temp)
            self.next_operation_at = now + OPERATION_INTERVAL

        # print(f"Current Temp: {self.target_temp:.2f}°C -> Fan Speed: {self.fan_speed}%")
        
