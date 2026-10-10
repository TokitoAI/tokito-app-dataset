"""Create a portable final dataset ZIP from a clean, validated Git checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def package(output, readiness_report):
    report_path = Path(readiness_report).resolve()
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('dataset_construction_complete') is not True or report.get('validation_passed') is not True:
        raise ValueError('Final dataset construction and validation have not been approved in the readiness report')
    revision = git('rev-parse','HEAD').decode().strip()
    if report.get('dataset_commit') != revision:
        raise ValueError('Readiness report does not cover the current dataset commit')
    if git('status','--porcelain').strip():
        raise ValueError('Checkout must be clean before final packaging')
    output = Path(output).resolve()
    temporary = output.with_suffix(output.suffix + '.partial')
    if output.exists() or temporary.exists():
        raise ValueError('Destination exists; choose a new output filename')
    paths = [ROOT / name.decode('utf-8') for name in git('ls-files','-z').split(b'\0') if name]
    for path in paths:
        if not path.resolve().is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f'Invalid tracked asset: {path}')
        with path.open('rb') as stream:
            if stream.read(64).startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise ValueError(f'Unresolved LFS asset: {path.relative_to(ROOT)}; fetch actual files first')
    required = sum(path.stat().st_size for path in paths)
    output.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(output.parent).free < required + 512 * 1024**2:
        raise ValueError('Insufficient free space for a complete portable ZIP')
    records = []
    with zipfile.ZipFile(temporary,'x',compression=zipfile.ZIP_DEFLATED,
                         compresslevel=3,allowZip64=True) as archive:
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            digest = hashlib.sha256()
            with path.open('rb') as source, archive.open('tokito-app-dataset/' + relative,'w',force_zip64=True) as target:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    target.write(chunk)
            records.append({'path':relative,'bytes':path.stat().st_size,'sha256':digest.hexdigest()})
        archive.writestr('tokito-app-dataset/FINAL_READINESS_REPORT.json',report_path.read_bytes())
        archive.writestr('tokito-app-dataset/PORTABLE_FILE_MANIFEST.json',json.dumps(
            {'dataset_commit':revision,'files':records,'contains_actual_lfs_payloads':True},indent=2))
    with zipfile.ZipFile(temporary) as archive:
        if corrupt := archive.testzip():
            raise ValueError(f'ZIP integrity failure: {corrupt}')
    temporary.rename(output)
    with output.open('rb') as stream:
        digest = hashlib.file_digest(stream,'sha256').hexdigest()
    output.with_suffix(output.suffix + '.sha256').write_text(digest + '  ' + output.name + '\n')
    print(f'Final portable dataset: {output} ({output.stat().st_size} bytes, {len(records)} files)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--readiness-report',type=Path,required=True)
    args = parser.parse_args()
    package(args.output,args.readiness_report)
