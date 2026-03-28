SELECT DISTINCT ON (caseid)
    primaryid::BIGINT,
    caseid::BIGINT,
    quarter,
    age,
    age_cod,
    sex,
    reporter_country,
    occp_cod
FROM raw_demo
WHERE primaryid IS NOT NULL AND caseid IS NOT NULL
ORDER BY caseid, fda_dt DESC NULLS LAST, caseversion DESC NULLS LAST;
