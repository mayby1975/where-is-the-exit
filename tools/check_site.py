#!/usr/bin/env python3
"""Verify every local HTML link, anchor, JSON file and source block on a built site."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import argparse,json,re,hashlib
from build_site import read,rows,load_bundle,ROOT

class Page(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.ids=[];self.links=[];self.schema=[];self.in_json=False;self.cur=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag in ('a','link') and 'href' in a:self.links.append(a['href'])
        if tag in ('script','img') and 'src' in a:self.links.append(a['src'])
        if tag=='script' and a.get('type')=='application/ld+json':self.in_json=True;self.cur=''
    def handle_data(self,data):
        if self.in_json:self.cur+=data
    def handle_endtag(self,tag):
        if tag=='script' and self.in_json:self.schema.append(json.loads(self.cur));self.in_json=False
def check(root,out):
    pages={};errors=[];links=0
    for p in out.rglob('*.html'):
        page=Page();page.feed(p.read_text(encoding='utf-8'));pages[p.resolve()]=page
        if len(set(page.ids))!=len(page.ids):errors.append('duplicate anchor '+str(p))
    for p,page in pages.items():
        for link in page.links:
            u=urlsplit(link)
            if u.scheme or u.netloc:continue
            target=(p.parent/unquote(u.path)).resolve() if u.path else p
            if target.is_dir():target=target/'index.html'
            links+=1
            if not target.is_relative_to(out.resolve()) or not target.exists():errors.append('missing/unsafe link '+str(p)+': '+link)
            elif u.fragment and (target not in pages or unquote(u.fragment) not in pages[target].ids):errors.append('missing anchor '+link+' in '+str(p))
    json_count=0
    for p in out.rglob('*'):
        if p.suffix=='.json':json.loads(p.read_text(encoding='utf-8'));json_count+=1
        elif p.suffix=='.jsonl':rows(p);json_count+=1
    cfg=read(root/'site.json');sourcecount=0;quotes=0
    for entry in cfg['works']+cfg.get('archives',[]):
        d=load_bundle(root,entry);B={b['id']:b for b in d['blocks']};S={s['id']:s for s in d['sections']};C={c['id'] for c in d['concepts']}
        slug=entry['id']+'--v'+d['metadata'].get('package_version','0').replace('.','-')
        if len(B)!=len(d['blocks']):errors.append('duplicate block ID')
        for b in d['blocks']:
            target=(out/'works'/slug/'read'/(b['section_id']+'.html')).resolve()
            if target not in pages or b['id'] not in pages[target].ids:errors.append('missing source block '+b['id'])
            sourcecount+=1
        for item in d['concepts']+d['claims']+d['relations']+d['qa']:
            ids=item.get('source_block_ids',[])
            if any(x not in B for x in ids):errors.append('invalid evidence '+item['id'])
            for q in item.get('supporting_quotes',[]):
                if q['block_id'] not in ids or q['quote'] not in B.get(q['block_id'],{}).get('text',''):errors.append('invalid quote '+item['id'])
                quotes+=1
        for r in d['relations']:
            if not {r['from_concept_id'],r['to_concept_id']}<=C:errors.append('invalid relation '+r['id'])
    info=read(out/'build-info.json')
    for p in pages:
        text=p.read_text(encoding='utf-8')
        if info['mode']=='production' and 'noindex' in text:errors.append('production noindex '+str(p))
        if info['mode']=='review' and '<meta name="robots" content="noindex,nofollow">' not in text:errors.append('review missing noindex')
    report={'result':'passed' if not errors else 'failed','html_pages':len(pages),'local_links_checked':links,'json_files_parsed':json_count,'source_block_anchors':sourcecount,'exact_quotes':quotes,'errors':errors,'limits':['不验证线上部署、爬虫收录或模型回答质量','本地链接检查不代替全部外部URL可用性检查']}
    if errors:raise ValueError(json.dumps(report,ensure_ascii=False))
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--site',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();report=check(a.root,a.site or a.root/'dist');text=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    print(text)
