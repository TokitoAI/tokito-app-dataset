"""Check saved AR joins and provenance without downloading GLB binaries.

Use build_ar_alignment_dataset.py --glb <cached asset> --check for the full
mesh/subtree audit. This metadata check does not establish camera accuracy.
"""
from collections import Counter

from build_ar_alignment_dataset import AR, ROOT, anchors, content_sha, read, sha


def main():
    dataset = read(ROOT/'data/ar-alignment/manifest.json')
    assert not dataset['release_eligible'] and not dataset['evaluation_valid']
    assert not dataset['training_policy']['production_training_export_allowed']
    for path, expected in dataset['inputs'].items():
        assert sha(ROOT/path) == expected, f'AR input changed: {path}'
    source_manifest = read(AR/'digital-twin-manifest.json')
    component_map = read(AR/'component-map.json')
    population = {c['refdes']: c for c in read(ROOT/'data/board-sources/nxp-frdm-mcxn236/structured-rev-c/components.json')['components']}
    for entry in read(AR/'provenance.json')['files']:
        assert sha(AR/entry['path']) == entry['sha256']
    asset = dataset['cad_assets'][0]
    assert asset['asset_id'] == source_manifest['assetId'] == component_map['asset_id']
    assert asset['glb_sha256'] == source_manifest['glbSha256']
    source_components = {c['component_id']: c for c in component_map['components'] if c['needs_3d_body']}
    assert set(asset['component_targets']) == set(source_components)
    assert asset['verified_independent_component_meshes'] == len(source_components)
    assert len({t['selector'] for t in asset['component_targets'].values()}) == len(source_components)
    for identifier, target in asset['component_targets'].items():
        assert target['source_dnp'] == population[source_components[identifier]['reference']]['dnp_explicit_in_bom']
        assert not target['physical_population_confirmed']
    counts, instance_ids, image_paths = Counter(), set(), set()
    for image in dataset['images']:
        assert image['image_path'] not in image_paths
        image_paths.add(image['image_path'])
        assert content_sha(ROOT/image['image_path']) == image['image_sha256']
        counts['paired_metric_landmarks'] += len(image['calibration_landmarks'])
        counts['instances'] += len(image['instances'])
        counts['unparented_contacts'] += len(image['unparented_contacts'])
        for instance in image['instances']:
            assert instance['instance_id'] not in instance_ids
            instance_ids.add(instance['instance_id'])
            counts['reviewed_body_polygons'] += instance['visible_body_polygon_xy_normalized'] is not None
            counts['candidate_mesh_bindings'] += instance['cad_binding'] is not None
            counts['photo_located_parented_contacts'] += sum(p.get('photo_bbox_xyxy_pixels') is not None for p in instance['pins'])
            binding = instance['cad_binding']
            if binding:
                source = source_components[binding['source_component_id']]
                assert binding['selector'] == source['glb_selector']
                assert binding['asset_id'] == asset['asset_id'] and binding['glb_sha256'] == asset['glb_sha256']
                assert source['reference'] == instance['observed_reference_designator']
                assert binding['mapping_status'] == 'source_candidate_photographed_revision_unverified'
                assert not binding['installed_order_code_confirmed']
                assert binding['source_dnp'] == population[source['reference']]['dnp_explicit_in_bom']
    assert dict(counts) == dataset['coverage']
    scan = read(ROOT/'data/phone-captures/2026-10-10/reviewed-scan-references.json')
    by_ref = {c['reference']: c for c in component_map['components']}
    for template in scan['templates']:
        if 'pose_corners_normalized' in template:
            saved = next(i for i in dataset['images'] if i['image_path'] == template['image_path'])
            assert saved['calibration_landmarks'] == anchors(template, by_ref)
            assert saved['asset_anchor_override_required']
    synthetic_path = ROOT/'data/ar-alignment/synthetic-nxp-provenance.json'
    if synthetic_path.exists():
        synthetic = read(synthetic_path)
        assert not synthetic['release_eligible'] and not synthetic['evaluation_valid']
        assert synthetic['source_glb_sha256'] == asset['glb_sha256']
        assert synthetic['population_profile']=='source-bom'
        assert synthetic['population_source_sha256']==sha(ROOT/'data/board-sources/nxp-frdm-mcxn236/structured-rev-c/components.json')
        assert synthetic['source_dnp_body_count']==sum(t['source_dnp'] for t in asset['component_targets'].values())
        assert len({v['u1_mask_id'] for v in synthetic['views']})==1
        assert next(v for v in synthetic['views'] if v['view']=='bottom')['u1_visible_pixels']==0
        assert content_sha(ROOT/synthetic['archive_path']) == synthetic['archive_sha256']
        assert {v['view'] for v in synthetic['views']} == set(dataset['multiview_coverage']['required_view_slots'])
    print(f'Validated AR metadata: {len(source_components)} source mesh targets, {counts["reviewed_body_polygons"]} reviewed real masks, {counts["paired_metric_landmarks"]} metric anchor pairs. GLB geometry verification is a separate check.')


if __name__ == '__main__':
    main()
