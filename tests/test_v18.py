import json
from backend import agents
from backend.grounding import grounded_answer,NO_MATCH

def test_paraphrase_with_mock_semantic(monkeypatch):
    monkeypatch.setattr('backend.grounding._semantic_scores',lambda q,s:[0.83]*len(s))
    answer,confidence,status=grounded_answer('How can I get my money back?', [{'source':'refund.md','text':'Customers may request a refund within thirty days of purchase.'}])
    assert 'refund.md' in answer and status=='extractive_verified'

def test_no_match_semantic(monkeypatch):
    monkeypatch.setattr('backend.grounding._semantic_scores',lambda q,s:[0.12]*len(s))
    answer,_,_=grounded_answer('How do I reset my password?', [{'source':'refund.md','text':'Customers may request a refund within thirty days of purchase.'}])
    assert answer==NO_MATCH

def test_tool_verification(monkeypatch,tmp_path):
    monkeypatch.setenv('AGENT_AUDIT_CSV',str(tmp_path/'audit.csv'))
    monkeypatch.setattr(agents,'retrieve',lambda query,top_k=5:[{'source':'policy.md','text':'Refunds are accepted within thirty days of purchase.'}])
    events=[];token=agents._TOOL_EVENTS.set(events)
    try:
        assert json.loads(agents.search_kb('refund'))[0]['source']=='policy.md'
        assert agents.log_ticket('Refund','Low','Neutral','refund','answer','policy.md',False,'')=='LOGGED'
    finally:agents._TOOL_EVENTS.reset(token)
    assert [x['tool'] for x in events]==['search_kb','log_ticket']
    assert all(x['success'] for x in events)
