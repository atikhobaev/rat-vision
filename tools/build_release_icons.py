from __future__ import annotations
from pathlib import Path
from io import BytesIO
import struct
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / 'ratvision/resources/brand/ratvision_icon.png'
ICO = ROOT / 'ratvision/resources/brand/ratvision.ico'
ICO_SIZES = (16,24,32,48,64,128,256)


def tighten_master(image: Image.Image, *, pad_ratio: float = 0.012) -> Image.Image:
    image = image.convert('RGBA')
    bbox = image.getchannel('A').getbbox()
    if not bbox:
        return image
    l,t,r,b = bbox
    pad = max(1, round(max(r-l,b-t)*pad_ratio))
    crop=image.crop((max(0,l-pad),max(0,t-pad),min(image.width,r+pad),min(image.height,b+pad)))
    side=max(crop.size)
    square=Image.new('RGBA',(side,side),(0,0,0,0))
    square.alpha_composite(crop,((side-crop.width)//2,(side-crop.height)//2))
    out=square.resize((1024,1024), Image.Resampling.LANCZOS)
    px=out.load()
    for y in range(out.height):
        for x in range(out.width):
            rr,gg,bb,aa=px[x,y]
            if aa == 0: px[x,y]=(0,0,0,0)
            elif aa < 255 and min(rr,gg,bb)>180: px[x,y]=(0,0,0,aa)
    return out


def prepare_frame(master: Image.Image, size: int) -> Image.Image:
    frame=master.resize((size,size), Image.Resampling.LANCZOS)
    px=frame.load()
    for y in range(size):
        for x in range(size):
            r,g,b,a=px[x,y]
            if a < 12: px[x,y]=(0,0,0,0)
            elif a < 255 and min(r,g,b)>180: px[x,y]=(0,0,0,a)
    # ICO small-size contract: exact transparent corner pixels.
    for x,y in ((0,0),(size-1,0),(0,size-1),(size-1,size-1)):
        px[x,y]=(0,0,0,0)
    return frame


def write_png_ico(frames: list[Image.Image], path: Path) -> None:
    payloads=[]
    for frame in frames:
        buf=BytesIO(); frame.save(buf, format='PNG', optimize=True); payloads.append(buf.getvalue())
    count=len(frames)
    header=struct.pack('<HHH',0,1,count)
    offset=6+16*count
    entries=[]
    for frame,data in zip(frames,payloads):
        w=0 if frame.width==256 else frame.width
        h=0 if frame.height==256 else frame.height
        entries.append(struct.pack('<BBBBHHII',w,h,0,0,1,32,len(data),offset))
        offset+=len(data)
    path.write_bytes(header+b''.join(entries)+b''.join(payloads))


def build_icons() -> None:
    master=tighten_master(Image.open(ICON))
    master.save(ICON)
    frames=[prepare_frame(master,s) for s in ICO_SIZES]
    write_png_ico(frames, ICO)

if __name__ == '__main__': build_icons()
