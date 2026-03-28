WITH
drug_event AS (
    SELECT
        d.drug_name_clean        AS drug_name,
        r.reaction_pt,
        COUNT(DISTINCT d.primaryid) AS a
    FROM clean_drug d
    INNER JOIN clean_reac r ON d.primaryid = r.primaryid
    WHERE d.drug_name_clean != 'UNKNOWN'
    GROUP BY d.drug_name_clean, r.reaction_pt
    HAVING COUNT(DISTINCT d.primaryid) >= 3
),
drug_totals AS (
    SELECT drug_name_clean AS drug_name, COUNT(DISTINCT primaryid) AS drug_total
    FROM clean_drug GROUP BY drug_name_clean
),
event_totals AS (
    SELECT reaction_pt, COUNT(DISTINCT primaryid) AS event_total
    FROM clean_reac GROUP BY reaction_pt
),
n_total AS (
    SELECT COUNT(DISTINCT primaryid) AS n FROM clean_demo
)
SELECT
    de.drug_name,
    de.reaction_pt,
    de.a                                        AS case_count,
    dt.drug_total                               AS drug_total,
    et.event_total                              AS event_total,
    nt.n                                        AS total_reports,
    -- PRR
    ROUND(
        (de.a::NUMERIC / dt.drug_total) /
        ((et.event_total - de.a)::NUMERIC / (nt.n - dt.drug_total))
    , 4)                                        AS prr,
    -- ROR
    ROUND(
        (de.a::NUMERIC * (nt.n - dt.drug_total - et.event_total + de.a)) /
        ((dt.drug_total - de.a)::NUMERIC * (et.event_total - de.a))
    , 4)                                        AS ror,
    CASE
        WHEN de.a >= 3
         AND (de.a::NUMERIC / dt.drug_total) / ((et.event_total - de.a)::NUMERIC / (nt.n - dt.drug_total)) >= 2
        THEN TRUE ELSE FALSE
    END                                         AS is_signal
FROM drug_event de
JOIN drug_totals dt  ON de.drug_name   = dt.drug_name
JOIN event_totals et ON de.reaction_pt = et.reaction_pt
CROSS JOIN n_total nt
ORDER BY prr DESC;
