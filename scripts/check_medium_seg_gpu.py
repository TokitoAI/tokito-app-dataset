"""One fresh-process AMP runtime check; no dataset training or saved weights."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json
from pathlib import Path
import time
import torch
from ultralytics import YOLO
from ultralytics.cfg import get_cfg

torch.set_num_threads(1)
torch.set_num_interop_threads(1)
torch.backends.cudnn.benchmark=False
report={'purpose':'synthetic_runtime_viability_only','dataset_training':False,
        'shape':[1,3,640,640],'amp':True,'torch':torch.__version__,
        'cpu_threads':1,'success':False}
start=time.perf_counter()
try:
    report['device']=torch.cuda.get_device_name(0)
    model=YOLO('yolo11m-seg.yaml').model.cuda().train()
    model.args=get_cfg(overrides={'overlap_mask':False})
    optimizer=torch.optim.SGD(model.parameters(),lr=.001)
    scaler=torch.amp.GradScaler('cuda',init_scale=128)
    torch.cuda.reset_peak_memory_stats()
    batch={'img':torch.rand(1,3,640,640,device='cuda'),
           'batch_idx':torch.tensor([0.],device='cuda'),
           'cls':torch.tensor([[0.]],device='cuda'),
           'bboxes':torch.tensor([[.5,.5,.4,.4]],device='cuda'),
           'masks':torch.ones(1,160,160,device='cuda')}
    with torch.amp.autocast('cuda',dtype=torch.float16):
        loss,_=model.loss(batch)
    scaler.scale(loss.sum()).backward()
    scaler.unscale_(optimizer)
    finite=all(torch.isfinite(p.grad).all().item() for p in model.parameters() if p.grad is not None)
    if not finite:
        raise ValueError('Non-finite gradients')
    scaler.step(optimizer)
    scaler.update()
    torch.cuda.synchronize()
    report.update(success=True,finite_gradients=True,loss=float(loss.sum().detach().cpu()))
except Exception as error:
    report['error']=repr(error)
finally:
    report['elapsed_seconds']=time.perf_counter()-start
    if torch.cuda.is_available():
        report['peak_allocated_bytes']=torch.cuda.max_memory_allocated()
        report['peak_reserved_bytes']=torch.cuda.max_memory_reserved()
    output=Path(__file__).resolve().parents[1]/'work/training-runtime/runtime-smoke-amp.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
raise SystemExit(0 if report['success'] else 2)
