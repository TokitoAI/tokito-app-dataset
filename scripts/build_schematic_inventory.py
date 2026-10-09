from pathlib import Path
import json,csv
for board in ['esp8266-nodemcu-reference','ultimainboard-2.1.4']:
 root=Path('data/board-sources')/board/'structured-source';result=[];issues=[]
 for sheet in (root/'schematic-records').glob('*.json'):
  rows=json.loads(sheet.read_text());symbols={x['stream_record_index']:x['fields'] for x in rows if x.get('fields',{}).get('RECORD')=='1'}
  params={i:{} for i in symbols}
  for row in rows:
   f=row.get('fields',{})
   if f.get('RECORD') not in ['34','41'] or 'OWNERINDEX' not in f:continue
   idx=int(f['OWNERINDEX'])+1
   if idx in symbols:params[idx][f.get('NAME','')]=f.get('TEXT','')
   elif f.get('NAME')=='Designator':issues.append({'sheet':sheet.name,'record':row['stream_record_index'],'owner_record':idx,'problem':'Designator owner not a component'})
  for i,f in symbols.items():
   result.append({'sheet':sheet.stem,'record_index':i,'designator':params[i].get('Designator',''),'comment':params[i].get('Comment',''),'library_reference':f.get('LIBREFERENCE',''),'description':f.get('COMPONENTDESCRIPTION',''),'part_id':f.get('CURRENTPARTID',''),'parameters':params[i]})
 (root/'schematic-component-inventory.json').write_text(json.dumps(result,indent=2))
 with (root/'schematic-component-inventory.csv').open('w',newline='',encoding='utf-8-sig') as out:
  w=csv.DictWriter(out,['sheet','record_index','designator','comment','library_reference','description','part_id'],extrasaction='ignore');w.writeheader();w.writerows(result)
 report={'symbol_records':len(result),'designated_symbols':sum(bool(x['designator']) for x in result),'distinct_designators':len({x['designator'] for x in result if x['designator']}),'owner_link_issues':issues,'scope':'schematic symbol and parameter inventory; multipart symbols retained; procurement and physical population not verified'}
 (root/'schematic-inventory-report.json').write_text(json.dumps(report,indent=2))
 print(board,json.dumps(report))
