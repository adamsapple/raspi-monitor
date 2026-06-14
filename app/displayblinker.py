import digitalio
from gpiozero import Button
import board
import time

##
# Display Blinker.
#  This class manages display visibility by controlling the backlight pin and a button.
#
class DisplayBlinker:
    def __init__(self, btn_pin_id: int, bl_pin: digitalio.DigitalInOut, interval: float):
        self.button   = Button(btn_pin_id, bounce_time=0.05)
        self.interval = interval
        self.bl_pin   = bl_pin    # backlight pin (if used)
        self.bl_pin.direction = digitalio.Direction.OUTPUT
        self.bl_pin.value     = True

        self.button.when_pressed  = self.button_pressed
        self.backlight_disable_at = time.time() + self.interval

    ##
    # button press handler.
    #
    def button_pressed(self) -> None:
        self.backlight_disable_at = time.time() + self.interval
        self.bl_pin.value = not self.bl_pin.value


    ##
    # whether display is visible or not.
    #
    @property
    def is_visible(self) -> bool:
        return self.bl_pin.value

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        if value != '':
          self.bl_pin.value = value
    ##
    # update display visibility.
    # 
    def update(self) -> None:
        if self.bl_pin.value:
            if time.time() > self.backlight_disable_at:
                self.bl_pin.value = False
