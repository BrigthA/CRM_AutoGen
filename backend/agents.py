"""Four specialized AutoGen agents. Deterministic fallbacks keep local demo operational without API keys."""
import os, json, re, time
from contextvars import ContextVar
from .rag import retrieve
from .grounding import grounded_answer, validate_grounding

SYSTEMS={
'QueryAgent':'Classify a customer complaint. Return JSON with category, urgency Low/Medium/High, sentiment, summary, and risk_flags. Never invent customer facts.',
'KnowledgeAgent':'Use only search_kb tool results. Return matching passages and source names. Do not fabricate policies.',
'ResolutionAgent':'Answer using only retrieved knowledge. Cite file names. If knowledge is missing, explicitly say it is unavailable; never promise completed actions.',
'LogAgent':'Record the ticket with log_ticket and indicate escalation based on mandatory rules. Emit LOGGED only after successful persistence.'}

def classify(text):
    t=text.lower()
    categories={'Billing':['charge','charged','card','payment','fraud','bank'], 'Refund':['return','refund'], 'Shipping':['order','shipping','delivery','late','arrive'], 'Account':['password','login','log in','account'], 'Product':['broken','blender','replacement','damaged']}
    category=next((k for k,words in categories.items() if any(w in t for w in words)),'General')
    flags=[k for k,words in {'legal':['lawyer','legal','sue','court'],'fraud':['fraud','scam'],'payment_dispute':['charged','chargeback','payment dispute','charged my card']}.items() if any(w in t for w in words)]
    angry=any(w in t for w in ['fix this now','furious','angry','unacceptable','lawyer'])
    urgency='High' if flags or angry else 'Medium' if any(w in t for w in ['broken','late','refund']) else 'Low'
    return {'category':category,'urgency':urgency,'sentiment':'Angry' if angry else 'Neutral','summary':text[:180], 'risk_flags':flags}

_TOOL_EVENTS=ContextVar('tool_events',default=None)

def _record_tool(name, success, elapsed_ms, detail=''):
    events=_TOOL_EVENTS.get()
    if events is not None: events.append({'tool':name,'success':success,'elapsed_ms':elapsed_ms,'detail':str(detail)[:160]})

def search_kb(query: str) -> str:
    """Search the approved customer-support knowledge base and return matching passages with source filenames."""
    start=time.monotonic()
    try:
        matches=retrieve(query,top_k=5)
    except Exception as exc:
        _record_tool('search_kb',False,int((time.monotonic()-start)*1000),type(exc).__name__)
        raise
    _record_tool('search_kb',True,int((time.monotonic()-start)*1000),f'{len(matches)} passages')
    return json.dumps([{'source':m['source'],'passage':m['text'][:1100]} for m in matches],ensure_ascii=False)


def log_ticket(category: str, urgency: str, sentiment: str, summary: str,
               answer: str, sources: str, escalate: bool, reason: str) -> str:
    """Append an audit row for the processed request; this does NOT create a CRM support ticket."""
    import csv, pathlib, threading
    from datetime import datetime, timezone
    path=pathlib.Path(os.getenv('AGENT_AUDIT_CSV','data/agent_audit.csv'))
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=['timestamp','category','urgency','sentiment','summary','answer','sources','escalate','reason']
    row=dict(zip(fields,[datetime.now(timezone.utc).isoformat(),category,urgency,sentiment,summary,answer,sources,str(escalate),reason]))
    start=time.monotonic()
    with _AUDIT_LOCK:
        with path.open('a',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields)
            if f.tell()==0: writer.writeheader()
            writer.writerow(row)
    _record_tool('log_ticket',True,int((time.monotonic()-start)*1000),str(path))
    return 'LOGGED'


import threading
_AUDIT_LOCK=threading.Lock()


def _parse_json(content):
    if isinstance(content,dict): return content
    match=re.search(r'\{.*\}',str(content),re.S)
    return json.loads(match.group(0)) if match else {}


