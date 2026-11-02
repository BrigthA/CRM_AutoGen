from backend.grounding import grounded_answer,NO_MATCH

def test_multi_document_answer():
    answer,score,status=grounded_answer('refund delivery damaged',[
        {'source':'refund.md','text':'A refund is available for eligible damaged products.'},
        {'source':'shipping.md','text':'Delivery tracking is available in your customer account.'}])
    assert status=='extractive_verified'
    assert 'refund.md' in answer and 'shipping.md' in answer
    assert score==1.0

def test_unrelated_answer_fails_closed():
    answer,score,status=grounded_answer('bank transfer reversal',[{'source':'policy.md','text':'Returns are accepted within thirty days of purchase.'}])
    assert answer==NO_MATCH

def test_cache_reuses_index(monkeypatch):
    from backend import rag
    rag.invalidate_index()
    monkeypatch.setattr(rag,'corpus',lambda:[])
    a=rag._load();b=rag._load()
    assert a is b
    rag.invalidate_index()
