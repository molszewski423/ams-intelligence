"""
AMS Intelligence — Knowledge Vault Ingestor Script

Ingests:
  1. ASHP + IDSA guideline text (curated from primary sources)
  2. PubMed AMS literature (live API fetch across 12 topic queries)

Run from project root:
    PYTHONPATH=src python scripts/ingest_vault.py [--pubmed-only] [--guidelines-only] [--max N]
"""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ── Guideline corpus (curated text from ASHP/IDSA primary sources) ─────────────

GUIDELINES: list[dict] = [
    {
        "source": "IDSA/SHEA 2016 — Implementing an Antibiotic Stewardship Program (Barlam et al., CID 2016; PMID 27080992)",
        "doc_type": "guideline",
        "text": """
Implementing an Antibiotic Stewardship Program: Guidelines by the Infectious Diseases Society of America and the Society for Healthcare Epidemiology of America (2016)

EXECUTIVE SUMMARY AND KEY RECOMMENDATIONS

Background:
Evidence-based guidelines for implementation and measurement of antibiotic stewardship interventions in inpatient populations including long-term care were prepared by a multidisciplinary expert panel of the Infectious Diseases Society of America and the Society for Healthcare Epidemiology of America. The guidelines are intended to provide practical, evidence-based recommendations for the implementation of antibiotic stewardship programs (ASPs).

Primary Goal:
To optimize clinical outcomes while minimizing unintended consequences of antimicrobial use, including toxicity, selection of pathogenic organisms such as Clostridioides difficile, and the emergence of resistance.

CORE RECOMMENDATIONS:

1. LEADERSHIP COMMITMENT (Strong; High Quality Evidence)
Hospitals and health systems should provide the necessary administrative support (including personnel, information technology, and financial resources) for antibiotic stewardship programs. Designate a physician leader and pharmacy leader with AMS training or experience.

2. ACCOUNTABILITY (Strong; Moderate Quality Evidence)
Designate a single physician leader accountable for program outcomes. The physician leader should have training or experience in infectious diseases and/or antibiotic stewardship. Designate a single pharmacy leader accountable for program outcomes who should have training or experience in infectious diseases pharmacy.

3. DRUG EXPERTISE (Strong; High Quality Evidence)
Include a pharmacist with infectious diseases training or experience. Pharmacists are critical to stewardship program success and should be key drivers of interventions.

4. ACTION (Strong; High Quality Evidence)
Implement at least one of the following core interventions:
   a. Prospective audit with intervention and feedback: Review antibiotic therapy and communicate recommendations to the prescriber. This approach is associated with reduced antibiotic use, cost, and adverse events (A-I).
   b. Formulary restriction and preauthorization: Require approval before dispensing selected antibiotics. This approach produces immediate reductions in targeted antibiotic use (A-II).

5. TRACKING (Strong; Moderate Quality Evidence)
Monitor antibiotic prescribing patterns using process measures (days of therapy per 1000 patient-days, antibiotic costs, compliance with guidelines) and outcome measures (rates of CDI, antibiotic-resistant organisms, antibiotic adverse events).

6. REPORTING (Strong; Moderate Quality Evidence)
Report antibiotic use and resistance data regularly to prescribers, pharmacists, nursing staff, and hospital leadership.

7. EDUCATION (Strong; High Quality Evidence)
Provide education about optimal antibiotic prescribing as a component of stewardship. Education alone is insufficient without accompanying active interventions.

SPECIFIC INTERVENTIONS:

De-escalation / Streamlining:
Streamline or de-escalate antibiotic therapy based on culture and susceptibility results. This approach reduces antibiotic exposure, costs, and adverse events without worse outcomes (A-II).

Dose Optimization:
Optimize antibiotic dosing based on published pharmacokinetic/pharmacodynamic (PK/PD) principles, individual patient characteristics (renal function, weight, severity of illness), and local susceptibility patterns. Dose optimization is a key component of stewardship (A-II). Extended infusion of beta-lactams should be considered for organisms with elevated MICs.

IV-to-PO Conversion:
Systematically identify candidates for IV-to-oral antibiotic conversion. This reduces central line complications, length of stay, and costs (A-I). Criteria for conversion include clinical improvement, functioning GI tract, no malabsorption conditions, and availability of oral formulations with high bioavailability.

Antibiotic Time-outs:
Reassess appropriateness of ongoing antibiotic therapy at 48–72 hours based on clinical presentation, culture results, and other diagnostic information. Document reassessment in the medical record.

Antibiotic Allergy Assessment:
Evaluate and document antibiotic allergy history. Many patients with reported penicillin allergy can safely receive penicillin-class antibiotics, and allergy evaluation can reduce unnecessary use of broader-spectrum alternatives.

MEASURING STEWARDSHIP OUTCOMES:

Process Measures:
- Days of therapy (DOT) per 1000 patient-days: preferred metric over DDD for inpatient settings
- Antibiotic costs per patient-day or per admission
- Compliance with hospital guidelines and recommended antibiotic regimens
- Time to appropriate antibiotic therapy
- Rates of appropriate de-escalation, IV-to-oral conversion, allergy assessment

Outcome Measures:
- CDI rates (per 10,000 patient-days)
- Rates of antibiotic-resistant organisms (MRSA, VRE, ESBL-producing organisms, carbapenem-resistant Enterobacteriaceae)
- Length of hospital stay
- 30-day readmission rates
- In-hospital mortality
- Antibiotic adverse events (nephrotoxicity, hepatotoxicity, Clostridioides difficile infection)

SPECIAL POPULATIONS AND SETTINGS:

Long-Term Care Facilities:
- Implement symptom-based diagnostic criteria to guide antibiotic prescribing
- Apply McGeer criteria or Loeb criteria for infection definitions
- Track antibiotic use by resident-days and infection category
- Reduce unnecessary treatment of asymptomatic bacteriuria

ICU Settings:
- Procalcitonin-guided discontinuation of antibiotics can reduce duration without harm
- Daily reassessment of antibiotic necessity is essential
- De-escalation and culture-guided therapy are priority targets
- Consider antifungal stewardship (azoles, echinocandins, amphotericin)

EVIDENCE RATINGS:
- A-I: Strong recommendation, High-quality evidence (RCTs)
- A-II: Strong recommendation, Moderate-quality evidence (well-designed cohort or case-control studies)
- B-I: Moderate recommendation, High-quality evidence
- B-II: Moderate recommendation, Moderate-quality evidence
- C-II: Optional recommendation, Moderate-quality evidence
""",
    },
    {
        "source": "IDSA/SHEA 2007 — Developing an Institutional Program to Enhance Antimicrobial Stewardship (Dellit et al., CID 2007; PMID 17173212)",
        "doc_type": "guideline",
        "text": """
IDSA/SHEA 2007 Guidelines for Developing an Institutional Program to Enhance Antimicrobial Stewardship

CORE PRINCIPLES:

Primary Goal:
Optimize clinical outcomes while minimizing unintended consequences of antimicrobial use including toxicity, selection of pathogenic organisms (Clostridium difficile), and emergence of resistance.

Two Primary Active Strategies:

1. PROSPECTIVE AUDIT WITH INTERVENTION AND FEEDBACK (A-I)
Direct interaction and feedback by an ID physician or clinical pharmacist regarding appropriateness of antimicrobial therapy can result in reduced inappropriate use and improved outcomes. Regular post-prescription review with feedback reduces unnecessary days of therapy by 22-37%.

2. FORMULARY RESTRICTION AND PREAUTHORIZATION (A-II)
Requiring approval before dispensing selected antimicrobials produces immediate and significant reductions in antimicrobial use and cost. Automatic computer-generated stop orders and approval systems are effective implementation tools.

Supplemental Strategies:

EDUCATION (B-II)
Provides important foundation but is only marginally effective without accompanying active interventions. Grand rounds, educational outreach, and pocket guides supplement active stewardship but cannot replace it.

EVIDENCE-BASED GUIDELINES (A-I)
Development and application of practice guidelines incorporating local resistance patterns improve utilization and clinical outcomes.

ANTIMICROBIAL CYCLING (C-II)
Insufficient evidence to recommend routine scheduled cycling of antimicrobials to prevent resistance. May be used in specific epidemiologic situations.

DE-ESCALATION / STREAMLINING (A-II)
Streamlining therapy based on culture results achieves substantial cost savings without adversely affecting outcomes. Target broad-spectrum empiric therapy and narrow based on susceptibility data.

DOSE OPTIMIZATION (A-II)
Tailoring antimicrobial dosing to individual patient pharmacokinetic/pharmacodynamic targets is an important component of stewardship. Extended infusion strategies for time-dependent antibiotics (beta-lactams) improve target attainment.

PARENTERAL TO ORAL CONVERSION (A-I)
Systematic criteria-based IV-to-oral switching decreases length of stay and associated complications without compromising outcomes. High-bioavailability oral agents (fluoroquinolones, metronidazole, linezolid, clindamycin, fluconazole) are candidates.

OUTCOMES AND FINANCIAL IMPACT:
Comprehensive programs demonstrate 22-36% reduction in antimicrobial use with annual savings of $200,000-$900,000. Resistance rates, CDI rates, and length of stay are additional measurable outcomes.

TEAM COMPOSITION:
Required: Infectious diseases physician + clinical pharmacist with ID training
Optional: Clinical microbiologist, IT specialist, infection control professional, hospital epidemiologist
""",
    },
    {
        "source": "ASHP-IDSA-SIDP-SCCM 2019 — Implementing Antibiotic Stewardship Programs in Health Systems (AJHP 2019)",
        "doc_type": "guideline",
        "text": """
Implementing Antibiotic Stewardship Programs in Health Systems — Joint Guidance from ASHP, IDSA, SIDP, and SCCM (2019)

PHARMACIST ROLES IN ANTIMICROBIAL STEWARDSHIP:

Core Functions:
1. Prospective audit and feedback — review antibiotic orders and communicate recommendations
2. Formulary management — maintain restricted antibiotic lists, manage preauthorization systems
3. Dose optimization — adjust doses for renal function, obesity, severity of illness using PK/PD principles
4. IV-to-oral conversion programs — apply criteria systematically
5. Antibiotic allergy assessment — document and reconcile reported allergies
6. Clinical guideline development — create and update institution-specific treatment guidelines
7. Antibiotic order set review — ensure guideline concordance in CPOE systems
8. Education — train prescribers, nursing staff, and pharmacy students
9. Culture/susceptibility monitoring — review results and recommend de-escalation
10. Antimicrobial use tracking — generate DOT reports, perform benchmarking

Pharmacist Competencies Required:
- Infectious diseases pharmacotherapy knowledge
- PK/PD principles for antimicrobial dosing
- Understanding of resistance mechanisms and local susceptibility patterns
- Therapeutic drug monitoring (vancomycin AUC-guided dosing, aminoglycoside monitoring)
- Antimicrobial adverse effect recognition and management
- Communication and prescriber relationship skills

VANCOMYCIN STEWARDSHIP (AUC-GUIDED MONITORING):
Current ASHP/IDSA/SIDP/SIDP guidelines recommend AUC-guided vancomycin monitoring over trough-only monitoring. Target AUC/MIC of 400-600 mg*h/L is associated with improved clinical outcomes and reduced nephrotoxicity. Bayesian estimation is preferred for AUC calculation.

CARBAPENEM STEWARDSHIP:
Reserve carbapenems for documented or highly suspected carbapenem-only pathogens. Implement CRE screening in high-risk patients. Ertapenem may be used for ESBL-producing organisms when anti-pseudomonal coverage not required.

ANTIFUNGAL STEWARDSHIP:
Diagnose invasive candidiasis with serum beta-D-glucan or Candida biomarkers when possible. De-escalate empiric antifungal therapy based on clinical stability and negative cultures. Azole step-down is appropriate for susceptible Candida species.

ANTIBIOTIC DURATION:
Shorter courses of antibiotics are associated with equivalent outcomes for most infections:
- Community-acquired pneumonia: 5 days (if good response by day 3)
- Uncomplicated urinary tract infection: 3-5 days (nitrofurantoin/trimethoprim-sulfamethoxazole)
- Skin and soft tissue infections: 5-7 days
- Intra-abdominal infections: 4 days after source control
- Bloodstream infections: variable by pathogen and source control

METRICS AND BENCHMARKING:
- NHSN Antimicrobial Use and Resistance (AUR) module: standardized infection ratio (SIR) and standardized antimicrobial administration ratio (SAAR)
- Days of therapy (DOT) per 1000 patient-days by ward type
- Percent antibiotic days covered by culture data
- Appropriate empiric therapy rates
- Antibiotic cost per patient-day

SPECIAL SCENARIOS:

Procalcitonin-Guided Therapy:
PCT-guided protocols reduce antibiotic duration in respiratory infections and sepsis without harming outcomes. PCT < 0.25 mcg/L supports antibiotic discontinuation in lower respiratory infections.

Rapid Diagnostics:
MALDI-TOF MS, rapid PCR panels (BioFire FilmArray), and direct-from-blood susceptibility testing accelerate identification and allow earlier de-escalation. Stewardship programs should have processes for acting on rapid diagnostic results 24/7.

Sepsis Bundles and AMS:
The surviving sepsis campaign 1-hour bundle should not delay stewardship interventions. De-escalation within 24-72 hours of culture results is a key stewardship opportunity in septic patients.
""",
    },
    {
        "source": "CDC Core Elements of Hospital Antibiotic Stewardship Programs (CDC, 2019)",
        "doc_type": "guideline",
        "text": """
CDC Core Elements of Hospital Antibiotic Stewardship Programs

The CDC Core Elements framework identifies seven key components for successful hospital antibiotic stewardship programs.

CORE ELEMENT 1: HOSPITAL LEADERSHIP COMMITMENT
- Dedicate necessary human, financial, and IT resources to the program
- Make antibiotic stewardship an organizational priority aligned with patient safety goals
- Include stewardship metrics in quality improvement dashboards
- Provide protected time for physician and pharmacy stewardship leads

CORE ELEMENT 2: ACCOUNTABILITY
- Designate a physician stewardship leader: ID physician, hospitalist, or clinician with AMS training
- Designate a pharmacy stewardship leader: PharmD with ID or AMS training preferred
- Define roles and responsibilities for both leaders
- Report program outcomes to hospital leadership and medical staff committees

CORE ELEMENT 3: PHARMACY EXPERTISE
- Pharmacist co-leadership is essential for program success
- Conduct prospective audit and feedback rounds
- Manage prior authorization and formulary restrictions
- Provide real-time consultation on antibiotic selection and dosing

CORE ELEMENT 4: ACTION — IMPLEMENT INTERVENTIONS
Recommended baseline interventions:
a) Antibiotic time-out at 48-72 hours: reassess appropriateness, duration, and route
b) Prospective audit with intervention and feedback
c) Facility-specific treatment guidelines for common infections
d) Preauthorization for broad-spectrum agents

Optional interventions:
- IV-to-oral conversion programs
- Renal dose optimization
- Allergy assessment programs
- Rapid diagnostic stewardship protocols
- Duration-of-therapy guidelines by infection type

CORE ELEMENT 5: TRACKING
Process Measures (required):
- Antibiotic use: Days of Therapy (DOT) per 1000 patient-days
- Antibiotic cost per patient-day
- Percent compliance with recommended regimens for specific conditions

Outcome Measures:
- Hospital-onset CDI rate per 10,000 patient-days
- MRSA bacteremia rates
- Rates of antibiotic-resistant organisms
- Length of stay

CORE ELEMENT 6: REPORTING
- Report antibiotic use data to prescribers at least quarterly
- Unit-specific reports help target improvement efforts
- Benchmark data against NHSN national comparators (SAAR)
- Report CDI and resistance rates alongside antibiotic use data

CORE ELEMENT 7: EDUCATION
- Provide education at onboarding and at least annually
- Include clinical decision support at the point of prescribing
- Offer case-based learning, guidelines updates, antibiogram review
- Engage medical students, residents, and nurses in stewardship education

KEY METRICS REFERENCE:
- Target carbapenem DOT/1000 PD: < 25
- Target fluoroquinolone DOT/1000 PD: < 75
- Target vancomycin DOT/1000 PD: < 65
- Target piperacillin-tazobactam DOT/1000 PD: < 80
- CDI hospital-onset target: < 6.3 per 10,000 patient-days (national benchmark)
- SAAR < 1.0 indicates use below predicted based on patient population
""",
    },
    {
        "source": "ASHP Statement — Pharmacist's Role in Antimicrobial Stewardship and Infection Prevention (AJHP 2010)",
        "doc_type": "guideline",
        "text": """
ASHP Statement on the Pharmacist's Role in Antimicrobial Stewardship and Infection Prevention and Control

PHARMACIST RESPONSIBILITIES IN AMS:

Patient Care Activities:
1. Review antimicrobial prescriptions for appropriateness (indication, drug selection, dose, route, duration)
2. Perform pharmacokinetic monitoring (vancomycin, aminoglycosides)
3. Identify and resolve drug interactions, adverse effects, and contraindications
4. Recommend de-escalation based on culture results
5. Facilitate IV-to-oral conversion using defined criteria
6. Conduct prospective audit rounds with ID physician or independently

Formulary Management:
- Maintain the antimicrobial formulary and restricted drug list
- Evaluate new antimicrobial agents for formulary inclusion
- Manage antimicrobial shortages and therapeutic substitution protocols
- Develop and review antimicrobial order sets in CPOE systems

Surveillance and Data Analysis:
- Generate and interpret facility antibiograms (annually or more frequently)
- Track DOT/1000 patient-days by drug class and patient care unit
- Monitor CDI rates and correlate with antibiotic use patterns
- Analyze FAERS and literature for emerging resistance signals
- Benchmark against NHSN national surveillance data

Guideline Development:
- Develop empiric antibiotic protocols based on local susceptibility patterns
- Update treatment guidelines for common infections (CAP, HAP/VAP, BSI, UTI, SSTI)
- Create syndrome-specific dosing guides incorporating PK/PD principles
- Write preauthorization criteria and stop-order policies

Education and Training:
- Educate medical staff, nursing, and trainees on antimicrobial stewardship
- Facilitate antibiogram review and interpretation sessions
- Lead case conferences on complex antimicrobial cases
- Contribute to pharmacy curriculum for antimicrobial pharmacotherapy

PHARMACOKINETIC/PHARMACODYNAMIC (PK/PD) PRINCIPLES:

Time-dependent antibiotics (maximize time above MIC):
- Beta-lactams (penicillins, cephalosporins, carbapenems): extended infusions, frequent dosing
- Vancomycin: AUC/MIC-guided dosing (target AUC 400-600 mg*h/L)
- Clindamycin, linezolid: standard dosing intervals adequate

Concentration-dependent antibiotics (maximize Cmax/MIC or AUC/MIC):
- Aminoglycosides: extended interval dosing (once-daily) preferred for most indications
- Fluoroquinolones: AUC/MIC > 125 for gram-negative organisms; target Cmax/MIC for resistant strains
- Daptomycin: Cmax/MIC driven; dose 6-10 mg/kg for bloodstream infection

Postantibiotic effect (PAE):
- Aminoglycosides: prolonged PAE against gram-negative organisms supports extended interval dosing
- Carbapenems: short PAE against gram-negatives supports frequent dosing or extended infusion

Renal Dosing Adjustments:
- CrCl-based adjustments required for: vancomycin, aminoglycosides, beta-lactams, fluoroquinolones, carbapenems
- Hemodialysis supplemental dosing: vancomycin, cefazolin, fluconazole, trimethoprim-sulfamethoxazole
- Continuous renal replacement therapy (CRRT): requires effluent rate-based calculations

INFECTION-SPECIFIC STEWARDSHIP TARGETS:

Community-Acquired Pneumonia (CAP):
- Preferred: beta-lactam + macrolide or respiratory fluoroquinolone (low risk)
- Severe: beta-lactam + azithromycin or beta-lactam + respiratory fluoroquinolone
- Duration: 5 days if good clinical response by day 3
- De-escalation trigger: procalcitonin < 0.25 mcg/L

Hospital-Acquired/Ventilator-Associated Pneumonia (HAP/VAP):
- Empiric coverage based on local antibiogram and prior antibiotic exposure
- P. aeruginosa risk factors require anti-pseudomonal coverage
- 7-day duration for most patients; shorter if PCT-guided
- Avoid prolonged carbapenems — de-escalate to cephalosporins when susceptibility confirmed

Urinary Tract Infections:
- Uncomplicated cystitis: 3-day nitrofurantoin or trimethoprim-sulfamethoxazole
- Do not treat asymptomatic bacteriuria (except pregnancy, pre-urologic procedure)
- Catheter-associated UTI: remove/replace catheter before interpreting urine cultures
- Pyelonephritis: 7 days if fluoroquinolone; 10-14 days if beta-lactam

Bloodstream Infections:
- Duration: S. aureus BSI minimum 14 days for uncomplicated, 4-6 weeks for complicated
- Gram-negative BSI: 7-14 days if source controlled
- Candida BSI: 14 days after last positive culture + resolution of symptoms
- Source control: remove infected catheters/devices as soon as possible
""",
    },
    {
        "source": "Surviving Sepsis Campaign 2021 — Antimicrobial Stewardship Integration",
        "doc_type": "guideline",
        "text": """
Surviving Sepsis Campaign 2021 Guidelines — Antimicrobial Management

ANTIBIOTIC TIMING IN SEPSIS:
- Administer antibiotics within 1 hour of septic shock recognition (Best Practice Statement)
- Administer within 3 hours for sepsis without shock (Weak recommendation)
- Do not delay appropriate antibiotic administration for diagnostic workup in shock

EMPIRIC THERAPY SELECTION:
- Base empiric selection on clinical syndrome, infection source, patient risk factors, and local resistance patterns
- Broad-spectrum empiric therapy appropriate for septic shock; target de-escalation within 24-72 hours
- Reserve carbapenems for patients with prior resistant organism isolation, healthcare exposure, or high local carbapenem-resistance rates
- Anti-MRSA coverage (vancomycin, linezolid, daptomycin) for suspected MRSA sources (skin, bone, catheter)

DE-ESCALATION WITHIN SEPSIS:
- Reassess antibiotic regimen daily for de-escalation opportunities (Strong recommendation)
- De-escalate from broad-spectrum to pathogen-directed therapy based on culture results
- Stop antibiotics if infection not confirmed (Best Practice Statement)
- Do not use antimicrobials for systemic inflammatory response syndrome (SIRS) without infection

DURATION OF THERAPY:
- 7-day courses sufficient for most septic patients with adequate source control (Weak recommendation)
- Shorter courses appropriate for rapidly responding patients
- Procalcitonin may guide shorter antibiotic duration (Weak recommendation)
- No fixed duration for sepsis of unknown source: reassess daily

ANTIFUNGAL THERAPY:
- Empiric antifungals not recommended for sepsis of non-fungal source (Weak recommendation against)
- Reserve for suspected invasive candidiasis (immunocompromised, abdominal source, prolonged ICU stay)

PROCALCITONIN-GUIDED THERAPY:
- Suggests antibiotic discontinuation in patients who initially appeared infected but have low PCT levels
- PCT < 0.25 mcg/L supports stopping antibiotics in clinically improving patients
- PCT-guided protocols reduce antibiotic duration by 1-2 days without increased mortality
""",
    },
    {
        "source": "IDSA Antimicrobial Resistance Guidelines — Key Resistance Mechanisms and Clinical Implications",
        "doc_type": "guideline",
        "text": """
IDSA Antimicrobial Resistance — Key Clinical Guidance

GRAM-NEGATIVE RESISTANCE:

Extended-Spectrum Beta-Lactamase (ESBL)-Producing Enterobacteriaceae:
- Resist all penicillins, cephalosporins, and aztreonam
- Preferred treatment: carbapenems (ertapenem for non-severe, meropenem/imipenem for severe)
- Alternatives for susceptible isolates: piperacillin-tazobactam (PK/PD optimization required), fosfomycin (UTI only), nitrofurantoin (UTI only)
- Avoid cephalosporins even if in vitro susceptible (inoculum effect)
- ESBL screening: ceftriaxone MIC > 1 mcg/mL warrants ESBL testing

Carbapenem-Resistant Enterobacteriaceae (CRE):
- KPC (Klebsiella pneumoniae carbapenemase): treat with ceftazidime-avibactam, meropenem-vaborbactam, or imipenem-cilastatin-relebactam
- NDM (New Delhi metallo-beta-lactamase): ceftazidime-avibactam + aztreonam, or cefiderocol
- OXA-48: ceftazidime-avibactam
- Contact precautions + CRE screening for close contacts

Pseudomonas aeruginosa:
- Multi-drug resistant (MDR): consider ceftolozane-tazobactam, ceftazidime-avibactam, imipenem-cilastatin-relebactam
- XDR/pan-drug resistant: cefiderocol, combination therapy (beta-lactam + aminoglycoside or colistin)
- Biofilm producers: higher doses, combination therapy required

Acinetobacter baumannii:
- Carbapenem-resistant: colistin/polymyxin B + carbapenem (high-dose meropenem), tigecycline-based combinations, cefiderocol, sulbactam-durlobactam
- Contact precautions essential

GRAM-POSITIVE RESISTANCE:

MRSA (Methicillin-Resistant Staphylococcus aureus):
- Vancomycin: AUC/MIC 400-600 mg*h/L; dose 15-20 mg/kg q8-12h, Bayesian-adjusted
- Daptomycin: 6 mg/kg/day (BSI); 8-10 mg/kg/day (endocarditis, bone/joint); check CPK
- Linezolid: 600 mg q12h; preferred for MRSA pneumonia over vancomycin (lung penetration)
- Ceftaroline: MSSA/MRSA, good tissue penetration; role in salvage therapy
- Alternative for susceptible community MRSA (skin): clindamycin, doxycycline, TMP-SMX

VRE (Vancomycin-Resistant Enterococcus):
- E. faecium VanA: linezolid, daptomycin (high dose: 8-12 mg/kg), tigecycline (not for BSI)
- Monitor linezolid for myelosuppression (> 2 weeks), serotonin syndrome, optic neuropathy
- Tedizolid: limited evidence vs. vancomycin-resistant Enterococcus

Clostridioides difficile:
- Mild-moderate: vancomycin 125 mg PO q6h x 10 days OR fidaxomicin 200 mg PO q12h x 10 days
- Severe (WBC > 15k, Cr > 1.5): vancomycin 125 mg PO q6h x 10 days
- Fulminant: vancomycin 500 mg PO/PR q6h + metronidazole 500 mg IV q8h + surgical consult
- Recurrence: fidaxomicin preferred over vancomycin for first recurrence; bezlotoxumab for prevention
- DO NOT use metronidazole as monotherapy for CDI (inferior outcomes)

RESISTANCE SURVEILLANCE METRICS:

NHSN Antimicrobial Resistance Targets:
- MRSA bacteremia standardized infection ratio (SIR): target < 1.0
- CDI SIR: target < 1.0
- ESBL-producing organisms: track rates by species
- CRE: zero-tolerance target; investigate all cases

Antibiogram Interpretation:
- Generate cumulative antibiograms annually per CLSI guidelines
- Report only first isolate per patient per analysis period
- Include minimum of 30 isolates per organism-drug combination
- Separate ICU from non-ICU antibiograms
- Use antibiogram to guide empiric therapy selection and formulary decisions
""",
    },
    {
        "source": "IDSA 2024 Guidance on the Treatment of Antimicrobial-Resistant Gram-Negative Infections (CID 2024)",
        "doc_type": "guideline",
        "text": """
IDSA 2024 Guidance on the Treatment of Antimicrobial-Resistant Gram-Negative Infections
Published: Clinical Infectious Diseases, 2024 (major revision of 2023 guidance)

CARBAPENEM-RESISTANT ACINETOBACTER BAUMANNII (CRAB):

Preferred Treatment (updated 2024):
- Sulbactam-durlobactam (Xacduro) + imipenem-cilastatin or meropenem
  * FDA approved May 2023; first dedicated CRAB-specific therapy
  * Dosing: sulbactam-durlobactam 1g/0.5g IV q6h (3-hr infusion) + carbapenem
  * Superior to colistin in ATTACK trial (28-day mortality 19% vs 32%)
  * Active against OXA-23, OXA-24/40, OXA-58 carbapenemases

Alternative Treatment (downgraded from preferred in 2024):
- High-dose ampicillin-sulbactam 27g/day (18g ampicillin + 9g sulbactam as continuous/extended infusion)
  * Use only if sulbactam-durlobactam unavailable
  * Combine with at least one other active agent (polymyxin, minocycline)

Other:
- Cefiderocol: reserve for XDR/PDR; broad Acinetobacter activity
- Tigecycline: removed from CRAB combination guidance in 2024 update

CARBAPENEM-RESISTANT ENTEROBACTERIACEAE (CRE):

KPC-producing (preferred):
- Ceftazidime-avibactam 2.5g IV q8h (3-hr infusion)
- Meropenem-vaborbactam 4g IV q8h (3-hr infusion)
- Imipenem-cilastatin-relebactam 1.25g IV q6h

NDM/MBL-producing (preferred):
- Ceftazidime-avibactam + aztreonam (concurrent IV; aztreonam not hydrolyzed by MBLs)
- Cefiderocol monotherapy (salvage for pan-drug resistant)

OXA-48-producing:
- Ceftazidime-avibactam preferred
- Cefiderocol alternative

PSEUDOMONAS AERUGINOSA (MDR/XDR):
- Ceftolozane-tazobactam 3g IV q8h (preferred for MDR without carbapenem resistance)
- Ceftazidime-avibactam (KPC or AmpC-mediated resistance)
- Imipenem-cilastatin-relebactam (restored susceptibility in some MDR strains)
- Cefiderocol (XDR/PDR, DTR Pseudomonas)
- Combination therapy not routinely recommended unless XDR

STENOTROPHOMONAS MALTOPHILIA (new 2024 guidance):
- TMP-SMX: preferred for susceptible isolates (15 mg/kg/day TMP component IV/PO divided q6-8h)
- Ceftazidime-avibactam + aztreonam: active against most isolates; CLSI broth disk elution method endorsed
- Do NOT test or use ceftazidime monotherapy (2024 guidance explicitly discourages)
- Tigecycline removed from combination recommendations
- Minocycline or levofloxacin: alternatives for susceptible isolates

KEY 2024 CHANGES:
1. Sulbactam-durlobactam replaces high-dose amp-sulbactam as preferred CRAB agent
2. Tigecycline removed from CRAB and S. maltophilia combination guidance
3. Ceftazidime monotherapy testing for S. maltophilia discouraged
4. CZA+ATM remains standard of care for NDM-producing CRE
5. Cefiderocol clarified as salvage agent for XDR/PDR organisms
""",
    },
    {
        "source": "CDI Treatment 2025 Update — Bezlotoxumab Discontinuation, Rebyota and Vowst (IDSA/SHEA 2021 base + 2025 formulary updates)",
        "doc_type": "guideline",
        "text": """
Clostridioides difficile Infection (CDI) — 2025 Treatment Updates
Base: IDSA/SHEA 2021 guidelines with 2024-2025 agent changes

CURRENT TREATMENT ALGORITHM:

Initial Episode:
- Preferred: Fidaxomicin 200 mg PO q12h x 10 days
- Alternative: Vancomycin 125 mg PO q6h x 10 days
- Metronidazole: NOT for primary CDI treatment (inferior to vancomycin/fidaxomicin); adjunct IV only in fulminant disease

Severe CDI (WBC >15k or Cr >1.5):
- Vancomycin 125 mg PO q6h x 10 days

Fulminant CDI (ileus, megacolon, hypotension):
- Vancomycin 500 mg PO/NGT q6h + rectal instillation if ileus
- Metronidazole 500 mg IV q8h (adjunct; reaches colon via IV when PO absorption impaired)
- Urgent surgical consultation

RECURRENT CDI:

First Recurrence:
- Fidaxomicin preferred over vancomycin (EXTEND trial; lower further recurrence)
- Vancomycin tapered/pulsed if fidaxomicin unavailable:
  125 mg QID x 10d → BID x 7d → QD x 7d → q2-3 days x 2-8 weeks

Second or Subsequent Recurrence — Microbiota Restoration:
1. Rebyota (fecal microbiota, live-jslm): FDA approved Nov 2022
   * Single-dose rectal administration (150 mL), 24-72h after last antibiotic
   * >70% prevention of further recurrence at 8 weeks
2. Vowst (fecal microbiota spores live-brpk): FDA approved April 2023
   * 3 capsules PO daily x 3 days, 24-72h after last antibiotic
   * ~88% prevention of recurrence (ECOSPOR III trial)

AGENT DISCONTINUED (2025):
- Bezlotoxumab (Zinplava): WITHDRAWN from market by manufacturer in 2025
  * Was a monoclonal antibody against C. difficile toxin B; single IV infusion during antibiotic treatment
  * Remove from formularies and clinical pathways immediately
  * Rebyota and Vowst are now the primary recurrence-prevention options for high-risk patients

CDI STEWARDSHIP METRICS:
- Hospital-onset CDI: < 6.3 per 10,000 patient-days (NHSN benchmark)
- Target zero inappropriate metronidazole for non-fulminant CDI
- Time to appropriate oral therapy: < 24 hours from diagnosis
""",
    },
]


