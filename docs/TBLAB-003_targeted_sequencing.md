# TBLAB-003: Targeted Sequencing for Drug-Resistant TB

> PRACTICE DOCUMENT. Written for developing and testing this tool only.
> It describes a generic targeted next-generation sequencing (tNGS) workflow and is not a vendor protocol or clinical guidance.

## 1. Purpose and scope

This SOP describes targeted next-generation sequencing (tNGS) of TB resistance genes directly from processed sputum. Instead of sequencing the whole genome, tNGS amplifies and sequences selected gene regions associated with drug resistance. It is used when rifampicin resistance has been detected by the rapid molecular test (TBLAB-002), to detect resistance to additional drugs.

## 2. Target genes and drugs

The panel targets the following genes:

| Gene | Drug |
|---|---|
| rpoB | rifampicin |
| katG, inhA and the fabG1-inhA promoter | isoniazid |
| gyrA, gyrB | fluoroquinolones |
| rv0678, atpE | bedaquiline |
| rrl, rplC | linezolid |
| pncA | pyrazinamide |
| embB | ethambutol |
| rrs | amikacin |

## 3. Specimen requirements

Use sputum that tested MTB DETECTED at low level or higher on the rapid molecular test. Specimens with MTB DETECTED very low or TRACE results have a high risk of sequencing failure and are not accepted for tNGS. Store decontaminated sputum at -20 °C if DNA extraction cannot be done within 7 days.

## 4. DNA extraction and amplification

Extract DNA from 1 ml of decontaminated sputum. Amplify the target regions in a single multiplex PCR of 40 cycles. Include a negative control (water) and a positive control (DNA from a reference strain) in every run. If the negative control shows amplification, the whole run is invalid and must be repeated.

## 5. Library preparation and sequencing

Prepare libraries from the purified amplicons using indexed adapters, so that up to 24 specimens can be sequenced in one run. Pool libraries in equimolar amounts. Each specimen must carry a unique index.

## 6. Quality control of sequencing data

A specimen passes sequencing QC when every target region has a median read depth of at least 100X. Target regions below 100X are reported as "failed region", and no resistance call is made for the drugs covered by that region. A mutation is reported only when it is present in at least 10% of reads at that position.

## 7. Interpretation and reporting

Mutations are interpreted using the WHO catalogue of mutations in Mycobacterium tuberculosis complex. Mutations graded as associated with resistance are reported as resistance to the corresponding drug. Mutations present in 10–90% of reads are reported as heteroresistance, meaning a mixed population of susceptible and resistant bacteria. Mutations not listed in the catalogue are reported as "uncharacterised" and referred for expert review. Treatment decisions are made by the clinical team and are outside the scope of this SOP.
