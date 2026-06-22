from dataclasses import dataclass
import psutil
import socket
import ipget
import re
import glob
import time
from asq.initiators import query

from app.history import History

##
# NodeのCPU使用率、メモリ使用率、ディスク使用率、温度、IPアドレスなどの統計情報を管理するクラス
#
@dataclass
class Stats:
    hostname: str = 'unknown'
    ip: str = 'unknown'
    temp: float = 0.0
    cpu: float = 0.0
    cpu_fan_rpm: float = 0.0
    cpu_fan_percentage: float = 0.0
    usedMem: float = 0.0
    totalMem: float = 0.0
    usedMemPercent:float = 0.0
    diskUseGB: float = 0.0
    diskTotalGB: float = 0.0

    stats_expired: float = 0.0
    UPDATE_INTERVAL  = 0
    NETWORK_INTERFACE = ""
    STORAGE_PARTITION = ""

    ##
    #
    #
    def __init__(self, update_interval, network_interface, storage_partition):
        self.UPDATE_INTERVAL   = update_interval
        self.NETWORK_INTERFACE = network_interface
        self.STORAGE_PARTITION = storage_partition
        self.stats_expired = time.time() + self.UPDATE_INTERVAL

        HISTORY_LEN = 120                 # 0.5s × 120 ≒ 60秒
        self.hist_cpu  = History(HISTORY_LEN)
        self.hist_temp = History(HISTORY_LEN)
        self.hist_up   = History(HISTORY_LEN)
        self.hist_down = History(HISTORY_LEN)

        self.net_up_bps   = 0.0
        self.net_down_bps = 0.0
        self._net_prev    = None          # (sent, recv, t)

        self.updateForce()


    ##
    #
    #
    def update(self, is_force = False):        
        if not is_force and time.time() < self.stats_expired:
            return
        
        self.stats_expired = time.time() + self.UPDATE_INTERVAL
        self.updateIp()
        self.updateCpu()
        self.updateTemp()
        self.updateMem()
        self.updateDisk()
        self.updateHostname()
        self.updateNet()                  # Phase3 で追加する
        self._pushHistory()

    ##
    #
    #
    def updateForce(self):
        self.fupdate(self, True)

    ##
    # Metricの履歴を保存しておく
    #
    def _pushHistory(self):
        self.hist_cpu.push(self.cpu)
        self.hist_temp.push(self.temp)
        self.hist_up.push(self.net_up_bps)
        self.hist_down.push(self.net_down_bps)
    
    ##
    #
    #
    def updateDisk(self):
        dsk  = self.getDiskInfo()
        giga = 1.0/1024/1024/1024
        self.diskUseGB   = dsk['used' ] * giga
        self.diskTotalGB = dsk['total'] * giga

    ##
    #
    #
    def getDiskInfo(self):
        disks = {}
        for partition in psutil.disk_partitions():
            path = partition.mountpoint
            dsk  = psutil.disk_usage(path=path)
            disks[path] = {'path': path, 'used': 0, 'total': 0}
            disks[path]['used']  = dsk.used
            disks[path]['total'] = dsk.total
    
        usedAll  = sum( x['used']  for x in disks.values())
        totalAll = sum( x['total'] for x in disks.values())
        
        return {'used': usedAll, 'total': totalAll}

    ##
    #
    #
    def updateCpu(self, interval = None):
        self.cpu = psutil.cpu_percent(interval=interval)
        #self.cpu = psutil.cpu_percent(interval=None)
        #self.cpu = psutil.cpu_percent(interval=1)
    
    ##
    #
    #
    def updateTemp(self):
        def _file2number(path, rate = 1.0):
            with open(path, 'r') as f:
                return float(f.read().strip()) * rate
            
        # cpu温度の取得
        self.temp = _file2number("/sys/class/thermal/thermal_zone0/temp", 0.001)

        # 温度センサーが複数ある場合は、最高温度を取得する
        path_list = glob.glob('/sys/class/hwmon/hwmon*/temp1_input')

        temperatures = (query(path_list)
                        .select(lambda path: _file2number(path, 0.001))
                        .to_list())

        # 最高温度を取得(そのうち使うかも)
        temp_max = max(temperatures) if temperatures else 0
        # print(f"Temperature Max: {temp_max}")

        fan_dir1 = glob.glob('/sys/devices/platform/cooling_fan/hwmon/hwmon*')[0]
        pwm_path = f"{fan_dir1}/pwm1"
        
        fan_dir2 = glob.glob('/sys/devices/platform/cooling_fan/hwmon/*/fan1_input')[0]
        rpm_path = f"{fan_dir2}"
        
        try:
            self.cpu_fan_rpm        = int(_file2number(rpm_path))
            self.cpu_fan_percentage = _file2number(pwm_path, 100.0 / 255.0)
        except FileNotFoundError:
            self.cpu_fan_rpm   = 0
            self.cpu_fan_percentage = 0.0
        

    ##
    #
    #
    def updateMem(self):
        mem = psutil.virtual_memory()
        self.usedMemPercent = mem.percent
        unit_to_giga = 1.0 /1024/1024/1024
        #self.usedMem       = mem.used  /1024/1024/1024
        self.usedMem        = (mem.total-mem.available) * unit_to_giga
        self.totalMem       = mem.total * unit_to_giga

    ##
    # IP
    def updateIp(self):
        try:
            self.ip = ipget.ipget().ipaddr(self.NETWORK_INTERFACE)
            self.ip = re.sub(r'/\d+', '', self.ip)
        except:
            self.ip = 'unknown'
            pass

    ##
    #
    #
    def updateHostname(self):
        self.hostname = socket.gethostname()

    ##
    #
    #
    def updateNet(self):
        now = time.time()
        try:
            c = psutil.net_io_counters(pernic=True).get(self.NETWORK_INTERFACE)
        except Exception:
            c = None
        if c is None:
            self.net_up_bps = self.net_down_bps = 0.0
            self._net_prev = None
            return
        if self._net_prev is not None:
            psent, precv, pt = self._net_prev
            dt = now - pt
            if dt > 0:
                self.net_up_bps   = max(0.0, (c.bytes_sent - psent) / dt)
                self.net_down_bps = max(0.0, (c.bytes_recv - precv) / dt)
        self._net_prev = (c.bytes_sent, c.bytes_recv, now)
