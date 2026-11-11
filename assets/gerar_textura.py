"""Script opcional para reproduzir a textura original do solo da cena.
A textura PNG já acompanha o trabalho; Pillow NÃO é exigido para executar main.py.
Geração original e autoral, sem material externo.
"""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

rng=np.random.default_rng(2026)
N=768
layers=np.zeros((N,N),dtype=np.float32)
for sz,weight in [(6,15),(19,9),(51,7),(160,3),(768,2)]:
    source=(rng.random((sz,sz))*255).astype(np.uint8)
    img=Image.fromarray(source,'L').resize((N,N),Image.Resampling.BICUBIC)
    layers+=(np.asarray(img,dtype=np.float32)/255-.5)*weight
# Veios de cor derivados de funções periódicas (sem borda visível)
y,x=np.mgrid[0:N,0:N]
veins=np.sin(x/N*np.pi*14+np.sin(y/N*np.pi*6)*.9)
veins2=np.cos((x+y*.23)/N*np.pi*25)
layers+=veins*2.5+veins2*1.9
# Textura em RGB claro; o material do solo dá o tom vermelho marciano.
base=np.stack([213+layers*1.25,204+layers*.95,190+layers*.8],axis=2)
base=np.uint8(np.clip(base,0,255))
image=Image.fromarray(base,'RGB')
d=ImageDraw.Draw(image,'RGBA')
for i in range(2200):
    cx=int(rng.integers(0,N));cy=int(rng.integers(0,N))
    r=float(rng.uniform(.3,2.3) if i%8 else rng.uniform(2.0,4.2))
    color=(92,56,41,int(rng.integers(28,75))) if i%3 else (250,224,174,85)
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=color)
path=Path(__file__).with_name('mars_ground.png')
image.save(path,optimize=True)
print('Textura gerada:',path)
