"""Benchmark real KB retrieval with cold/warm latency and labeled relevance checks.
Run: python -m scripts.benchmark_retrieval --queries tests/retrieval_queries.json
Queries JSON: [{"query":"...","expected_sources":["policy.md"]}, ...]
"""
import argparse,json,time,statistics
from pathlib import Path
from backend.rag import retrieve,invalidate_index
from backend.grounding import grounded_answer

def run(queries, output):
    invalidate_index()
    timings=[]; records=[]
    for row in queries:
        start=time.perf_counter();matches=retrieve(row['query']);ms=round((time.perf_counter()-start)*1000,2)
        answer,confidence,status=grounded_answer(row['query'],matches)
        actual={m['source'] for m in matches};expected=set(row.get('expected_sources',[]))
        records.append({'query':row['query'],'latency_ms':ms,'sources':sorted(actual),'expected_sources':sorted(expected),'hit_at_5':bool(actual&expected) if expected else None,'grounding_status':status,'confidence':confidence,'answer':answer})
        timings.append(ms)
    labeled=[r['hit_at_5'] for r in records if r['hit_at_5'] is not None]
    report={'query_count':len(records),'cold_first_query_ms':timings[0] if timings else None,'mean_ms':round(statistics.mean(timings),2) if timings else None,'median_ms':round(statistics.median(timings),2) if timings else None,'p95_ms':sorted(timings)[max(0,int(.95*(len(timings)-1)))] if timings else None,'hit_at_5':round(sum(labeled)/len(labeled),3) if labeled else None,'results':records}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--queries',required=True);parser.add_argument('--output',default='data/retrieval_benchmark.json');args=parser.parse_args()
    report=run(json.loads(Path(args.queries).read_text(encoding='utf-8')),Path(args.output))
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
