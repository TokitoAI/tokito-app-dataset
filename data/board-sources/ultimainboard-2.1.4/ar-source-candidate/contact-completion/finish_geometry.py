import json,struct,hashlib,math,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent; ROOT=next(p for p in HERE.parents if (p/'data/board-sources/ultimainboard-2.1.4').exists())
source=ROOT/'data/board-sources/ultimainboard-2.1.4/ar-source-candidate/ultimaker-source-selectable.glb'; raw=source.read_bytes(); size=struct.unpack_from('<I',raw,12)[0]; doc=json.loads(raw[20:20+size]); bs=struct.unpack_from('<I',raw,20+size)[0]; binary=bytearray(raw[28+size:28+size+bs]); inv=json.loads((HERE/'source-pad-inventory.json').read_text()); pos={r['ref']:{'x_mm':r['position_mm'][0],'y_mm':r['position_mm'][1]} for r in inv['footprints']}
# Infer exact source export origin from all source component translations.
off=[]
for n in doc['nodes']:
 ref=n.get('name','').removeprefix('ref:')
 if ref in pos and 'translation' in n:
  r=pos[ref]; off.append([r['x_mm']-1000*n['translation'][0],r['y_mm']-1000*n['translation'][2]])
origin=np.array([148.5011,105.003595]); residual=float(np.median(np.max(np.abs(np.array(off)-origin),axis=1)))
assert residual<.0003,(origin,residual)
records=[]
def add(name,faces,color,extra):
 faces=np.asarray(faces,dtype=np.float32); points=faces.reshape(-1,3).astype('<f4'); normal=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]); normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-15); normal=np.repeat(normal,3,axis=0).astype('<f4'); attrs={}
 for sem,val in [('POSITION',points),('NORMAL',normal)]:
  binary.extend(b'\0'*(-len(binary)%4)); vi=len(doc['bufferViews']); payload=val.tobytes();doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(payload),'target':34962});binary.extend(payload);ac={'bufferView':vi,'componentType':5126,'count':len(val),'type':'VEC3'}
  if sem=='POSITION':ac.update(min=val.min(axis=0).tolist(),max=val.max(axis=0).tolist())
  attrs[sem]=len(doc['accessors']);doc['accessors'].append(ac)
 mi=len(doc['materials']);doc['materials'].append({'name':name,'doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':.15,'roughnessFactor':.6}});mesh=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'material':mi}]});ni=len(doc['nodes']);doc['nodes'].append({'name':name,'mesh':mesh,'extras':extra});doc['nodes'][0]['children'].append(ni);return ni,mesh

def region(pad,side):
 x,z=(np.array(pad['position_mm'])-origin)/1000; sx,sz=np.array(pad['size_mm'])/1000;angle=-math.radians(pad['rotation_deg']); y=.00172 if side=='top' else -.00013
 if pad['shape']==0:
  polygon=np.array([[math.cos(t)*sx/2,math.sin(t)*sz/2] for t in np.linspace(0,2*math.pi,33)[:-1]])
 elif pad['shape']==1:polygon=np.array([[-sx/2,-sz/2],[sx/2,-sz/2],[sx/2,sz/2],[-sx/2,sz/2]])
 else:raise ValueError('Unsupported pad shape '+str(pad['shape']))
 r=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]); polygon=polygon@r.T+np.array([x,z]); verts=np.c_[polygon[:,0],np.full(len(polygon),y),polygon[:,1]]; c=np.array([x,y,z]);return [[c,verts[i],verts[(i+1)%len(verts)]] for i in range(len(verts))]
for f in inv['footprints']:
 ref=f['ref']
 if not(ref.startswith('TP') or ref.startswith('Fid') or ref=='JP2'):continue
 faces=[]
 for p in f['pads']:
  for side,key in [('top','top_copper'),('bottom','bottom_copper')]:
   if p[key]:faces.extend(region(p,side))
 if not faces:continue
 extra={'source_reference':ref,'geometry_status':'source_pad_surface_selection_proxy','population_verified':False,'photo_correspondence_verified':False,'physical_body':False,'z_offset_explanation':'selection overlays at top 1.72mm / bottom -0.13mm to avoid coincident source copper surfaces; not contact thickness'}
 ni,mi=add('ref:'+ref,faces,[.72,.57,.18,1],extra);records.append({'reference':ref,'selector':'ref:'+ref,'node':ni,'mesh':mi,'kind':'test_contact' if ref.startswith('TP') else 'fiducial' if ref.startswith('Fid') else 'solder_jumper','source_pads':f['pads'],'geometry_status':extra['geometry_status']})
