#!/usr/bin/env python3
"""Build a portable static library from evidence bundles. Python 3.10+, stdlib only."""
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlsplit, quote
import argparse, json, html, re, shutil, hashlib

ROOT=Path(__file__).resolve().parents[1]
PROFILE_LABEL={'thought':'思想与论述','fiction':'小说','essay':'短文','product':'产品资料'}
STATUS_LABEL={'author_framework':'作者理论框架','author_interpretation':'作者解释','author_proposal':'作者提案','author_speculation':'作者推演与猜想','established_concept_as_used_by_author':'已有概念的本书用法'}
def read(p,default=None):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def rows(p):
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()] if p.exists() else []
def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def esc(s):return html.escape(str(s),quote=True)
def safe(s):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*',s):raise ValueError('Unsafe identifier: '+s)
    return s
def resolve_package(root,entry):
    p=(root/entry['package']).resolve()
    if not p.is_relative_to(root.resolve()):raise ValueError('Package escapes project root')
    return p
def load_bundle(root,entry):
    safe(entry['id']);p=resolve_package(root,entry)
    m=read(p/'metadata.json',{});b=rows(p/'data/blocks.jsonl');s=read(p/'data/sections.json',[])
    if not b or not s:raise ValueError('Missing blocks/sections in '+str(p))
    return dict(entry=entry,path=p,metadata=m,blocks=b,sections=s,concepts=read(p/'data/concepts.json',[]),claims=read(p/'data/claims.json',[]),relations=read(p/'data/relations.json',[]),qa=rows(p/'data/qa.jsonl'))

