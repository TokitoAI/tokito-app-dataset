"""Render six CAD views with depth-tested instance masks and fixed component IDs.

These are synthetic geometry labels, not phone captures or accuracy evidence.
Requires NumPy/Pillow; all geometry comes from the hash-verified released GLB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw, __version__ as pillow_version

from build_ar_alignment_dataset import AR, ROOT, audit_nodes, read


def local_matrix(node):
    if 'matrix' in node:
        return np.asarray(node['matrix'], dtype=np.float64).reshape((4, 4), order='F')
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    rotation = np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)],
    ])
    result = np.eye(4)
    result[:3, :3] = rotation @ np.diag(node.get('scale', [1, 1, 1]))
    result[:3, 3] = node.get('translation', [0, 0, 0])
    return result


def load_triangles(path, component_map, source_dnp=None, ignore_non_triangle=False):
    raw = Path(path).read_bytes()
    json_size, _ = struct.unpack_from('<II', raw, 12)
    document = json.loads(raw[20:20+json_size])
    offset = 20 + json_size
    binary_size, binary_type = struct.unpack_from('<II', raw, offset)
    if binary_type != 0x004E4942:
        raise ValueError('A GLB binary buffer is required')
    binary = raw[offset+8:offset+8+binary_size]
    types = {5120: '<i1', 5121: '<u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
    sizes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}

    def accessor(index):
        item = document['accessors'][index]
        if 'sparse' in item:
            raise ValueError('Sparse accessor is not supported')
        view = document['bufferViews'][item['bufferView']]
        if view.get('buffer', 0) != 0:
            raise ValueError('External GLB buffer is not supported')
        dtype = np.dtype(types[item['componentType']])
        columns = sizes[item['type']]
        start = view.get('byteOffset', 0) + item.get('byteOffset', 0)
        stride = view.get('byteStride', columns * dtype.itemsize)
        return np.ndarray((item['count'], columns), dtype=dtype, buffer=binary,
                          offset=start, strides=(stride, dtype.itemsize)).copy()

    physical = sorted((c for c in component_map['components'] if c['needs_3d_body']), key=lambda c: c['component_id'])
    records = {i + 2: c for i, c in enumerate(physical)}
    ids = {c['glb_selector']: index for index, c in records.items()}
    hidden = {c['glb_selector'] for c in physical if source_dnp and c['reference'] in source_dnp}
    triangles, labels, colors = [], [], []
    nodes = document['nodes']

    def visit(index, parent, inherited_id):
        node = nodes[index]
        if node.get('name') in hidden:
            return
        matrix = parent @ local_matrix(node)
        label = ids.get(node.get('name'), inherited_id)
        if 'mesh' in node:
            for primitive in document['meshes'][node['mesh']]['primitives']:
                if primitive.get('mode', 4) != 4:
                    if ignore_non_triangle:
                        continue  # Surface review omits line/point primitives; GLB is unchanged.
                    raise ValueError('Only triangle geometry is supported')
                vertices = accessor(primitive['attributes']['POSITION']).astype(np.float64)
                vertices = vertices @ matrix[:3, :3].T + matrix[:3, 3]
                indices = accessor(primitive['indices']).ravel() if 'indices' in primitive else np.arange(len(vertices))
                faces = vertices[indices.reshape(-1, 3)]
                material = document.get('materials', [{}])[primitive.get('material', 0)]
                color = material.get('pbrMetallicRoughness', {}).get('baseColorFactor', [.3, .3, .3, 1])[:3]
                triangles.append(faces)
                labels.extend([label] * len(faces))
                colors.extend([color] * len(faces))
        for child in node.get('children', []):
            visit(child, matrix, label)

    for root in document['scenes'][document.get('scene', 0)]['nodes']:
        visit(root, np.eye(4), 1)  # 0=background, 1=board, 2..=stable component IDs
    return np.concatenate(triangles), np.asarray(labels, dtype=np.uint16), np.asarray(colors), records


def camera(position, target, width, height):
    position, target = np.asarray(position), np.asarray(target)
    forward = target - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [-1., 0., 0.])
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    rotation = np.stack([right, down, forward])
    translation = -rotation @ position
    focal = width * 1.35
    k = np.array([[focal, 0, width/2], [0, focal, height/2], [0, 0, 1.]])
    return rotation, translation, k


def project(points, rotation, translation, intrinsics):
    camera_points = np.asarray(points) @ rotation.T + translation
    uvw = camera_points @ intrinsics.T
    return uvw[..., :2] / uvw[..., 2, None], camera_points[..., 2]


def rasterize(triangles, labels, colors, rotation, translation, intrinsics, width, height):
    screen, depth = project(triangles, rotation, translation, intrinsics)
    image = np.full((height, width, 3), 28, dtype=np.uint8)
    instances = np.zeros((height, width), dtype=np.uint16)
    zbuffer = np.full((height, width), np.inf)
    normals = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
    norms = np.linalg.norm(normals, axis=1)
    normals /= np.maximum(norms[:, None], 1e-16)
    light = np.asarray([-.2, .9, .4]); light /= np.linalg.norm(light)
    shades = .35 + .65 * np.abs(normals @ light)
    face_colors = np.clip(colors * shades[:, None] * 255, 0, 255).astype(np.uint8)
    for index, points in enumerate(screen):
        if np.min(depth[index]) <= 0.005 or not np.isfinite(points).all():
            continue
        x0, y0 = np.maximum(np.floor(points.min(axis=0)).astype(int), [0, 0])
        x1, y1 = np.minimum(np.ceil(points.max(axis=0)).astype(int), [width-1, height-1])
        if x0 > x1 or y0 > y1:
            continue
        a, b, c = points
        denom = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        if abs(denom) < 1e-9:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1+1)+.5, np.arange(y0, y1+1)+.5)
        w0 = ((b[1]-c[1])*(xs-c[0]) + (c[0]-b[0])*(ys-c[1])) / denom
        w1 = ((c[1]-a[1])*(xs-c[0]) + (a[0]-c[0])*(ys-c[1])) / denom
        w2 = 1-w0-w1
        inside = (w0 >= -1e-8) & (w1 >= -1e-8) & (w2 >= -1e-8)
        face_depth = 1 / (w0/depth[index, 0] + w1/depth[index, 1] + w2/depth[index, 2])
        region = zbuffer[y0:y1+1, x0:x1+1]
        visible = inside & (face_depth < region)
        region[visible] = face_depth[visible]
        instances[y0:y1+1, x0:x1+1][visible] = labels[index]
        image[y0:y1+1, x0:x1+1][visible] = face_colors[index]
    return image, instances, zbuffer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--glb', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--height', type=int, default=896)
    parser.add_argument('--population', choices=['source-bom', 'all-source-bodies'], default='source-bom',
                        help='Default suppresses bodies explicitly marked DNP in the acquired Rev C BOM')
    args = parser.parse_args()
    if not 128 <= args.width <= 2048 or not 128 <= args.height <= 2048:
        raise ValueError('Bounded render size must be between 128 and 2048')
    manifest, component_map = read(AR/'digital-twin-manifest.json'), read(AR/'component-map.json')
    audit_nodes(args.glb, manifest, component_map)
    population_file = ROOT/'data/board-sources/nxp-frdm-mcxn236/structured-rev-c/components.json'
    population = {c['refdes']: c for c in read(population_file)['components']}
    if set(population) != {c['reference'] for c in component_map['components']}:
        raise ValueError('CAD references do not match source BOM population records')
    source_dnp = {ref for ref, c in population.items() if c['dnp_explicit_in_bom']}
    triangles, labels, colors, records = load_triangles(args.glb, component_map,
                                                      source_dnp if args.population == 'source-bom' else None)
    target = [.056, .00151, -.0245]
    views = {
        'top': [.056, .16, -.0245], 'bottom': [.056, -.16, -.0245],
        'oblique_positive_board_x': [.176, .14, -.0245],
        'oblique_negative_board_x': [-.064, .14, -.0245],
        'oblique_positive_board_y': [.056, .14, .0955],
        'oblique_negative_board_y': [.056, .14, -.1445],
    }
    scan = read(ROOT/'data/phone-captures/2026-10-10/reviewed-scan-references.json')
    source = next(t for t in scan['templates'] if t['class_id'] == 3)
    landmark_points = [[x, 0., z] for x, z in source['pose_metric_landmarks_metres']]
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=True)
    results, previews = [], []
    for name, position in views.items():
        rotation, translation, k = camera(position, target, args.width, args.height)
        rgb, masks, depth = rasterize(triangles, labels, colors, rotation, translation, k, args.width, args.height)
        image_file, mask_file = output/f'{name}.png', output/f'{name}.instances.png'
        Image.fromarray(rgb).save(image_file)
        Image.fromarray(masks).save(mask_file)
        keypoints, keypoint_depths = project(landmark_points, rotation, translation, k)
        count = CounterPixels(masks)
        component_rows = []
        for index, record in records.items():
            ys, xs = np.where(masks == index)
            component_rows.append({'mask_id': index, 'source_component_id': record['component_id'],
                                   'class_name': record['component_class'],
                                   'source_dnp': record['reference'] in source_dnp,
                                   'included_in_render': args.population == 'all-source-bodies' or record['reference'] not in source_dnp,
                                   'glb_selector': record['glb_selector'], 'source_side': record['side'],
                                   'model_quality': record['model_quality'], 'visible_pixels': count.get(index, 0),
                                   'bbox_xyxy_pixels': [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)] if len(xs) else None})
        landmarks = []
        for identifier, point, uv, point_depth in zip(source['pose_landmark_ids'], landmark_points, keypoints, keypoint_depths):
            in_frame = point_depth > 0 and 0 <= uv[0] < args.width and 0 <= uv[1] < args.height
            occluded = in_frame and depth[int(uv[1]), int(uv[0])] < point_depth - .00015
            landmarks.append({'id': identifier, 'asset_xyz_metres': point, 'image_xy_pixels': uv.tolist(),
                              'geometry_occlusion_status': 'outside_image' if not in_frame else
                              ('nearer_surface_on_ray' if occluded else 'no_nearer_surface_on_ray')})
        results.append({'view': name, 'image': image_file.name, 'mask': mask_file.name,
                        'image_sha256': hashlib.sha256(image_file.read_bytes()).hexdigest(),
                        'mask_sha256': hashlib.sha256(mask_file.read_bytes()).hexdigest(),
                        'camera': {'width': args.width, 'height': args.height, 'intrinsics': k.tolist(),
                                   'asset_to_camera_rotation': rotation.tolist(),
                                   'asset_to_camera_translation_metres': translation.tolist(),
                                   'camera_axes': 'x right, y down, z forward'},
                        'calibration_landmarks': landmarks, 'components': component_rows})
        preview = Image.fromarray(rgb); draw = ImageDraw.Draw(preview)
        draw.text((10, 10), f'SYNTHETIC CAD: {name}', fill='white')
        for landmark in landmarks:
            x, y = landmark['image_xy_pixels']; draw.ellipse((x-3, y-3, x+3, y+3), fill='red')
            draw.text((x+5, y), landmark['id'], fill='white')
        preview.thumbnail((320, 448)); previews.append(preview)
        print(json.dumps({'view': name, 'visible_component_meshes': sum(c['visible_pixels']>0 for c in component_rows)}), flush=True)
    sheet = Image.new('RGB', (960, 896), '#171717')
    for i, preview in enumerate(previews): sheet.paste(preview, ((i%3)*320, (i//3)*448))
    sheet.save(output/'six-view-preview.jpg', quality=95)
    report = {'schema_version': '1.0', 'data_role': 'synthetic_geometry_supervision',
              'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'numpy_version': np.__version__, 'pillow_version': pillow_version,
              'population_profile': args.population,
              'population_source_sha256': hashlib.sha256(population_file.read_bytes()).hexdigest(),
              'source_dnp_body_count': sum(c['reference'] in source_dnp for c in records.values()),
              'release_eligible': False, 'evaluation_valid': False, 'glb_sha256': manifest['glbSha256'],
              'asset_id': manifest['assetId'], 'mask_encoding': 'uint16; 0 background, 1 board, 2.. stable component IDs',
              'renderer': 'depth-tested triangle rasterizer; CAD materials with simple flat lighting',
              'limits': ['Not camera photographs or flip-tracking evidence',
                         'BOM population flags are source design facts; fitted population on the photographed specimen remains unconfirmed',
                         'Approximate/placeholder CAD packages retain their model-quality status',
                         'Actual mask pixels preserve occlusion; bounding boxes are not segmentation masks'],
              'views': results}
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')


def CounterPixels(mask):
    ids, counts = np.unique(mask, return_counts=True)
    return {int(i): int(n) for i, n in zip(ids, counts)}


if __name__ == '__main__':
    main()