# Explicit approximate envelopes. Footprint source anchors are authoritative;
# no manufacturer dimensional or specimen accuracy claim is made.
for ref,height in [('K1',15.5),('L2',4.5)]:
 f=next(f for f in inv['footprints'] if f['ref']==ref);p=np.array([r['position_mm'] for r in f['pads']]);lo=p.min(0);hi=p.max(0)
 if ref=='U9': center=p.mean(0);lo=center-[1.45,.8];hi=center+[1.45,.8]
 elif ref=='L2':center=np.array(f['position_mm']);lo=center-[3,3];hi=center+[3,3]
 else:lo-=1.5;hi+=1.5
 low=np.array([(lo[0]-origin[0])/1000,.00174,(lo[1]-origin[1])/1000]);high=np.array([(hi[0]-origin[0])/1000,.00174+height/1000,(hi[1]-origin[1])/1000]);v=np.array([[x,y,z] for x in [low[0],high[0]] for y in [low[1],high[1]] for z in [low[2],high[2]]]);ix=[[0,1,3],[0,3,2],[4,6,7],[4,7,5],[0,4,5],[0,5,1],[2,3,7],[2,7,6],[0,2,6],[0,6,4],[1,5,7],[1,7,3]]
 extra={'source_reference':ref,'source_value':f['value'],'geometry_status':'approximate_package_envelope_not_manufacturer_verified','population_verified':False,'photo_correspondence_verified':False,'height_mm_assumed':height,'dimension_basis':'source pad region plus approximate package envelope; not metrology'};ni,mi=add('ref:'+ref,v[ix],[.75,.75,.66,1] if ref=='J34' else [.16,.17,.18,1],extra);records.append({'reference':ref,'selector':'ref:'+ref,'node':ni,'mesh':mi,'kind':'approximate_package','source_value':f['value'],'bounds_metres':[low.tolist(),high.tolist()],'geometry_status':extra['geometry_status']})
sys.path.insert(0,str(ROOT/'scripts'))
from render_ar_multiview import load_triangles
library_path=HERE/'j34-u9-library-bodies.glb'
library_triangles,library_labels,library_colors,library_records=load_triangles(library_path,{'components':[{'component_id':ref,'reference':ref,'glb_selector':ref,'needs_3d_body':True} for ref in ['J34','U9']]})
for label,record in library_records.items():
 ref=record['reference']; faces=library_triangles[library_labels==label]; assert len(faces)>0
 extra={'source_reference':ref,'geometry_status':'matching_package_kicad_library_step_candidate','population_verified':False,'photo_correspondence_verified':False,'library_glb_sha256':hashlib.sha256(library_path.read_bytes()).hexdigest()}
 ni,mi=add('ref:'+ref,faces,list(library_colors[library_labels==label][0])+[1],extra);records.append({'reference':ref,'selector':'ref:'+ref,'node':ni,'mesh':mi,'kind':'library_package','geometry_status':extra['geometry_status'],'bounds_metres':[faces.min(axis=(0,1)).tolist(),faces.max(axis=(0,1)).tolist()]})
doc['buffers'][0]['byteLength']=len(binary);binary.extend(b'\0'*(-len(binary)%4));chunk=json.dumps(doc,separators=(',',':')).encode();chunk+=b' '*(-len(chunk)%4);output=HERE/'ultimaker-source-contact-selectable-candidate.glb';output.write_bytes(struct.pack('<III',0x46546c67,2,28+len(chunk)+len(binary))+struct.pack('<II',len(chunk),0x4e4f534a)+chunk+struct.pack('<II',len(binary),0x004e4942)+binary)
allrefs=[n['name'][4:] for n in doc['nodes'] if n.get('name','').startswith('ref:')]; assert len(allrefs)==len(set(allrefs)); missing=sorted(set(pos)-set(allrefs)); report={'release_eligible':False,'source_glb_sha256':hashlib.sha256(raw).hexdigest(),'source_pcb_sha256':inv['pcb_sha256'],'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'units':'metres','source_export_origin_mm':origin.tolist(),'source_origin_fit_median_residual_mm':residual,'original_selectable_refs':310,'added_selectable_refs':len(records),'total_selectable_refs':len(allrefs),'missing_refs':missing,'photo_registration_verified':False,'physical_flip_verified':False,'limitations':['K1/L2 package envelopes remain approximations; J34/U9 are matching package KiCad STEP library candidates','Contact selections are source pad surface proxies with explicit display offsets','All physical population remains unverified','Photographed specimen alignment and phone calibration are unverified'],'added_regions':records};(HERE/'geometry-coverage.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='added_regions'},indent=2))
