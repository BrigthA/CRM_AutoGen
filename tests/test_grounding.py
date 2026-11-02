from backend.grounding import grounded_answer, NO_MATCH

def test_extracts_only_approved_sentences():
    evidence=[{'source':'returns.md','text':'Customers may request a refund within 30 days of delivery. Returns require the original receipt.'}]
    answer,score,status=grounded_answer('Can I request a refund within 30 days?',evidence)
    assert 'Customers may request a refund within 30 days of delivery.' in answer
    assert '(Source: returns.md)' in answer
    assert status=='extractive_verified'

def test_unrelated_evidence_rejected():
    answer,score,status=grounded_answer('How do I reset my password?', [{'source':'returns.md','text':'Customers may request a refund within 30 days of delivery.'}])
    assert answer==NO_MATCH and score==0

def test_empty_evidence():
    assert grounded_answer('Where is my order?',[])[0]==NO_MATCH
