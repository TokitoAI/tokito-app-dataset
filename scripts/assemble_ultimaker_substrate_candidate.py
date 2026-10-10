"""Combine source PCB substrate with provisional Antigravity component bodies."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from render_ar_multiview import load_triangles

ROOT = Path(__file__).resolve().parents[1]


def assemble(component_glb, component_map, output):
    source = ROOT / 'data/board-sources/ultimainboard-2.1.4/generated-kicad/board-only.glb'
    board, _, _, _ = load_triangles(source, {'components': []})
    low, high = board.min(axis=(0,1)), board.max(axis=(0,1))
    if not np.allclose((high-low)[[0,2]], [.175,.079], atol=.0002):
        raise ValueError('Source substrate dimensions mismatch')
    offset = np.array([(low[0]+high[0])/2, high[1], (low[2]+high[2])/2])
    board = board - offset
    mapping = json.loads(Path(component_map).read_text())
    triangles, labels, colors, records = load_triangles(component_glb, mapping)
    groups = [('pcb:substrate', board, [.08,.32,.16,1])]
    for label, record in records.items():
        groups.append((record['glb_selector'], triangles[labels == label],
                       list(colors[labels == label][0]) + [1]))
    document = {'asset': {'version':'2.0','generator':'Tokito source substrate candidate'},
                'scene':0,'scenes':[{'nodes':[0]}],
                'nodes':[{'name':'Ultimaker_candidate_root','children':[]}],
                'meshes':[],'materials':[],'accessors':[],'bufferViews':[],
                'buffers':[{'byteLength':0}]}
    binary = bytearray()
    for name, faces, color in groups:
        positions = faces.reshape(-1,3).astype('<f4')
        if not len(positions):
            raise ValueError('Empty component geometry')
        normals = np.cross(faces[:,1]-faces[:,0], faces[:,2]-faces[:,0])
        lengths = np.linalg.norm(normals,axis=1)
        normals = normals / np.maximum(lengths[:,None],1e-15)
        normals = np.repeat(normals,3,axis=0).astype('<f4')
        attributes = {}
        for semantic, values in [('POSITION',positions),('NORMAL',normals)]:
            view = len(document['bufferViews'])
            payload = values.tobytes()
            document['bufferViews'].append({'buffer':0,'byteOffset':len(binary),
                                           'byteLength':len(payload),'target':34962})
            binary.extend(payload)
            accessor = {'bufferView':view,'componentType':5126,'count':len(values),'type':'VEC3'}
            if semantic == 'POSITION':
                accessor.update(min=values.min(axis=0).tolist(),max=values.max(axis=0).tolist())
            attributes[semantic] = len(document['accessors'])
            document['accessors'].append(accessor)
        index = len(document['meshes'])
        document['materials'].append({'name':name,'doubleSided':True,
            'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':0,'roughnessFactor':.7}})
        document['meshes'].append({'name':name,'primitives':[{'attributes':attributes,'material':index}]})
        document['nodes'][0]['children'].append(len(document['nodes']))
        document['nodes'].append({'name':name,'mesh':index,
            'extras':{'geometry_status':'source_substrate' if index==0 else 'provisional_box_body'}})
    document['buffers'][0]['byteLength'] = len(binary)
    chunk = json.dumps(document,separators=(',',':')).encode()
    chunk += b' ' * (-len(chunk)%4)
    binary.extend(b'\0' * (-len(binary)%4))
    raw = (struct.pack('<III',0x46546c67,2,28+len(chunk)+len(binary))
           + struct.pack('<II',len(chunk),0x4e4f534a)+chunk
           + struct.pack('<II',len(binary),0x004e4942)+binary)
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(raw)
    digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    provenance = {'release_eligible':False,'photo_registration_verified':False,
        'board_source_sha256':digest(source),'component_candidate_sha256':digest(component_glb),
        'component_map_sha256':digest(component_map),'output_sha256':digest(output),
        'source_to_centered_top_plane_translation_metres':(-offset).tolist(),
        'substrate_thickness_metres':float(high[1]-low[1]),
        'selectable_components':len(records),
        'limitations':['Component positions/identities remain Antigravity provisional candidates',
                       'Source substrate thickness differs from nominal stackup by 0.16 mm',
                       'Physical photo registration and flip tracking unverified']}
    output.with_suffix('.provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(provenance))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component-glb',required=True)
    parser.add_argument('--component-map',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args()
    assemble(args.component_glb,args.component_map,args.output)
