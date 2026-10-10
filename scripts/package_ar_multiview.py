"""Verify rendered camera/mask/identity pairs and package synthetic AR labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile

import numpy as np
from PIL import Image

from build_ar_alignment_dataset import AR, ROOT, read, sha
from render_ar_multiview import project


def package(rendered, output, provenance_path):
    if not output.is_relative_to(ROOT):
        raise ValueError('Dataset archive output must be inside the repository')
    report = read(rendered/'manifest.json')
    if report['release_eligible'] or report['evaluation_valid']:
        raise ValueError('Synthetic render cannot claim real-camera evaluation eligibility')
    if report['generator_sha256'] != sha(ROOT/'scripts/render_ar_multiview.py'):
        raise ValueError('Render does not match the current generator')
    source = read(AR/'digital-twin-manifest.json')
    if report['glb_sha256'] != source['glbSha256'] or report['asset_id'] != source['assetId']:
        raise ValueError('Synthetic render does not match the source asset')
    population_path = ROOT/'data/board-sources/nxp-frdm-mcxn236/structured-rev-c/components.json'
    if report['population_source_sha256'] != sha(population_path):
        raise ValueError('Render population source changed')
    required = read(ROOT/'annotations/multiview-capture-review.json')['required_view_slots']
    if {v['view'] for v in report['views']} != set(required) or len(report['views']) != len(required):
        raise ValueError('Synthetic six-view set is incomplete or has duplicate views')
    components = {c['component_id']: c for c in read(AR/'component-map.json')['components'] if c['needs_3d_body']}
    identity_map, visible, summary, files = None, set(), [], [rendered/'manifest.json', rendered/'six-view-preview.jpg']
    for view in report['views']:
        rgb_path, mask_path = (rendered/view['image']).resolve(), (rendered/view['mask']).resolve()
        if not rgb_path.is_relative_to(rendered) or not mask_path.is_relative_to(rendered):
            raise ValueError('Render media path escapes its source directory')
        if sha(rgb_path) != view['image_sha256'] or sha(mask_path) != view['mask_sha256']:
            raise ValueError('Rendered image/mask digest mismatch')
        mask = np.asarray(Image.open(mask_path))
        width, height = view['camera']['width'], view['camera']['height']
        if mask.dtype != np.uint16 or mask.shape != (height, width) or Image.open(rgb_path).size != (width, height):
            raise ValueError('Mask encoding or render dimensions differ from the camera contract')
        ids = {c['mask_id']: c['source_component_id'] for c in view['components']}
        if len(ids) != len(components) or set(ids.values()) != set(components):
            raise ValueError('Component-ID coverage differs from source geometry')
        if identity_map is not None and ids != identity_map:
            raise ValueError('Component mask IDs changed between views')
        identity_map = ids
        if not set(np.unique(mask)) <= {0, 1, *ids}:
            raise ValueError('Mask contains unknown component IDs')
        for record in view['components']:
            actual = int(np.sum(mask == record['mask_id']))
            if actual != record['visible_pixels']:
                raise ValueError('Visibility metadata differs from depth-tested mask pixels')
            if record['class_name'] != components[record['source_component_id']]['component_class']:
                raise ValueError('Mask class differs from source component type')
            if not record['included_in_render'] and actual:
                raise ValueError('Excluded DNP component has positive mask pixels')
            if actual:
                visible.add(record['source_component_id'])
        camera = view['camera']; rotation = np.asarray(camera['asset_to_camera_rotation']); translation = np.asarray(camera['asset_to_camera_translation_metres'])
        np.testing.assert_allclose(rotation@rotation.T, np.eye(3), atol=1e-10)
        np.testing.assert_allclose(np.linalg.det(rotation), 1, atol=1e-10)
        landmarks = view['calibration_landmarks']
        reprojection, _ = project([l['asset_xyz_metres'] for l in landmarks], rotation, translation, np.asarray(camera['intrinsics']))
        np.testing.assert_allclose(reprojection, [l['image_xy_pixels'] for l in landmarks], atol=1e-8)
        u1 = next(c for c in view['components'] if c['source_component_id'] == 'nxp-frdm-mcxn236:C:U1')
        summary.append({'view': view['view'], 'visible_components': sum(c['visible_pixels']>0 for c in view['components']),
                        'u1_mask_id': u1['mask_id'], 'u1_visible_pixels': u1['visible_pixels']})
        files.extend([rgb_path, mask_path])
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(files):
            info = zipfile.ZipInfo(path.name, date_time=(2026,10,10,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('Synthetic archive CRC validation failed')
    result = {'schema_version': '1.0', 'data_role': report['data_role'], 'release_eligible': False,
              'evaluation_valid': False, 'source_glb_sha256': report['glb_sha256'],
              'generator_sha256': report['generator_sha256'], 'packager_sha256': sha(Path(__file__)),
              'population_profile': report['population_profile'], 'source_dnp_body_count': report['source_dnp_body_count'],
              'population_source_sha256': report['population_source_sha256'],
              'archive_path': output.relative_to(ROOT).as_posix(), 'archive_sha256': sha(output),
              'archive_bytes': output.stat().st_size, 'component_ids_stable_across_views': True,
              'visible_source_components_union': len(visible), 'views': summary, 'limits': report['limits']}
    provenance_path.parent.mkdir(parents=True, exist_ok=True)
    provenance_path.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rendered', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT/'data/ar-alignment/nxp-synthetic-six-view.zip')
    parser.add_argument('--provenance', type=Path, default=ROOT/'data/ar-alignment/synthetic-nxp-provenance.json')
    args = parser.parse_args()
    result = package(args.rendered.resolve(), args.output.resolve(), args.provenance.resolve())
    print(json.dumps({'views': len(result['views']), 'visible_source_components_union': result['visible_source_components_union'],
                      'source_dnp_body_count': result['source_dnp_body_count'], 'archive_bytes': result['archive_bytes']}))


if __name__ == '__main__':
    main()
