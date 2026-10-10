import json,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw
root=next(p for p in Path(__file__).resolve().parents if (p/'scripts/render_ar_multiview.py').is_file())
sys.path.insert(0,str(root/'scripts'))
from render_ar_multiview import load_triangles
out=Path(__file__).parent
refs=root/'data/phone-captures/2026-10-10/reviewed-scan-references.json'
reference=next(v for v in json.loads(refs.read_text())['templates'] if v['id']=='IMG_20261010_092203.jpg')
imagepath=root/reference['image_path']; raw=imagepath.read_bytes()
assert hashlib.sha256(raw).hexdigest()==reference['image_sha256']
im=ImageOps.exif_transpose(Image.open(imagepath)).convert('RGB'); w,h=im.size
src=np.array(reference['pose_metric_landmarks_metres']); dst=np.array(reference['pose_corners_normalized'])*[w,h]
A=[];b=[]
for (x,y),(u,v) in zip(src,dst):
 A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);b.extend([u,v])
H=np.r_[np.linalg.solve(A,b),1].reshape(3,3)
def project(p):
 q=np.c_[p,np.ones(len(p))]@H.T
 return q[:,:2]/q[:,2,None]
def hull(p):
 p=sorted(set(map(tuple,p)))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lo=[];up=[]
 for a in p:
  while len(lo)>1 and cross(lo[-2],lo[-1],a)<=0:lo.pop()
  lo.append(a)
 for a in reversed(p):
  while len(up)>1 and cross(up[-2],up[-1],a)<=0:up.pop()
  up.append(a)
 return lo[:-1]+up[:-1]
mp=root/'data/board-sources/nxp-frdm-mcxn236/ar-reference/component-map.json'
revpath=mp.parent/'revision-compatibility-review.json'; rev=json.loads(revpath.read_text())
conflict=set()
for changes in [rev['b1_changes'],rev['c_changes']]:
 for key,values in changes.items():
  if isinstance(values,list):conflict.update(v.split(':')[0] for v in values)
glb=root/'data/board-sources/nxp-frdm-mcxn236/ar-reference/frdm-mcxn236-rev-c-source-candidate.glb'
tris,labels,colors,records=load_triangles(glb,json.loads(mp.read_text()))
population_path=root/'data/board-sources/nxp-frdm-mcxn236/structured-rev-c/components.json'
population={r['refdes']:r for r in json.loads(population_path.read_text())['components']}
catalog=[];draw=ImageDraw.Draw(im)
for idx,c in records.items():
 points=tris[labels==idx].reshape(-1,3)
 if not len(points):continue
 poly=hull(project(points[:,[0,2]]))
 source_dnp=population[c['reference']]['dnp_explicit_in_bom']
 suppressed=c['reference'] in conflict or c['side']!='top' or source_dnp
 record={'source_candidate_component_id':c['component_id'],'reference':c['reference'],'source_side':c['side'],'polygon_xy_pixels':[list(p) for p in poly],'height_bounds_metres':[float(points[:,1].min()),float(points[:,1].max())],'status':'suppressed_revision_sensitive_reference_or_bottom' if suppressed else 'candidate_planar_projection_second_review_required','installed_identity_confirmed':False,'source_geometry_quality':c['model_quality']}
 catalog.append(record)
 record['source_dnp']=source_dnp
 if source_dnp and c['reference'] not in conflict and c['side']=='top':
  record['status']='suppressed_source_dnp; specimen_population_not_asserted'
 if not suppressed and len(poly)>2:
  draw.line(poly+[poly[0]],fill='#ff6600',width=3)
  draw.text(poly[0],c['reference'],fill='#ffff00',stroke_width=1,stroke_fill='black')
for name,p in zip(reference['pose_landmark_ids'],dst):
 x,y=p;draw.ellipse((x-10,y-10,x+10,y+10),outline='#00ffff',width=4);draw.text((x+12,y),name,fill='#00ffff')
doc={'schema_version':'1.0','image_path':reference['image_path'],'image_sha256':hashlib.sha256(raw).hexdigest(),'image_dimensions':[w,h],'coordinate_frame':'upright_exif_transposed_image_pixels','method':'planar_homography_of_GL B_world_XZ_mesh_convex_hull'.replace('GL B','GLB'),'not_ground_truth':True,'training_export_eligible':False,'production_eligible':False,'camera_calibration_verified':False,'height_parallax_accounted':False,'landmark_kind':'mounting_hole_centres_not_board_corners','landmark_ids':reference['pose_landmark_ids'],'metric_landmarks_metres':src.tolist(),'image_landmarks_pixels':dst.tolist(),'homography':H.tolist(),'anchor_reprojection_error_pixels':np.linalg.norm(project(src)-dst,axis=1).tolist(),'anchor_uncertainty_pixels':12,'boundary_uncertainty_pixels':None,'uncertainty_note':'Height-dependent parallax and C/B placement differences unknown. Convex hull includes leads, concavities and hidden geometry, not visible-body masks. Four fitted anchors do not independently verify alignment.','source_glb_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'component_map_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'revision_review_sha256':hashlib.sha256(revpath.read_bytes()).hexdigest(),'suppressed_changed_references':sorted(conflict),'catalog':catalog}
(out/'nxp-planar-proposals.json').write_text(json.dumps(doc,indent=2)+'\n')
im.save(out/'nxp-planar-proposals-overlay.jpg',quality=94)
print(json.dumps({'records':len(catalog),'visible_candidates':sum(c['status'].startswith('candidate') for c in catalog),'max_anchor_error':max(doc['anchor_reprojection_error_pixels']),'dims':[w,h]}))
