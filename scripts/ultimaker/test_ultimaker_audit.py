import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build_ar_alignment_dataset import audit_nodes, read

ar_dir = Path('data/board-sources/ultimainboard-2.1.4/ar-reference')
manifest = read(ar_dir / 'digital-twin-manifest.json')
component_map = read(ar_dir / 'component-map.json')
glb = ar_dir / 'ultimainboard_2_1_4_visible.glb'

targets = audit_nodes(glb, manifest, component_map)
print(f"PASSED AUDIT! Audited {len(targets)} selectable Ultimaker component targets successfully:")
for k, v in targets.items():
    print(f"  {k:35s}: selector={v['selector']:12s}, meshes={v['mesh_ids']}")
