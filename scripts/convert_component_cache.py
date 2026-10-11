"""Convert an existing compressed training cache to memory-mapped NPY arrays."""
import json
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
manifest_path = root / 'work/component-segmentation-v2/manifest.json'
manifest = json.loads(manifest_path.read_text())
cache = root / manifest['sample_cache']
fields = ('image', 'masks', 'boxes', 'classes', 'background')
for source in sorted(cache.glob('*.npz')):
    target = source.with_suffix('')
    target.mkdir(exist_ok=True)
    with np.load(source, allow_pickle=False) as archive:
        for name in fields:
            output = target / f'{name}.npy'
            if not output.exists():
                np.save(output, archive[name])
    print(source.name, flush=True)
manifest['sample_cache_format'] = 'memory-mapped NPY; uint8 images/masks and bool reviewed-background rasters'
manifest_path.write_text(json.dumps(manifest, indent=2))
