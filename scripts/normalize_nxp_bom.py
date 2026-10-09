from pathlib import Path
import csv,json,re,collections
root=Path('data/board-sources/nxp-frdm-mcxn947/structured-rev-c')
rows=list(csv.reader((root/'bom-ManufacturerBomReport.csv').open(encoding='utf-8-sig')))
header_idx=next(i for i,r in enumerate(rows) if r and r[0]=='Level' and 'Reference Designator' in r)
header=rows[header_idx];groups={};issues=[]
for source_row,r in enumerate(rows[header_idx+1:],header_idx+2):
 if not r or not any(r):continue
 d=dict(zip(header,r));refs=d.get('Reference Designator','').strip()
 if not refs:continue
 key=(d['Level'],d['Item Number'],refs,d.get('Find Num',''))
 if key not in groups:
  groups[key]={'level':d['Level'],'item_number':d['Item Number'],'name':d['Name'],'description':d['Description'],'quantity':d['Quantity'],'reference_designators':[s.strip() for s in refs.split(',') if s.strip()],'source_rows':[],'manufacturer_alternatives':[]}
 g=groups[key]
 if d['Quantity']!=g['quantity']:issues.append({'source_row':source_row,'issue':'quantity differs among alternatives'})
 g['source_rows'].append(source_row)
 g['manufacturer_alternatives'].append({k:d.get(k,'') for k in ['Manufacturer Item Number','Manufacturer Name','Manufacturer','Manufacturer Lifecycle','Manufacturer Notes','Preferred Status','BOM Notes']})
parts=list(groups.values());refs=collections.Counter(x for p in parts for x in p['reference_designators'])
duplicates={k:v for k,v in refs.items() if v>1}
bad=[s for s in refs if not re.fullmatch(r'[A-Za-z]+\d+',s)]
netlist=json.loads((root/'netlist.json').read_text());netrefs={p['refdes'] for n in netlist for p in n['pins']}
report={'source_header_row':header_idx+1,'grouped_parts':len(parts),'distinct_bom_refdes':len(refs),'manufacturer_rows':sum(len(p['manufacturer_alternatives']) for p in parts),'duplicate_refdes_groups':duplicates,'non_simple_refdes_tokens':bad,'quantity_issues':issues,'netlist_only_refdes':sorted(netrefs-set(refs)),'bom_only_refdes':sorted(set(refs)-netrefs),'scope':'source BOM grouping preserves manufacturer alternatives; distinct counts are not verified physical population'}
(root/'bom-parts.json').write_text(json.dumps(parts,indent=2))
(root/'bom-normalization-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
