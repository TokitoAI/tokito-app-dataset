import pcbnew,sys,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'data/board-sources/ultimainboard-2.1.4').exists());base=H/'library-models';source=R/'data/board-sources/ultimainboard-2.1.4/generated-kicad/Ultimainboard-2.1.4.imported.kicad_pcb';b=pcbnew.LoadBoard(str(source));records=[]
for f in b.GetFootprints():
 ref=f.GetReference()
 if ref not in ['U9','J34']:continue
 rel='Package_TO_SOT_SMD.3dshapes/SOT-23-5.step' if ref=='U9' else 'Connector_JST.3dshapes/JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical.step';p=base/rel
 m=pcbnew.FP_3DMODEL();m.m_Filename=str(p).replace('\\','/');m.m_Scale=pcbnew.VECTOR3D(1,1,1);m.m_Rotation=pcbnew.VECTOR3D(0,0,0 if ref=='U9' else 180);m.m_Offset=pcbnew.VECTOR3D(0 if ref=='U9' else 1.25,0,0);f.Models().clear();f.Models().append(m)
 records.append({'reference':ref,'step_library_path':str(p),'step_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'footprint_rotation_degrees':f.GetOrientationDegrees(),'model_rotation_degrees':[0,0,0 if ref=='U9' else 180],'model_offset_mm':[0 if ref=='U9' else 1.25,0,0],'package_match':'source LP2985 DBV SOT23-5 package' if ref=='U9' else 'source B2B-XH-A two-pin 2.5mm vertical connector','photographed_population_verified':False,'library_geometry_not_manufacturer_metrology':True})
assert len(records)==2
out=H/'Ultimainboard-2.1.4.library-model-candidate.kicad_pcb';pcbnew.SaveBoard(str(out),b);(H/'library-model-provenance.json').write_text(json.dumps({'original_pcb_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'modified_copy_pcb_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'library_models':records},indent=2));print('prepared isolated board copy')