async def _autogen_pipeline(text, classification, matches, sources):
    from autogen_agentchat.agents import AssistantAgent
    from autogen_ext.models.openai import OpenAIChatCompletionClient
    client=OpenAIChatCompletionClient(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),api_key=os.environ['OPENAI_API_KEY'])
    stages=[]
    events=[]
    token=_TOOL_EVENTS.set(events)
    async def stage(agent, task):
        start=time.monotonic()
        result=await agent.run(task=task)
        content=result.messages[-1].content
        stages.append((agent.name,str(content),int((time.monotonic()-start)*1000)))
        return content
    try:
        q=AssistantAgent('QueryAgent',model_client=client,system_message=SYSTEMS['QueryAgent']+' Return a single JSON object.')
        raw=await stage(q,'Classify this customer message as JSON: '+text)
        predicted=_parse_json(raw)
        for key in ('category','sentiment','summary'):
            if isinstance(predicted.get(key),str): classification[key]=predicted[key][:250]
        if predicted.get('urgency') in ('Low','Medium','High') and classification['urgency']!='High': classification['urgency']=predicted['urgency']
        # A real tool invocation is mandatory; do not trust the model to fabricate retrieved passages.
        # Capture actual tool output rather than relying solely on ContextVar propagation.
        # Some AutoGen versions run tools in a different execution context.
        tool_payloads=[]
        def verified_search_kb(query: str) -> str:
            """Search approved KB passages and return filename-backed evidence."""
            result=search_kb(query)
            tool_payloads.append(result)
            return result
        knowledge=AssistantAgent('KnowledgeAgent',model_client=client,tools=[verified_search_kb],system_message=SYSTEMS['KnowledgeAgent']+' You MUST call verified_search_kb once before responding.',reflect_on_tool_use=True)
        await stage(knowledge,'Call verified_search_kb for this question and report its source filenames: '+text)
        if not tool_payloads:
            # Deterministic fallback is disclosed in stage logs; never claim an agent tool call.
            tool_payloads.append(search_kb(text))
            stages.append(('ToolVerification','KnowledgeAgent did not call the tool; backend executed search_kb as a verified fallback.',0))
        else:
            stages.append(('ToolVerification','KnowledgeAgent executed verified_search_kb successfully.',0))
        verified_matches=[{'source':x['source'],'text':x['passage']} for x in json.loads(tool_payloads[-1])]
        matches=verified_matches
        sources=sorted({m['source'] for m in matches})
        evidence=json.dumps([{'source':m['source'],'passage':m['text']} for m in matches],ensure_ascii=False)
        resolution=AssistantAgent('ResolutionAgent',model_client=client,system_message=SYSTEMS['ResolutionAgent']+' Respond in plain text, no JSON. Do not add facts beyond evidence.')
        if matches:
            proposed=str(await stage(resolution,'Customer question: '+text+'\nVerified evidence: '+evidence+'\nWrite a concise helpful reply citing source filenames.'))
        else:
            proposed=str(await stage(resolution,'There are no matching approved passages. Say honestly that no approved answer was found. Question: '+text))
        # Fail closed: a filename citation is NOT proof of claim-level grounding.
        # Only return verbatim source sentences selected from the verified retrieval.
        answer, confidence, grounding = grounded_answer(text, matches)
        stages.append(('GroundingValidator',json.dumps({'status':grounding,'llm_draft_accepted':False,'draft_length':len(proposed)}),0))
        reasons=_escalation_reasons(classification, matches, confidence)
        # The agent is instructed to call log_ticket, and the backend verifies persistence separately.
        log_agent=AssistantAgent('LogAgent',model_client=client,tools=[log_ticket],system_message=SYSTEMS['LogAgent']+' Call log_ticket exactly once with all required fields. No customer ticket is created by this tool.',reflect_on_tool_use=True)
        await stage(log_agent,'Log this processed request using log_ticket. category='+classification['category']+' urgency='+classification['urgency']+' sentiment='+classification['sentiment']+' summary='+classification['summary']+' answer='+answer+' sources='+','.join(sources)+' escalate='+str(bool(reasons))+' reason='+'; '.join(reasons))
        if not any(e['tool']=='log_ticket' and e['success'] for e in events):
            log_ticket(classification['category'],classification['urgency'],classification['sentiment'],classification['summary'],answer,','.join(sources),bool(reasons),'; '.join(reasons))
            stages.append(('ToolVerification','LogAgent tool invocation not verified; backend persisted audit fallback.',0))
        stages.append(('ToolVerification',json.dumps(events[-1]),0))
        return classification,answer,sources,confidence,reasons,stages
    finally:
        _TOOL_EVENTS.reset(token)
        await client.close()


def _escalation_reasons(classification,matches,confidence):
    reasons=[]
    if classification['urgency']=='High': reasons.append('High urgency')
    if classification['sentiment']=='Angry': reasons.append('Angry customer')
    reasons.extend(classification.get('risk_flags',[]))
    if not matches: reasons.append('No matching knowledge')
    if confidence<0.5: reasons.append('Low confidence')
    return list(dict.fromkeys(reasons))


def run_pipeline(text, customer_context=None):
    """Execute four genuine AutoGen agents with tools when OPENAI_API_KEY is configured.

    In offline demo mode deterministic processing remains available, explicitly marked as fallback.
    """
    classification=classify(text)
    start=time.monotonic()
    matches=retrieve(text)
    sources=sorted({m['source'] for m in matches})
    if os.getenv('OPENAI_API_KEY'):
        import asyncio
        # Do not silently misrepresent an AutoGen failure as successful agent execution.
        return asyncio.run(_autogen_pipeline(text,classification,matches,sources))
    stages=[('QueryAgent',json.dumps({'mode':'offline-fallback',**classification}),0),
            ('KnowledgeAgent',json.dumps({'mode':'offline-fallback','sources':sources,'passages':len(matches)}),int((time.monotonic()-start)*1000))]
    response, confidence, grounding = grounded_answer(text, matches)
    stages.append(('ResolutionAgent',json.dumps({'mode':'offline-fallback','response':response,'confidence':confidence}),0))
    reasons=_escalation_reasons(classification,matches,confidence)
    marker=log_ticket(classification['category'],classification['urgency'],classification['sentiment'],classification['summary'],response,','.join(sources),bool(reasons),'; '.join(reasons))
    stages.append(('LogAgent',json.dumps({'mode':'offline-fallback','status':marker,'escalate':bool(reasons),'reasons':reasons}),0))
    return classification,response,sources,confidence,reasons,stages
