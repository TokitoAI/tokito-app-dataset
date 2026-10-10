"""Verify provenance and conservative view claims for supplementary iQOO clips."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/video-captures/2026-10-10/physical-view-followup/additional-flip-clips/manifest.json'


def validate(path=MANIFEST):
    manifest_path = Path(path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['training_export_eligible'] or manifest['metric_pose_verified'] or manifest['continuous_flip_verified']:
        raise ValueError('Supplementary clips cannot activate training or metric pose')
    expected = {'ultimainboard_2_1_4', 'esp32_devkit_30pin_clone'}
    rows = manifest['recordings']
    if {row['board_family'] for row in rows} != expected or len(rows) != len(expected):
        raise ValueError('Expected one supplementary clip for Ultimaker and ESP32')
    result = []
    for row in rows:
        target = (ROOT / row['path']).resolve()
        if not target.is_relative_to(ROOT) or not _matches_payload_or_lfs_pointer(target, row['sha256'], row['bytes']):
            raise ValueError('Source payload or LFS pointer mismatch: ' + row['path'])
        if not row['underside_seen'] or row['four_oblique_sides_seen'] or row['continuous_flip_verified']:
            raise ValueError('Unreviewed view promoted to verified')
        if not row['continuous_flip_video_present']:
            raise ValueError('Expected continuous flip clip presence')
        if row['codec'] != 'hevc' or (row['width'], row['height']) != (1920, 1080):
            raise ValueError('Unexpected camera video metadata')
        review = row['review_contact_sheet']
        sheet = (ROOT / review['path']).resolve()
        if not sheet.is_relative_to(ROOT) or not _matches_payload_or_lfs_pointer(sheet, review['sha256'], review['bytes']):
            raise ValueError('Review sheet payload or LFS pointer mismatch: ' + review['path'])
        result.append({'board_family': row['board_family'], 'sha256_verified': True,
                       'underside_seen': True, 'four_oblique_sides_seen': False,
                       'training_export_eligible': False})
    return result


def _matches_payload_or_lfs_pointer(path, digest, size=None):
    with Path(path).open('rb') as stream:
        prefix = stream.read(256)
    pointer_lines = prefix.splitlines()
    if pointer_lines and pointer_lines[0] == b'version https://git-lfs.github.com/spec/v1':
        fields = dict(line.decode('ascii').split(' ', 1)
                      for line in pointer_lines[1:] if b' ' in line)
        try:
            return (fields.get('oid') == 'sha256:' + digest
                    and (size is None or int(fields.get('size', '-1')) == size))
        except ValueError:
            return False
    actual_size = Path(path).stat().st_size
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    return (actual_size == size if size is not None else True) and hasher.hexdigest() == digest


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
