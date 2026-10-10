"""Add an explicitly provisional ESP32 board body; never activate metric anchors."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def add(source, manifest_path, output):
    source = Path(source)
    raw = source.read_bytes()
    length = struct.unpack_from('<I',raw,12)[0]
    document = json.loads(raw[20:20+length])
    offset = 20 + length
    binary_length, kind = struct.unpack_from('<II',raw,offset)
    if kind != 0x004e4942:
        raise ValueError('Expected embedded binary buffer')
    binary = bytearray(raw[offset+8:offset+8+binary_length])
    manifest = json.loads(Path(manifest_path).read_text())
    bounds = manifest['boardPlaneBoundsMetres']
    xmin,xmax = bounds['minimum']['x'],bounds['maximum']['x']
    zmin,zmax = bounds['minimum']['z'],bounds['maximum']['z']
    thickness = bounds['maximum']['y'] - bounds['minimum']['y']
    points = [(x,y,z) for y in (-thickness,0) for z in (zmin,zmax) for x in (xmin,xmax)]
    # Six separate faces with consistent outward winding.
    faces = [(0,1,3),(0,3,2),(4,6,7),(4,7,5),(0,4,5),(0,5,1),
             (2,3,7),(2,7,6),(0,2,6),(0,6,4),(1,5,7),(1,7,3)]
    vertices = [value for face in faces for i in face for value in points[i]]
    binary.extend(b'\0' * (-len(binary)%4))
    payload = struct.pack('<'+str(len(vertices))+'f',*vertices)
    view = len(document['bufferViews'])
    document['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(payload),'target':34962})
    binary.extend(payload)
    accessor = len(document['accessors'])
    document['accessors'].append({'bufferView':view,'componentType':5126,'count':36,'type':'VEC3',
                                 'min':[xmin,-thickness,zmin],'max':[xmax,0,zmax]})
    material = len(document.setdefault('materials',[]))
    document['materials'].append({'name':'provisional_pcb','doubleSided':True,
        'pbrMetallicRoughness':{'baseColorFactor':[.025,.07,.04,1],'metallicFactor':0,'roughnessFactor':.8}})
    mesh = len(document['meshes'])
    document['meshes'].append({'name':'provisional_pcb','primitives':[{'attributes':{'POSITION':accessor},'material':material}]})
    node = len(document['nodes'])
    document['nodes'].append({'name':'pcb:provisional_substrate','mesh':mesh,
        'extras':{'geometry_status':'nominal_rectangular_approximation','calibration_eligible':False,
                  'holes_modeled':False,'specimen_dimensions_verified':False}})
    document['scenes'][document.get('scene',0)]['nodes'].append(node)
    document['buffers'][0]['byteLength'] = len(binary)
    chunk = json.dumps(document,separators=(',',':')).encode()
    chunk += b' ' * (-len(chunk)%4)
    data = struct.pack('<III',0x46546c67,2,28+len(chunk)+len(binary))
    data += struct.pack('<II',len(chunk),0x4e4f534a)+chunk+struct.pack('<II',len(binary),0x004e4942)+binary
    output = Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(data)
    output.with_suffix('.provenance.json').write_text(json.dumps({
        'release_eligible':False,'calibration_eligible':False,'photo_registration_verified':False,
        'source_candidate_sha256':hashlib.sha256(raw).hexdigest(),
        'source_manifest_sha256':hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
        'output_sha256':hashlib.sha256(data).hexdigest(),
        'limitations':['Rectangular substrate only; mounting holes and bevels not modeled',
                       'Dimensions inherited from unverified Antigravity nominal assumptions',
                       'Component bodies and placements still provisional']},indent=2)+'\n')
    print('Provisional ESP32 substrate added; all original component meshes preserved')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('manifest')
    parser.add_argument('output')
    args = parser.parse_args()
    add(args.source,args.manifest,args.output)
