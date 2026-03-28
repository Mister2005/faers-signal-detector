-- Raw ingestion tables (one row per report per file)

CREATE TABLE IF NOT EXISTS raw_demo (
    primaryid       BIGINT,
    caseid          BIGINT,
    caseversion     INTEGER,
    i_f_code        VARCHAR(1),     -- 'I' = initial, 'F' = follow-up
    event_dt        VARCHAR(8),     -- YYYYMMDD format (often partial)
    mfr_dt          VARCHAR(8),
    init_fda_dt     VARCHAR(8),
    fda_dt          VARCHAR(8),
    rept_cod        VARCHAR(10),    -- EXP=expedited, PER=periodic, etc.
    auth_num        VARCHAR(50),
    mfr_num         VARCHAR(100),
    mfr_sndr        VARCHAR(100),
    lit_ref         TEXT,
    age             NUMERIC,
    age_cod         VARCHAR(10),    -- YR, MON, WK, DY
    age_grp         VARCHAR(5),
    sex             VARCHAR(10),    -- M, F, UNK
    e_sub           VARCHAR(1),
    wt              NUMERIC,
    wt_cod          VARCHAR(10),
    rept_dt         VARCHAR(8),
    to_mfr          VARCHAR(1),
    occp_cod        VARCHAR(10),    -- HP=health professional, CS=consumer
    reporter_country VARCHAR(100),
    occr_country    VARCHAR(100),
    quarter         VARCHAR(10)     -- e.g. '2023Q1' - added during ingestion
);

CREATE TABLE IF NOT EXISTS raw_drug (
    primaryid       BIGINT,
    caseid          BIGINT,
    drug_seq        INTEGER,
    role_cod        VARCHAR(5),     -- PS=primary suspect, SS=secondary suspect, C=concomitant, I=interacting
    drugname        TEXT,
    prod_ai         TEXT,           -- active ingredient
    val_vbm         INTEGER,
    route           VARCHAR(100),
    dose_vbm        TEXT,
    cum_dose_chr    TEXT,
    cum_dose_unit   TEXT,
    dechal          VARCHAR(1),     -- dechallenge: did AE stop when drug stopped?
    rechal          VARCHAR(1),     -- rechallenge: did AE return when drug restarted?
    lot_num         VARCHAR(50),
    exp_dt          VARCHAR(8),
    nda_num         VARCHAR(20),
    dose_amt        TEXT,
    dose_unit       TEXT,
    dose_freq       VARCHAR(50),
    quarter         VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS raw_reac (
    primaryid       BIGINT,
    caseid          BIGINT,
    pt              TEXT,           -- MedDRA Preferred Term
    drug_rec_act    TEXT,
    quarter         VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS raw_outc (
    primaryid       BIGINT,
    caseid          BIGINT,
    outc_cod        VARCHAR(5),     -- DE=death, LT=life-threatening, HO=hospitalization, DS=disability, CA=congenital anomaly, RI=required intervention, OT=other
    quarter         VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS raw_indi (
    primaryid       BIGINT,
    caseid          BIGINT,
    drug_seq        INTEGER,
    indi_drug_seq   INTEGER,
    indi_pt         TEXT,           -- indication (what drug was prescribed for)
    quarter         VARCHAR(10)
);

-- Cleaned / deduplicated tables

CREATE TABLE IF NOT EXISTS clean_demo (
    primaryid           BIGINT PRIMARY KEY,
    caseid              BIGINT,
    quarter             VARCHAR(10),
    age_years           NUMERIC,    -- normalized to years
    sex                 VARCHAR(10),
    reporter_country    VARCHAR(100),
    occp_cod            VARCHAR(10),
    serious             BOOLEAN     -- TRUE if any serious outcome exists
);

CREATE TABLE IF NOT EXISTS clean_drug (
    primaryid           BIGINT,
    drug_seq            INTEGER,
    role_cod            VARCHAR(5),
    drug_name_raw       TEXT,
    drug_name_clean     TEXT,       -- standardized generic name
    route               VARCHAR(100),
    quarter             VARCHAR(10),
    PRIMARY KEY (primaryid, drug_seq)
);

CREATE TABLE IF NOT EXISTS clean_reac (
    primaryid           BIGINT,
    reaction_pt         TEXT,       -- uppercased MedDRA preferred term
    soc_name            TEXT,       -- system organ class (from reference file)
    quarter             VARCHAR(10),
    PRIMARY KEY (primaryid, reaction_pt)
);

CREATE TABLE IF NOT EXISTS clean_outc (
    primaryid           BIGINT,
    outc_cod            VARCHAR(5),
    quarter             VARCHAR(10),
    PRIMARY KEY (primaryid, outc_cod)
);

-- Signal results table

CREATE TABLE IF NOT EXISTS signal_results (
    drug_name           TEXT,
    reaction_pt         TEXT,
    quarter_cutoff      VARCHAR(10),    -- signals computed up to this quarter (cumulative)
    case_count          INTEGER,        -- = a
    drug_total          INTEGER,        -- = a + b
    event_total         INTEGER,        -- = a + c
    total_reports       INTEGER,        -- = N
    prr                 NUMERIC,
    chi2                NUMERIC,
    ror                 NUMERIC,
    ror_ci_lower        NUMERIC,
    ror_ci_upper        NUMERIC,
    is_signal           BOOLEAN,        -- TRUE if all thresholds met
    PRIMARY KEY (drug_name, reaction_pt, quarter_cutoff)
);

-- Indexes for dashboard query performance
CREATE INDEX IF NOT EXISTS idx_clean_drug_name ON clean_drug(drug_name_clean);
CREATE INDEX IF NOT EXISTS idx_clean_reac_pt ON clean_reac(reaction_pt);
CREATE INDEX IF NOT EXISTS idx_signal_drug ON signal_results(drug_name);
CREATE INDEX IF NOT EXISTS idx_signal_reaction ON signal_results(reaction_pt);
CREATE INDEX IF NOT EXISTS idx_signal_quarter ON signal_results(quarter_cutoff);
CREATE INDEX IF NOT EXISTS idx_signal_is_signal ON signal_results(is_signal);
