"""Build transparent tonal artwork from the editable SVG sources. No proprietary APK input.
Requires Pillow and fonttools. Run from the repository root: python tools/build.py
"""
from pathlib import Path
import hashlib, json, math, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
from fontTools.svgLib.path import parse_path
from fontTools.pens.basePen import BasePen

ROOT=Path(__file__).resolve().parents[1]
SCALE=10
def render(svg):
    image=Image.new('RGBA',(100*SCALE,100*SCALE));draw=ImageDraw.Draw(image)
    def color(value):return None if value=='none' else value
    class Pen(BasePen):
        def __init__(self):super().__init__(None);self.paths=[];self.points=[]
        def _moveTo(self,p):
            if self.points:self.paths.append((self.points,False))
            self.points=[p]
        def _lineTo(self,p):self.points.append(p)
        def _curveToOne(self,a,b,c):
            p=self.points[-1]
            for i in range(1,33):
                t=i/32;u=1-t;self.points.append(tuple(u**3*p[j]+3*u*u*t*a[j]+3*u*t*t*b[j]+t**3*c[j] for j in (0,1)))
        def _qCurveToOne(self,a,b):
            p=self.points[-1]
            for i in range(1,25):
                t=i/24;u=1-t;self.points.append(tuple(u*u*p[j]+2*u*t*a[j]+t*t*b[j] for j in (0,1)))
        def _closePath(self):self.paths.append((self.points,True));self.points=[]
        def _endPath(self):
            if self.points:self.paths.append((self.points,False));self.points=[]
    root=ET.fromstring(svg)
    for element in root:
        tag=element.tag.split('}')[-1];a=element.attrib
        fill=color(a.get('fill','#eeeeee'));stroke=color(a.get('stroke','none'));width=max(1,round(float(a.get('stroke-width',2))*SCALE))
        def point(x,y):return (float(x)*SCALE,float(y)*SCALE)
        if tag=='path':
            pen=Pen();parse_path(a['d'],pen);pen._endPath()
            for points,closed in pen.paths:
                pts=[point(*p) for p in points]
                if fill and len(pts)>2:draw.polygon(pts,fill=fill)
                if stroke:
                    if closed:pts=pts+[pts[0]]
                    draw.line(pts,fill=stroke,width=width,joint='curve')
        elif tag in ('circle','ellipse'):
            cx=float(a['cx']);cy=float(a['cy']);rx=float(a.get('r',a.get('rx',0)));ry=float(a.get('r',a.get('ry',0)))
            draw.ellipse([point(cx-rx,cy-ry),point(cx+rx,cy+ry)],fill=fill,outline=stroke,width=width)
        elif tag=='rect':
            x=float(a['x']);y=float(a['y']);w=float(a['width']);h=float(a['height']);radius=float(a.get('rx',0))
            draw.rounded_rectangle([point(x,y),point(x+w,y+h)],radius*SCALE,fill=fill,outline=stroke,width=width)
        elif tag=='line':draw.line([point(a['x1'],a['y1']),point(a['x2'],a['y2'])],fill=stroke,width=width)
    return image.resize((256,256),Image.Resampling.LANCZOS)

def main():
    index=json.loads((ROOT/'catalog.json').read_text(encoding='utf8'));entries=[];preview=[]
    (ROOT/'icons').mkdir(exist_ok=True)
    for item in index:
        name=item['id'];svg=(ROOT/'src'/f'{name}.svg').read_text(encoding='utf8');image=render(svg)
        path=ROOT/'icons'/f'{name}.png';image.save(path,optimize=True)
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        for package in item['packages']:
            entries.append(dict(package=package,label=item['label'],path=f'icons/{name}.png',sha256=sha,dynamic=item.get('dynamic','')))
        preview.append((item['label'],image))
    (ROOT/'index.json').write_text(json.dumps(dict(schema=1,icons=entries),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    cols=5;rows=math.ceil(len(preview)/cols);board=Image.new('RGB',(cols*180,rows*205),'#243444');d=ImageDraw.Draw(board)
    for i,(label,image) in enumerate(preview):
        x=i%cols*180;y=i//cols*205;plate=Image.new('RGBA',(160,160),'#718899');board.paste(plate,(x+10,y+10));im=image.resize((150,150));board.paste(im,(x+15,y+15),im)
        d.text((x+10,y+177),index[i]['id'],fill='white')
    board.save(ROOT/'preview.png')
    print(f'{len(index)} artwork sources, {len(entries)} package mappings')
if __name__=='__main__':main()
