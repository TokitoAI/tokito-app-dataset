"""Fail-closed partial-instance diagnostic loss for Ultralytics 8.4.174.

No dataset eligibility is changed by importing this module. Callers must provide
reviewed_background_masks in the SAME raster as batch['img']; True pixels are
explicitly reviewed empty background, never merely unlabelled board pixels.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

SUPPORTED_ULTRALYTICS_VERSION = '8.4.174'


def partial_classification_bce(logits, targets, reviewed_background_anchors):
    """Retain positives/class competition and reviewed-empty negative anchors.

    Classification targets are task-assigned soft scores. Any anchor assigned a
    positive is supervised across classes, including its soft-target negative
    part. Every unassigned anchor is ignored unless its location is explicitly
    reviewed background. The returned tensor has the stock BCE shape.
    """
    if logits.shape != targets.shape or logits.ndim != 3:
        raise ValueError('logits and targets must share [batch, anchors, classes] shape')
    if reviewed_background_anchors.shape != logits.shape[:2]:
        raise ValueError('background anchor raster shape mismatch')
    if reviewed_background_anchors.dtype != torch.bool:
        raise ValueError('reviewed background must be boolean, not implicit confidence')
    if not torch.isfinite(targets).all():
        raise ValueError('non-finite classification target scores')
    if ((targets < 0) | (targets > 1.001)).any():
        raise ValueError(f'invalid classification target range: min={targets.min().item()} max={targets.max().item()} dtype={targets.dtype}')
    targets = targets.float().clamp_(0.0, 1.0)
    supervised = targets.gt(0).any(-1) | reviewed_background_anchors
    return F.binary_cross_entropy_with_logits(logits, targets, reduction='none') * supervised.unsqueeze(-1)


def sample_reviewed_background(background, anchor_xy_pixels, image_hw):
    """Sample explicit reviewed empty regions at stock anchor centres.

    No interpolation/resizing happens here: unknown transforms are prohibited.
    Out-of-canvas points fail instead of being clamped into reviewed background.
    """
    if background.ndim != 3 or background.dtype != torch.bool:
        raise ValueError('background must be boolean [batch, height, width]')
    height, width = map(int, image_hw)
    if background.shape[-2:] != (height, width):
        raise ValueError('background is not in the actual training-image canvas')
    if anchor_xy_pixels.ndim != 2 or anchor_xy_pixels.shape[-1] != 2:
        raise ValueError('anchor coordinates must be [anchors, 2]')
    xy = anchor_xy_pixels.floor().long()
    if ((xy[:, 0] < 0) | (xy[:, 0] >= width) | (xy[:, 1] < 0) | (xy[:, 1] >= height)).any():
        raise ValueError('anchor centre outside supplied canvas')
    return background[:, xy[:, 1], xy[:, 0]]


class _PartialClassificationBCE(nn.Module):
    def __init__(self):
        super().__init__()
        self.background_anchors = None

    def forward(self, logits, targets):
        if self.background_anchors is None:
            raise RuntimeError('reviewed background was not bound to this batch')
        return partial_classification_bce(logits, targets, self.background_anchors)


try:
    from ultralytics.utils.loss import v8SegmentationLoss
    from ultralytics.utils.tal import make_anchors
except ImportError:
    # Numerical helper tests remain usable where only torch is installed.
    v8SegmentationLoss = object


class PartialComponentSegmentationLoss(v8SegmentationLoss):
    def __init__(self, model):
        import ultralytics
        if ultralytics.__version__ != SUPPORTED_ULTRALYTICS_VERSION:
            raise RuntimeError('Untested Ultralytics loss API: ' + ultralytics.__version__)
        if getattr(model.model[-1], 'one2one_cv2', None) is not None:
            raise RuntimeError('End-to-end head is unsupported')
        super().__init__(model)
        self.bce = _PartialClassificationBCE()

    def get_assigned_targets_and_loss(self, preds, batch):
        background = batch.get('reviewed_background_masks')
        if background is None:
            raise ValueError('Every partial batch needs explicit reviewed_background_masks')
        if 'img' not in batch or batch['img'].ndim != 4:
            raise ValueError('Actual training images are required to verify canvas dimensions')
        image_hw = batch['img'].shape[-2:]
        feature_hw = tuple(int(v * self.stride[0]) for v in preds['feats'][0].shape[-2:])
        if feature_hw != tuple(image_hw):
            raise ValueError('Image and prediction canvas dimensions differ')
        if background.shape[0] != batch['img'].shape[0]:
            raise ValueError('Reviewed background batch size mismatch')
        anchors, stride = make_anchors(preds['feats'], self.stride, 0.5)
        background = background.to(self.device)
        self.bce.background_anchors = sample_reviewed_background(background, anchors * stride, image_hw)
        try:
            return super().get_assigned_targets_and_loss(preds, batch)
        finally:
            self.bce.background_anchors = None

    @staticmethod
    def single_mask_loss(gt_mask, pred, proto, xyxy, area):
        # Preserve the exact stock objective. Avoid a [all foreground,640,640]
        # prediction/BCE temporary and retained activation on the 4GB GPU.
        total = proto.sum() * 0
        for start in range(0, len(pred), 8):
            inputs = (gt_mask[start:start+8], pred[start:start+8], proto,
                      xyxy[start:start+8], area[start:start+8])
            if torch.is_grad_enabled() and (pred.requires_grad or proto.requires_grad):
                value = checkpoint(v8SegmentationLoss.single_mask_loss, *inputs,
                                   use_reentrant=False)
            else:
                value = v8SegmentationLoss.single_mask_loss(*inputs)
            total = total + value
        return total

    def loss(self, preds, batch):
        if isinstance(preds['proto'], tuple):
            raise RuntimeError('Semantic segmentation auxiliary loss has not been made ignore-aware')
        return super().loss(preds, batch)

def build_partial_segmentation_loss(model):
    """Construct a pinned criterion without altering Ultralytics installation."""
    import ultralytics
    if ultralytics.__version__ != SUPPORTED_ULTRALYTICS_VERSION:
        raise RuntimeError('Untested Ultralytics loss API: ' + ultralytics.__version__)
    if getattr(model.model[-1], 'one2one_cv2', None) is not None:
        raise RuntimeError('End-to-end head is unsupported by this diagnostic criterion')
    return PartialComponentSegmentationLoss(model)
