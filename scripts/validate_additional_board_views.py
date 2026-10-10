"""Verify iQOO capture hashes and conservative per-board view claims."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/video-captures/2026-10-10/physical-view-followup/additional-board-views/manifest.json'


def validate(path=MANIFEST):
    manifest = json.loads(Path(path).resolve().read_text(encoding='utf-8'))
    if manifest['training_export_eligible'] or manifest['metric_pose_verified'] or manifest['continuous_flip_verified']:
        raise ValueError('Additional board views cannot activate training or metric pose')
    rows = manifest['recordings']
    expected_paths = {
        'ultimaker_video_20261010_211129.mp4', 'nxp_video_20261010_211200.mp4',
        'nxp_video_20261010_211217.mp4', 'mixed-esp32-ultimaker_video_20261010_211236.mp4',
    }
    if {Path(row['path']).name for row in rows} != expected_paths or len(rows) != len(expected_paths):
        raise ValueError('Unexpected additional view recordings')
    result = []
    for row in rows:
        target = (ROOT / row['path']).resolve()
        if not target.is_relative_to(ROOT) or not _matches(target, row['sha256'], row['bytes']):
            raise ValueError('Source payload or LFS pointer mismatch: ' + row['path'])
        if row['codec'] != 'hevc' or (row['width'], row['height']) != (1920, 1080):
            raise ValueError('Unexpected camera video metadata')
        claims = row['view_claims']
        if {claim['board_family'] for claim in claims} != set(row['board_families']):
            raise ValueError('Board family and view claims disagree')
        for claim in claims:
            if claim['four_oblique_sides_seen'] or claim['continuous_flip_verified']:
                raise ValueError('Unverified side or continuous-flip claim promoted')
        review = row['review_contact_sheet']
        sheet = (ROOT / review['path']).resolve()
        if not sheet.is_relative_to(ROOT) or not _matches(sheet, review['sha256'], review['bytes']):
            raise ValueError('Review sheet payload or LFS pointer mismatch: ' + review['path'])
        result.append({'path': row['path'], 'sha256_verified': True,
                       'board_families': row['board_families'], 'claims': claims,
                       'training_export_eligible': False})
    return result


def _matches(path, digest, size):
    with Path(path).open('rb') as stream:
        prefix = stream.read(256)
    lines = prefix.splitlines()
    if lines and lines[0] == b'version https://git-lfs.github.com/spec/v1':
        fields = dict(line.decode('ascii').split(' ', 1) for line in lines[1:] if b' ' in line)
        try:
            return fields.get('oid') == 'sha256:' + digest and int(fields.get('size', '-1')) == size
        except ValueError:
            return False
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    return Path(path).stat().st_size == size and hasher.hexdigest() == digest


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
