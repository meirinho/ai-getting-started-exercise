import io
import json

from exercise import check, pipeline


def test_check_prints_each_item_and_exits_zero(cfg):
    pipeline.run(cfg)
    items = check.verify(cfg)
    buf = io.StringIO()
    code = check.print_report(items, stream=buf)
    text = buf.getvalue()
    assert code == 0
    for ident in (
        "output_file",
        "extracted_text",
        "next_meeting",
        "budget",
        "responsible",
        "off_topic_question",
    ):
        assert ident in text
    assert "6 items checked, 6 ok, 0 failed." in text


def test_check_fails_with_nonzero_exit(cfg):
    pipeline.run(cfg)
    path = cfg.output_dir / "result.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in data["questions"]:
        if row["id"] == "budget":
            row["answer"]["text"] = "wrong value, no number"
            row["answer"]["citations"] = []
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    items = check.verify(cfg)
    buf = io.StringIO()
    code = check.print_report(items, stream=buf)
    assert code != 0
    assert "FAIL" in buf.getvalue()
    assert any(i["id"] == "budget" and not i["ok"] for i in items)