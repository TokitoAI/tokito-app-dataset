import json,struct,hashlib,math,sys
from pathlib import Path
import numpy as np
from scipy.spatial import Delaunay
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'input'
cm=json.loads((SOURCE/'component-map.json').read_text())
raw=(SOURCE/'esp32_devkit_v1_30pin_visible.glb').read_bytes(); n=struct.unpack_from('<I',raw,12)[0]; old=json.loads(raw[20:20+n])
d={'asset':{'version':'2.0','generator':'Tokito evidence-qualified ESP32 package candidate'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'accessors':[],'bufferViews':[],'buffers':[{'byteLength':0}],'materials':[]}; binary=bytearray(); alltris=[]
colors={'pcb':(.025,.07,.04),'black':(.08,.08,.085),'silver':(.65,.65,.67),'gold':(.75,.53,.18),'tan':(.66,.43,.12)}
for key,c in colors.items():d['materials'].append({'name':key,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[*c,1],'roughnessFactor':.7,'metallicFactor':.55 if key in ['silver','gold'] else 0}})
def box(cx,cy,cz,w,h,l):
 p=np.array([(x,y,z) for y in [cy-h/2,cy+h/2] for z in [cz-l/2,cz+l/2] for x in [cx-w/2,cx+w/2]])
 f=[(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),(2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)]
 return p[np.array(f)]
def ring(x,z,r,outer,y,thick=0):
 t=np.arange(32)*2*np.pi/32; a=np.column_stack([x+r*np.cos(t),np.full(32,y),z+r*np.sin(t)]); b=np.column_stack([x+outer*np.cos(t),np.full(32,y),z+outer*np.sin(t)]); faces=[]
 for i in range(32):j=(i+1)%32;faces.extend([[a[i],b[i],b[j]],[a[i],b[j],a[j]]])
 return np.array(faces)
