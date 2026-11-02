from dotenv import load_dotenv
load_dotenv()
import os, io, csv, json, smtplib
from datetime import timedelta
from email.message import EmailMessage
from typing import Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from .db import SessionLocal, Customer, Ticket, Message, Document, Run, Feedback, Review, Notification, Conversation, ChatTurn, now
from .agents import run_pipeline
from .guardrails import validate_customer_input
from .rag import retrieve, invalidate_index
from .notifications import notify_escalation

app=FastAPI(title='AI Support CRM API',version='0.1.0')
class Complaint(BaseModel):
    customer_name:str=Field(min_length=1,max_length=150)
    email:Optional[str]=None
    order_id:Optional[str]=None
    complaint:str=Field(min_length=5,max_length=10000)
class ReviewIn(BaseModel):
    action:str
    reviewer:str='Admin'
    notes:str=''
    response:Optional[str]=None
class FeedbackIn(BaseModel):
    helpful:bool
    comment:str=''
class StatusIn(BaseModel):
    status:str
    assigned_to:Optional[str]=None

def ticket_dict(t,customer=None):
    return {'id':t.id,'ticket_id':f'TKT-{t.id:04d}','customer_id':t.customer_id,'customer_name':customer.name if customer else '', 'order_id':t.order_id,'complaint':t.complaint,'category':t.category,'urgency':t.urgency,'sentiment':t.sentiment,'summary':t.summary,'response':t.response,'sources':t.sources.split(',') if t.sources else [],'status':t.status,'escalation_reason':t.escalation_reason,'confidence':t.confidence,'assigned_to':t.assigned_to,'created_at':t.created_at.isoformat() if t.created_at else '', 'due_at':t.due_at.isoformat() if t.due_at else ''}

@app.get('/health')
def health(): return {'status':'ok'}
@app.post('/tickets')
def submit(payload:Complaint):
    check=validate_customer_input(payload.complaint)
    if not check.allowed: raise HTTPException(status_code=422,detail=check.reason)
    payload.complaint=check.text
    with SessionLocal() as db:
        customer=db.query(Customer).filter(Customer.email==payload.email).first() if payload.email else None
        if not customer:
            customer=Customer(name=payload.customer_name,email=payload.email)
            db.add(customer); db.flush()
        ticket=Ticket(customer_id=customer.id,order_id=payload.order_id,complaint=payload.complaint,status='In Progress',due_at=now()+timedelta(hours=24))
        db.add(ticket); db.flush(); ticket_id=ticket.id
        db.add(Message(ticket_id=ticket_id,role='customer',content=payload.complaint)); db.commit()
    try:
        classification,response,sources,confidence,reasons,stages=run_pipeline(payload.complaint)
        with SessionLocal() as db:
            t=db.get(Ticket,ticket_id)
            t.category=classification['category']; t.urgency=classification['urgency']; t.sentiment=classification['sentiment']; t.summary=classification['summary']; t.response=response; t.sources=','.join(sources); t.confidence=confidence; t.escalation_reason='; '.join(reasons) or ('High urgency requires human review' if str(t.urgency).strip().lower()=='high' else ''); t.status='Escalated' if reasons or str(t.urgency).strip().lower()=='high' else 'Answered'; t.updated_at=now()
            t.due_at=t.created_at+timedelta(hours=4 if t.urgency=='High' else 24 if t.urgency=='Medium' else 72)
            db.add(Message(ticket_id=ticket_id,role='assistant',content=response))
            for name,detail,ms in stages: db.add(Run(ticket_id=ticket_id,agent=name,detail=detail,duration_ms=ms))
            db.commit()
            if t.status=='Escalated': notify_escalation(t, db.get(Customer,t.customer_id))
            return ticket_dict(t,db.get(Customer,t.customer_id))
    except Exception as exc:
        with SessionLocal() as db:
            t=db.get(Ticket,ticket_id); t.status='Escalated'; t.escalation_reason='Processing failure: requires human review'; db.commit()
            notify_escalation(t,db.get(Customer,t.customer_id))
        raise HTTPException(503,'Ticket created but AI processing failed; human review required') from exc

@app.get('/tickets')
def tickets(search:str='',status:str='',category:str='',urgency:str='',limit:int=Query(100,ge=1,le=1000)):
    with SessionLocal() as db:
        q=db.query(Ticket,Customer).join(Customer,Ticket.customer_id==Customer.id)
        if search:
            term=f'%{search}%'; q=q.filter(or_(Ticket.complaint.ilike(term),Ticket.summary.ilike(term),Ticket.order_id.ilike(term),Customer.name.ilike(term)))
            if search.upper().startswith('TKT-') and search[4:].isdigit(): q=q.filter(Ticket.id==int(search[4:]))
        if status: q=q.filter(Ticket.status==status)
        if category: q=q.filter(Ticket.category==category)
        if urgency: q=q.filter(Ticket.urgency==urgency)
        return [ticket_dict(t,c) for t,c in q.order_by(Ticket.id.desc()).limit(limit).all()]
