# Completion criterion (written before running)

This file was written **before** the pipeline runs. It describes the limited task, the input, and what the output must satisfy. The automated checker reads the same content in `criteria.yaml` (`python -m exercise check`) and exits non-zero when any item fails.

## The hand-done task

Read the fictional meeting minutes and answer, using the document’s wording:

1. Quando é a próxima reunião?
2. Qual foi o orçamento aprovado?
3. Quem é a responsável pelo relatório de novembro?

A fourth question, deliberately outside the document («Qual é a taxa de juros do financiamento imobiliário?»), checks whether the flow abstains when the text has no answer.

The input is `data/fictional-meeting-minutes.pdf`: a short fictional document with no sensitive data, generated in this repository.

## What the output must satisfy

1. **extracted_text.** The PDF was read with pypdf and the extracted text contains three anchor phrases: next meeting date (15 de dezembro de 2026), approved amount (4.800,00), and responsible name (Carla Dias).
2. **next_meeting.** The answer contains «15 de dezembro de 2026» and cites file and page.
3. **budget.** The answer contains «4.800,00» and cites file and page.
4. **responsible.** The answer contains «Carla Dias» and cites file and page.
5. **off_topic_question.** The flow abstains (does not invent an interest rate missing from the text).
6. **output_file.** `output/result.json` exists with, for each question, answer text, citations, mode used, and whether it abstained.

The flow is complete only when all six items pass. “Looks right” is not enough: the check is against this criterion, written beforehand.