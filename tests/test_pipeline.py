from exercicio import checar, pipeline


def test_fluxo_modo_teste_cumpre_o_criterio(cfg):
    saida = pipeline.rodar(cfg)
    assert saida["llm"] == "teste"
    assert saida["embeddings"] == "fake"
    assert (cfg.pasta_saida / "resultado.json").is_file()
    itens = checar.conferir(cfg, saida)
    falhas = [i for i in itens if not i["ok"]]
    assert not falhas, falhas
