from pathlib import Path
import olefile,struct,json,hashlib,collections
report=[]
for board in ['ultimainboard-2.1.4','esp8266-nodemcu-reference']:
    root=Path('data/board-sources')/board;out=root/'structured-source'/'schematic-records';out.mkdir(parents=True,exist_ok=True)
    for src in root.rglob('*.SchDoc'):
        data=olefile.OleFileIO(src).openstream('FileHeader').read();pos=0;rows=[]
        while pos<len(data):
            header=struct.unpack_from('<I',data,pos)[0];pos+=4
            size=header&0xffffff;flags=header>>24
            assert size<=len(data)-pos,(str(src),pos,size)
            raw=data[pos:pos+size];pos+=size
            if not flags:
                text=raw.rstrip(b'\0').decode('cp1252')
                props=dict(p.split('=',1) for p in text.split('|') if '=' in p)
                rows.append({'stream_record_index':len(rows),'fields':props})
            else:rows.append({'stream_record_index':len(rows),'binary_record_flags':flags,'bytes':size,'sha256':hashlib.sha256(raw).hexdigest()})
        dest=out/(src.stem+'.json');dest.write_text(json.dumps(rows,indent=2))
        counts=collections.Counter(x.get('fields',{}).get('RECORD','HEADER') for x in rows)
        report.append({'board':board,'source':str(src.relative_to(root)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'records':len(rows),'record_type_counts':dict(counts),'output':str(dest.relative_to(root))})
Path('data/board-sources/schematic-extraction-report.json').write_text(json.dumps({'sheets':report,'scope':'native FileHeader property records; source indexes and field names preserved; no inferred netlist or component labels'},indent=2))
print('Extracted',len(report),'schematic sheets;',sum(x['records'] for x in report),'native records')
