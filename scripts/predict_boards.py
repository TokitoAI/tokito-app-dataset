from pathlib import Path
import argparse,json,math
from PIL import Image,ImageOps
def main():
 parser=argparse.ArgumentParser(description='Experimental single-board front-view detector and crop classifier')
 parser.add_argument('input');parser.add_argument('--output',required=True);parser.add_argument('--confidence',type=float,default=.25);parser.add_argument('--min-aspect',type=float,default=.35);args=parser.parse_args()
 from ultralytics import YOLO
 import torch
 torch.set_num_threads(6)
 root=Path(__file__).resolve().parents[1];models=root/'models/board-family-v1'
 detector=YOLO(str(models/'detector.pt'));classifier=YOLO(str(models/'classifier.pt'))
 bundles=json.loads((root/'data/photo-model/source-bundles.json').read_text())
 src=Path(args.input);files=sorted(p for p in src.iterdir() if p.suffix.lower() in ['.jpg','.jpeg','.png']) if src.is_dir() else [src]
 records=[]
 for p in files:
  with Image.open(p) as im:image=ImageOps.exif_transpose(im).convert('RGB')
  result=detector.predict(image,imgsz=416,conf=args.confidence,iou=.5,device='cpu',verbose=False)[0]
  candidates=[]
  for b in result.boxes:
   coords=b.xyxy[0].tolist();w=coords[2]-coords[0];h=coords[3]-coords[1]
   if w<=0 or h<=0 or min(w,h)/max(w,h)<args.min_aspect:continue
   candidates.append({'coords':coords,'confidence':float(b.conf.item()),'detector_class':result.names[int(b.cls.item())]})
  record={'image':p.name,'status':'no_supported_candidate','detections_considered':len(result.boxes),'scope':'single-board front-view prototype; closed five-family classifier; exact part links unresolved'}
  if candidates:
   best=max(candidates,key=lambda x:x['confidence']);a=best['coords'];w,h=image.size
   crop=image.crop([max(0,math.floor(a[0])),max(0,math.floor(a[1])),min(w,math.ceil(a[2])),min(h,math.ceil(a[3]))])
   classified=classifier.predict(crop,imgsz=224,device='cpu',verbose=False)[0];name=classified.names[classified.probs.top1]
   record.update({'status':'model_candidate','predicted_class':name,'class_confidence':float(classified.probs.top1conf),'box_confidence':best['confidence'],'bbox_xyxy_pixels':a,'bbox_xyxy_normalized':[a[0]/w,a[1]/h,a[2]/w,a[3]/h],'detector_class_before_crop_classification':best['detector_class'],'candidate_source_bundle':bundles.get(name),'exact_component_refdes_link':None})
  records.append(record)
 out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'min_aspect':args.min_aspect,'confidence':args.confidence,'results':records},indent=2));print('Predicted',len(records),'files')
if __name__=='__main__':main()
