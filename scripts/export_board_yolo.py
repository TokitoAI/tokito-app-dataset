from pathlib import Path
from PIL import Image,ImageOps
import json
root=Path('data/photo-model');rows=json.loads((root/'board-annotations.json').read_text());names=['esp32_board','esp8266_board','ultimainboard','nxp_frdm_mcxn236_board','raspberry_pi_3b_board']
val_captures={'IMG_20261009_221154.jpg','IMG_20261009_221155.jpg','IMG_20261009_221156.jpg','IMG_20261009_221657.jpg','IMG_20261009_222033.jpg','IMG_20261009_222038.jpg','IMG_20261009_222042.jpg','IMG_20261009_222108.jpg','IMG_20261009_222113.jpg','IMG_20261009_222340.jpg','IMG_20261009_222343.jpg'}
counts={'train':0,'val':0,'held_out_crop_variant':0};export=[]
for row in rows:
 cid=row['class_id'];fn=row['file'];box=row['bbox_xyxy_normalized']
 # Visually reviewed contact sheets: tight phone crops bound the entire visible board.
 if '_1.' in fn:box=[0.,0.,1.,1.]
 elif cid==4:box=[max(0,box[0]-.02),max(0,box[1]-.02),min(1,box[2]+.025),min(1,box[3]+.04)]
 row['bbox_xyxy_normalized']=box;row['box_status']='visually-reviewed-board-box';row['review_notes']='80-box contact sheets reviewed; tight crop boxes expanded to full visible assembly; Pi boxes include port protrusions.'
 row['board_class']=names[cid]
 if cid==3:row['exact_model']='FRDM-MCXN236';row['model_evidence']='readable silkscreen on IMG_20261009_221755_1.jpg';row['reference_947_link']='not-a-match'
 capture=row['candidate_capture_group'];split='val' if capture in val_captures else 'train'
 if split=='val' and '_1.' in fn:counts['held_out_crop_variant']+=1;row['split']='held_out_crop_variant';continue
 row['split']=split;counts[split]+=1
 for folder in ['images','labels']:(root/'yolo-boards'/folder/split).mkdir(parents=True,exist_ok=True)
 with Image.open(root/'photos/raw'/fn) as im:im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((1280,1280));im.save(root/'yolo-boards/images'/split/fn,quality=95)
 x1,y1,x2,y2=box;assert 0<=x1<x2<=1 and 0<=y1<y2<=1
 (root/'yolo-boards/labels'/split/(Path(fn).stem+'.txt')).write_text(f'{cid} {(x1+x2)/2:.8f} {(y1+y2)/2:.8f} {x2-x1:.8f} {y2-y1:.8f}\n')
 export.append(row)
(root/'board-annotations.json').write_text(json.dumps(rows,indent=2))
base=(root/'yolo-boards').resolve().as_posix()
(root/'yolo-boards/data.yaml').write_text('path: '+base+'\ntrain: images/train\nval: images/val\nnames:\n'+''.join(f'  {i}: {n}\n' for i,n in enumerate(names)))
(root/'yolo-boards/split-report.json').write_text(json.dumps({'counts':counts,'validation_classes':[names[i] for i in sorted({r['class_id'] for r in export if r['split']=='val'})],'limitations':'One physical specimen per family, one session; no independent specimen test; ESP32 only one pose burst so held in training, no validation metric for ESP32; crop/original groups never split across folds. Validation is diagnostic.'},indent=2))
print(counts)
