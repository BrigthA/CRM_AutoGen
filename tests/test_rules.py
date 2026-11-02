from backend.agents import classify

def test_payment_escalation():
    x=classify('You charged my card three times! Fix this now or I am contacting a lawyer.')
    assert x['urgency']=='High'
    assert x['category']=='Billing'
    assert 'legal' in x['risk_flags']