CSS='''
:root{--ink:#20312f;--muted:#63736e;--line:#d6ddd5;--paper:#f6f5ef;--accent:#326b59;--card:#fffef8}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:var(--paper);color:var(--ink);font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.85}a{color:var(--accent);text-underline-offset:4px;overflow-wrap:anywhere}a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid #b77022;outline-offset:3px}header{border-bottom:1px solid var(--line);background:#e7ede4;padding:18px max(5vw,20px)}header a{text-decoration:none;font-weight:650}nav{display:flex;flex-wrap:wrap;gap:20px;margin-top:8px;font-size:14px}main{max-width:1100px;margin:auto;padding:42px 24px 70px}h1{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:clamp(30px,5vw,50px);line-height:1.35;font-weight:650;letter-spacing:.03em}h2{font-size:25px;margin-top:2em;line-height:1.5}h3{font-size:20px;line-height:1.55}.eyebrow,.muted{color:var(--muted)}.eyebrow{letter-spacing:.15em;font-size:12px}.lead{font-size:20px;max-width:800px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}.card{padding:24px;border:1px solid var(--line);background:var(--card);border-radius:10px}.card h2,.card h3{margin-top:0}.badge{font-size:12px;border:1px solid var(--line);padding:3px 8px;display:inline-block;border-radius:20px;margin-right:5px}.notice{border-left:3px solid var(--accent);padding:12px 18px;background:#eaf0e6}.reader{max-width:820px}.reader p.source{font-family:"Songti SC","Noto Serif CJK SC",serif;font-size:19px;white-space:pre-wrap;text-align:justify;margin:1.35em 0}.source:hover .anchor,.source:focus-within .anchor{opacity:1}.anchor{font-family:system-ui,sans-serif;font-size:11px;opacity:.4;text-decoration:none;margin-left:9px}.source:target{background:#fff1c9;box-shadow:0 0 0 8px #fff1c9}.tablewrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:15px}th,td{border:1px solid var(--line);padding:12px;vertical-align:top;text-align:left;min-width:110px}blockquote{margin:20px 0;padding:14px 20px;background:#eaf0e6;border-left:3px solid var(--accent)}blockquote p{white-space:pre-wrap}.toc li{margin:10px 0}footer{border-top:1px solid var(--line);max-width:1100px;margin:auto;padding:22px;color:var(--muted);font-size:13px}.actions{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0}.button,button{display:inline-block;padding:9px 18px;border:1px solid var(--accent);background:var(--accent);color:white;text-decoration:none;border-radius:5px;cursor:pointer}.button.secondary{background:transparent;color:var(--accent)}input[type=search]{width:min(100%,650px);padding:13px;border:1px solid var(--line);border-radius:5px;font:inherit}.searchrow{display:flex;gap:10px;flex-wrap:wrap}.sectionmark{padding-top:16px}.pager{display:flex;justify-content:space-between;gap:20px;margin-top:50px}.figure{width:100%;max-width:420px;height:auto}code{font-size:13px;overflow-wrap:anywhere}details{margin:16px 0}summary{cursor:pointer}.links{display:flex;flex-wrap:wrap;gap:16px}@media(max-width:600px){main{padding:25px 18px 50px}.reader p.source{font-size:18px}header{padding:14px 18px}h2{font-size:23px}.card{padding:18px}nav{gap:14px}.grid{grid-template-columns:1fr}}@media print{header,footer,.pager,.anchor{display:none}body{background:white}main{max-width:none}.card{break-inside:avoid}}
'''
JS='''
const form=document.querySelector('#search-form');
if(form){form.addEventListener('submit',async e=>{e.preventDefault();const q=document.querySelector('#query').value.trim().toLowerCase();const out=document.querySelector('#results');out.replaceChildren();if(!q){out.textContent='请输入关键词。';return;}try{const data=await fetch('search-index.json').then(r=>{if(!r.ok)throw Error();return r.json()});const runs=q.match(/[\\u3400-\\u9fff]+|[a-z0-9_-]+/g)||[];const terms=runs.flatMap(s=>/[\\u3400-\\u9fff]/.test(s)&&s.length>1?Array.from({length:s.length-1},(_,i)=>s.slice(i,i+2)):[s]);const hits=data.map(x=>{const text=(x.title+' '+x.text+' '+(x.terms||'')).toLowerCase();let score=text.includes(q)?100:0;for(const t of terms)if(text.includes(t))score+=1;return {...x,score}}).filter(x=>x.score>0).sort((a,b)=>b.score-a.score).slice(0,30);const note=document.createElement('p');note.textContent=hits.length?'以下为关键词候选，相关性不代表事实已核验。':'没有匹配，请换用本书术语或查阅目录。';out.append(note);for(const x of hits){const card=document.createElement('article');card.className='card';const a=document.createElement('a');a.href=x.url;a.textContent=x.title;const p=document.createElement('p');const pos=Math.max(0,x.text.toLowerCase().indexOf(q));p.textContent=x.text.slice(Math.max(0,pos-50),pos+200)+'…';card.append(a,p);out.append(card)}}catch(err){out.textContent='检索文件未能读取。请通过本地HTTP预览或线上网站使用检索；也可直接查阅目录。'}});const initial=new URLSearchParams(location.search).get('q');if(initial){document.querySelector('#query').value=initial.slice(0,200);form.requestSubmit();}}
'''

