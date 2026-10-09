"""Propose boxes for hash-matched, class-reviewed photos without changing labels.

This foreground heuristic was designed for the initial capture session. Its
outputs require visual review and are saved under work/photo-contact only.
New photos must have a board-class review before using this script.
"""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
from scipy import ndimage
import numpy as np,json,hashlib
repo=Path(__file__).resolve().parents[1]
root=repo/'data/photo-model';manifest=json.loads((root/'photo-manifest.json').read_text());names=['esp32_board','esp8266_board','ultimainboard','nxp_frdm_mcxn236_board','raspberry_pi_3b_board']
reviews=json.loads((root/'board-review.json').read_text())['images']
for rec in manifest:
 filename=rec['file'];review=reviews.get(filename)
 if Path(filename).name!=filename:raise ValueError('Expected a photo filename: '+filename)
 if review is None or not 0<=review['class_id']<len(names):raise ValueError('Photo needs board-class review: '+filename)
 digest=hashlib.sha256((root/'photos/raw'/filename).read_bytes()).hexdigest()
 if digest!=rec['sha256'] or digest!=review['sha256']:raise ValueError('Reviewed photo changed or LFS file not pulled: '+filename)
records=[];thumbs=[]
for rec in manifest:
 filename=rec['file'];clock=int(filename.split('_')[2].split('.')[0]);cid=reviews[filename]['class_id']
 dest=root/'photos/raw'/filename
 with Image.open(dest) as im:im=ImageOps.exif_transpose(im).convert('RGB')
 w,h=im.size;small=im.copy();small.thumbnail((600,600));a=np.asarray(small).astype(float);r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
 mask=(g>b*1.15)&(r>b*1.18)&(r>g*.72)&(np.maximum(r,g)>80)
 if cid==4:mask=(g>b*1.1)&(g>r*.85)&(g>70)
 if cid==2 and 222033<=clock<=222113 and '_1.' not in filename:mask[int(mask.shape[0]*.78):]=False
 mask=ndimage.binary_closing(mask,iterations=4);mask=ndimage.binary_fill_holes(mask)
 labels,n=ndimage.label(mask);sizes=np.bincount(labels.ravel());sizes[0]=0
 if not n:raise ValueError('No candidate '+filename)
 ys,xs=np.where(labels==sizes.argmax());sw,sh=small.size
 box=[max(0,(xs.min()-4)/sw),max(0,(ys.min()-4)/sh),min(1,(xs.max()+5)/sw),min(1,(ys.max()+5)/sh)]
 row={**rec,'board_class':names[cid],'class_id':cid,'oriented_width':w,'oriented_height':h,'bbox_xyxy_normalized':box,'board_identity_status':'class_from_hash_matched_review','box_status':'proposal-needs-review','box_method':'colour foreground mask plus connected component'};records.append(row)
 thumb=im.copy();thumb.thumbnail((320,240));d=ImageDraw.Draw(thumb);d.rectangle([box[0]*thumb.width,box[1]*thumb.height,box[2]*thumb.width,box[3]*thumb.height],outline='red',width=3);thumbs.append((filename,thumb,names[cid]))
work=repo/'work/photo-contact';work.mkdir(parents=True,exist_ok=True)
(work/'board-annotation-proposals.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
for page in range((len(thumbs)+19)//20):
 canvas=Image.new('RGB',(1280,1425),'#dddddd');d=ImageDraw.Draw(canvas)
 for j,(filename,im,name) in enumerate(thumbs[page*20:(page+1)*20]):
  x=j%4*320;y=j//4*285;canvas.paste(im,(x+(320-im.width)//2,y));d.text((x+2,y+242),filename,fill='black');d.text((x+2,y+260),name,fill='black')
 canvas.save(work/f'boxes-{page+1}.jpg')
print(json.dumps({name:sum(x['board_class']==name for x in records) for name in names}))
