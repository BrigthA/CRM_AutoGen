"""Persistent hybrid BM25 + FAISS retrieval; indexes rebuilt only on KB changes."""
import os,re,json,hashlib,threading,tempfile
from pathlib import Path
from functools import lru_cache
from .db import SessionLocal,Document

_LOCK=threading.RLock()
_CACHE=None
STOP=set('the and for with this that what where how can you my is are a i to of in it do please help me about'.split())

def chunks(text,size=1100,overlap=150):
    result=[]; pos=0
    while pos<len(text):
        result.append(text[pos:pos+size])
        if pos+size>=len(text):break
        pos+=size-overlap
    return result

def corpus():
    with SessionLocal() as db:
        docs=db.query(Document).order_by(Document.id).all()
        return [{'key':f'{d.id}:{i}','source':d.filename,'text':part,'document_id':d.id} for d in docs for i,part in enumerate(chunks(d.content))]

@lru_cache(maxsize=1)
def encoder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(os.getenv('EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'))

def index_dir():return Path(os.getenv('RAG_INDEX_DIR','data/rag_index'))

def _signature(items):
    h=hashlib.sha256()
    h.update(os.getenv('EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2').encode())
    for item in items:
        h.update(item['key'].encode());h.update(item['source'].encode());h.update(item['text'].encode())
    return h.hexdigest()

def invalidate_index():
    global _CACHE
    with _LOCK:_CACHE=None

def _load():
    global _CACHE
    with _LOCK:
        if _CACHE is not None:return _CACHE
        items=corpus();signature=_signature(items);folder=index_dir();meta=folder/'metadata.json';idxfile=folder/'vectors.faiss'
        faiss_index=None
        try:
            import faiss
            if meta.exists() and idxfile.exists():
                stored=json.loads(meta.read_text(encoding='utf-8'))
                if stored.get('signature')==signature and stored.get('count')==len(items):
                    candidate=faiss.read_index(str(idxfile))
                    if candidate.ntotal==len(items):faiss_index=candidate
            if faiss_index is None and items:
                import numpy as np
                vectors=encoder().encode([x['text'] for x in items],normalize_embeddings=True,convert_to_numpy=True).astype('float32')
                faiss_index=faiss.IndexFlatIP(vectors.shape[1]);faiss_index.add(vectors)
                folder.mkdir(parents=True,exist_ok=True)
                # Write data before metadata; signature protects readers from stale index files.
                temp=folder/'vectors.tmp.faiss';faiss.write_index(faiss_index,str(temp));os.replace(temp,idxfile)
                temp_meta=folder/'metadata.tmp.json';temp_meta.write_text(json.dumps({'signature':signature,'count':len(items)}),encoding='utf-8');os.replace(temp_meta,meta)
        except (ImportError,OSError,ValueError,RuntimeError):
            faiss_index=None # BM25 still works without embedding dependencies
        try:
            from rank_bm25 import BM25Okapi
            bm=BM25Okapi([re.findall(r'\w+',x['text'].lower()) for x in items]) if items else None
        except ImportError:bm=None
        _CACHE=(items,bm,faiss_index)
        return _CACHE

def retrieve(query,top_k=5):
    from collections import defaultdict
    items,bm,idx=_load()
    if not items or not query.strip():return []
    rankings=[]
    if bm is not None:
        scores=bm.get_scores(re.findall(r'\w+',query.lower()))
        rankings.append(sorted(range(len(items)),key=lambda i:float(scores[i]),reverse=True)[:20])
    if idx is not None:
        try:
            import numpy as np
            q=encoder().encode([query],normalize_embeddings=True,convert_to_numpy=True).astype('float32')
            similarities,ids=idx.search(q,min(20,len(items)))
            rankings.append([int(i) for i in ids[0] if i>=0])
        except (ImportError,RuntimeError,ValueError):pass
    if not rankings:return []
    combined=defaultdict(float)
    for ranklist in rankings:
        for rank,i in enumerate(ranklist):combined[i]+=1/(60+rank+1)
    terms=set(re.findall(r'\w+',query.lower()))-STOP
    results=[]
    for i in sorted(combined,key=combined.get,reverse=True)[:max(20,top_k)]:
        overlap=terms.intersection(set(re.findall(r'\w+',items[i]['text'].lower())))
        # Keep semantic matches for paraphrases when FAISS exists; grounding decides if safe.
        if overlap or idx is not None:
            results.append({**items[i],'score':round(combined[i],6)})
        if len(results)>=top_k:break
    return results
