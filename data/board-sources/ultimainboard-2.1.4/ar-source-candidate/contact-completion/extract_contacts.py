import pcbnew,json,hashlib,sys
from pathlib import Path
p=Path(sys.argv[1]); b=pcbnew.LoadBoard(str(p)); rows=[]
for f in b.GetFootprints():
 row={'ref':f.GetReference(),'value':f.GetValue(),'position_mm':[pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y)],'rotation_deg':f.GetOrientationDegrees(),'side':'bottom' if f.IsFlipped() else 'top','pads':[]}
 for pad in f.Pads():
  row['pads'].append({'number':pad.GetNumber(),'position_mm':[pcbnew.ToMM(pad.GetPosition().x),pcbnew.ToMM(pad.GetPosition().y)],'size_mm':[pcbnew.ToMM(pad.GetSize().x),pcbnew.ToMM(pad.GetSize().y)],'shape':int(pad.GetShape()),'rotation_deg':pad.GetOrientationDegrees(),'drill_mm':[pcbnew.ToMM(pad.GetDrillSize().x),pcbnew.ToMM(pad.GetDrillSize().y)],'top_copper':pad.IsOnLayer(pcbnew.F_Cu),'bottom_copper':pad.IsOnLayer(pcbnew.B_Cu)})
 rows.append(row)
Path(sys.argv[2]).write_text(json.dumps({'pcb_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'thickness_mm':pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()),'footprints':rows},indent=2))
print(len(rows))
