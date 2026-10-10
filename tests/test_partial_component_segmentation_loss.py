"""Numerical evidence for ignore-aware classification (no training eligibility claim)."""
import sys
import unittest
from pathlib import Path
try:
    import torch
except ModuleNotFoundError as exc:
    if exc.name != 'torch':
        raise
    raise unittest.SkipTest('Optional torch runtime absent; GPU numerical evidence runs separately') from exc
import torch.nn.functional as F
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from partial_component_segmentation_loss import partial_classification_bce,sample_reviewed_background,build_partial_segmentation_loss

class TestPartialClassificationLoss(unittest.TestCase):
    def _gradient_check(self,device):
        logits=torch.tensor([[[2.,-1.],[1.,-2.],[0.,1.]]],device=device,requires_grad=True)
        targets=torch.tensor([[[0.,0.],[0.6,0.],[0.,0.]]],device=device)
        bg=torch.tensor([[False,False,True]],device=device)
        actual=partial_classification_bce(logits,targets,bg)
        stock=F.binary_cross_entropy_with_logits(logits,targets,reduction='none')
        torch.testing.assert_close(actual[:,1:],stock[:,1:])
        self.assertEqual(actual[:,0].sum().item(),0)
        actual.sum().backward()
        self.assertTrue(torch.equal(logits.grad[:,0],torch.zeros_like(logits.grad[:,0])))
        self.assertGreater(logits.grad[:,1].abs().sum().item(),0)
        self.assertGreater(logits.grad[:,2].abs().sum().item(),0)
        # Raising ignored predictions cannot change the objective.
        changed=logits.detach().clone();changed[:,0]=100
        torch.testing.assert_close(partial_classification_bce(changed,targets,bg),actual.detach())

    def test_cpu_ignored_negatives_retained_positives_background(self):self._gradient_check('cpu')
    @unittest.skipUnless(torch.cuda.is_available(),'CUDA unavailable')
    def test_cuda_ignored_negatives_retained_positives_background(self):self._gradient_check('cuda')
    def test_unknown_canvas_and_nonboolean_fail(self):
        bg=torch.zeros(1,8,8,dtype=torch.bool); anchors=torch.tensor([[2.,2.]])
        with self.assertRaises(ValueError):sample_reviewed_background(bg,anchors,(16,16))
        with self.assertRaises(ValueError):sample_reviewed_background(bg.float(),anchors,(8,8))
        with self.assertRaises(ValueError):sample_reviewed_background(bg,torch.tensor([[8.,2.]]),(8,8))
    def test_sampling_preserves_reviewed_regions(self):
        bg=torch.zeros(1,8,8,dtype=torch.bool);bg[:,0:4,0:4]=True
        sampled=sample_reviewed_background(bg,torch.tensor([[2.,2.],[6.,6.]]),(8,8))
        self.assertEqual(sampled.tolist(),[[True,False]])

class TestActualSegmentationLoss(unittest.TestCase):
    @unittest.skipUnless(torch.cuda.is_available(),'Actual model integration tested on CUDA')
    def test_model_forward_loss_backward_and_missing_raster_fail(self):
        try:
            import ultralytics
        except ImportError:self.skipTest('Ultralytics absent')
        if ultralytics.__version__!='8.4.174':self.skipTest('Pinned runtime unavailable')
        from ultralytics.nn.tasks import SegmentationModel
        from ultralytics.cfg import get_cfg
        torch.set_num_threads(1)
        model=SegmentationModel('yolo11m-seg.yaml',nc=2,verbose=False).cuda().train()
        model.args=get_cfg(); model.args.overlap_mask=False
        criterion=build_partial_segmentation_loss(model)
        imgs=torch.rand(1,3,128,128,device='cuda')
        predictions=model(imgs)
        mask=torch.zeros(1,128,128,device='cuda');mask[:,40:88,40:88]=1
        batch={'img':imgs,'batch_idx':torch.tensor([0.],device='cuda'),'cls':torch.tensor([[0.]],device='cuda'),'bboxes':torch.tensor([[.5,.5,.375,.375]],device='cuda'),'masks':mask}
        with self.assertRaises(ValueError):criterion(predictions,batch)
        bg=torch.zeros(1,128,128,dtype=torch.bool,device='cuda');bg[:,:16,:]=True
        batch['reviewed_background_masks']=bg
        predictions['scores'].retain_grad()
        assigned=criterion.get_assigned_targets_and_loss(predictions,batch)[0]
        fg,_,_,anchors,strides=assigned
        background_anchors=sample_reviewed_background(bg,anchors*strides,(128,128))
        ignored=~fg & ~background_anchors
        self.assertGreater(ignored.sum().item(),0)
        self.assertGreater(fg.sum().item(),0)
        loss,parts=criterion(predictions,batch)
        self.assertTrue(torch.isfinite(loss).all())
        loss.sum().backward()
        score_grad=predictions['scores'].grad.permute(0,2,1)
        self.assertEqual(score_grad[ignored].abs().sum().item(),0)
        self.assertGreater(score_grad[fg].abs().sum().item(),0)
        self.assertGreater(score_grad[background_anchors & ~fg].abs().sum().item(),0)
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum()>0 for p in model.parameters()))
        self.assertEqual(set(parts),{'box_loss','seg_loss','cls_loss','dfl_loss','sem_loss'})

