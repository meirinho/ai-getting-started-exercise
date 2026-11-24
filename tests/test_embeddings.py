from exercise.embeddings import embed_passages, embed_query


def test_fake_vectors_are_deterministic():
    a = embed_passages("fake", ["first passage", "second passage"])
    b = embed_passages("fake", ["first passage", "second passage"])
    assert (a == b).all()


def test_fake_query_vector():
    q = embed_query("fake", "Quando é a próxima reunião?")
    assert q.shape == (128,)