from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[1];p=root/'data/photo-model';rows=json.loads((p/'board-annotations.json').read_text())
assert len(rows)==80,'Expected reviewed initial80-file snapshot; update this control in a reviewed PR'
names=['esp32_board','esp8266_board','ultimainboard','nxp_frdm_mcxn236_board','raspberry_pi_3b_board'];folds={'train':set(),'val':set()};counts={'train':0,'val':0,'held_out_crop_variant':0}
for row in rows:
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
print('Validated80 source hashes/board boxes, YOLO labels,62/11/7 split and no original/crop leakage.')