def main():
    parser = argparse.ArgumentParser(description="AMS Vault Ingestor")
    parser.add_argument("--pubmed-only",      action="store_true", help="Only ingest PubMed literature")
    parser.add_argument("--guidelines-only",  action="store_true", help="Only ingest static guidelines")
    parser.add_argument("--max",              type=int, default=30, help="Max PubMed articles per query")
    parser.add_argument("--min-year",         type=int, default=2018, help="Minimum publication year for PubMed")
    args = parser.parse_args()

    from shared.vault_ingestor import add_text, add_pubmed_articles, vault_stats

    do_guidelines = not args.pubmed_only
    do_pubmed     = not args.guidelines_only

    # ── 1. Static Guidelines ─────────────────────────────────────────────────
    if do_guidelines:
        print("\n=== Ingesting ASHP / IDSA / CDC Guidelines ===")
        total_chunks = 0
        for g in GUIDELINES:
            print(f"\n  Source: {g['source'][:70]}...")
            n = add_text(
                text=g["text"],
                source=g["source"],
                doc_type=g["doc_type"],
                verbose=True,
            )
            total_chunks += n
            print(f"  -> {n} chunks ingested")
            time.sleep(0.2)
        print(f"\nGuidelines total: {total_chunks} chunks ingested")

    # ── 2. PubMed Literature ─────────────────────────────────────────────────
    if do_pubmed:
        print("\n=== Fetching PubMed AMS Literature ===")
        from data_sources.pubmed_client import fetch_ams_literature
        articles = fetch_ams_literature(max_per_query=args.max, min_year=args.min_year)
        print(f"\nFetched {len(articles)} articles. Embedding and ingesting...")
        n = add_pubmed_articles(articles, verbose=True)
        print(f"\nPubMed total: {n} chunks ingested")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n=== Vault Summary ===")
    stats = vault_stats()
    print(f"Total chunks in vault: {stats['total_chunks']}")
    print(f"Unique sources: {len(stats['sources'])}")
    for src, cnt in sorted(stats['sources'].items(), key=lambda x: -x[1])[:20]:
        print(f"  {cnt:4d}  {src[:80]}")


if __name__ == "__main__":
    main()
