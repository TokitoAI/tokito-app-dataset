import json,struct,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'data/board-sources/ultimainboard-2.1.4').exists())
def load(p):
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);sz=struct.unpack_from('<I',raw,20+n)[0];return d,raw[28+n:28+n+sz]
a,ab=load(R/'data/board-sources/ultimainboard-2.1.4/ar-source-candidate/ultimaker-source-selectable.glb');b,bb=load(H/'ultimaker-source-contact-selectable-candidate.glb');assert bb[:len(ab)]==ab
assert b['nodes'][1:len(a['nodes'])]==a['nodes'][1:]
for field in ['meshes','materials','accessors','bufferViews']:assert b[field][:len(a[field])]==a[field]
owners={};meshowners={};refs=[]
for i,n in enumerate(b['nodes']):
 if not n.get('name','').startswith('ref:'):continue
 ref=n['name'][4:];refs.append(ref);stack=[i];has=False
 while stack:
  j=stack.pop();assert j not in owners;owners[j]=ref;node=b['nodes'][j];stack.extend(node.get('children',[]))
  if 'mesh' in node:
   m=node['mesh'];assert m not in meshowners;meshowners[m]=ref;has=True
 assert has
assert len(refs)==len(set(refs))==570
report={'original_binary_buffer_preserved':True,'original_meshes_materials_nodes_preserved':True,'selectable_reference_count':len(refs),'independent_node_ownership':True,'independent_mesh_ownership':True,'geometry_only_not_photo_registration':True}
(H/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
