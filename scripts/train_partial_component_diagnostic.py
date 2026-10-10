"""Known-specimen partial-component diagnostic; no production accuracy claim."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import argparse,copy,hashlib,json,random,time
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
from PIL import Image,ImageDraw
import torch
from partial_component_segmentation_loss import build_partial_segmentation_loss
ROOT=Path(__file__).resolve().parents[1]
FILES=['annotations/esp32-dense-component-review.json','annotations/esp8266-dense-component-review.json','annotations/esp8266-video-component-review.json','annotations/nxp-dense-component-review.json','annotations/ultimainboard-dense-component-review.json','data/video-captures/2026-10-10/esp32-keyframes/reviewed-front-macro.json']
OUT=ROOT/'work/partial-component-diagnostic'

def letterbox_geometry(width,height,size=640):
    ratio=min(size/width,size/height);nw,nh=round(width*ratio),round(height*ratio)
    return dict(new_width=nw,new_height=nh,left=(size-nw)//2,top=(size-nh)//2,sx=nw/width,sy=nh/height,size=size)

def transform_polygon(polygon,g):
    return [(x*g['sx']+g['left'],y*g['sy']+g['top']) for x,y in polygon]

def letterbox(image,background_polygons,size=640):
    g=letterbox_geometry(*image.size,size); canvas=Image.new('RGB',(size,size),(114,114,114));canvas.paste(image.resize((g['new_width'],g['new_height']),Image.Resampling.BILINEAR),(g['left'],g['top']))
    bg=Image.new('L',image.size);draw=ImageDraw.Draw(bg)
    for p in background_polygons:draw.polygon([tuple(v) for v in p],fill=255)
    bgcanvas=Image.new('L',(size,size));bgcanvas.paste(bg.resize((g['new_width'],g['new_height']),Image.Resampling.NEAREST),(g['left'],g['top']))
    return canvas,np.array(bgcanvas)>0,g

def observable_class(row,board):
    family=row.get('observed_marking_family') or row.get('observed_part_family') or ''
    cls=row['class_name'];scope=row.get('boundary_scope','').lower()
    if 'CP2102' in family or ('esp32' in board.lower() and row.get('observed_reference_designator')=='U2'):return 'ic_cp2102_family'
    if 'MCXN236' in family:return 'ic_mcxn236_family'
    if '25Q64JV' in family:return 'ic_25q64jv_family'
    if cls in ['rf_shield','rf_module'] and ('shield_top_surface_only' in scope or cls=='rf_shield'):
        return 'esp12e_shield' if 'ESP-12E' in family else 'rf_shield_unresolved'
    aliases={'rf_module':'rf_module_substrate','integrated_circuit':'ic_unresolved','switch':'switch_body','tactile_switch':'switch_body','capacitor':'chip_passive_body','ceramic_capacitor':'chip_passive_body','resistor':'chip_passive_body','chip_passive':'chip_passive_body','three_terminal_package':'three_terminal_body_unresolved','three_terminal_power_package':'power_package_unresolved','transistor_package':'three_terminal_body_unresolved','transistor':'three_terminal_body_unresolved','usb_connector':'usb_connector_body','usb_b_connector':'usb_b_connector_body','header_connector':'header_housing','pin_header':'header_housing','connector':'connector_housing','terminal_block':'terminal_block','electrolytic_capacitor':'electrolytic_capacitor','crystal_oscillator':'crystal_body','crystal':'crystal_body','diode':'diode_body','relay':'relay_body','inductor':'inductor_body','led':'led_body'}
    return aliases.get(cls)

def collect():
    images={};excluded=[]
    for file in FILES:
        doc=json.loads((ROOT/file).read_text());board=doc['board_family'];photo=doc.get('photo',{})
        for r in doc.get('masks',doc.get('instances',[])):
            if r.get('training_export_eligible') is False and r.get('class_name')=='unknown_package':excluded.append(r['instance_id']);continue
            cls=observable_class(r,board)
            if cls is None:excluded.append(r['instance_id']);continue
            path=r.get('image_path') or doc.get('image_path') or photo.get('path')
            group=r.get('capture_group_id') or r.get('capture_session_id') or doc.get('capture_session_id') or 'ultimainboard:20261009_night'
            split='val' if ('video-captures' in path or ('nxp_' in path and '20261009' in path)) else 'train'
            h=r.get('image_sha256') or doc.get('image_sha256') or photo.get('sha256')
            im=images.setdefault(path,dict(path=path,sha256=h,board_family=board,physical_specimen_id=r.get('physical_specimen_id') or doc.get('physical_specimen_id') or 'bench-ultimainboard-01',capture_group_id=group,split=split,rows=[]))
            if im['split']!=split or im['capture_group_id']!=group:raise ValueError('Inconsistent image split/group')
            im['rows'].append(dict(instance_id=r['instance_id'],class_name=cls,polygon=r['polygon_xy_pixels'],observed_reference_designator=r.get('observed_reference_designator'),observed_marking_family=r.get('observed_marking_family'),source_part_candidate=r.get('source_part_candidate'),identity_policy='observed family or observable package type; source candidate not promoted',source_annotation=file))
    names=sorted({r['class_name'] for im in images.values() for r in im['rows']});classids={n:i for i,n in enumerate(names)}
    # Explicit source/hash/group binding; same physical specimen across sessions is disclosed.
    groups={}
    for im in images.values():
        if hashlib.sha256((ROOT/im['path']).read_bytes()).hexdigest()!=im['sha256']:raise ValueError('Changed source '+im['path'])
        if im['capture_group_id'] in groups and groups[im['capture_group_id']]!=im['split']:raise ValueError('Capture-group leakage')
        groups[im['capture_group_id']]=im['split']
        for r in im['rows']:r['class_id']=classids[r['class_name']]
    return list(images.values()),names,excluded

def prepare(size):
    OUT.mkdir(parents=True,exist_ok=True);images,names,excluded=collect()
    bgfile=OUT/'background-regions.json'; bg=json.loads(bgfile.read_text()) if bgfile.exists() else {}
    if 'images' in bg:bg={r['image_path']:r.get('regions',[]) for r in bg['images']}
    fallback=['data/phone-captures/2026-10-10/IMG_20261010_092144.jpg','data/phone-captures/2026-10-10/IMG_20261010_092221.jpg','data/phone-captures/2026-10-10/IMG_20261010_092203.jpg']
    for path in fallback:bg.setdefault(path,[dict(polygon_xy_pixels=[[0,0],[600,0],[600,600],[0,600]],review_evidence='Original full-resolution photograph visually inspected: corner rectangle contains empty desk only.')])
    samples=[]
    for i,entry in enumerate(images):
        image=Image.open(ROOT/entry['path']).convert('RGB');regions=bg.get(entry['path'],[])

        for region in regions:
            if region.get('image_sha256',entry['sha256']) != entry['sha256']:raise ValueError('Background review source hash mismatch')
            if not region.get('review_evidence'):raise ValueError('Missing explicit background review evidence')
        polygons=[x['polygon_xy_pixels'] for x in regions]
        canvas,bgraster,g=letterbox(image,polygons,size);masks=[];bboxes=[];classes=[];exportrows=[]
        for r in entry['rows']:
            poly=transform_polygon(r['polygon'],g);m=Image.new('L',(size,size));ImageDraw.Draw(m).polygon(poly,fill=1);m=np.array(m)
            if m.sum()==0:continue
            xy=np.array(poly);x1,y1=xy.min(0);x2,y2=xy.max(0);x1=max(0,x1);y1=max(0,y1);x2=min(size,x2);y2=min(size,y2)
            if x2<=x1 or y2<=y1:continue
            masks.append(m);classes.append(r['class_id']);bboxes.append([(x1+x2)/2/size,(y1+y2)/2/size,(x2-x1)/size,(y2-y1)/size]);exportrows.append(r)
        if not masks:raise ValueError('No visible reviewed instances '+entry['path'])
        if (np.stack(masks).any(0)&bgraster).any():raise ValueError('Reviewed empty background overlaps a positive')
        sample=dict(image=torch.from_numpy(np.array(canvas).copy()).permute(2,0,1).float().div(255),masks=torch.from_numpy(np.stack(masks)).float(),background=torch.from_numpy(bgraster),boxes=torch.tensor(bboxes,dtype=torch.float32),classes=torch.tensor(classes,dtype=torch.float32).view(-1,1),entry=entry)
        samples.append(sample);entry['transform']=g;entry['background_regions']=regions;entry['exported_instance_count']=len(masks);entry['rows']=exportrows
        canvas.save(OUT/f'canvas-{i:02d}.jpg');Image.fromarray(bgraster.astype('uint8')*255).save(OUT/f'background-{i:02d}.png')
        np.savez_compressed(OUT/f'sample-{i:02d}.npz',image=np.array(canvas),background=bgraster,masks=np.stack(masks),classes=np.array(classes),boxes=np.array(bboxes))
    manifest=dict(schema_version='1.0',task='segment',model='YOLO11m-seg',imgsz=size,class_names=names,images=images,excluded_instances=excluded,evaluation_valid=False,production_eligible=False,coverage='partial_instances_with_ignore_loss',split_policy='capture sessions separate; SAME known physical specimens across train/val; no independent test; Ultimaker absent from val',geometry_augmentations=False,background_policy='only explicitly visually reviewed empty pixels; unknown pixels ignored')
    manifest['per_board_split_counts']={board:dict(Counter(im['split']+'_images' for im in images if im['board_family']==board)) for board in {im['board_family'] for im in images}}
    manifest['class_split_counts']={name:dict(Counter(im['split'] for im in images for row in im['rows'] if row['class_name']==name)) for name in names}
    manifest['source_annotation_hashes']={file:hashlib.sha256((ROOT/file).read_bytes()).hexdigest() for file in FILES}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));return samples,manifest

def batch(sample):
    return dict(img=sample['image'][None].cuda(),masks=sample['masks'].cuda(),batch_idx=torch.zeros(len(sample['boxes']),device='cuda'),bboxes=sample['boxes'].cuda(),cls=sample['classes'].cuda(),reviewed_background_masks=sample['background'][None].cuda())

def save_checkpoint(model,path,epoch,names,args):
    saved=copy.deepcopy(model).half().cpu();saved.names=dict(enumerate(names));saved.criterion=None
    torch.save(dict(model=saved,epoch=epoch,train_args=vars(args),diagnostic_only=True,evaluation_valid=False),path)

def audited_metrics(yolo,samples,names):
    # Mask IoU matching; unmatched predictions count as FP only inside reviewed empty background.
    tp=fp=fn=ignored=0;details=[];per_board={}
    for sample in samples:
        image=sample['image'].permute(1,2,0).numpy()*255
        result=yolo.predict(source=image.astype('uint8')[:,:,::-1].copy(),imgsz=image.shape[0],conf=.25,iou=.7,device=0,verbose=False)[0]
        gt=sample['masks'].numpy()>0;gtcls=sample['classes'].flatten().numpy().astype(int);used=set();itp=ifp=iignore=0
        if result.masks is not None:
            pm=result.masks.data.cpu().numpy()>0.5;pc=result.boxes.cls.cpu().numpy().astype(int)
            for pred,c in zip(pm,pc):
                if pred.shape!=gt.shape[-2:]:pred=np.array(Image.fromarray(pred).resize((gt.shape[-1],gt.shape[-2]),Image.Resampling.NEAREST))
                all_overlaps=[np.logical_and(pred,g).sum()/max(np.logical_or(pred,g).sum(),1) for g in gt]
                matches=[(all_overlaps[j],j) for j,g in enumerate(gt) if gtcls[j]==c and j not in used]
                best=max(matches,default=(0,-1))
                if best[0]>=.5:used.add(best[1]);itp+=1
                elif max(all_overlaps,default=0)>=.5:ifp+=1
                elif pred.any() and (pred&sample['background'].numpy()).sum()/pred.sum()>=.9:ifp+=1
                else:iignore+=1
        ifn=len(gt)-len(used);tp+=itp;fp+=ifp;fn+=ifn;ignored+=iignore;details.append(dict(path=sample['entry']['path'],board_family=sample['entry']['board_family'],tp=itp,fp_audited_regions=ifp,fn_reviewed_instances=ifn,ignored_predictions=iignore,reviewed_background_pixels=int(sample['background'].sum())))
        counts=per_board.setdefault(sample['entry']['board_family'],dict(tp=0,fp=0,fn=0,images=0))
        counts['tp']+=itp;counts['fp']+=ifp;counts['fn']+=ifn;counts['images']+=1
    return dict(mask_iou_threshold=.5,confidence=.25,tp=tp,fp_audited_regions=fp,fn_reviewed_instances=fn,ignored_predictions=ignored,audited_region_precision=tp/(tp+fp) if tp+fp else None,reviewed_instance_recall=tp/(tp+fn) if tp+fn else None,evaluation_valid=False,scope='partial reviewed regions on known specimens; unmatched unknown-region predictions ignored, not false positives',images=details,per_board=per_board,missing_validation_families=['ultimainboard_2_1_4'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');parser.add_argument('--evaluate',type=Path);parser.add_argument('--epochs',type=int,default=1000);parser.add_argument('--patience',type=int,default=80);parser.add_argument('--imgsz',type=int,default=640);parser.add_argument('--pretrained',default='yolo11m-seg.pt');args=parser.parse_args()
    torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.backends.cudnn.benchmark=False;random.seed(42);np.random.seed(42);torch.manual_seed(42)
    samples,manifest=prepare(args.imgsz);train=[s for s in samples if s['entry']['split']=='train'];val=[s for s in samples if s['entry']['split']=='val']
    print(json.dumps(dict(train_images=len(train),val_images=len(val),classes=manifest['class_names'],instances=sum(len(s['boxes']) for s in samples),evaluation_valid=False)),flush=True)
    if args.evaluate:
        from ultralytics import YOLO
        evaluated=YOLO(str(args.evaluate));metrics=audited_metrics(evaluated,val,manifest['class_names']);(OUT/'run/audited-region-metrics.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics),flush=True);return
    if not args.run:return
    if not torch.cuda.is_available():raise RuntimeError('CUDA required')
    run=OUT/'run';
    if run.exists():
        entries=list(run.iterdir())
        if any(p.name!='weights' or any(p.iterdir()) for p in entries): raise FileExistsError('Refusing to overwrite non-empty diagnostic run directory')
    run.mkdir(parents=True,exist_ok=True);weights=run/'weights';weights.mkdir(exist_ok=True)
    from ultralytics import YOLO
    from ultralytics.nn.tasks import SegmentationModel
    from ultralytics.cfg import get_cfg
    pretrained=YOLO(args.pretrained);model=SegmentationModel(pretrained.model.yaml,nc=len(manifest['class_names']),verbose=False);model.load(pretrained.model);model=model.cuda();model.args=get_cfg();model.args.overlap_mask=False;model.args.task='segment';model.names=dict(enumerate(manifest['class_names']))
    criterion=build_partial_segmentation_loss(model);optimizer=torch.optim.AdamW(model.parameters(),lr=0.00001,weight_decay=.0005);scaler=torch.amp.GradScaler('cuda');best=float('inf');best_epoch=0;records=[];start=time.time()
    for epoch in range(1,args.epochs+1):
        model.train();random.shuffle(train);tot=0
        lr=0.00001*(.1+.9*(1+np.cos(np.pi*(epoch-1)/args.epochs))/2)*min(1,epoch/3)
        for group in optimizer.param_groups:group['lr']=lr
        for sample in train:
            b=batch(sample);optimizer.zero_grad(set_to_none=True)
            with torch.autocast('cuda',dtype=torch.float16):loss,parts=criterion(model(b['img']),b);objective=loss.sum()
            if not torch.isfinite(objective):raise RuntimeError('Nonfinite training loss')
            scaler.scale(objective).backward();scaler.unscale_(optimizer);torch.nn.utils.clip_grad_norm_(model.parameters(),10);scaler.step(optimizer);scaler.update();tot+=objective.item()
        model.eval();vl=0
        with torch.no_grad():
            for sample in val:
                b=batch(sample)
                with torch.autocast('cuda',dtype=torch.float16):loss,_=criterion(model(b['img']),b)
                vl+=loss.sum().item()
        vl/=len(val);record=dict(epoch=epoch,train_loss=tot/len(train),validation_partial_loss=vl,lr=lr,elapsed_seconds=time.time()-start,evaluation_valid=False)
        if not np.isfinite(vl):raise RuntimeError('Nonfinite validation loss')
        if vl<best-1e-4:best=vl;best_epoch=epoch;save_checkpoint(model,weights/'best.pt',epoch,manifest['class_names'],model.args)
        record['best_epoch']=best_epoch;records.append(record);(run/'progress.json').write_text(json.dumps(dict(status='running',epoch=epoch,best_epoch=best_epoch,best_partial_loss=best,patience=args.patience,epoch_ceiling=args.epochs,latest=record),indent=2));print(json.dumps(record),flush=True)
        if epoch%10==0:save_checkpoint(model,weights/'last.pt',epoch,manifest['class_names'],model.args)
        if epoch-best_epoch>=args.patience:break
    save_checkpoint(model,weights/'last.pt',epoch,manifest['class_names'],model.args)
    (run/'history.json').write_text(json.dumps(records,indent=2));del criterion,optimizer,model,pretrained;torch.cuda.empty_cache()
    bestmodel=YOLO(str(weights/'best.pt'));metrics=audited_metrics(bestmodel,val,manifest['class_names']);(run/'audited-region-metrics.json').write_text(json.dumps(metrics,indent=2))
    report=dict(status='completed',epochs_completed=epoch,best_epoch=best_epoch,epoch_ceiling=args.epochs,patience=args.patience,stop_reason='patience' if epoch<args.epochs else 'epoch_ceiling',elapsed_seconds=time.time()-start,best_checkpoint=str(weights/'best.pt'),checkpoint_sha256=hashlib.sha256((weights/'best.pt').read_bytes()).hexdigest(),metrics=metrics,evaluation_valid=False,production_eligible=False,limitations=manifest['split_policy'])
    (run/'progress.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

if __name__=='__main__':main()