class TestDiagnosticLetterbox(unittest.TestCase):
    def test_image_background_and_positive_share_exact_resize_and_padding(self):
        from PIL import Image,ImageDraw
        import numpy as np
        from train_partial_component_diagnostic import letterbox,transform_polygon
        image=Image.new('RGB',(16,8));ImageDraw.Draw(image).rectangle((2,2,4,4),fill=(255,255,255))
        background=[[[10,1],[12,1],[12,3],[10,3]]]
        canvas,bg,g=letterbox(image,background,32)
        self.assertEqual((g['sx'],g['sy'],g['left'],g['top']),(2,2,0,8))
        self.assertEqual(transform_polygon([[2,2],[4,4]],g),[(4,12),(8,16)])
        self.assertTrue(bg[10:16,20:26].all())
        self.assertFalse(bg[:8].any());self.assertFalse(bg[24:].any())
        independent=Image.new('L',(16,8));ImageDraw.Draw(independent).polygon([tuple(v) for v in background[0]],fill=255)
        expected=np.zeros((32,32),dtype=bool);expected[8:24]=np.array(independent.resize((32,16),Image.Resampling.NEAREST))>0
        self.assertTrue(np.array_equal(bg,expected))
        pixels=np.array(canvas)
        self.assertTrue((pixels[13:17,5:9]>200).all())

class TestAuditedRegionMetrics(unittest.TestCase):
    def test_duplicate_wrong_class_background_fp_and_unknown_ignore(self):
        from types import SimpleNamespace
        from train_partial_component_diagnostic import audited_metrics
        masks=torch.zeros(5,32,32);masks[:3,8:12,8:12]=1;masks[3,20:24,20:24]=1;masks[4,0:4,0:4]=1
        result=SimpleNamespace(masks=SimpleNamespace(data=masks),boxes=SimpleNamespace(cls=torch.tensor([0,0,1,0,0])))
        class Stub:
            def predict(self,**kwargs):return [result]
        bg=torch.zeros(32,32,dtype=torch.bool);bg[0:4,0:4]=True
        sample=dict(image=torch.zeros(3,32,32),masks=masks[:1],classes=torch.tensor([[0]]),background=bg,entry=dict(path='synthetic',board_family='synthetic_board'))
        report=audited_metrics(Stub(),[sample],['first','second'])
        self.assertEqual((report['tp'],report['fp_audited_regions'],report['fn_reviewed_instances'],report['ignored_predictions']),(1,3,0,1))
        self.assertEqual(report['audited_region_precision'],.25)
        self.assertEqual(report['reviewed_instance_recall'],1)
        self.assertFalse(report['evaluation_valid'])

class TestChunkedMaskLoss(unittest.TestCase):
    def test_chunked_loss_and_gradients_match_stock(self):
        try:
            from ultralytics.utils.loss import v8SegmentationLoss
            from partial_component_segmentation_loss import PartialComponentSegmentationLoss
        except ImportError:self.skipTest('Ultralytics absent')
        torch.manual_seed(7)
        gt=torch.randint(0,2,(19,32,32)).float();xy=torch.tensor([[2.,3.,29.,30.]]*19);area=torch.full((19,),.7)
        proto=torch.randn(4,32,32,requires_grad=True);pred=torch.randn(19,4,requires_grad=True)
        original=v8SegmentationLoss.single_mask_loss(gt,pred,proto,xy,area)
        grads=torch.autograd.grad(original,(pred,proto))
        chunked=PartialComponentSegmentationLoss.single_mask_loss(gt,pred,proto,xy,area)
        chunkgrads=torch.autograd.grad(chunked,(pred,proto))
        torch.testing.assert_close(chunked,original,rtol=1e-5,atol=1e-6)
        for a,b in zip(grads,chunkgrads):torch.testing.assert_close(a,b,rtol=1e-5,atol=1e-6)

if __name__=='__main__':unittest.main()