@app.get('/tickets/export')
def export():
    data=tickets(limit=1000); out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=list(data[0].keys()) if data else ['ticket_id','status']); writer.writeheader()
    for r in data: writer.writerow({k:json.dumps(v) if isinstance(v,list) else v for k,v in r.items()})
    return StreamingResponse(iter([out.getvalue()]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=tickets.csv'})
@app.get('/tickets/{ticket_id}')
def get_ticket(ticket_id:int):
    with SessionLocal() as db:
        t=db.get(Ticket,ticket_id)
        if not t: raise HTTPException(404,'Ticket not found')
        result=ticket_dict(t,db.get(Customer,t.customer_id)); result['messages']=[{'role':m.role,'content':m.content} for m in db.query(Message).filter_by(ticket_id=t.id).order_by(Message.id)]; result['agent_runs']=[{'agent':r.agent,'detail':r.detail,'duration_ms':r.duration_ms} for r in db.query(Run).filter_by(ticket_id=t.id).order_by(Run.id)]; return result
@app.post('/tickets/{ticket_id}/review')
def review(ticket_id:int,payload:ReviewIn):
    if payload.action not in ['Approve','Reject','Resolve','Reopen','Assign']: raise HTTPException(400,'Invalid review action')
    with SessionLocal() as db:
        t=db.get(Ticket,ticket_id)
        if not t: raise HTTPException(404,'Ticket not found')
        if payload.response is not None: t.response=payload.response
        t.status={'Approve':'Answered','Reject':'Escalated','Resolve':'Resolved','Reopen':'Open','Assign':'In Progress'}[payload.action]
        if payload.action=='Assign': t.assigned_to=payload.reviewer
        t.updated_at=now(); db.add(Review(ticket_id=ticket_id,action=payload.action,notes=payload.notes,reviewer=payload.reviewer)); db.commit()
        if payload.action=='Reject': notify_escalation(t,db.get(Customer,t.customer_id))
        return ticket_dict(t,db.get(Customer,t.customer_id))
@app.post('/tickets/{ticket_id}/feedback')
def feedback(ticket_id:int,payload:FeedbackIn):
    with SessionLocal() as db:
        if not db.get(Ticket,ticket_id): raise HTTPException(404,'Ticket not found')
        db.add(Feedback(ticket_id=ticket_id,helpful=payload.helpful,comment=payload.comment)); db.commit(); return {'saved':True}
@app.get('/customers')
def customers():
    with SessionLocal() as db:
        return [{'id':c.id,'name':c.name,'email':c.email,'phone':c.phone,'language':c.language,'tickets':db.query(Ticket).filter_by(customer_id=c.id).count()} for c in db.query(Customer).order_by(Customer.id.desc()).all()]
@app.get('/customers/{customer_id}')
def customer(customer_id:int):
    with SessionLocal() as db:
        c=db.get(Customer,customer_id)
        if not c: raise HTTPException(404,'Customer not found')
        return {'id':c.id,'name':c.name,'email':c.email,'language':c.language,'tickets':[ticket_dict(t,c) for t in db.query(Ticket).filter_by(customer_id=c.id).order_by(Ticket.id.desc())]}
@app.get('/documents')
def documents():
    with SessionLocal() as db: return [{'id':d.id,'filename':d.filename,'version':d.version,'created_at':d.created_at.isoformat()} for d in db.query(Document).order_by(Document.id.desc())]
# Each file is validated independently so a bad document does not abort a batch.
import hashlib
from fastapi import Form

def _extract_document(name: str, data: bytes) -> str:
    if not name.lower().endswith(('.pdf', '.txt', '.md')):
        raise ValueError('Only PDF, TXT and MD are supported')
    if len(data) > 8 * 1024 * 1024:
        raise ValueError('File exceeds 8 MB')
    if not data:
        raise ValueError('Empty file')
    if name.lower().endswith('.pdf'):
        from pypdf import PdfReader
        try:
            content = '\n'.join(page.extract_text() or '' for page in PdfReader(io.BytesIO(data)).pages)
        except Exception as exc:
            raise ValueError('Cannot parse PDF') from exc
    else:
        try:
            content = data.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValueError('Use UTF-8 text files') from exc
    if not content.strip():
        raise ValueError('No extractable text found')
    return content

def _save_document(name: str, data: bytes) -> dict:
    content = _extract_document(name, data)
    # Normalized text also detects the same document uploaded as PDF and Markdown.
    normalized = ' '.join(content.split()).casefold()
    digest = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    with SessionLocal() as db:
        existing_docs = db.query(Document).all()
        for old in existing_docs:
            if hashlib.sha256(' '.join(old.content.split()).casefold().encode('utf-8')).hexdigest() == digest:
                return {'filename': name, 'status': 'skipped', 'reason': f'Duplicate content already stored as {old.filename} (ID {old.id})', 'document_id': old.id}
        prior = [d for d in existing_docs if d.filename.casefold() == name.casefold()]
        version = max((d.version for d in prior), default=0) + 1
        doc = Document(filename=name, content=content, version=version)
        db.add(doc); db.commit(); db.refresh(doc)
        invalidate_index()
        return {'filename': name, 'status': 'uploaded', 'id': doc.id, 'characters': len(content), 'version': version}

@app.post('/documents/upload')
async def upload(file: UploadFile = File(...)):
    name = (file.filename or 'untitled').replace('\\', '/').split('/')[-1][:255]
    data = await file.read(8 * 1024 * 1024 + 1)
    try:
        result = _save_document(name, data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return result

@app.post('/documents/upload-batch')
async def upload_batch(files: list[UploadFile] = File(...)):
    if len(files) > 50:
        raise HTTPException(400, 'Maximum 50 files per batch')
    results = []
    for file in files:
        name = (file.filename or 'untitled').replace('\\', '/').split('/')[-1][:255]
        try:
            data = await file.read(8 * 1024 * 1024 + 1)
            results.append(_save_document(name, data))
        except (ValueError, Exception) as exc:
            # Unexpected failures are reported per-file; no raw stack traces to clients.
            results.append({'filename': name, 'status': 'failed', 'reason': str(exc) if isinstance(exc, ValueError) else 'Server error processing file'})
        finally:
            await file.close()
    return {'total': len(results), 'uploaded': sum(x['status']=='uploaded' for x in results), 'skipped': sum(x['status']=='skipped' for x in results), 'failed': sum(x['status']=='failed' for x in results), 'results': results}

@app.delete('/documents/{document_id}')
def delete_doc(document_id:int):
    with SessionLocal() as db:
        d=db.get(Document,document_id)
        if not d: raise HTTPException(404,'Document not found')
        db.delete(d); db.commit(); invalidate_index(); return {'deleted':True}
@app.get('/search')
def search(q:str): return {'matches':retrieve(q)}
@app.get('/runs')
def runs(limit:int=100):
    with SessionLocal() as db: return [{'ticket_id':r.ticket_id,'agent':r.agent,'detail':r.detail,'duration_ms':r.duration_ms,'created_at':r.created_at.isoformat()} for r in db.query(Run).order_by(Run.id.desc()).limit(limit)]
@app.get('/runs/export')
def export_agent_runs(limit:int=Query(10000,ge=1,le=100000)):
    """Auditable, readable CSV containing all persisted ticket-agent executions."""
    output=io.StringIO(); writer=csv.writer(output)
    writer.writerow(['run_id','ticket_id','agent','stage_status','duration_ms','created_at','ticket_status','priority','question','answer','sources','stage_detail'])
    with SessionLocal() as db:
        rows=(db.query(Run,Ticket).join(Ticket,Run.ticket_id==Ticket.id)
              .order_by(Run.id.desc()).limit(limit).all())
        for run,ticket in rows:
            writer.writerow([run.id,f'TKT-{ticket.id:04d}',run.agent,'Completed',run.duration_ms,
                run.created_at.isoformat() if run.created_at else '',ticket.status,ticket.urgency,
                ticket.complaint,ticket.response or '',ticket.sources or '',run.detail or ''])
    return StreamingResponse(iter([output.getvalue()]),media_type='text/csv',
        headers={'Content-Disposition':'attachment; filename=agent_execution_logs.csv'})

@app.get('/evaluation/grounding')
def grounding_evaluation(limit:int=Query(200,ge=1,le=1000)):
    """Heuristic checks; source existence is not proof of semantic entailment."""
    with SessionLocal() as db:
        docs={d.filename for d in db.query(Document.filename).all()}
        rows=db.query(Ticket).order_by(Ticket.id.desc()).limit(limit).all()
        results=[]
        for t in rows:
            cited=[x.strip() for x in (t.sources or '').split(',') if x.strip()]
            valid=[x for x in cited if x in docs]
            missing=[x for x in cited if x not in docs]
            no_knowledge=not cited
            honest_fallback=('could not find' in (t.response or '').lower() or
                'unavailable' in (t.response or '').lower())
            results.append({'ticket_id':f'TKT-{t.id:04d}', 'source_count':len(cited),
                'valid_sources':valid,'missing_sources':missing,
                'grounding_check':'Source names verified' if cited and not missing else
                  'Explicit knowledge gap' if no_knowledge and honest_fallback else 'Needs manual review'})
        return {'checked':len(results),'verified_source_names':sum(r['grounding_check']=='Source names verified' for r in results),
                'knowledge_gaps':sum(r['grounding_check']=='Explicit knowledge gap' for r in results),
                'needs_review':sum(r['grounding_check']=='Needs manual review' for r in results),
                'disclaimer':'Source existence alone does not establish answer factuality or entailment.',
                'results':results}

@app.get('/feedback')
def feedback_list():
    with SessionLocal() as db: return [{'ticket_id':f.ticket_id,'helpful':f.helpful,'comment':f.comment} for f in db.query(Feedback).order_by(Feedback.id.desc())]
@app.get('/stats')
def stats():
    with SessionLocal() as db:
        rows=db.query(Ticket).all(); total=len(rows)
        return {'total':total,'resolved':sum(t.status=='Resolved' for t in rows),'escalated':sum(t.status=='Escalated' for t in rows),'answered':sum(t.status=='Answered' for t in rows),'sla_compliance':round(100*sum(not(t.due_at and t.due_at.replace(tzinfo=None)<now().replace(tzinfo=None) and t.status not in ('Resolved','Answered')) for t in rows)/total) if total else 100,'categories':{c:sum(t.category==c for t in rows) for c in sorted({t.category for t in rows})}}
@app.get('/knowledge-gaps')
def gaps():
    with SessionLocal() as db:
        rows=db.query(Ticket).filter(Ticket.escalation_reason.ilike('%No matching knowledge%')).all()
        return [{'ticket_id':t.id,'question':t.complaint[:180],'category':t.category} for t in rows]


# Conversation history is separate from tickets: chatting never creates a ticket.
class ConversationIn(BaseModel):
    customer_name:str='Demo Customer'
    email:Optional[str]=None
    order_id:Optional[str]=None
class ChatIn(BaseModel):
    question:str=Field(min_length=5,max_length=10000)
class TicketDecision(BaseModel):
    turn_id:int

def chat_turn_dict(turn):
    return {'id':turn.id,'question':turn.question,'answer':turn.answer,'category':turn.category,'urgency':turn.urgency,
            'sources':json.loads(turn.sources or '[]'),'agent_process':json.loads(turn.stages or '[]'),
            'ticket_id':f'TKT-{turn.ticket_id:04d}' if turn.ticket_id else None}

@app.post('/conversations')
def create_conversation(payload:ConversationIn):
    with SessionLocal() as db:
        c=Conversation(customer_name=payload.customer_name or 'Demo Customer',email=payload.email,order_id=payload.order_id)
        db.add(c);db.commit();db.refresh(c)
        return {'id':c.id,'title':c.title}

@app.get('/conversations')
def list_conversations(limit:int=50):
    with SessionLocal() as db:
        return [{'id':c.id,'title':c.title,'customer_name':c.customer_name,'created_at':c.created_at.isoformat()}
                for c in db.query(Conversation).order_by(Conversation.id.desc()).limit(min(limit,100)).all()]

@app.get('/conversations/{conversation_id}')
def get_conversation(conversation_id:int):
    with SessionLocal() as db:
        c=db.get(Conversation,conversation_id)
        if not c: raise HTTPException(404,'Conversation not found')
        turns=db.query(ChatTurn).filter_by(conversation_id=conversation_id).order_by(ChatTurn.id).all()
        return {'id':c.id,'title':c.title,'customer_name':c.customer_name,'email':c.email,'order_id':c.order_id,
                'turns':[chat_turn_dict(t) for t in turns]}

@app.post('/conversations/{conversation_id}/messages')
def chat_message(conversation_id:int,payload:ChatIn):
    check=validate_customer_input(payload.question)
    if not check.allowed: raise HTTPException(status_code=422,detail=check.reason)
    payload.question=check.text
    with SessionLocal() as db:
        c=db.get(Conversation,conversation_id)
        if not c: raise HTTPException(404,'Conversation not found')
        classification,answer,sources,confidence,reasons,stages=run_pipeline(payload.question)
        # A chat execution is not a ticket creation; report this honestly in LogAgent.
        formatted=[]
        for agent,detail,duration in stages:
            try: parsed=json.loads(detail)
            except (ValueError,TypeError): parsed={'detail':detail}
            if agent=='LogAgent': parsed={'status':'No ticket created','detail':'Waiting for customer feedback or Create Ticket action'}
            formatted.append({'agent':agent,'detail':parsed,'duration_ms':duration,'status':'Completed'})
        turn=ChatTurn(conversation_id=c.id,question=payload.question,answer=answer,
                      category=classification['category'],urgency=classification['urgency'],
                      sources=json.dumps(sources),stages=json.dumps(formatted))
        if c.title=='New conversation': c.title=payload.question[:90]
        db.add(turn);db.commit();db.refresh(turn)
        return chat_turn_dict(turn)

@app.post('/conversations/{conversation_id}/ticket')
def create_ticket_from_chat(conversation_id:int,payload:TicketDecision):
    with SessionLocal() as db:
        c=db.get(Conversation,conversation_id)
        turn=db.get(ChatTurn,payload.turn_id)
        if not c or not turn or turn.conversation_id!=conversation_id: raise HTTPException(404,'Conversation or message not found')
        if turn.ticket_id:
            t=db.get(Ticket,turn.ticket_id)
            if t and t.status=='Escalated':
                notify_escalation(t,db.get(Customer,t.customer_id))
            return ticket_dict(t,db.get(Customer,t.customer_id))
        customer=db.query(Customer).filter_by(email=c.email).first() if c.email else None
        if not customer:
            customer=Customer(name=c.customer_name,email=c.email)
            db.add(customer);db.flush()
        classification=classify_for_ticket(turn)
        # Keep the original issue as the ticket summary, not the follow-up that
        # triggered ticket creation. Use the earliest persisted chat turn.
        first_turn=(db.query(ChatTurn)
                    .filter(ChatTurn.conversation_id==conversation_id)
                    .order_by(ChatTurn.id.asc()).first())
        original_question=(first_turn.question if first_turn else turn.question).strip()
        high=str(turn.urgency).strip().lower()=='high'
        t=Ticket(customer_id=customer.id,order_id=c.order_id,complaint=turn.question,
                 response=turn.answer,category=turn.category,urgency=turn.urgency,
                 summary=original_question[:180],sources=','.join(json.loads(turn.sources or '[]')),
                 status='Escalated' if high else 'Open',
                 escalation_reason='High urgency' if high else '',
                 due_at=now()+timedelta(hours=4 if high else 24))
        db.add(t);db.flush()
        db.add(Message(ticket_id=t.id,role='customer',content=turn.question))
        db.add(Message(ticket_id=t.id,role='assistant',content=turn.answer))
        for step in json.loads(turn.stages or '[]'):
            db.add(Run(ticket_id=t.id,agent=step['agent'],detail=json.dumps(step['detail']),duration_ms=step['duration_ms']))
        turn.ticket_id=t.id
        db.commit()
        if t.status=='Escalated': notify_escalation(t,customer)
        return ticket_dict(t,customer)

def classify_for_ticket(turn):
    return {'category':turn.category,'urgency':turn.urgency}

@app.get('/notifications')
def list_notifications(limit:int=Query(200,ge=1,le=1000)):
    """Return persisted SMTP delivery attempts with associated ticket metadata."""
    with SessionLocal() as db:
        rows=(db.query(Notification,Ticket)
              .outerjoin(Ticket,Notification.ticket_id==Ticket.id)
              .order_by(Notification.created_at.desc(),Notification.id.desc())
              .limit(limit).all())
        sender=os.getenv('SMTP_FROM','').strip() or os.getenv('SMTP_USER','').strip()
        return [{'id':n.id,'from_email':sender,'to_email':n.recipient,
                 'ticket_id':f'TKT-{n.ticket_id:04d}' if n.ticket_id is not None else '—',
                 'subject':n.subject,'delivery_status':n.state,
                 'ticket_status':t.status if t else 'Unknown',
                 'priority':t.urgency if t else 'Unknown',
                 'created_at':n.created_at.isoformat() if n.created_at else ''}
                for n,t in rows]

@app.get('/notifications/smtp-status')
def smtp_status():
    """Safe SMTP diagnostics: never return passwords or addresses."""
    keys=('SMTP_HOST','SMTP_PORT','SMTP_USER','SMTP_PASSWORD','SMTP_FROM','SMTP_TO_EMAIL')
    configured={key:bool(os.getenv(key,'').strip()) for key in keys}
    return {'configured':all(configured.values()),'fields':configured,
            'note':'Configuration only; does not test network access or Gmail authentication.'}