class Site:
    def __init__(self,root,out,config,production=False,base=None):
        self.root=root;self.out=out;self.cfg=config;self.production=production;self.base=base;self.pages=[];self.search=[]
        self.bundles=[load_bundle(root,w) for w in config['works']+config.get('archives',[])]
    def slug(self,d):
        return safe(d['entry']['id']+'--v'+d['metadata'].get('package_version','0').replace('.','-'))
    def page(self,path,title,body,description='',schema=None,reader=False):
        depth=len(Path(path).parts)-1;prefix='../'*depth
        canonical=''
        if self.base:canonical='<link rel="canonical" href="'+esc(self.base+'/'+quote(path,safe='/'))+'">'
        data=''
        if schema:data='<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script>'
        text='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+' · '+esc(self.cfg['site_title'])+'</title><meta name="description" content="'+esc(description or self.cfg['description'])+'"><meta name="robots" content="'+('index,follow' if self.production else 'noindex,nofollow')+'">'+canonical+'<link rel="stylesheet" href="'+prefix+'assets/site.css">'+data+'</head><body><header><a href="'+prefix+'index.html">'+esc(self.cfg['site_title'])+'</a><nav aria-label="主导航"><a href="'+prefix+'index.html">作品</a><a href="'+prefix+'search.html">检索</a><a href="'+prefix+'machine.html">知识文件</a><a href="'+prefix+'rights.html">版本与使用</a></nav></header><main'+(' class="reader"' if reader else '')+'>'+body+'</main><footer>作者：'+esc(self.cfg['author'])+' · '+('公开版' if self.production else '本地审阅版，尚未上线')+'。知识整理保留原文依据；作者观点、假说及虚构叙事各依所属作品解释。</footer><script src="'+prefix+'assets/site.js" defer></script></body></html>'
        p=self.out/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8');self.pages.append(path)
    def source_url(self,work,b):return 'works/'+work+'/read/'+safe(b['section_id'])+'.html#'+safe(b['id'])
    def build_work(self,d):
        entry=d['entry'];wid=self.slug(d);m=d['metadata'];w=m.get('work',{});title=w.get('title',wid);B={x['id']:x for x in d['blocks']};S={x['id']:x for x in d['sections']};folder='works/'+wid+'/'
        grouped=defaultdict(list)
        for b in d['blocks']:safe(b['id']);safe(b['section_id']);grouped[b['section_id']].append(b)
        def refs(item,up='../../../'):
            return ' '.join('<a href="'+up+self.source_url(wid,B[bid])+'">'+esc(bid)+'</a>' for bid in item.get('source_block_ids',[]))
        schema={'@context':'https://schema.org','@type':'Book' if entry['profile'] in ('thought','fiction') else 'CreativeWork','name':title,'author':{'@type':'Person','name':w.get('author_name_as_printed',self.cfg['author'])},'inLanguage':w.get('language','zh-CN'),'identifier':w.get('edition_identifier',wid),'description':self.cfg['description']}
        if self.base:schema['url']=self.base+'/'+folder+'index.html'
        chapters=[s for s in d['sections'] if s.get('level')==2]
        toc='<ol class="toc">'+''.join('<li><a href="read/'+esc(s['id'])+'.html">'+esc(s['title'])+'</a></li>' for s in d['sections'] if s['id'] in grouped)+'</ol>'
        subtitle=w.get('subtitle','')
        body='<div class="eyebrow">'+esc(PROFILE_LABEL[entry['profile']])+' / '+esc(m.get('package_version','待定版本'))+'</div><h1>'+esc(title)+'</h1><p class="lead">'+esc(subtitle)+'</p><p>作者 '+esc(w.get('author_name_as_printed',self.cfg['author']))+'</p><div class="actions"><a class="button" href="read/'+esc(next(iter(grouped)))+'.html">开始阅读</a><a class="button secondary" href="concepts.html">概念与知识</a><a class="button secondary" href="qa.html">问题与原文</a></div><p class="notice">此站呈现本书原文与依据原文整理的知识。整理条目不是新的审定正文；作者框架、案例阐释和未来设想不等于已经完成外部验证的结论。</p><div class="grid"><div class="card"><h2>'+str(len(chapters))+' 章</h2><p>完整目录与稳定段落编号</p></div><div class="card"><h2>'+str(len(d['concepts']))+' 个知识条目</h2><p>定义、边界及原文依据</p></div><div class="card"><h2>'+str(len(d['qa']))+' 个参考问题</h2><p>包含书内证据不足的边界</p></div></div><h2>目录</h2>'+toc+'<h2>原稿图像</h2><p class="muted">图像原件集中保存；原有位置及完整排版请参阅PDF。</p>'
        notices={'fiction':'此作品中的人物、事件与设定属于虚构世界；人物陈述不自动代表作者观点或现实事实。当前工具完成静态发布，剧透过滤和角色权限尚未实现。','essay':'短文按各自写作背景与版本理解。跨作品关联属于导读，不能以主题相近推定观点完全相同。','product':'产品资料须按型号、版本、适用范围和有效日期理解。未经证实的效果、认证、报价和承诺不应补写。'}
        if entry['profile'] in notices:
            body=re.sub(r'<p class="notice">.*?</p>','<p class="notice">'+esc(notices[entry['profile']])+'</p>',body,count=1)
            body=body.replace(str(len(chapters))+' 章',str(len(grouped))+' 节')
        for f in sorted((d['path']/'assets').glob('*')):
            if f.suffix.lower() in ('.jpg','.jpeg','.png'):
                target=self.out/folder/'images'/f.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
                body+='<img class="figure" loading="lazy" src="images/'+esc(f.name)+'" alt="原稿图像 '+esc(f.name)+'">'
        self.page(folder+'index.html',title,body,schema=schema)
        sections=list(grouped)
        for i,sid in enumerate(sections):
            sec=S[sid];starts_heading=grouped[sid][0]['kind']=='heading';parts=['<div class="eyebrow">'+esc(title)+'</div>'+('' if starts_heading else '<h1>'+esc(sec['title'])+'</h1>'),'<p class="muted">原文。PDF所在节起始页：'+esc(sec.get('pdf_page','未标注'))+'。页码不代表以下每段的实际页。</p>']
            for b in grouped[sid]:
                anchor='<a class="anchor" aria-label="引用段落 '+b['id']+'" href="#'+b['id']+'">'+b['id']+'</a>'
                text=esc(b['text'])
                if b['kind']=='table':
                    table=''.join('<tr>'+''.join('<'+('th' if j==0 else 'td')+'>'+esc(c).replace('\n','<br>')+'</'+('th' if j==0 else 'td')+'>' for c in r)+'</tr>' for j,r in enumerate(b['rows']))
                    parts.append('<div class="source tablewrap" id="'+b['id']+'">'+anchor+'<table>'+table+'</table></div>')
                elif b['kind']=='heading' or b.get('style')=='5':
                    tag='h1' if starts_heading and b is grouped[sid][0] else 'h2'
                    parts.append('<'+tag+' class="source sectionmark" id="'+b['id']+'">'+text.replace('\n','<br>')+anchor+'</'+tag+'>')
                else:parts.append('<p class="source" id="'+b['id']+'">'+text+anchor+'</p>')
                self.search.append({'kind':'source','title':title+' / '+sec['title']+' / '+b['id'],'text':b['text'],'url':self.source_url(wid,b)})
            prev='<a href="'+sections[i-1]+'.html">← 上一节</a>' if i else '<span></span>'
            nxt='<a href="'+sections[i+1]+'.html">下一节 →</a>' if i+1<len(sections) else '<span></span>'
            parts.append('<div class="pager">'+prev+'<a href="../index.html">目录</a>'+nxt+'</div>')
            self.page(folder+'read/'+sid+'.html',sec['title'],''.join(parts),reader=True)
        cards=[]
        for c in d['concepts']:
            safe(c['id']);href='concept/'+c['id']+'.html';cards.append('<article class="card"><h2><a href="'+href+'">'+esc(c['name'])+'</a></h2><p>'+esc(c['definition'][:130])+'…</p></article>')
            quotes=''.join('<blockquote><p>'+esc(q['quote'])+'</p><cite>'+refs({'source_block_ids':[q['block_id']]},'../../../')+'</cite></blockquote>' for q in c.get('supporting_quotes',[]))
            aliases='、'.join(a if isinstance(a,str) else a['term'] for a in c.get('aliases',[]))
            page='<div class="eyebrow">知识整理 / '+esc(STATUS_LABEL.get(c.get('claim_status'),'作者解释'))+'</div><h1>'+esc(c['name'])+'</h1><p class="muted">别名：'+esc(aliases)+'</p><p class="lead">'+esc(c['definition'])+'</p><h2>适用范围与边界</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in c.get('scope_and_limits',[]))+'</ul><h2>原文依据</h2>'+quotes+'<p>'+refs(c)+'</p><p><a href="../concepts.html">返回知识目录</a></p>'
            self.page(folder+href,c['name'],page,description=c['definition'][:160]);self.search.append({'kind':'concept','title':c['name'],'text':c['definition']+' '+aliases,'url':folder+href})
        # Propagate explicit editorial names/aliases to their cited source entries.
        aliases_by_id=defaultdict(list)
        for concept in d['concepts']:
            names=[concept['name']]+[a if isinstance(a,str) else a['term'] for a in concept.get('aliases',[])]
            for bid in concept['source_block_ids']:aliases_by_id[bid].extend(names)
        for item in self.search:
            if item['kind']=='source' and item['url'].startswith(folder):item['terms']=' '.join(dict.fromkeys(aliases_by_id[item['url'].rsplit('#',1)[-1]]))
        self.page(folder+'concepts.html',title+' · 知识条目','<h1>概念与知识</h1><p>每个条目均标明原文依据与适用边界。</p><div class="grid">'+''.join(cards)+'</div>')
        qbody='<h1>问题与原文</h1><p>参考答案是依据书稿整理的导读，不代表已经运行在线模型问答。</p>'
        for q in d['qa']:
            qbody+='<article class="card" id="'+safe(q['id'])+'"><h2>'+esc(q['query'])+'</h2><p>'+esc(q.get('answer',''))+'</p><p class="muted">'+esc(q.get('misreading_to_avoid',''))+'</p><p>'+refs(q,'../../')+'</p></article>'
            self.search.append({'kind':'qa','title':q['query'],'text':q.get('answer',''),'url':folder+'qa.html#'+q['id']})
        self.page(folder+'qa.html',title+' · 参考问答',qbody)
        claimbody='<h1>命题与论证</h1><p>以下归纳属于作者论述的知识整理。</p>'
        for c in d['claims']:claimbody+='<article class="card" id="'+safe(c['id'])+'"><h2>'+esc(c['claim'])+'</h2><p>'+esc(c.get('argument_summary',''))+'</p><p>'+refs(c,'../../')+'</p><ul>'+''.join('<li>'+esc(x)+'</li>' for x in c.get('scope_and_limits',[]))+'</ul></article>'
        self.page(folder+'claims.html',title+' · 命题',claimbody)
        # Only public deliverables are copied; no manuscript DOCX, private reports, credentials or configuration.
        machine=self.out/'machine'/wid;machine.mkdir(parents=True,exist_ok=True)
        for name in ['metadata.json','book.txt','book.jsonld','citation.json']:
            if (d['path']/name).exists():shutil.copy2(d['path']/name,machine/name)
        # Explicit public format allowlist: never copy arbitrary files from a working data folder.
        public_data=['blocks.jsonl','chunks.jsonl','sections.json','concepts.json','claims.json','relations.json','qa.jsonl','字段说明.txt']
        (machine/'data').mkdir(exist_ok=True)
        for name in public_data:
            source=d['path']/'data'/name
            if source.is_file():shutil.copy2(source,machine/'data'/name)
        declared_pdfs=[f['path'] for f in m.get('source_edition',{}).get('files',[]) if f.get('path','').lower().endswith('.pdf')]
        chosen=entry.get('public_pdf')
        if chosen and chosen not in declared_pdfs:raise ValueError('Public PDF must be a declared source asset')
        if not chosen and len(declared_pdfs)>1:raise ValueError('Multiple declared PDFs; select public_pdf explicitly')
        chosen=chosen or (declared_pdfs[0] if declared_pdfs else None)
        if chosen:
            pdf=(d['path']/chosen).resolve()
            if not pdf.is_relative_to(d['path'].resolve()):raise ValueError('PDF path escapes package')
            record=next(f for f in m['source_edition']['files'] if f['path']==chosen)
            if hashlib.sha256(pdf.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('PDF source hash mismatch')
            shutil.copy2(pdf,machine/'book.pdf')
        dump(machine/'web.jsonld',schema)
        exportmeta=read(machine/'metadata.json',{})
        if exportmeta:
            exportmeta['status']='公开静态网站发布副本' if self.production else '本地网站审阅副本；尚未上线'
            exportmeta.setdefault('work',{})['public_canonical_url']=self.base+'/'+folder+'index.html' if self.base else None
            for asset in exportmeta.get('source_edition',{}).get('files',[]):
                original=asset.pop('path')
                asset['source_bundle_path']=original
                asset['included_in_web_export']=original==chosen
                asset['path']='book.pdf' if original==chosen else None
            exportmeta['web_export_note']='source_bundle_path仅记录审阅源包内的历史路径，不是网站链接；path为当前导出副本路径，null表示未包含。'
            exportmeta['rights']['statement']=entry['rights']['statement'];dump(machine/'metadata.json',exportmeta)
    def run(self):
        if self.out.exists():shutil.rmtree(self.out)
        (self.out/'assets').mkdir(parents=True)
        (self.out/'.knowledge-site-output').write_text('generated-static-library-v1\n',encoding='utf-8')
        (self.out/'assets/site.css').write_text(CSS,encoding='utf-8');(self.out/'assets/site.js').write_text(JS,encoding='utf-8')
        for d in self.bundles:self.build_work(d)
        cards=''.join('<article class="card"><div class="eyebrow">'+esc(PROFILE_LABEL[d['entry']['profile']])+'</div><h2><a href="works/'+self.slug(d)+'/index.html">'+esc(d['metadata'].get('work',{}).get('title',d['entry']['id']))+'</a></h2><p>'+esc(d['metadata'].get('work',{}).get('subtitle',''))+'</p><div class="links"><a href="works/'+self.slug(d)+'/index.html">阅读</a><a href="works/'+self.slug(d)+'/concepts.html">知识条目</a><a href="works/'+self.slug(d)+'/claims.html">命题</a></div></article>' for d in self.bundles if d['entry'] in self.cfg['works'])
        self.page('index.html','作品首页','<div class="eyebrow">'+esc(self.cfg['author'])+' / WORKS & KNOWLEDGE</div><h1>从作品出发，<br>让思想有据可寻。</h1><p class="lead">阅读原文，理解概念，追溯每一条知识的出处。</p><div class="grid">'+cards+'</div><h2>如何使用</h2><div class="grid"><div><h3>阅读与理解</h3><p>按目录阅读完整正文，或从问题和概念进入具体论述。</p></div><div><h3>引用与核对</h3><p>每段保留来源编号，点击编号可以取得该段链接。版本信息帮助核对原文。</p></div><div><h3>资料与工具</h3><p>纯文本和结构化知识文件可供具备相关能力的工具读取。具体使用依作品许可。</p></div></div>')
        self.page('search.html','检索','<h1>检索作品与知识</h1><p>试试“GIR”“退出成本”“冗余”“主权个人”。检索在浏览器内进行。</p><form id="search-form"><label for="query">关键词</label><div class="searchrow"><input type="search" id="query" required maxlength="200"><button type="submit">检索</button></div></form><noscript><p>检索需要JavaScript；正文和目录可直接阅读。</p></noscript><div id="results" class="grid" aria-live="polite" style="margin-top:24px"></div>')
        machinebody='<h1>知识文件</h1><p>提供可直接读取的原文和知识整理。引用时请保留作者、作品、版本及来源段落。JSONL是数据格式，接入具体工具时仍需适配。</p>'
        for d in self.bundles:
            wid=self.slug(d);base='machine/'+wid+'/'
            machinebody+='<article class="card"><h2>'+esc(d['metadata'].get('work',{}).get('title',wid))+'</h2><ul>'+''.join('<li><a href="'+base+x+'">'+esc(label)+'</a></li>' for x,label in [('book.txt','全文 TXT'),('book.pdf','电子书 PDF'),('metadata.json','作品与版本信息'),('data/blocks.jsonl','原文段落 JSONL'),('data/concepts.json','知识条目 JSON'),('data/claims.json','命题 JSON'),('data/relations.json','关系 JSON'),('data/qa.jsonl','问答 JSONL'),('data/chunks.jsonl','检索切片 JSONL') ] if (self.out/base/x).exists())+'</ul></article>'
        self.page('machine.html','知识文件',machinebody)
        rights='<h1>版本与使用</h1><p>此站不以书稿日期代替正式出版日期。未确认的出版社、ISBN、DOI及百科条目均不填写。</p>'
        for d in self.bundles:rights+='<article class="card"><h2>'+esc(d['metadata'].get('work',{}).get('title',d['entry']['id']))+'</h2><p>知识包版本：'+esc(d['metadata'].get('package_version','未标注'))+'</p><p>'+esc(d['entry']['rights']['statement'])+'</p><p>原文与知识整理分开管理。引用请核对来源；第三方历史、科学和统计材料仍需独立核验。</p></article>'
        self.page('rights.html','版本与使用',rights)
        dump(self.out/'search-index.json',self.search)
        (self.out/'.nojekyll').touch()
        robots='User-agent: *\n'+('Allow: /\nSitemap: '+self.base+'/sitemap.xml\n' if self.production else 'Disallow: /\n')
        (self.out/'robots.txt').write_text(robots,encoding='utf-8')
        if self.base:
            xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+esc(self.base+'/'+quote(p,safe='/'))+'</loc></url>' for p in self.pages)+'</urlset>'
            (self.out/'sitemap.xml').write_text(xml,encoding='utf-8')
        dump(self.out/'build-info.json',{'mode':'production' if self.production else 'review','base_url':self.base,'html_pages':len(self.pages),'search_entries':len(self.search),'works':[x['id'] for x in self.cfg['works']],'publicly_deployed':False,'note':'构建成功不表示已部署、收录或被模型训练。'})
        print(json.dumps({'output':str(self.out),'pages':len(self.pages),'search_entries':len(self.search),'mode':'production' if self.production else 'review'},ensure_ascii=False))

