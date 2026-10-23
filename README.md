# TB ProtoCheck: Cited Q&A for TB Laboratory Protocols

A retrieval-augmented (RAG) tool that answers questions about TB laboratory and
molecular diagnostic protocols, where **every answer must quote its source, and
every quote is checked automatically against the original document.**

> Status: v0.1, work in progress. Runs on three practice SOPs (see *Documents*);
> public WHO documents are being added next.

## Why

TB diagnostics depend on precise lab procedures: specimen storage limits,
reagent ratios, PCR controls, sequencing depth thresholds. LLMs can answer
questions about these documents quickly, but a wrong number (14 days instead of
10, 50X instead of 100X) can invalidate a result. Existing TB chatbots focus on
answering; this project focuses on **proving each answer is backed by the source.**

## How it works

```
question
   │
   ▼
1. Retrieve  ── BM25 keyword search finds the most relevant protocol sections
   ▼
2. Answer    ── OpenAI answers using ONLY those sections, as structured JSON:
   │            every claim = section ID + exact quote
   ▼
3. Verify    ── Python (no AI) checks every claim:
   │              • does the cited section exist?
   │              • is the quote word-for-word in that section?
   │              • do the numbers in the claim match the quote?
   │              • is any number in the answer unsupported?
   ▼
VERIFIED / FAILED / REFUSED
```

The model is also instructed to **refuse** questions the documents don't answer,
and any treatment or dosing question, which is a clinical decision.

Example (`python demo_verifier.py`):

```
Answer: Specimens can be stored for up to 14 days at 2–8 °C.
Verification: FAILED
  -> numbers in statement not in quote: ['14']
```

## Documents

Three **practice SOPs** written for development. They describe generic workflows
and are **not** official, validated or clinical guidance:

| ID | Topic |
|---|---|
| TBLAB-001 | Sputum collection, transport, storage and rejection criteria |
| TBLAB-002 | Cartridge-based PCR test for TB and rifampicin resistance (RRDR, result categories, limitations) |
| TBLAB-003 | Targeted NGS for drug-resistant TB (target genes, controls, read-depth QC, heteroresistance) |

To add a document: save it as Markdown in `docs/` with a first line
`# DOC-ID: Title` and numbered `## 1. Section` headings.

## Evaluation

`tests/questions.csv`: 22 questions.

* 19 answerable, including answers inside tables and "no" answers
  (e.g. *Can the test detect rpoB I491F?*: no, it lies outside the RRDR)
* 3 that must be refused: a treatment question, a fact not in the documents, and
  a trap (*read depth for whole-genome sequencing?* The SOP only covers targeted
  sequencing, so reusing its 100X value would be wrong)

Metrics: retrieval hit rate, citation verification, answer correctness, correct
refusal and overall pass rate, each with a **Wilson 95% confidence interval**.
Failures are written to `results/failures.md` for failure-case analysis.

| Metric | Result |
|---|---|
| Retrieval hit rate (top 4) | 19/19 = 100% (95% CI 83%–100%) |
| LLM metrics | *to be added after the first OpenAI run* |

## Setup and usage

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."          # Windows PowerShell: $env:OPENAI_API_KEY="sk-..."

python demo_verifier.py                 # offline: see what the verifier catches
python evaluate.py --retrieval-only     # offline: retrieval evaluation
python ask.py "Are TRACE specimens accepted for targeted sequencing?" --show-sources
python evaluate.py                      # full evaluation with OpenAI
```

## Roadmap

- [x] Citable sections, BM25 retrieval, structured cited answers, verifier
- [x] 22-question evaluation set incl. refusal traps
- [ ] Run full OpenAI evaluation and write failure-case analysis
- [ ] Add public WHO TB diagnostic documents (PDF → text)
- [ ] Compare prompt versions and retrieval methods (BM25 vs embeddings)
- [ ] Link to my TB resistance explainer: answer "what does this mutation mean?" from the WHO catalogue

## Limitations

* The verifier proves a quote exists in the cited section, not that it fully
  supports the claim's meaning. Numbers are checked, wording is not.
* Practice documents are short and clean; real PDFs will be messier.
* Not a clinical tool.
