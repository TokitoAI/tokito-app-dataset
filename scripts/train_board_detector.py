from pathlib import Path
import json,os,argparse
os.environ['YOLO_CONFIG_DIR']=str(Path('work/yolo-settings').resolve())
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--checkpoint',default='yolov8n.pt');parser.add_argument('--epochs',type=int,default=60);parser.add_argument('--name',default='board-detector-v2');args=parser.parse_args()
 import torch
 from ultralytics import YOLO
 torch.set_num_threads(6)
 model=YOLO(args.checkpoint)
 data=str(Path('data/photo-model/yolo-boards/data.yaml').resolve())
 result=model.train(data=data,epochs=args.epochs,imgsz=416,batch=8,device='cpu',workers=0,project=str(Path('data/photo-model/runs').resolve()),name=args.name,exist_ok=True,seed=42,deterministic=True,patience=20,cache=False,degrees=180,fliplr=.5,flipud=.5,freeze=10,optimizer='AdamW',lr0=.002,warmup_epochs=1,plots=True)
 run=Path(result.save_dir);report={'run':str(run),'best_checkpoint':str(run/'weights/best.pt'),'epochs_requested':args.epochs,'image_size':416,'device':'cpu','scope':'five-family board detection only; no part or document detector; diagnostic single-specimen validation','validation_esp32':'absent; do not claim held-out ESP32 accuracy','torch':torch.__version__}
 Path('data/photo-model/board-training-report.json').write_text(json.dumps(report,indent=2))
 print(json.dumps(report),flush=True)
if __name__=='__main__':main()

