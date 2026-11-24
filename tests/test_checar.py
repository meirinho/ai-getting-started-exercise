import io
import json

from exercicio import checar, pipeline


def test_checar_imprime_cada_item_e_sai_zero(cfg):
    pipeline.rodar(cfg)
    itens = checar.conferir(cfg)
    buf = io.StringIO()
    codigo = checar.imprimir(itens, destino=buf)
    texto = buf.getvalue()
    assert codigo == 0
    for ident in (
        "arquivo_saida",
        "texto_extraido",
        "proxima_reuniao",
        "orcamento",
        "responsavel",
        "pergunta_fora",
    ):
        assert ident in texto
    assert "6 itens conferidos, 6 ok, 0 falhou." in texto


def test_checar_falha_com_codigo_diferente_de_zero(cfg):
    pipeline.rodar(cfg)
    caminho = cfg.pasta_saida / "resultado.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    for p in dados["perguntas"]:
        if p["id"] == "orcamento":
            p["resposta"]["texto"] = "valor errado, sem o número"
            p["resposta"]["citacoes"] = []
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    itens = checar.conferir(cfg)
    buf = io.StringIO()
    codigo = checar.imprimir(itens, destino=buf)
    assert codigo != 0
    assert "FALHOU" in buf.getvalue()
    assert any(i["id"] == "orcamento" and not i["ok"] for i in itens)
