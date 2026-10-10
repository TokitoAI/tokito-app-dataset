"""Verify provenance and conservative view claims for the iQOO follow-up clips."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/video-captures/2026-10-10/physical-view-followup/manifest.json'


def validate(path=MANIFEST):
    manifest_path = Path(path).resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['training_export_eligible'] or manifest['metric_pose_verified'] or manifest['continuous_flip_verified']:
        raise ValueError('Follow-up clips cannot activate training or metric pose')
    if len(manifest['recordings']) != 4:
        raise ValueError('Expected one new clip for each active board')
    families = set()
    result = []
    for row in manifest['recordings']:
        if row['board_family'] in families:
            raise ValueError('Duplicate board family')
        families.add(row['board_family'])
        target = (ROOT / row['path']).resolve()
        if not target.is_relative_to(ROOT) or not target.is_file():
            raise ValueError('Missing or out-of-repository source clip')
        if not _matches_payload_or_lfs_pointer(target, row['sha256'], row['bytes']):
            raise ValueError('Source payload or LFS pointer mismatch: ' + row['path'])
        if row['underside_seen'] or row['four_oblique_sides_seen'] or row['continuous_rotate_flip_seen']:
            raise ValueError('Unreviewed view promoted to verified')
        if row['display_rotation_degrees'] != -90 or row['codec'] != 'hevc':
            raise ValueError('Unexpected camera video metadata')
        for review in row['review_contact_sheets']:
            sheet = (ROOT / review['path']).resolve()
            if (not sheet.is_relative_to(ROOT) or not sheet.is_file()
                    or not _matches_payload_or_lfs_pointer(sheet, review['sha256'])):
                raise ValueError('Missing or changed review sheet: ' + review['path'])
        result.append({'board_family': row['board_family'], 'sha256_verified': True,
                       'duration_seconds': row['duration_seconds'],
                       'training_export_eligible': False})
    return result


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


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
    return (actual_size == size if size is not None else True) and _sha256(path) == digest


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