def add(name,parts,status):
 prim=[]
 for tris,color in parts:
  arr=np.array(tris,dtype='<f4').reshape(-1,3)/1000; start=len(binary);payload=arr.tobytes();binary.extend(payload);vi=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(payload),'target':34962});ai=len(d['accessors']);d['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(arr),'type':'VEC3','min':arr.min(0).tolist(),'max':arr.max(0).tolist()});prim.append({'attributes':{'POSITION':ai},'material':list(colors).index(color)});alltris.extend((tri,colors[color]) for tri in np.array(tris))
 mi=len(d['meshes']);d['meshes'].append({'name':name,'primitives':prim});ni=len(d['nodes']);d['nodes'].append({'name':name,'mesh':mi,'extras':{'geometry_status':status,'calibration_eligible':False,'identity_verified':False}});d['scenes'][0]['nodes'].append(ni)
# Nominal dimensions inherited explicitly; circles triangulate true openings, never calibration truth.
holes=[(x,z,1.5) for x in [-11.5,11.5] for z in [-22.5,22.5]]+[(x,(i-7)*2.54,.5) for x in [-12.7,12.7] for i in range(15)]
pts=[[-14,-25.75],[14,-25.75],[14,25.75],[-14,25.75]]
for x,z,r in holes:
 pts.extend([[x+r*math.cos(t),z+r*math.sin(t)] for t in np.arange(32)*2*math.pi/32])
p=np.array(pts); surface=[]
for ids in Delaunay(p).simplices:
 tri=p[ids];c=tri.mean(0)
 if any((c[0]-x)**2+(c[1]-z)**2<r*r for x,z,r in holes):continue
 surface.extend([np.column_stack([tri[:,0],np.zeros(3),tri[:,1]]),np.column_stack([tri[::-1,0],np.full(3,-1.6),tri[::-1,1]])])
for x,z,r in holes:
 for i in range(32):
  a=i*2*math.pi/32;b=(i+1)*2*math.pi/32;v=np.array([[x+r*math.cos(a),0,z+r*math.sin(a)],[x+r*math.cos(b),0,z+r*math.sin(b)],[x+r*math.cos(a),-1.6,z+r*math.sin(a)],[x+r*math.cos(b),-1.6,z+r*math.sin(b)]]);surface.extend([v[[0,2,3]],v[[0,3,1]]])
for a,b in zip(pts[:4],pts[1:4]+pts[:1]):
 v=np.array([[a[0],0,a[1]],[b[0],0,b[1]],[a[0],-1.6,a[1]],[b[0],-1.6,b[1]]]);surface.extend([v[[0,1,3]],v[[0,3,2]]])
add('pcb:provisional_substrate',[(surface,'pcb')],'nominal_dimension_drilled_substrate_not_specimen_measurement')
for c in cm['components']:
 ref=c['reference'];x=c['board_position_mm']['x'];z=c['board_position_mm']['y'];parts=[]
 if ref.startswith('MH'):continue
 if ref in ['J2','J3']:
  for i in range(15):parts.append((ring(x,(i-7)*2.54,.5,.95,.025),'gold'))
  status='observed_top_header_contacts_nominal_pitch_underside_population_unknown'
 elif ref=='MOD1':
  parts=[(box(x,.4,z,18,.8,25.5),'pcb'),(box(x,1.5,z-3.2,16,1.4,17.4),'silver')]
  status='observed_ESP-32_shield_module_variant_and_dimensions_unverified'
 elif ref=='J1':
  parts=[(box(x,1.35,z-1.9,7.5,2.7,.5),'silver'),(box(x-3.6,1.35,z, .4,2.7,4),'silver'),(box(x+3.6,1.35,z,.4,2.7,4),'silver'),(box(x,2.65,z,7.5,.3,4),'silver'),(box(x,.15,z,7.5,.3,4),'silver'),(box(x,1,z,5.8,.7,3),'black')];status='micro_usb_open_shell_visual_approximation'
 elif ref in ['SW1','SW2']:
  parts=[(box(x,.6,z,3.5,1.2,4.5),'silver'),(box(x,1.5,z,2, .7,2),'black')];status='tactile_switch_visual_approximation'
 elif ref=='U1':
  parts=[(box(x,.85,z,6.5,1.7,3.5),'black'),(box(x,.3,z-2.4,3,.6,2),'silver')]
  parts.extend((box(x+dx,.2,z+2.4,.65,.4,1.7),'silver') for dx in [-2.3,0,2.3]);status='SOT223_observed_body_and_tab_nominal_dimensions'
 elif ref=='U2':
  parts=[(box(x,.45,z,5,.9,5),'black')]
  for i in range(7):
   pos=(i-3)*.65
   parts.extend([(box(x+pos,.08,z-2.65,.3,.16,.5),'silver'),(box(x+pos,.08,z+2.65,.3,.16,.5),'silver'),(box(x-2.65,.08,z+pos,.5,.16,.3),'silver'),(box(x+2.65,.08,z+pos,.5,.16,.3),'silver')])
  status='CP2102_marking_family_QFN28_package_approximation'
 else:
  w,l,h=(3.5,2.8,1.5) if ref=='C_TAN1' else (2,1.25,.8)
  parts=[(box(x,h/2,z,w,h,l),'tan' if ref=='C_TAN1' else 'black'),(box(x-w/2,.2,z,.35,.4,l),'silver'),(box(x+w/2,.2,z,.35,.4,l),'silver')];status='unverified_package_approximation_preserved_selector'
 add('ref:'+ref,parts,status)
d['buffers'][0]['byteLength']=len(binary);j=json.dumps(d,separators=(',',':')).encode();j+=b' '*(-len(j)%4);glb=struct.pack('<III',0x46546c67,2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
out=ROOT/'esp32-package-candidate.glb';out.write_bytes(glb)
report={'release_eligible':False,'calibration_eligible':False,'photo_registration_verified':False,'source_glb_sha256':hashlib.sha256(raw).hexdigest(),'source_component_map_sha256':hashlib.sha256((SOURCE/'component-map.json').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(glb).hexdigest(),'selectable_components':15,'true_nominal_openings':34,'observations':['Four mounting holes visible in source video sheet','Top view shows header contacts without protruding pins; underside pin population unverified','RF shield literal marking ESP-32; WROOM32 exact identity unverified'],'limitations':['All metric dimensions inherited nominal assumptions, not measurements','Remaining small part references/positions copied as provisional, not photograph source joins','No calibrated camera or complete real underside/four-side/flip set','Only approximate package shapes; no production activation'],'triangle_count':len(alltris)}
(ROOT/'provenance.json').write_text(json.dumps(report,indent=2)+'\n')
# Deterministic orthographic top/oblique visual review, no camera calibration claim.
im=Image.new('RGB',(1200,900),'#e5e8ee');dr=ImageDraw.Draw(im)
for center,oblique in [(300,False),(900,True)]:
 def project(v):
  x,y,z=v
  return (center+11*x+(3*z if oblique else 0),450+10*z-(14*y if oblique else 0))
 for tri,color in sorted(alltris,key=lambda t:float(t[0][:,1].mean())):
  dr.polygon([project(v) for v in tri],fill=tuple(int(v*255) for v in color))
 dr.text((center-180,40),'PROVISIONAL - no metric calibration',fill='black')
im.save(ROOT/'preview.jpg',quality=95)
print(json.dumps(report,indent=2))

