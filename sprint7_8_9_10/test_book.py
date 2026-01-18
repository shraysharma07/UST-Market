try:
    from .book import Book
except ImportError:
    from book import Book

def ch(cmd, side, pos, oid, px=100, q=5, seq=1):
    return {
        "cmd": cmd,
        "side": side,
        "pos": pos,
        "oid": oid,
        "px": px,
        "qdiff": q,
        "seq": seq,
        "ts": "",
    }

def test_add_shifts():
    b = Book()
    b.apply(ch("ADD", "B", 1, "A", seq=1))
    b.apply(ch("ADD", "B", 1, "B", seq=2))
    bids, _ = b.snapshot()
    assert [o[0] for o in bids] == ["B", "A"]

def test_delete_partial():
    b = Book()
    b.apply(ch("ADD", "A", 1, "X", q=10))
    b.apply(ch("DELETE", "A", 1, "X", q=4))
    _, asks = b.snapshot()
    assert asks[0][2] == 6

def test_delete_full():
    b = Book()
    b.apply(ch("ADD", "A", 1, "X", q=5))
    b.apply(ch("DELETE", "A", 1, "X", q=5))
    _, asks = b.snapshot()
    assert asks == []

def test_alter_repositions():
    b = Book()
    b.apply(ch("ADD", "B", 1, "A"))
    b.apply(ch("ADD", "B", 2, "B"))
    b.apply(ch("ALTER", "B", 2, "A"))
    bids, _ = b.snapshot()
    assert [o[0] for o in bids] == ["B", "A"]
