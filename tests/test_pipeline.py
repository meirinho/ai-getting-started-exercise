from exercise import check, pipeline


def test_test_mode_flow_meets_criteria(cfg):
    output = pipeline.run(cfg)
    assert output["llm"] == "test"
    assert output["embeddings"] == "fake"
    assert (cfg.output_dir / "result.json").is_file()
    items = check.verify(cfg, output)
    failures = [i for i in items if not i["ok"]]
    assert not failures, failures