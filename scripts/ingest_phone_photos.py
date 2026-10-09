from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import hashlib,json,re,shutil
src=Path.home()/'Downloads';root=Path('data/photo-model');raw=root/'photos/raw';raw.mkdir(parents=True,exist_ok=True)
paths=sorted(src.glob('IMG_20261009*.jpg'));records=[]
for p in paths:
 b=p.read_bytes();digest=hashlib.sha256(b).hexdigest()
 with Image.open(p) as im:
  im.verify()
 with Image.open(p) as im:
  w,h=im.size;exif=im.getexif();orientation=exif.get(274,1)
 dest=raw/p.name
 if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest()!=digest:raise ValueError('Changed photo: '+p.name)
 if not dest.exists():shutil.copy2(p,dest)
 records.append({'file':p.name,'width':w,'height':h,'exif_orientation':orientation,'bytes':len(b),'sha256':digest,'candidate_capture_group':re.sub(r'_1(?=\.jpg$)','',p.name),'source':'Downloads','board_class':None,'review_status':'unreviewed'})
(root/'photo-manifest.json').write_text(json.dumps(records,indent=2))
base=[p for p in paths if not p.stem.endswith('_1')]
out=Path('work/photo-contact');out.mkdir(exist_ok=True)
for page in range((len(base)+15)//16):
 canvas=Image.new('RGB',(1440,1120),'#e5e5e5');draw=ImageDraw.Draw(canvas)
 for j,p in enumerate(base[page*16:(page+1)*16]):
  with Image.open(p) as im:
   thumb=ImageOps.exif_transpose(im).convert('RGB');thumb.thumbnail((350,245))
  x=(j%4)*360;y=(j//4)*280;canvas.paste(thumb,(x+(350-thumb.width)//2,y))
  draw.text((x+5,y+250),p.name,fill='black')
 canvas.save(out/f'contact-{page+1}.jpg')
print(json.dumps({'photos':len(paths),'base_captures':len(base),'paired_variants':len(paths)-len(base),'contact_sheets':(len(base)+15)//16}))
