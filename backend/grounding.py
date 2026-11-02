"""Evidence-only multi-passage answer synthesis with conservative relevance gating.
Never publish LLM-generated claims without independent evidence validation.
"""
import re, os
from functools import lru_cache
STOP=set('a an the and or for to of in on is are was were be been with this that it i you my me we our how what when where why can could would should do does did please help about have has had from at by'.split())
NO_MATCH='I could not find sufficiently relevant approved information for this question. A support specialist can investigate if you choose to create a ticket.'

def terms(s):return {w for w in re.findall(r'[a-z0-9]+',s.lower()) if len(w)>2 and w not in STOP}

def _sentences(text):
    for sentence in re.split(r'(?<=[.!?])\s+|\n+',text):
        s=sentence.strip()
        if 24<=len(s)<=450:yield s

@lru_cache(maxsize=1)
def _semantic_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(os.getenv('EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'))

def _semantic_scores(question, sentences):
    """Optional semantic ranking; safe lexical fallback when embeddings unavailable."""
    if os.getenv('SEMANTIC_GROUNDING','1') == '0': return None
    try:
        import numpy as np
        model=_semantic_model()
        vectors=model.encode([question]+sentences, normalize_embeddings=True,convert_to_numpy=True)
        return [float(v) for v in vectors[1:] @ vectors[0]]
    except (ImportError, RuntimeError, OSError, ValueError):
        return None

def grounded_answer(question,matches,max_sentences=3):
    q=terms(question)
    if not q or not matches:return NO_MATCH,0.0,'no_evidence'
    candidates=[]
    for m in matches:
        source=str(m.get('source','')); passage=str(m.get('text',''))
        if not source or not passage: continue
        for sentence in _sentences(passage):
            overlap=q & terms(sentence)
            candidates.append((sentence,source,overlap))
    if not candidates:return NO_MATCH,0.0,'insufficient_evidence'
    similarities=_semantic_scores(question,[c[0] for c in candidates])
    threshold=float(os.getenv('SEMANTIC_GROUNDING_THRESHOLD','0.52'))
    ranked=[]
    for i,(sentence,source,overlap) in enumerate(candidates):
        lexical=len(overlap)/len(q)
        semantic=similarities[i] if similarities is not None else 0.0
        # Semantic similarity alone can be misleading. Require a fairly strong
        # similarity and at least one meaningful shared term or a very strong match.
        supported=(bool(overlap) or (semantic>=threshold and (overlap or semantic>=0.72)))
        if supported: ranked.append((max(lexical,semantic),sentence,source,overlap))
    if not ranked:return NO_MATCH,0.0,'insufficient_evidence'
    ranked.sort(key=lambda item:item[0],reverse=True)
    selected=[];seen=set();covered=set()
    for score,sentence,source,overlap in ranked:
        if sentence.casefold() in seen or (not (overlap-covered) and selected):continue
        selected.append((sentence,source));seen.add(sentence.casefold());covered|=overlap
        if len(selected)>=max_sentences:break
    coverage=len(covered)/len(q)
    semantic_best=max((x[0] for x in ranked),default=0.0)
    if similarities is None and (coverage<0.60 or (len(q)>=3 and len(covered)<2)):
        return NO_MATCH,round(coverage,2),'low_evidence_coverage'
    if similarities is not None and coverage<0.60 and semantic_best<threshold:
        return NO_MATCH,round(semantic_best,2),'low_semantic_relevance'
    answer=' '.join(f'{sentence} (Source: {source})' for sentence,source in selected)
    assert validate_grounding(answer,selected)
    return answer,round(max(coverage,semantic_best),2),'extractive_verified'

def validate_grounding(answer,chosen):
    return bool(chosen) and answer==' '.join(f'{s} (Source: {src})' for s,src in chosen)
