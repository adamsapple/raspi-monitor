from pathlib import Path
#import inspect
import gzip
import shutil
import tarfile
import io

from PIL import ImageFont
from PIL import BdfFontFile
from PIL import PcfFontFile

FONT_SIZE = 14

#FONT_PATH    = f"./fonts/ter-u{FONT_SIZE}n.bdf"
#FONT_PATH    = f"./fonts/misaki_gothic.bdf"
#FONT_PATH    = f"./fonts/HaxorMedium-10.bdf"
#FONT_PATH    = f"./fonts/6x10.bdf"
FONT_PATH    = f"./fonts/Bm5x8.bdf"
#ARCHIVE_PATH = Path("fonts/terminus-font-4.49.1.tar.gz")
#FONT_PATH    = f"terminus-font-4.49.1/ter-u{FONT_SIZE}n.bdf"
#FONT_PATH    = f"./fonts/Bm437 NEC MultiSpeed.bdf"
#ARCHIVE_PATH = Path("fonts/unifont-17.0.04.pcf.gz")
#FONT_PATH    = "unifont-17.0.04.pcf"

#ARCHIVE_PATH = Path("fonts/shinonome-0.9.11p1.tar.bz2")
#FONT_PATH    = "shinonome-0.9.11/bdf/shnmk12p.bdf"

#ARCHIVE_PATH = Path("fonts/efont-unicode-bdf-0.4.2.tar.bz2")
#FONT_PATH    = "efont-unicode-bdf-0.4.2/f12.bdf"

#with open(f"/usr/share/fonts/X11/misc/ter-u{FONT_SIZE}n.bdf", "rb") as fp:
#    font = BdfFontFile.BdfFontFile(fp)
#    font.save("fonts/ter-u{FONT_SIZE}n")   # fonts/ter-u14n.pil と companion bitmap を作る

#with gzip.open(f"/usr/share/fonts/X11/misc/ter-u{FONT_SIZE}n_iso-8859-1.pcf.gz", "rb") as fp:
#    font = PcfFontFile.PcfFontFile(fp)
#    font.save(f"fonts/ter-u{FONT_SIZE}n.pil")   # fonts/ter-u14n.pil と companion bitmap を作る

#with open(f"fonts/misaki_gothic.bdf", "rb") as fp:
#    font = BdfFontFile.BdfFontFile(fp)
#    font.save(f"fonts/misaki_gothic.pil")   # companion bitmap を作る

#with gzip.open(f"./fonts/unifont-17.0.04.pcf.gz", "rb") as fp:
#    font = PcfFontFile.PcfFontFile(fp)
#    font.save(f"./fonts/unifont-17.0.04.pil")   # fonts/ter-u14n.pil と companion bitmap を作

##
#
#
def pcfgz2pil(archive_path:str) ->str:
    p1 = Path(archive_path)
    out_path = p1.with_suffix(".pil")

    with gzip.open(p1, "rb") as fp:
        font = PcfFontFile.PcfFontFile(fp)
        font.save(out_path)
    
    return out_path

##
#
#
def bdftgz2pil(archive_path:str, font_path:str) -> str:
    p1 = Path(archive_path)
    p2 = Path(font_path)
    out_path = p1.with_name(f"{p2.stem}.pil")

    with tarfile.open(p1, "r:gz") as tf:
        data = tf.extractfile(font_path).read()
        font = BdfFontFile.BdfFontFile(io.BytesIO(data))
        font.save(out_path)

    return out_path

##
#
#
def bdftbz22pil(archive_path:str, font_path:str) -> str:
    p1 = Path(archive_path)
    p2 = Path(font_path)
    out_path = p1.with_name(f"{p2.stem}.pil")
    print(f"out_path: {out_path}")
    with tarfile.open(p1, "r:bz2") as tf:
        tf.list()
        data = tf.extractfile(font_path).read()
        font = BdfFontFile.BdfFontFile(io.BytesIO(data))
        font.save(out_path)

    return out_path

##
#
#
def bdf2pil(path: str) -> str:
    p = Path(path)
    out_path = p.with_suffix(".pil")
    
    with open(p, "rb") as fp:
        font = BdfFontFile.BdfFontFile(fp)
        font.save(out_path)   # companion bitmap を作る
    
    return out_path

##
#
#
def main():
    #if not ARCHIVE_PATH.exists():
    #    raise FileNotFoundError(f"Archive not found: {ARCHIVE_PATH}")

    #func = bdftbz22pil
    #func = bdftgz2pil
    #out_path = func(ARCHIVE_PATH, FONT_PATH)
    
    #func = pcfgz2pil
    func = bdf2pil
    out_path = func(FONT_PATH)
    
    print(f"{func.__name__}->\nConverted: {FONT_PATH} -> {out_path}")
    

if __name__ == "__main__":
    main()