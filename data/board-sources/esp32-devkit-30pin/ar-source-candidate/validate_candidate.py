import json,struct,hashlib
from pathlib import Path
import numpy as np
p=Path(__file__).parent;raw=(p/'esp32-package-candidate.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+size]);off=28+size;binary=raw[off:];names=[n['name'] for n in d['nodes']];assert len(set(names))==len(names);assert len([n for n in names if n.startswith('ref:')])==15
meshids=[n['mesh'] for n in d['nodes']];assert len(set(meshids))==len(meshids)
tri=[]
for prim in d['meshes'][0]['primitives']:
 a=d['accessors'][prim['attributes']['POSITION']];v=d['bufferViews'][a['bufferView']];t=np.frombuffer(binary,dtype='<f4',count=a['count']*3,offset=v['byteOffset']).reshape(-1,3,3)*1000;tri.extend(t)
tri=np.array(tri);top=tri[np.all(np.abs(tri[:,:,1])<1e-5,axis=1)][:,:,[0,2]]
def hit(point):
 for t in top:
  a,b,c=t;u=b-a;v=c-a;q=np.array(point)-a;det=u[0]*v[1]-u[1]*v[0]
  if abs(det)<1e-8:continue
  s=(q[0]*v[1]-q[1]*v[0])/det;r=(u[0]*q[1]-u[1]*q[0])/det
  if s>=-1e-7 and r>=-1e-7 and s+r<=1+1e-7:return True
 return False
holes=[(x,z) for x in [-11.5,11.5] for z in [-22.5,22.5]]+[(x,(i-7)*2.54) for x in [-12.7,12.7] for i in range(15)]
assert all(not hit(h) for h in holes);assert hit((0,0));assert all(not n['extras']['calibration_eligible'] for n in d['nodes'])
report={'selectors_unique':True,'independent_meshes':True,'component_selectors':15,'opening_centers_without_surface':len(holes),'central_pcb_surface_present':True,'sha256':hashlib.sha256(raw).hexdigest(),'glb_bytes':len(raw),'calibration_disabled':True,'visual_review':'Top and oblique preview inspected; shaped USB/switch/QFN/regulator/module bodies and top header contacts; underside pin population unknown visible; placement still unverified'}
(p/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
