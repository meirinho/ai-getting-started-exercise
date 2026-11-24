# Critério de conclusão (escrito antes de rodar)

Este arquivo foi escrito **antes** do fluxo rodar. Ele descreve a tarefa
limitada, a entrada e o que a saída precisa cumprir. A conferência automática
lê o mesmo conteúdo em `criterio.yaml` (`python -m exercicio checar`) e
termina com código diferente de zero se algum item falhar.

## A tarefa, feita à mão

Ler a ata de reunião fictícia e responder, com as palavras do texto:

1. Quando é a próxima reunião?
2. Qual foi o orçamento aprovado?
3. Quem é a responsável pelo relatório de novembro?

Uma quarta pergunta, de propósito fora do documento («Qual é a taxa de
juros do financiamento imobiliário?»), serve para conferir se o fluxo se
abstém quando o texto não traz a resposta.

A entrada é o PDF `dados/ata-reuniao-ficticia.pdf`: um documento curto,
fictício, sem informação sensível, gerado neste repositório.

## O que a saída precisa cumprir

1. **texto_extraido.** O PDF foi lido com o pypdf e o texto extraído contém as
   três frases âncora: a data da próxima reunião (15 de dezembro de 2026), o
   valor aprovado (4.800,00) e o nome da responsável (Carla Dias).
2. **proxima_reuniao.** A resposta contém «15 de dezembro de 2026» e cita o
   arquivo e a página.
3. **orcamento.** A resposta contém «4.800,00» e cita o arquivo e a página.
4. **responsavel.** A resposta contém «Carla Dias» e cita o arquivo e a página.
5. **pergunta_fora.** O fluxo se abstém (não inventa uma taxa que o texto não traz).
6. **arquivo_saida.** Existe `saida/resultado.json` com, para cada pergunta, o
   texto da resposta, as citações, o modo usado e se houve abstenção.

O fluxo só está concluído quando os seis itens passam. Rodar e «parecer certo»
não basta: a conferência é contra este critério, escrito antes.
