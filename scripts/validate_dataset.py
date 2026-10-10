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
 dxf_lines=dxf_bytes.decode().splitlines()
 dxf_digest=next(line.split(':',1)[1] for line in dxf_lines if line.startswith('oid sha256:'))
 dxf_lfs_size=int(next(line.split(' ',1)[1] for line in dxf_lines if line.startswith('size ')))
 assert dxf_lfs_size==dxf_meta['bytes']
else:
 dxf_digest=hashlib.sha256(dxf_bytes).hexdigest()
 assert b'AC1009' in dxf_bytes[:128], 'Expected the official ASCII DXF AC1009 header'
assert dxf_digest==dxf_meta['sha256'] and dxf_meta['bytes']==1435223
model_dir=p/'board-yolo11m-finetune-experiment'
model_report=json.loads((model_dir/'training-report.json').read_text(encoding='utf-8'))
for filename,record in model_report['artifacts'].items():
 artifact=(model_dir/filename).read_bytes()
 if artifact.startswith(b'version https://git-lfs.github.com/spec/v1'):
  artifact_lines=artifact.decode().splitlines()
  artifact_digest=next(line.split(':',1)[1] for line in artifact_lines if line.startswith('oid sha256:'))
  artifact_lfs_size=int(next(line.split(' ',1)[1] for line in artifact_lines if line.startswith('size ')))
  assert artifact_lfs_size==record['bytes'],filename
 else:artifact_digest=hashlib.sha256(artifact).hexdigest()
 assert artifact_digest==record['sha256'],filename
 assert len(artifact)==record['bytes'] or artifact.startswith(b'version https://git-lfs.github.com/spec/v1'),filename
phone_folder=root/'data/phone-captures/2026-10-10'
if phone_folder.is_dir():
 phone_manifest=json.loads((phone_folder/'manifest.json').read_text())
 phone_rows=phone_manifest['photos'];assert len(phone_rows)==33
 assert len({row['board_family'] for row in phone_rows})==5
 phone_by_name={row['image_file']:row for row in phone_rows};assert len(phone_by_name)==33
 for row in phone_rows:
  photo=(root/row['image_path']).resolve();assert photo.is_relative_to(phone_folder.resolve())
  b=photo.read_bytes()
  if b.startswith(b'version https://git-lfs.github.com/spec/v1'):
   phone_digest=next(line.split(':',1)[1] for line in b.decode().splitlines() if line.startswith('oid sha256:'))
  else:phone_digest=hashlib.sha256(b).hexdigest()
  assert phone_digest==row['image_sha256'],row['image_file']
  assert row['image_width']>0 and row['image_height']>0
  assert row['image_file'] not in {old['file'] for old in rows},'Unreviewed intake must not leak into the training split'
 review_path=phone_folder/'reviewed-scan-references.json'
 if review_path.is_file():
  scan=json.loads(review_path.read_text());assert not scan['release_eligible'] and not scan['evaluation_valid']
  assert {row['class_id'] for row in scan['templates']}==set(range(5))
  label_ids=set();pin_count=0
  for template in scan['templates']:
   photo=phone_by_name[template['id']];assert template['image_sha256']==photo['image_sha256']
   assert template['image_path']==photo['image_path']
   assert template['board']==class_map[template['class_id']]['display_name']
   x1,y1,x2,y2=template['board_bbox_xyxy_normalized'];assert 0<=x1<x2<=1 and 0<=y1<y2<=1
   for label in template['labels']:
    assert label['id'] not in label_ids;label_ids.add(label['id'])
    a,b,c,d=label['bbox_xyxy_normalized'];assert x1<=a<c<=x2 and y1<=b<d<=y2,label['id']
    if label['kind']=='pin':
     pin_count+=1;assert label['identity_status']=='reviewed_photo_contact_with_printed_alias'
     assert label['source']['printed_alias'] and 'Literal silkscreen' in label['source']['mapping_scope']
    else:
     assert label['kind']=='part' and label['identity_status'] in {'reviewed_photo_module_marking','reviewed_photo_marking_family_order_code_unconfirmed'}
   if 'pose_corners_normalized' in template:
    assert template['pose_corner_status']=='reviewed_photo_metric_landmarks'
    assert template['pose_landmark_kind']=='mounting_hole_centres'
    assert template['pose_landmark_ids']==['BH1','BH4','BH2','BH3']
    assert template['pose_metric_landmarks_metres']==[[0.0,0.0],[0.0,-0.049000004],[0.112000005,-0.049000004],[0.112000005,0.0]]
    anchor_source=template['metric_landmark_source']
    anchor_bytes=(root/anchor_source['path']).read_bytes()
    if anchor_bytes.startswith(b'version https://git-lfs.github.com/spec/v1'):
     anchor_digest=next(line.split(':',1)[1] for line in anchor_bytes.decode().splitlines() if line.startswith('oid sha256:'))
    else:anchor_digest=hashlib.sha256(anchor_bytes).hexdigest()
    assert anchor_digest==anchor_source['sha256']
    assert template['corner_uncertainty_pixels']>0
    assert len(template['pose_corners_normalized'])==4
    assert all(x1<=x<=x2 and y1<=y<=y2 for x,y in template['pose_corners_normalized'])
  assert len(label_ids)==63 and pin_count==60
print('Validated80 source hashes/board boxes, YOLO labels,62/11/7 split, no original/crop leakage, Pi mechanical DXF provenance, and fine-tune artifact hashes.')
print('Validated 33 intake hashes and five partial scan references with 60 literal contact aliases and three marking families.')
