import digitalio
from gpiozero import Button
import board
import time

##
# Display Blinker.
#  This class manages display visibility by controlling the backlight pin and a button.
#
class DisplayBlinker:
    def __init__(self, btn_pin_id: int, bl_pin: digitalio.DigitalInOut, interval: float, hold_time: float = 0.6):
        self.button   = Button(btn_pin_id, bounce_time=0.05, hold_time=hold_time)
        self.interval = interval       
        self.bl_pin   = bl_pin    # backlight pin (if used)
        self.bl_pin.direction = digitalio.Direction.OUTPUT
        self.bl_pin.value     = True

        self.button.when_pressed  = self._button_pressed
        self.button.when_held     = self._on_held
        self.button.when_released = self._on_released

        self._held     = False
        self.on_pushed = None          # 表示中のページ送り用

        self.backlight_disable_at = time.time() + self.interval

    ##
    # button press handler.
    #
    def _button_pressed(self) -> None:
        self._held = False                       # 長押し判定をリセット
    

    def _on_held(self) -> None:
        self._held = True
        self.bl_pin.value = False                # 長押し => 消灯

    def _on_released(self) -> None:
        if self._held:
            return                               # 長押しは処理済み
        
        self.backlight_disable_at = time.time() + self.interval
        
        if not self.bl_pin.value:
            self.bl_pin.value = True             # 消灯中のタップ => 点灯のみ
        elif self.on_pushed is not None:
            self.on_pushed()                        # 表示中のタップ => ページ送り

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
