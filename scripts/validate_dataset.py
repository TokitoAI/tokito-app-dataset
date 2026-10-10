from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];p=root/'data/photo-model';rows=json.loads((p/'board-annotations.json').read_text())
class_map=json.loads((p/'board-class-display-names.json').read_text(encoding='utf-8'))['ordered_classes']
yaml_names=(p/'yolo-boards/data.yaml').read_text(encoding='utf-8')
assert len(class_map)==5 and [item['class_id'] for item in class_map]==list(range(5))
for item in class_map:
 expected=f"  {item['class_id']}: {json.dumps(item['display_name'],ensure_ascii=False)}"
 assert expected in yaml_names,expected
assert len(rows)==80,'Expected reviewed initial80-file snapshot; update this control in a reviewed PR'
names=['esp32_board','esp8266_board','ultimainboard','nxp_frdm_mcxn236_board','raspberry_pi_3b_board'];folds={'train':set(),'val':set()};counts={'train':0,'val':0,'held_out_crop_variant':0}
approved=json.loads((p/'board-review.json').read_text())['images']
for row in rows:
 review=approved[row['file']];assert review['sha256']==row['sha256'] and review['class_id']==row['class_id'] and review['bbox_xyxy_normalized']==row['bbox_xyxy_normalized']
 assert row['board_class']==names[row['class_id']]
 assert row['box_status']=='visually-reviewed-board-box'
 x1,y1,x2,y2=row['bbox_xyxy_normalized'];assert 0<=x1<x2<=1 and 0<=y1<y2<=1
 raw=p/'photos/raw'/row['file'];assert raw.exists()
 b=raw.read_bytes()
 if b.startswith(b'version https://git-lfs.github.com/spec/v1'):
  digest=next(line.split(':',1)[1] for line in b.decode().splitlines() if line.startswith('oid sha256:'))
 else:digest=hashlib.sha256(b).hexdigest()
 assert digest==row['sha256'],row['file']
 split=row['split'];counts[split]+=1
 if split=='held_out_crop_variant':continue
 folds[split].add(row['candidate_capture_group'])
 label=p/'yolo-boards/labels'/split/(Path(row['file']).stem+'.txt')
 parts=label.read_text().split();assert len(parts)==5 and int(parts[0])==row['class_id']
 values=list(map(float,parts[1:]));assert all(0<=v<=1 for v in values)
 expected=[(x1+x2)/2,(y1+y2)/2,x2-x1,y2-y1];assert all(abs(a-b)<1e-7 for a,b in zip(values,expected))
 assert (p/'yolo-boards/images'/split/row['file']).exists()
 if row['class_id']==3:assert row['exact_model']=='FRDM-MCXN236' and row['reference_947_link']=='not-a-match'
assert not folds['train']&folds['val'],'Capture group leakage'
assert counts=={'train':62,'val':11,'held_out_crop_variant':7},counts
dxf=root/'data/board-sources/raspberry-pi-3b-v1.2/mechanical.dxf'
dxf_meta=json.loads((dxf.parent/'mechanical-dxf-provenance.json').read_text(encoding='utf-8'))
dxf_bytes=dxf.read_bytes()
if dxf_bytes.startswith(b'version https://git-lfs.github.com/spec/v1'):
 dxf_digest=next(line.split(':',1)[1] for line in dxf_bytes.decode().splitlines() if line.startswith('oid sha256:'))
else:dxf_digest=hashlib.sha256(dxf_bytes).hexdigest()
assert dxf_digest==dxf_meta['sha256'] and dxf_meta['bytes']==1435223
assert b'AC1009' in dxf_bytes[:128], 'Expected the official ASCII DXF AC1009 header'
model_dir=p/'board-yolo11m-finetune-experiment'
model_report=json.loads((model_dir/'training-report.json').read_text(encoding='utf-8'))
for filename,record in model_report['artifacts'].items():
 artifact=(model_dir/filename).read_bytes()
 if artifact.startswith(b'version https://git-lfs.github.com/spec/v1'):
  artifact_digest=next(line.split(':',1)[1] for line in artifact.decode().splitlines() if line.startswith('oid sha256:'))
 else:artifact_digest=hashlib.sha256(artifact).hexdigest()
 assert artifact_digest==record['sha256'],filename
 assert len(artifact)==record['bytes'] or artifact.startswith(b'version https://git-lfs.github.com/spec/v1'),filename
print('Validated80 source hashes/board boxes, YOLO labels,62/11/7 split, no original/crop leakage, Pi mechanical DXF provenance, and fine-tune artifact hashes.')
