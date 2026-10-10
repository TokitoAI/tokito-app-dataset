from pathlib import Path
import os,json,argparse,collections
from PIL import Image,ImageOps
os.environ['YOLO_CONFIG_DIR']=str(Path('work/yolo-settings').resolve())
ROOT=Path('data/photo-model')
DATA=ROOT/'classifier-dataset'
RUN=ROOT/'classifier-runs'/'board-crop-v1'

def prepare():
    annotations=json.loads((ROOT/'board-annotations.json').read_text())
    extra_group='IMG_20261009_221914.jpg'
    val_groups={x['candidate_capture_group'] for x in annotations if x['split']=='val'}|{extra_group}
    items=[]
    for x in annotations:
        assert x['box_status']=='visually-reviewed-board-box'
        with Image.open(ROOT/'photos/raw'/x['file']) as original:
            image=ImageOps.exif_transpose(original).convert('RGB')
            assert image.size==(x['oriented_width'],x['oriented_height'])
            w,h=image.size;b=x['bbox_xyxy_normalized']
            pixels=[max(0,round(b[0]*w)),max(0,round(b[1]*h)),min(w,round(b[2]*w)),min(h,round(b[3]*h))]
            cropped=image.crop(pixels)
            group=x['candidate_capture_group']
            fold='train' if group not in val_groups else ('val' if x['file']==group else 'excluded_val_variant')
            destination=DATA/fold/x['board_class']/x['file']
            destination.parent.mkdir(parents=True,exist_ok=True);cropped.save(destination,quality=95)
            items.append({'file':x['file'],'board_class':x['board_class'],'capture_group':group,'split':fold,'crop':str(destination),'crop_box_pixels':pixels})
    train={x['capture_group'] for x in items if x['split']=='train'}
    val={x['capture_group'] for x in items if x['split']=='val'}
    assert not train&val
    (ROOT/'classifier-dataset-manifest.json').write_text(json.dumps({'scope':'single-specimen single-session diagnostic; no independent test','extra_esp32_validation_group':extra_group,'counts':dict(collections.Counter(x['split'] for x in items)),'images':items},indent=2))
    print('prepared',collections.Counter(x['split'] for x in items),flush=True)

def train():
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(6)
    model=YOLO('yolov8n-cls.pt')
    model.train(data=str(DATA.resolve()),epochs=40,imgsz=224,batch=8,workers=0,device='cpu',project=str((ROOT/'classifier-runs').resolve()),name='board-crop-v1',exist_ok=True,seed=42,deterministic=True,patience=40,freeze=9,optimizer='AdamW',lr0=.003,lrf=.1,warmup_epochs=1,scale=.1,fliplr=.5,flipud=.5,erasing=0,auto_augment=None,plots=True)

def evaluate():
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(6)
    manifest=json.loads((ROOT/'classifier-dataset-manifest.json').read_text())
    model=YOLO(str(RUN/'weights/best.pt'))
    records=[]
    for x in manifest['images']:
        result=model.predict(x['crop'],imgsz=224,device='cpu',verbose=False)[0]
        name=result.names[result.probs.top1]
        records.append({**x,'predicted_class':name,'confidence':float(result.probs.top1conf),'correct':name==x['board_class'],'class_probabilities':{result.names[i]:float(v) for i,v in enumerate(result.probs.data)}})
    counts={fold:{'correct':sum(x['correct'] for x in records if x['split']==fold),'total':sum(x['split']==fold for x in records)} for fold in ['train','val','excluded_val_variant']}
    confusion=dict(collections.Counter(f"{x['board_class']} -> {x['predicted_class']}" for x in records if not x['correct']))
    report={'scope':'80 known-photo manual-board-crop diagnostic; train examples included; no independent specimen/session accuracy; no component detector','weights':str(RUN/'weights/best.pt'),'counts':counts,'total_correct':sum(x['correct'] for x in records),'total':len(records),'errors':confusion,'predictions':records}
    (ROOT/'classifier-predictions.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='predictions'}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['all','prepare','train','evaluate'],default='all');args=parser.parse_args()
    if args.stage in ['all','prepare']:prepare()
    if args.stage in ['all','train']:train()
    if args.stage in ['all','evaluate']:evaluate()
