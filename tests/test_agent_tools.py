import csv
from backend.agents import classify, log_ticket, _escalation_reasons

def test_high_urgency():
    c=classify('Fraud: I was charged twice')
    assert c['urgency']=='High'
    assert 'High urgency' in _escalation_reasons(c, [], 0.0)

def test_log_ticket_writes_csv(tmp_path,monkeypatch):
    path=tmp_path/'audit.csv'
    monkeypatch.setenv('AGENT_AUDIT_CSV',str(path))
    assert log_ticket('Billing','High','Angry','Duplicate charge','Contact support','billing.md',True,'High urgency')=='LOGGED'
    with path.open(encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    assert rows[0]['urgency']=='High'
    assert rows[0]['sources']=='billing.md'
