"""Name actual source component subtrees for independent AR highlighting."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def index(source, output):
    raw = Path(source).read_bytes()
    length, kind = struct.unpack_from('<II', raw, 12)
    if kind != 0x4e4f534a:
        raise ValueError('Missing JSON chunk')
    document = json.loads(raw[20:20+length])
    inventory = ROOT / 'data/board-sources/ultimainboard-2.1.4/structured-source/components.json'
    refs = {row['SOURCEDESIGNATOR'] for row in json.loads(inventory.read_text())}
    nodes = document['nodes']
    matches, owners, mesh_owners = {}, {}, {}
    for i, node in enumerate(nodes):
        ref = node.get('name')
        if ref not in refs:
            continue
        if ref in matches:
            raise ValueError(f'Duplicate source reference {ref}')
        stack, seen, meshes = [i], set(), set()
        while stack:
            child = stack.pop()
            if child in seen or child in owners:
                raise ValueError('Shared component node')
            seen.add(child)
            owners[child] = ref
            current = nodes[child]
            stack.extend(current.get('children', []))
            if 'mesh' in current:
                mesh = current['mesh']
                if mesh in mesh_owners:
                    raise ValueError('Shared component mesh')
                mesh_owners[mesh] = ref
                meshes.add(mesh)
        if not meshes:
            continue
        node['name'] = 'ref:' + ref
        node.setdefault('extras', {})['tokito_component'] = {
            'reference':ref,'mapping_status':'source_design_geometry; photo_correspondence_pending'}
        matches[ref] = {'glb_selector':node['name'],'mesh_indices':sorted(meshes),
                        'node_indices':sorted(seen)}
    chunk = json.dumps(document,separators=(',',':')).encode()
    chunk += b' ' * (-len(chunk)%4)
    tail = raw[20+length:]
    updated = struct.pack('<III',0x46546c67,2,20+len(chunk)+len(tail))
    updated += struct.pack('<II',len(chunk),0x4e4f534a)+chunk+tail
    output = Path(output)
    output.write_bytes(updated)
    report = {'release_eligible':False,'source_geometry_only':True,
              'photo_correspondence_verified':False,
              'source_glb_sha256':hashlib.sha256(raw).hexdigest(),
              'source_inventory_sha256':hashlib.sha256(inventory.read_bytes()).hexdigest(),
              'output_sha256':hashlib.sha256(updated).hexdigest(),
              'selectable_source_references':len(matches),
              'references_without_selectable_geometry':sorted(refs-set(matches)),
              'components':matches}
    output.with_suffix('.index.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(matches)} independently selectable source references; {len(refs-set(matches))} missing bodies')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('output')
    args = parser.parse_args()
    index(args.source,args.output)
