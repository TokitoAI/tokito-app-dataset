from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if (p/'data/board-sources/ultimainboard-2.1.4').exists());sys.path.insert(0,str(ROOT/'scripts'))
from render_ar_multiview import load_triangles,camera,rasterize
p=HERE/'ultimaker-source-contact-selectable-candidate.glb';report=json.loads((HERE/'geometry-coverage.json').read_text()); comps=[{'component_id':r['reference'],'reference':r['reference'],'glb_selector':r['selector'],'needs_3d_body':True} for r in report['added_regions']]
t,l,c,records=load_triangles(p,{'components':comps},ignore_non_triangle=True)
views=[]
for name,eye in [('top',[0,.29,0]),('bottom',[0,-.29,0])]:
 forward=(np.array([0,.0008,0])-np.array(eye));forward/=np.linalg.norm(forward);right=np.array([1.,0.,0.]);down=np.cross(forward,right);R=np.stack([right,down,forward]);T=-R@np.array(eye);K=np.array([[864.,0.,320.],[0.,864.,160.],[0.,0.,1.]]);im,mask,dep=rasterize(t,l,c,R,T,K,640,320);Image.fromarray(im).save(HERE/(name+'.png'));Image.fromarray(mask).save(HERE/(name+'.instances.png'));views.append((name,im));print(name,'complete',flush=True)
canvas=Image.new('RGB',(640,690),'#1c1c1c');draw=ImageDraw.Draw(canvas)
for i,(name,im) in enumerate(views):canvas.paste(Image.fromarray(im),(0,25+i*345));draw.text((10,i*345+5),name+' SOURCE GEOMETRY / UNVERIFIED POPULATION',fill='white')
canvas.save(HERE/'top-bottom-review.jpg',quality=95)
(HERE/'render-evidence.json').write_text(json.dumps({'asset_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'triangles_rendered':len(t),'triangle_only_review':True,'physical_flip_test':False,'review_image':'top-bottom-review.jpg','views':['top','bottom']},indent=2))
