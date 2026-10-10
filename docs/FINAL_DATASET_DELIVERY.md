# Final portable dataset delivery

User-requested destination: `E:/TokitoDataset/tokito-app-dataset-final.zip`.
Create this only after final data construction and validation, rather than
labeling an incomplete working snapshot as final. Include all tracked dataset
files with actual Git LFS payloads: photographs, videos, annotations, source
schematics/BOM/Gerbers, model assets, scripts and documentation. Git history,
temporary work directories and external account state are excluded.

The export script requires a clean checkout and an independently reviewed
readiness report with `dataset_construction_complete: true`,
`validation_passed: true` and `dataset_commit` equal to the final commit. These
flags are packaging prerequisites, not substitutes for the full goal audit.
Do not generate a passing report while the actual dataset remains incomplete.
Any required external model assets must be materialized in the repository before
export; the script rejects unresolved LFS pointers.

```powershell
python scripts/package_final_dataset.py --output E:/TokitoDataset/tokito-app-dataset-final.zip --readiness-report PATH_TO_REVIEWED_FINAL_READINESS_REPORT.json
```

The ZIP includes a per-file SHA-256 manifest and the readiness report. Packaging
verifies ZIP integrity and writes a separate `.zip.sha256` file. It refuses to
overwrite an existing ZIP. The resulting archive can be shared directly without
requiring Git LFS or access to the private GitHub repository.

Current status: delivery requested; four additional front-face video sources
and a partial ESP32 macro review are preserved. Exhaustive labels, independent
camera/pose checks, final model training and phone validation are still pending;
final construction is not complete.
