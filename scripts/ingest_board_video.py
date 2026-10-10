"""Preserve source video lineage and extract upright frames at actual source PTS.

Extraction never creates training labels or assigns independent test specimens.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True, encoding='utf-8').stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--board-family', required=True)
    parser.add_argument('--specimen-id', required=True)
    parser.add_argument('--session-id', required=True)
    parser.add_argument('--source-device-path', required=True)
    parser.add_argument('--expected-source-sha256', required=True)
    parser.add_argument('--timestamps', default='0,2,4,6,8,10,12,14,16,17.5')
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    args = parser.parse_args()
    video, output = args.video.resolve(), args.output.resolve()
    if not video.is_relative_to(ROOT) or not output.is_relative_to(ROOT):
        raise ValueError('Video and dataset output must stay inside this repository')
    digest = sha(video)
    if digest != args.expected_source_sha256:
        raise ValueError('Source video differs from the device-verified digest')
    class_rows = json.loads((ROOT/'data/photo-model/board-class-display-names.json').read_text(encoding='utf-8'))['ordered_classes']
    families = [row['internal_key'] for row in class_rows]
    # Class name fields are not tied to a display label or inferred from filenames.
    if args.board_family not in families:
        raise ValueError('Unknown board family')
    class_id = next(row['class_id'] for row in class_rows if row['internal_key'] == args.board_family)
    probe = json.loads(command([args.ffprobe, '-v', 'error', '-select_streams', 'v:0',
                                '-show_streams', '-show_format', '-show_frames', '-of', 'json', str(video)]))
    stream = probe['streams'][0]
    frames = probe['frames']
    times = [float(row['best_effort_timestamp_time']) for row in frames]
    if not times or any(not math.isfinite(t) for t in times) or times != sorted(times):
        raise ValueError('Decoded frame presentation timestamps are invalid')
    requested = sorted({float(t) for t in args.timestamps.split(',')})
    if len(requested) > 32 or any(not math.isfinite(t) or t < 0 or t > times[-1]-times[0] for t in requested):
        raise ValueError('Keyframe request is outside the decoded source timeline')
    selected = sorted({min(range(len(times)), key=lambda i: abs(times[i]-(times[0]+target))) for target in requested})
    decoded = ROOT/'work/video-intake'/digest[:16]
    decoded.mkdir(parents=True, exist_ok=True)
    select_filter = 'select=' + '+'.join(f'eq(n\\,{i})' for i in selected)
    command([args.ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
             '-i', str(video), '-map', '0:v:0', '-vf', select_filter,
             '-fps_mode', 'vfr', '-q:v', '2', str(decoded/'frame_%04d.jpg')])
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for ordinal, source_index in enumerate(selected, start=1):
        decoded_path = decoded/f'frame_{ordinal:04d}.jpg'
        pts = times[source_index]
        filename = f'{video.stem}_n{source_index:06d}_pts{round(pts*1000):08d}ms.jpg'
        target = output/filename
        shutil.copyfile(decoded_path, target)
        with Image.open(target) as image:
            width, height = image.size
            image.verify()
        rows.append({'id': f'{video.stem}:n{source_index:06d}', 'image_path': target.relative_to(ROOT).as_posix(),
                     'image_sha256': sha(target), 'image_width': width, 'image_height': height,
                     'source_frame_index': source_index, 'source_pts_seconds': pts,
                     'source_video_sha256': digest, 'physical_specimen_id': args.specimen_id,
                     'capture_session_id': args.session_id, 'board_family_hint': args.board_family,
                     'board_class_id_hint': class_id, 'source_offset_seconds': pts-times[0],
                     'board_box_review_status': 'not_reviewed', 'part_review_status': 'not_reviewed',
                     'pin_review_status': 'not_reviewed', 'training_export_eligible': False})
    rotation = next((side['rotation'] for side in stream.get('side_data_list', []) if 'rotation' in side), 0)
    report = {'schema_version': '1.0', 'release_eligible': False, 'evaluation_valid': False,
              'source_video': {'path': video.relative_to(ROOT).as_posix(), 'sha256': digest,
                               'bytes': video.stat().st_size, 'device_path': args.source_device_path},
              'video': {key: stream.get(key) for key in ['codec_name','pix_fmt','width','height','r_frame_rate','avg_frame_rate','duration','nb_frames','color_space','color_transfer','color_primaries']},
              'decoded_frame_count': len(frames), 'source_display_rotation_degrees': rotation,
              'frame_coordinate_contract': 'FFmpeg default display-matrix autorotation; saved upright JPEG pixels',
              'ffmpeg_version': command([args.ffmpeg, '-version']).splitlines()[0],
              'extractor_sha256': sha(Path(__file__)), 'camera_calibration': None,
              'physical_specimen_id': args.specimen_id, 'capture_session_id': args.session_id,
              'specimen_assignment_status': 'same_bench_specimen_assumed_for_leakage_control',
              'all_frames_share_split_group': True, 'keyframes': rows,
              'limits': ['Frames remain outside training until annotation and coverage review',
                         'Adjacent frames and previous captures of this specimen are not independent test boards',
                         'Video timestamps are measured; camera intrinsics and metric pose are not supplied by extraction']}
    (output/'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({'keyframes': len(rows), 'source_decoded_frames': len(frames),
                      'duration_seconds': stream.get('duration'), 'upright_size': [rows[0]['image_width'], rows[0]['image_height']]}))


if __name__ == '__main__':
    main()