def build(root,out,production=False,base=None):
    cfg=read(root/'site.json');base=(base or cfg.get('base_url') or '').rstrip('/') or None
    if not cfg or not isinstance(cfg.get('works'),list):raise ValueError('Missing site.json works configuration')
    entries=cfg['works']+cfg.get('archives',[])
    if len({w['id'] for w in cfg['works']})!=len(cfg['works']):raise ValueError('Only one current edition per work ID is allowed')
    bundles=[load_bundle(root,w) for w in entries]
    slugs=[safe(w['entry']['id']+'--v'+w['metadata'].get('package_version','0').replace('.','-')) for w in bundles]
    if len(set(slugs))!=len(slugs):raise ValueError('Duplicate work/version URL; each published edition must have a unique path')
    if any(w['profile'] not in ('thought','fiction','essay','product') for w in entries):raise ValueError('Unknown content profile')
    if production:
        u=urlsplit(base or '')
        if u.scheme!='https' or not u.netloc or u.query or u.fragment:raise ValueError('Production requires a real HTTPS base URL, without query or fragment')
        if cfg.get('public_release_approved') is not True:raise ValueError('Public release is not approved in site.json; boolean true required')
        if any(w.get('rights',{}).get('public_web') is not True for w in entries):raise ValueError('Public web rights must be confirmed for every work; boolean true required')
    resolved_out=out.resolve();resolved_root=root.resolve()
    if resolved_out in (resolved_root, resolved_root.parent) or resolved_root.is_relative_to(resolved_out):raise ValueError('Unsafe output location')
    if not resolved_out.is_relative_to(resolved_root):raise ValueError('Output must be a dedicated build folder inside the project root')
    for w in entries:
        p=resolve_package(root,w)
        if p.is_relative_to(resolved_out) or resolved_out.is_relative_to(p):raise ValueError('Output overlaps source package')
    if resolved_out.exists() and (not resolved_out.is_dir() or not (resolved_out/'.knowledge-site-output').is_file()):raise ValueError('Refusing to replace a folder not marked as generated site output')
    Site(root,out,cfg,production,base).run()
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path);p.add_argument('--production',action='store_true');p.add_argument('--base-url');a=p.parse_args()
    build(a.root.resolve(),a.output or a.root/'dist',a.production,a.base_url)
