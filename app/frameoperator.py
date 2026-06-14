import time

class FrameOperator:

    def __init__(self):
        self.is_running = False
        self.func       = None
        self.fps        = 10


    def start(self):
        if self.is_running:
            return

        sec_prev = -1
        frame_count = 0
        self.is_running = True
        while self.is_running:
            start_time = time.time()
            frame_count += 1
            self.func()
            #draw_info(draw, font)
            #device.display(image)
            end_time = time.time()
            sec = int(end_time)

            if sec_prev != sec:
                sec_prev = sec
                #print(f"frame_count: {frame_count}")
                frame_count = 0

            elapsed_time_sec = (end_time - start_time)
            sleep_sec = max(0, (1.0 / self.fps) - elapsed_time_sec)
            #print(f"sleep_sec: {sleep_sec}")
            time.sleep(sleep_sec)



    def stop(self):
        self.is_running = False
