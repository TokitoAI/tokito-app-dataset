import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_ar_alignment_dataset import AR, ROOT, anchors, audit_nodes, read, reviewed_polygon
from render_ar_multiview import camera, load_triangles, rasterize


class AlignmentContracts(unittest.TestCase):
    def test_unreviewed_nxp_bottom_view_is_preserved_without_training_negatives(self):
        manifest = read(ROOT/'data/ar-alignment/manifest.json')
        path = 'data/phone-captures/2026-10-10/IMG_20261010_192033.jpg'
        image = next(row for row in manifest['images'] if row['image_path'] == path)
        self.assertEqual(image['component_coverage'], 'unreviewed')
        self.assertEqual(image['instances'], [])
        self.assertEqual(image['calibration_landmarks'], [])
        self.assertEqual(image['view_metadata']['view_slot'], 'bottom')
        self.assertIsNone(image['view_metadata']['camera_calibration_id'])
        self.assertEqual(manifest['multiview_coverage']['reviewed_real_view_count'], 6)
        self.assertEqual(manifest['multiview_coverage']['specimens_with_all_required_real_views'], 0)

    def test_nxp_source_candidate_masks_attach_to_existing_photo_record(self):
        manifest = read(ROOT/'data/ar-alignment/manifest.json')
        path = 'data/photo-model/photos/raw/IMG_20261009_221755_1.jpg'
        matches = [row for row in manifest['images'] if row['image_path'] == path]
        self.assertEqual(len(matches), 1)
        image = matches[0]
        instances = {item['instance_id']: item for item in image['instances']}
        for ref, part_number in [('U1', 'MCXN236VDFT'), ('U8', 'LPC55S69JEV98'), ('U12', 'W25Q64JVSSIQ')]:
            instance = instances[f'IMG_20261009_221755_1.jpg:{ref}']
            self.assertIn(part_number, instance['observed_label'])
            self.assertIsNotNone(instance['visible_body_polygon_xy_normalized'])
            self.assertEqual(instance['cad_binding']['mapping_status'], 'source_candidate_photographed_revision_unverified')
            self.assertFalse(instance['cad_binding']['installed_order_code_confirmed'])

    def test_esp32_photo_masks_keep_unmapped_parts_separate_from_verified_u2(self):
        manifest = read(ROOT/'data/ar-alignment/manifest.json')
        path = 'data/phone-captures/2026-10-10/IMG_20261010_092144.jpg'
        image = next(row for row in manifest['images'] if row['image_path'] == path)
        instances = {item['instance_id']: item for item in image['instances']}
        u2 = instances['IMG_20261010_092144.jpg:U2']
        self.assertEqual(u2['class_name'], 'integrated_circuit')
        self.assertIsNotNone(u2['visible_body_polygon_xy_normalized'])
        self.assertEqual(u2['observed_reference_designator'], 'U2')
        for suffix, class_name in [('RF_MODULE','rf_module'),('USB','usb_connector'),
                                   ('BOOT_SWITCH','switch'),('EN_SWITCH','switch')]:
            instance = instances[f'IMG_20261010_092144.jpg:{suffix}']
            self.assertEqual(instance['class_name'], class_name)
            self.assertIsNotNone(instance['visible_body_polygon_xy_normalized'])
            self.assertIsNone(instance['observed_reference_designator'])
            self.assertIsNone(instance['cad_binding'])

    def test_swapping_hole_identities_cannot_silently_change_calibration(self):
        row = next(t for t in read(ROOT/'data/phone-captures/2026-10-10/reviewed-scan-references.json')['templates'] if t['class_id'] == 3)
        components = {c['reference']: c for c in read(AR/'component-map.json')['components']}
        self.assertEqual([a['id'] for a in anchors(row, components)], ['BH1', 'BH4', 'BH2', 'BH3'])
        row = copy.deepcopy(row)
        row['pose_landmark_ids'][0:2] = reversed(row['pose_landmark_ids'][0:2])
        with self.assertRaisesRegex(ValueError, 'inconsistent with CAD source'):
            anchors(row, components)

    def test_body_mask_uses_original_upright_dimensions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'photo.jpg'
            exif = Image.Exif(); exif[274] = 6
            Image.new('RGB', (16,8)).save(path, exif=exif)
            mask = {'image_path': str(path), 'image_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'image_width': 8, 'image_height': 16, 'polygon_xy_pixels': [[1,2],[6,2],[6,12],[1,12]],
                    'observed_reference_designator': 'U1'}
            row = {'image_path': str(path), 'image_sha256': mask['image_sha256']}
            label = {'bbox_xyxy_normalized': [0,0,1,1], 'source': {'observed_refdes': 'U1'}}
            self.assertEqual(len(reviewed_polygon(mask, label, row)), 4)
            mask['image_height'] = 8
            with self.assertRaisesRegex(ValueError, 'dimensions do not match'):
                reviewed_polygon(mask, label, row)

    def test_nxp_usb_masks_keep_revision_candidate_links_cautious(self):
        image = 'data/phone-captures/2026-10-10/IMG_20261010_092203.jpg'
        template = next(t for t in read(ROOT/'data/phone-captures/2026-10-10/reviewed-scan-references.json')['templates']
                        if t['image_path'] == image)
        mask_rows = {m['instance_id']: m for m in read(ROOT/'annotations/ar-instance-masks.json')['masks']}
        labels = {row['id']: row for row in template['labels']}
        for ref in ('J10', 'J11'):
            identifier = f'IMG_20261010_092203.jpg:{ref}'
            mask, label = mask_rows[identifier], labels[identifier]
            self.assertEqual(mask['class_name'], 'usb_connector')
            self.assertEqual(mask['source_component_id'], f'nxp-frdm-mcxn236:C:{ref}')
            self.assertEqual(mask['source_mapping_status'], 'source_candidate_photographed_revision_unverified')
            self.assertFalse(mask['installed_order_code_confirmed'])
            polygon = [[x / mask['image_width'], y / mask['image_height']]
                       for x, y in mask['polygon_xy_pixels']]
            self.assertEqual(len(polygon), 12)
            x1, y1, x2, y2 = label['bbox_xyxy_normalized']
            self.assertTrue(all(x1 <= x <= x2 and y1 <= y <= y2 for x, y in polygon))

    def test_shared_mesh_is_rejected_for_independent_highlighting(self):
        document = {'nodes': [
            {'name': 'ref:U1', 'mesh': 0, 'extras': {'tokito_component': {'reference': 'U1'}}},
            {'name': 'ref:U2', 'mesh': 0, 'extras': {'tokito_component': {'reference': 'U2'}}}],
            'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]}],
            'accessors': [{'count': 3, 'min': [0,0,0], 'max': [1,1,1]}]}
        chunk = json.dumps(document).encode(); chunk += b' ' * (-len(chunk) % 4)
        raw = struct.pack('<III', 0x46546C67, 2, 20+len(chunk)) + struct.pack('<II', len(chunk), 0x4E4F534A) + chunk
        manifest = {'assetId': 'test', 'componentNodePrefix': 'ref:', 'boardIdentity': 'test',
                    'boardRevision': 'A', 'units': 'METRE', 'axes': 'RIGHT_HANDED_Y_UP',
                    'glbBytes': len(raw), 'glbSha256': hashlib.sha256(raw).hexdigest()}
        components = {'asset_id': 'test', 'component_node_prefix': 'ref:', 'board_id': 'test', 'board_revision': 'A',
                      'components': [{'component_id': 'test:A:'+ref, 'reference': ref, 'glb_selector': 'ref:'+ref,
                                      'needs_3d_body': True, 'model_quality': 'test', 'board_position_mm': {'x':0,'y':0},
                                      'component_class': 'integrated_circuit',
                                      'side': 'top'} for ref in ['U1','U2']]}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'test.glb'; path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'share a mesh'):
                audit_nodes(path, manifest, components)

    def test_mask_occlusion_is_depth_tested_independent_of_face_order(self):
        near = np.array([[-.4,-.4,1],[.4,-.4,1],[0,.4,1]])
        triangles = np.stack([near, near*2])
        k = np.array([[20,0,16],[0,20,16],[0,0,1]])
        for order in [[0,1],[1,0]]:
            _, labels, _ = rasterize(triangles[order], np.array([2,3])[order], np.full((2,3), .5),
                                     np.eye(3), np.zeros(3), k, 32, 32)
            self.assertEqual(labels[16,16], 2)
            self.assertFalse(np.any(labels == 3))

    def test_top_and_bottom_cameras_are_rigid_poses_in_one_asset_frame(self):
        for position in [[.05,.16,-.02],[.05,-.16,-.02]]:
            r, t, _ = camera(position, [.05,0,-.02], 640, 896)
            np.testing.assert_allclose(r@r.T, np.eye(3), atol=1e-12)
            self.assertAlmostEqual(np.linalg.det(r), 1.0)
            np.testing.assert_allclose(r@position+t, np.zeros(3), atol=1e-12)

    def test_source_dnp_suppression_restores_visible_part_and_keeps_its_id(self):
        vertices = np.array([[-.4,-.4,1],[.4,-.4,1],[0,.4,1],
                             [-.8,-.8,2],[.8,-.8,2],[0,.8,2]], dtype='<f4')
        document = {'scenes': [{'nodes': [0]}], 'nodes': [{'children': [1,2]},
                    {'name': 'ref:J7', 'mesh': 0}, {'name': 'ref:L10', 'mesh': 1}],
                    'meshes': [{'primitives': [{'attributes': {'POSITION': 0}}]},
                               {'primitives': [{'attributes': {'POSITION': 1}}]}],
                    'bufferViews': [{'buffer': 0, 'byteOffset': 0}, {'buffer': 0, 'byteOffset': 36}],
                    'accessors': [{'bufferView': i, 'type': 'VEC3', 'componentType': 5126, 'count': 3} for i in range(2)]}
        chunk = json.dumps(document).encode(); chunk += b' ' * (-len(chunk)%4)
        binary = vertices.tobytes()
        raw = struct.pack('<III', 0x46546C67, 2, 28+len(chunk)+len(binary)) + struct.pack('<II',len(chunk),0x4E4F534A)+chunk+struct.pack('<II',len(binary),0x004E4942)+binary
        component_map = {'components': [{'component_id': ref, 'reference': ref, 'glb_selector': 'ref:'+ref, 'needs_3d_body': True} for ref in ['J7','L10']]}
        k = np.array([[20,0,16],[0,20,16],[0,0,1]])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'population.glb'; path.write_bytes(raw)
            full = load_triangles(path, component_map)
            populated = load_triangles(path, component_map, {'J7'})
            self.assertEqual(full[3], populated[3])
            _, full_mask, _ = rasterize(*full[:3], np.eye(3), np.zeros(3), k, 32, 32)
            _, fitted_mask, _ = rasterize(*populated[:3], np.eye(3), np.zeros(3), k, 32, 32)
            self.assertEqual(full[3][int(full_mask[16,16])]['component_id'], 'J7')
            self.assertEqual(populated[3][int(fitted_mask[16,16])]['component_id'], 'L10')


if __name__ == '__main__':
    unittest.main()
