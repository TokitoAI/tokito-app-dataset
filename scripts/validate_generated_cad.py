"""Check generated CAD file integrity, DRC status and board-only 3D geometry."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]


def check_file(path, digest, size=None):
    raw = path.read_bytes()
    if raw.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        assert f'oid sha256:{digest}\n'.encode() in raw, path
        if size is not None:
            assert f'size {size}\n'.encode() in raw, path
        return None
    assert hashlib.sha256(raw).hexdigest() == digest, path
    assert size is None or len(raw) == size, path
    return raw


def main():
    manifests = sorted((ROOT / 'data/board-sources').glob('**/generated-kicad/provenance.json'))
    assert len(manifests) == 3
    total, payloads = 0, 0
    for path in manifests:
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data['status'] == 'generated_candidate_requires_engineering_review'
        assert data['drc']['fabrication_approved'] is False
        check_file(ROOT / data['source']['path'], data['source']['sha256'])
        names = set()
        for item in data['generated_files']:
            name = item['path']
            assert name not in names and not Path(name).is_absolute() and '..' not in Path(name).parts
            names.add(name)
            raw = check_file(path.parent / name, item['sha256'], item['bytes'])
            total += 1
            payloads += raw is not None
            if raw is not None and name == 'board-only.step':
                assert raw.startswith(b'ISO-10303-21;')
                assert b'AUTOMOTIVE_DESIGN' in raw and b'MANIFOLD_SOLID_BREP' in raw
            if raw is not None and name == 'board-only.glb':
                assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
                length, kind = struct.unpack_from('<II', raw, 12)
                assert kind == 0x4e4f534a
                gltf = json.loads(raw[20:20+length])
                positions = [gltf['accessors'][primitive['attributes']['POSITION']]
                             for mesh in gltf['meshes'] for primitive in mesh['primitives']]
                assert positions and all(accessor['type'] == 'VEC3' for accessor in positions)
                mins = [min(accessor['min'][axis] for accessor in positions) for axis in range(3)]
                maxs = [max(accessor['max'][axis] for accessor in positions) for axis in range(3)]
                assert all(math.isfinite(v) for v in mins + maxs)
                extents = [(upper-lower)*1000 for lower, upper in zip(mins, maxs)]
                assert all(abs(a-b) < 0.2 for a, b in zip(extents, data['board_only_3d']['xyz_extent_mm']))
        assert {'board-only.step', 'board-only.glb', 'drc-report.json', 'pcb-stats.json'} <= names
        assert any(name.endswith('.kicad_pcb') for name in names)
        assert any(name.endswith('.drl') for name in names)
        drc = json.loads((path.parent / data['drc']['report']).read_text(encoding='utf-8'))
        assert dict(Counter(item['severity'] for item in drc['violations'])) == data['drc']['violation_counts_by_severity']
        assert len(drc['unconnected_items']) == data['drc']['unconnected_item_count']
        stats = json.loads((path.parent / 'pcb-stats.json').read_text(encoding='utf-8'))['board']
        assert stats['has_outline'] is True
        for key, target in [('width', 'width_mm'), ('height', 'height_mm'), ('board_thickness', 'thickness_mm')]:
            assert abs(float(stats[key].split()[0])-data['pcb_statistics'][target]) < 0.0001
        print(path.parent.relative_to(ROOT), 'integrity and provisional DRC status checked')
    print(f'Validated {total} generated files ({payloads} full payloads, {total-payloads} Git LFS identities).')


if __name__ == '__main__':
    main()
