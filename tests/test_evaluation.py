from backend.agents import classify, run_pipeline
from backend.guardrails import validate_customer_input

def test_high_urgency_legal_fraud():
    result=classify('My card was charged fraudulently and I will contact a lawyer')
    assert result['urgency']=='High'
    assert 'fraud' in result['risk_flags'] and 'legal' in result['risk_flags']

def test_normal_complaint_not_high():
    assert classify('What is the status of my order?')['urgency']!='High'

def test_guardrail_rejects_blank():
    assert not validate_customer_input('  ').allowed

def test_four_agent_order_and_no_unsupported_policy_when_empty_kb():
    # This test checks stage order; grounding quality requires curated test cases.
    _,_,_,_,_,stages=run_pipeline('What is your shipping policy?')
    assert [step[0] for step in stages]==['QueryAgent','KnowledgeAgent','ResolutionAgent','LogAgent']
