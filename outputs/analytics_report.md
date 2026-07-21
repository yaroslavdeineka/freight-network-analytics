# Freight Network Analytics — Query Results

*Generated 2026-07-21 18:18 · real data through **2026-07-17***

<details><summary><b>Port codes used in this report</b></summary>

| Code | Port | Country |
|---|---|---|
| `EGALY` | Alexandria | Egypt |
| `KRPUS` | Busan | South Korea |
| `GBFXT` | Felixstowe | United Kingdom |
| `PLGDN` | Gdansk | Poland |
| `DEHAM` | Hamburg | Germany |
| `AEJEA` | Jebel Ali | UAE |
| `USLGB` | Long Beach | United States |
| `TRMER` | Mersin | Turkey |
| `USNYC` | New York | United States |
| `INNSA` | Nhava Sheva | India |
| `UAODS` | Odesa | Ukraine |
| `NLRTM` | Rotterdam | Netherlands |
| `BRSSZ` | Santos | Brazil |
| `CNSHA` | Shanghai | China |
| `CNSZX` | Shenzhen | China |
| `SGSIN` | Singapore | Singapore |

</details>


## 01_executive_kpis

*Source: `analytics/01_executive_kpis.sql`*

| month   |   shipments |   mom_change |   mom_growth_pct |   total_cbm |   cumulative_cbm |   shipments_3mo_avg |   active_customers |   on_time_pct |   avg_transit_days |
|:--------|------------:|-------------:|-----------------:|------------:|-----------------:|--------------------:|-------------------:|--------------:|-------------------:|
| 2024-07 |          15 |            — |              —   |       276.1 |            276.1 |                15   |                  6 |          80   |               16.9 |
| 2024-08 |          82 |           67 |            446.7 |      1458.6 |           1734.7 |                48.5 |                 13 |          80.5 |               16.6 |
| 2024-09 |         221 |          139 |            169.5 |      4018.2 |           5752.9 |               106   |                 18 |          81   |               16.7 |
| 2024-10 |         194 |          -27 |            -12.2 |      3529.3 |           9282.2 |               165.7 |                 18 |          79.4 |               16.8 |
| 2024-11 |         212 |           18 |              9.3 |      4424.3 |          13706.5 |               209   |                 26 |          83   |               15.8 |
| 2024-12 |         164 |          -48 |            -22.6 |      2992.4 |          16698.9 |               190   |                 26 |          83.5 |               16.3 |
| 2025-01 |          88 |          -76 |            -46.3 |      1753.9 |          18452.8 |               154.7 |                 28 |          85.2 |               16.3 |
| 2025-02 |         110 |           22 |             25   |      1873.9 |          20326.7 |               120.7 |                 30 |          80   |               16.4 |
| 2025-03 |         154 |           44 |             40   |      2543.4 |          22870.1 |               117.3 |                 38 |          78.6 |               17.2 |
| 2025-04 |         208 |           54 |             35.1 |      3483.1 |          26353.2 |               157.3 |                 38 |          81.3 |               16.5 |
| 2025-05 |         180 |          -28 |            -13.5 |      3312.4 |          29665.6 |               180.7 |                 40 |          78.9 |               16.5 |
| 2025-06 |         174 |           -6 |             -3.3 |      3425   |          33090.6 |               187.3 |                 38 |          76.4 |               16.8 |
| 2025-07 |         178 |            4 |              2.3 |      3720.7 |          36811.3 |               177.3 |                 45 |          83.1 |               16.8 |
| 2025-08 |         211 |           33 |             18.5 |      3823.3 |          40634.6 |               187.7 |                 48 |          82   |               16.7 |
| 2025-09 |         318 |          107 |             50.7 |      6150.5 |          46785.1 |               235.7 |                 52 |          51.6 |               20.3 |
| 2025-10 |         362 |           44 |             13.8 |      6837.3 |          53622.4 |               297   |                 58 |          45   |               20.8 |
| 2025-11 |         366 |            4 |              1.1 |      6808.1 |          60430.5 |               348.7 |                 60 |          79.2 |               16.7 |
| 2025-12 |         345 |          -21 |             -5.7 |      6601.7 |          67032.2 |               357.7 |                 64 |          82.9 |               16.1 |
| 2026-01 |         190 |         -155 |            -44.9 |      3574.2 |          70606.4 |               300.3 |                 59 |          82.1 |               16.6 |
| 2026-02 |         201 |           11 |              5.8 |      3521.9 |          74128.3 |               245.3 |                 61 |          83.1 |               15.8 |
| 2026-03 |         389 |          188 |             93.5 |      7505.6 |          81633.9 |               260   |                 69 |          82.8 |               15.8 |
| 2026-04 |         366 |          -23 |             -5.9 |      6951.1 |          88585   |               318.7 |                 68 |          79.8 |               16.8 |
| 2026-05 |         345 |          -21 |             -5.7 |      6172.7 |          94757.7 |               366.7 |                 63 |          84.3 |               16.7 |
| 2026-06 |         127 |         -218 |            -63.2 |      2860.6 |          97618.3 |               279.3 |                 51 |          87.1 |               12.7 |


## 02_route_pathfinding

*Source: `analytics/02_route_pathfinding.sql`*

| routing                       |   legs | modes            |   transit_days |   cost_per_cbm_usd |   cost_rank |   speed_rank |
|:------------------------------|-------:|:-----------------|---------------:|-------------------:|------------:|-------------:|
| UAODS → EGALY → CNSHA         |      2 | sea / sea        |             21 |              78    |           1 |            1 |
| UAODS → TRMER → EGALY → CNSHA |      3 | sea / sea / sea  |             21 |              86    |           2 |            1 |
| UAODS → EGALY → SGSIN → CNSHA |      3 | sea / sea / sea  |             22 |              91    |           3 |            3 |
| UAODS → PLGDN → NLRTM → CNSHA |      3 | rail / sea / sea |             35 |             122.65 |           4 |            4 |
| UAODS → TRMER → NLRTM → CNSHA |      3 | sea / sea / sea  |             39 |             124    |           5 |            5 |
| UAODS → EGALY → NLRTM → CNSHA |      3 | sea / sea / sea  |             40 |             127    |           6 |            6 |


## 03_transit_bottlenecks

*Source: `analytics/03_transit_bottlenecks.sql`*

| stage                                | location   |   observations |   median_days |   p90_days |   worst_case_days |   p90_to_median_ratio |
|:-------------------------------------|:-----------|---------------:|--------------:|-----------:|------------------:|----------------------:|
| DEPARTED → TRANSSHIPMENT_IN          | NLRTM      |            728 |          7.96 |      28.08 |              28.4 |                   3.5 |
| DEPARTED → ARRIVED                   | GBFXT      |             90 |         27.58 |      27.88 |              27.9 |                   1   |
| TRANSSHIPMENT_OUT → ARRIVED          | NLRTM      |          1,738 |         13.08 |      18.5  |              32.7 |                   1.4 |
| TRANSSHIPMENT_OUT → ARRIVED          | DEHAM      |            969 |          9.67 |      17.13 |              21.8 |                   1.8 |
| TRANSSHIPMENT_OUT → ARRIVED          | CNSHA      |            311 |         14.75 |      16.96 |              20.7 |                   1.1 |
| DEPARTED → ARRIVED                   | USLGB      |            505 |         14.58 |      16.54 |              19.6 |                   1.1 |
| TRANSSHIPMENT_OUT → ARRIVED          | USLGB      |            208 |         12.6  |      14.73 |              17.3 |                   1.2 |
| DEPARTED → ARRIVED                   | USNYC      |            418 |         10.54 |      12.54 |              15.6 |                   1.2 |
| DEPARTED → TRANSSHIPMENT_IN          | TRMER      |            582 |          3.08 |       9.04 |               9.4 |                   2.9 |
| DEPARTED → ARRIVED                   | DEHAM      |             69 |          3.92 |       7.75 |               7.9 |                   2   |
| BOOKED → CARGO_RECEIVED              | SGSIN      |            210 |          3.23 |       6.04 |               7.5 |                   1.9 |
| TRANSSHIPMENT_IN → TRANSSHIPMENT_OUT | NLRTM      |            582 |          1.25 |       6    |              13.7 |                   4.8 |
| DEPARTED → TRANSSHIPMENT_IN          | SGSIN      |          1,437 |          4.83 |       5.92 |               6.4 |                   1.2 |
| BOOKED → CARGO_RECEIVED              | TRMER      |            306 |          3.33 |       5.79 |               8.5 |                   1.7 |
| BOOKED → CARGO_RECEIVED              | EGALY      |            204 |          3.13 |       5.61 |               7.6 |                   1.8 |


## 04_customer_segmentation

*Source: `analytics/04_customer_segmentation.sql`*

| segment              |   customers |   shipments |      revenue_usd |   revenue_share_pct |   class_a_customers |   class_b_customers |   class_c_customers |
|:---------------------|------------:|------------:|-----------------:|--------------------:|--------------------:|--------------------:|--------------------:|
| Champion             |          16 |        2658 |      4.63929e+06 |                52.4 |                  16 |                   0 |                   0 |
| Core                 |          24 |         993 |      1.60699e+06 |                18.1 |                   8 |                  10 |                   6 |
| At Risk (high value) |          11 |         613 |      1.11686e+06 |                12.6 |                  11 |                   0 |                   0 |
| Dormant              |          13 |         379 | 616097           |                 7   |                   2 |                   8 |                   3 |
| Loyal                |           8 |         304 | 480304           |                 5.4 |                   5 |                   3 |                   0 |
| New / Developing     |           8 |         253 | 402368           |                 4.5 |                   1 |                   4 |                   3 |


## 05_cohort_retention

*Source: `analytics/05_cohort_retention.sql`*

| cohort   |   size |   q0 |   q1_pct |   q2_pct |   q3_pct |   q4_pct |   q5_pct |   q6_pct |
|:---------|-------:|-----:|---------:|---------:|---------:|---------:|---------:|---------:|
| 2024-Q3  |     19 |   18 |      100 |      100 |       95 |       95 |       95 |       95 |
| 2024-Q4  |     13 |   12 |      100 |      100 |      100 |       92 |       77 |       85 |
| 2025-Q1  |     10 |    9 |      100 |      100 |       90 |       90 |       70 |        — |
| 2025-Q2  |      5 |    5 |      100 |      100 |      100 |       60 |        — |        — |
| 2025-Q3  |     10 |   10 |      100 |      100 |       90 |        — |        — |        — |
| 2025-Q4  |     11 |   11 |      100 |      100 |        — |        — |        — |        — |
| 2026-Q1  |     12 |   12 |      100 |        — |        — |        — |        — |        — |


## 06_fx_normalized_revenue

*Source: `analytics/06_fx_normalized_revenue.sql`*

| region      | quarter   |   invoices |      revenue_usd |   avg_invoice_usd |   currencies_billed |
|:------------|:----------|-----------:|-----------------:|------------------:|--------------------:|
| Asia        | 2024-Q3   |        167 | 281757           |              1687 |                   2 |
| Asia        | 2024-Q4   |        319 | 615295           |              1929 |                   2 |
| Asia        | 2025-Q1   |        200 | 326533           |              1633 |                   2 |
| Asia        | 2025-Q2   |        299 | 568243           |              1900 |                   2 |
| Asia        | 2025-Q3   |        407 | 780894           |              1919 |                   2 |
| Asia        | 2025-Q4   |        584 |      1.13636e+06 |              1946 |                   2 |
| Asia        | 2026-Q1   |        436 | 805012           |              1846 |                   2 |
| Asia        | 2026-Q2   |        505 |      1.05748e+06 |              2094 |                   2 |
| Asia        | subtotal  |      2,917 |      5.57158e+06 |              1910 |                   2 |
| Europe      | 2024-Q3   |         89 | 130655           |              1468 |                   3 |
| Europe      | 2024-Q4   |        178 | 267523           |              1503 |                   3 |
| Europe      | 2025-Q1   |        102 | 149868           |              1469 |                   3 |
| Europe      | 2025-Q2   |        190 | 289703           |              1525 |                   3 |
| Europe      | 2025-Q3   |        202 | 312763           |              1548 |                   3 |
| Europe      | 2025-Q4   |        347 | 512522           |              1477 |                   3 |
| Europe      | 2026-Q1   |        237 | 351781           |              1484 |                   3 |
| Europe      | 2026-Q2   |        265 | 385378           |              1454 |                   3 |
| Europe      | subtotal  |      1,610 |      2.40019e+06 |              1491 |                   3 |
| MEA         | 2024-Q3   |         47 |  64539           |              1373 |                   2 |
| MEA         | 2024-Q4   |         74 | 105731           |              1429 |                   2 |
| MEA         | 2025-Q1   |         53 |  74053           |              1397 |                   2 |
| MEA         | 2025-Q2   |         76 |  75487           |               993 |                   2 |
| MEA         | 2025-Q3   |         85 | 151561           |              1783 |                   2 |
| MEA         | 2025-Q4   |        133 | 183555           |              1380 |                   2 |
| MEA         | 2026-Q1   |        113 | 152220           |              1347 |                   2 |
| MEA         | 2026-Q2   |         99 | 129772           |              1311 |                   2 |
| MEA         | subtotal  |        680 | 936918           |              1378 |                   2 |
| ── TOTAL ── |           |      5,207 |      8.90869e+06 |              1711 |                   4 |


## 07_receivables_aging

*Source: `analytics/07_receivables_aging.sql`*

| aging_bucket           |   invoices |   outstanding_usd |   share_pct |   customers_affected |
|:-----------------------|-----------:|------------------:|------------:|---------------------:|
| 1 · Not yet due        |        117 |            224003 |        28.3 |                   51 |
| 2 · 1-30 days overdue  |         78 |            146791 |        18.5 |                   30 |
| 3 · 31-60 days overdue |         26 |             32315 |         4.1 |                    9 |
| 4 · 61-90 days overdue |         13 |             17654 |         2.2 |                    7 |
| 5 · 90+ days overdue   |        225 |            371743 |        46.9 |                   10 |


## 07b · PAYMENT DISCIPLINE & DSO — WHO ACTUALLY PAYS?

*Source: `analytics/07b_payment_discipline.sql`*

| customer                 |   invoices |   paid |   avg_days_late |   paid_late_pct |   outstanding_usd |   overdue_90d_usd |   dso_days |
|:-------------------------|-----------:|-------:|----------------:|----------------:|------------------:|------------------:|-----------:|
| ── ALL CUSTOMERS ──      |      5,207 |  4,748 |             6   |            46.3 |           792,506 |           360,765 |         47 |
| Meridian Exports S.A.    |        252 |    173 |            34.1 |            96.5 |           132,884 |           101,979 |        179 |
| Global Logistics LLP     |        212 |    141 |            37.5 |            97.2 |           111,063 |            90,567 |        237 |
| Global Distribution LLC  |        237 |    165 |            32.4 |            94.5 |           102,589 |            84,468 |        205 |
| Central Exports GmbH     |         39 |     23 |            32.4 |           100   |            34,355 |            17,046 |        256 |
| Orion Logistics LLC      |         48 |     38 |            11.6 |            84.2 |            31,537 |                 — |        118 |
| Prime Commodities OÜ     |         26 |     15 |            25   |            93.3 |            27,057 |            15,625 |        220 |
| Summit Exports LLC       |         28 |     17 |            33.2 |           100   |            25,140 |            18,355 |        250 |
| Vector Trading GmbH      |         42 |     34 |            10.1 |            79.4 |            22,063 |                 — |        104 |
| Crown Exports Sp. z o.o. |         42 |     31 |            11.6 |            96.8 |            21,168 |                 — |        132 |
| Global Manufacturing OÜ  |         30 |     15 |            30   |            93.3 |            20,076 |                 — |        141 |
| Orion Trading Sp. z o.o. |         37 |     22 |            28.1 |            95.5 |            18,884 |             9,733 |        140 |
| Coastal Group Sp. z o.o. |         39 |     32 |            13.6 |            87.5 |            16,182 |                 — |         89 |
| Anchor Supply PLC        |         27 |     15 |            33.9 |            93.3 |            15,322 |                 — |        156 |
| Baltic Industries LLP    |        237 |    234 |            -1.9 |            23.9 |            12,779 |                 — |         20 |
| United Industries PLC    |        244 |    238 |            -2.1 |            17.2 |            12,437 |             3,667 |         23 |


## 08_anomaly_detection

*Source: `analytics/08_anomaly_detection.sql`*

| shipment_id    | lane          |   actual_days |   lane_avg_days |   z_score |   days_late_vs_eta | severity      |
|:---------------|:--------------|--------------:|----------------:|----------:|-------------------:|:--------------|
| SHP-2025-04618 | CNSHA → NLRTM |            38 |            22.5 |      4.36 |                 18 | 🔴 investigate |
| SHP-2025-01887 | CNSHA → NLRTM |            38 |            22.5 |      4.36 |                 17 | 🔴 investigate |
| SHP-2025-01491 | CNSHA → NLRTM |            38 |            22.5 |      4.36 |                 19 | 🔴 investigate |
| SHP-2025-00075 | CNSHA → NLRTM |            38 |            22.5 |      4.36 |                 17 | 🔴 investigate |
| SHP-2025-03070 | TRMER → DEHAM |            26 |            11.4 |      4.23 |                 16 | 🔴 investigate |
| SHP-2025-02682 | CNSHA → GBFXT |            45 |            30.3 |      4.2  |                 17 | 🔴 investigate |
| SHP-2025-01095 | CNSHA → NLRTM |            37 |            22.5 |      4.08 |                 16 | 🔴 investigate |
| SHP-2025-03762 | CNSHA → NLRTM |            37 |            22.5 |      4.08 |                 16 | 🔴 investigate |
| SHP-2025-03611 | CNSHA → NLRTM |            37 |            22.5 |      4.08 |                 16 | 🔴 investigate |
| SHP-2025-01390 | EGALY → PLGDN |            25 |            11.5 |      3.98 |                 17 | 🔴 investigate |
| SHP-2025-00583 | TRMER → DEHAM |            25 |            11.4 |      3.94 |                 16 | 🔴 investigate |
| SHP-2025-02872 | TRMER → DEHAM |            25 |            11.4 |      3.94 |                 16 | 🔴 investigate |
| SHP-2025-00812 | TRMER → DEHAM |            25 |            11.4 |      3.94 |                 15 | 🔴 investigate |
| SHP-2025-02347 | CNSHA → GBFXT |            44 |            30.3 |      3.92 |                 15 | 🔴 investigate |
| SHP-2025-03208 | CNSHA → GBFXT |            44 |            30.3 |      3.92 |                 15 | 🔴 investigate |
| SHP-2025-04396 | CNSHA → GBFXT |            44 |            30.3 |      3.92 |                 16 | 🔴 investigate |
| SHP-2025-01860 | CNSHA → GBFXT |            44 |            30.3 |      3.92 |                 15 | 🔴 investigate |
| SHP-2025-00751 | CNSHA → GBFXT |            44 |            30.3 |      3.92 |                 15 | 🔴 investigate |
| SHP-2025-01942 | INNSA → NLRTM |            32 |            17.7 |      3.89 |                 16 | 🔴 investigate |
| SHP-2025-04461 | INNSA → NLRTM |            32 |            17.7 |      3.89 |                 16 | 🔴 investigate |


## 09_aml_screening

*Source: `analytics/09_aml_screening.sql`*

| screen                | customer_name            | invoice_id     | issue_date          |   amount |   evidence_count |   evidence_amount |
|:----------------------|:-------------------------|:---------------|:--------------------|---------:|-----------------:|------------------:|
| A · STRUCTURING       | Baltic Commodities S.A.  | INV-2025-90000 | 2025-09-10 00:00:00 |  9596.55 |                4 |          37940    |
| A · STRUCTURING       | Baltic Commodities S.A.  | INV-2025-90001 | 2025-09-12 00:00:00 |  9403.88 |                4 |          37940    |
| A · STRUCTURING       | Baltic Commodities S.A.  | INV-2025-90002 | 2025-09-14 00:00:00 |  9424.22 |                4 |          37940    |
| A · STRUCTURING       | Baltic Commodities S.A.  | INV-2025-90003 | 2025-09-16 00:00:00 |  9515.35 |                4 |          37940    |
| B · DUPLICATE BILLING | Crown Exports Sp. z o.o. | INV-2026-00092 | 2026-05-08 00:00:00 |  3680.41 |                2 |           7360.82 |
| B · DUPLICATE BILLING | Crown Exports Sp. z o.o. | INV-2025-95001 | 2026-05-11 00:00:00 |  3680.41 |                2 |           7360.82 |
| B · DUPLICATE BILLING | Global Manufacturing OÜ  | INV-2026-04429 | 2026-04-06 00:00:00 |  6525.88 |                2 |          13051.8  |
| B · DUPLICATE BILLING | Global Manufacturing OÜ  | INV-2025-95000 | 2026-04-16 00:00:00 |  6525.88 |                2 |          13051.8  |
| B · DUPLICATE BILLING | United Industries PLC    | INV-2024-03163 | 2024-11-14 00:00:00 |  3666.69 |                2 |           7333.38 |
| B · DUPLICATE BILLING | United Industries PLC    | INV-2025-95002 | 2024-11-24 00:00:00 |  3666.69 |                2 |           7333.38 |


## 10 · DATA QUALITY SUITE — TRUST, BUT VERIFY

*Source: `analytics/10_data_quality.sql`*

| check_name                                       | severity   |   violations |
|:-------------------------------------------------|:-----------|-------------:|
| 01 · Shipments with ATA before ATD (time travel) | critical   |            0 |
| 02 · Delivered shipments missing arrival date    | critical   |            0 |
| 03 · Orphan events (no parent shipment)          | critical   |            0 |
| 04 · Orphan invoices (no parent shipment)        | critical   |            0 |
| 05 · Invoices paid before they were issued       | critical   |            0 |
| 06 · Shipments referencing unknown ports         | critical   |            0 |
| 07 · Non-positive volumes or amounts             | critical   |            0 |
| 11 · Chokepoint lanes referencing unknown ports  | critical   |            0 |
| 08 · Currency codes without an FX fixing         | warning    |            0 |
| 09 · Shipments billed more than once (review)    | warning    |            4 |
| 10 · Bookings dated before customer onboarding   | warning    |            0 |


## 11_real_port_activity

*Source: `analytics/11_real_port_activity.sql`*

| port_name   | region   | data_through        |   days_observed |   ctr_calls_per_day |   ctr_calls_yoy_pct |   cargo_kt_per_day |   cargo_yoy_pct |
|:------------|:---------|:--------------------|----------------:|--------------------:|--------------------:|-------------------:|----------------:|
| Alexandria  | MEA      | 2026-07-17 00:00:00 |              90 |                 3.2 |               -14.5 |              178.7 |            18.1 |
| Nhava Sheva | Asia     | 2026-07-17 00:00:00 |              90 |                 7.7 |                17.7 |              477   |            13.6 |
| Gdansk      | Europe   | 2026-07-17 00:00:00 |              90 |                 2.4 |                -6.5 |              239   |             8.9 |
| Hamburg     | Europe   | 2026-07-17 00:00:00 |              90 |                 9.6 |                -1.8 |              367.3 |             5.3 |
| Santos      | Americas | 2026-07-17 00:00:00 |              90 |                 6.4 |                -2.2 |              451.7 |             2.5 |
| Long Beach  | Americas | 2026-07-17 00:00:00 |              90 |                 5.4 |                 0.6 |              566.7 |             0.6 |
| Rotterdam   | Europe   | 2026-07-17 00:00:00 |              90 |                18   |                -3.2 |              950.9 |            -2   |
| Mersin      | MEA      | 2026-07-17 00:00:00 |              90 |                 3.4 |               -11.2 |               82.7 |            -2.1 |
| Singapore   | Asia     | 2026-07-17 00:00:00 |              90 |                39   |                -3.7 |             2328.5 |            -2.8 |
| Busan       | Asia     | 2026-07-17 00:00:00 |              90 |                31.5 |                -3.7 |              408.1 |            -3.1 |
| Felixstowe  | Europe   | 2026-07-17 00:00:00 |              90 |                 2.4 |               -10.5 |               68.6 |            -4.1 |
| New York    | Americas | 2026-07-17 00:00:00 |              90 |                 6   |                -8.8 |              285.3 |            -5.2 |
| Shenzhen    | Asia     | 2026-07-17 00:00:00 |              90 |                 9.5 |                -7.2 |              120.5 |            -8.7 |
| Shanghai    | Asia     | 2026-07-17 00:00:00 |              90 |                33.2 |               -13.3 |             1193.2 |           -23.8 |
| Jebel Ali   | MEA      | 2026-07-17 00:00:00 |              90 |                 1.3 |               -90.3 |               84.7 |           -86.1 |
| Odesa       | Europe   | 2026-07-17 00:00:00 |              90 |                 0   |                 —   |                0   |             —   |


## 12 · NETWORK EXPOSURE TO REAL PORT TRENDS — SYNTHETIC ⋈ REAL

*Source: `analytics/12_network_exposure_real.sql`*

| port_name   | region   |   shipments_180d |   cbm_180d |   share_of_book_pct |   real_calls_yoy_pct | real_world_signal            |
|:------------|:---------|-----------------:|-----------:|--------------------:|---------------------:|:-----------------------------|
| Rotterdam   | Europe   |              794 |     15,123 |                21.9 |                 -3.2 | !  softening                 |
| Shanghai    | Asia     |              657 |     11,923 |                17.3 |                -13.3 | !! declining traffic         |
| Hamburg     | Europe   |              442 |      8,437 |                12.2 |                 -1.8 | stable                       |
| Odesa       | Europe   |              448 |      7,974 |                11.6 |                  —   | baseline too short           |
| Long Beach  | Americas |              245 |      4,462 |                 6.5 |                  0.6 | stable                       |
| Shenzhen    | Asia     |              177 |      3,387 |                 4.9 |                 -7.2 | !  softening                 |
| Nhava Sheva | Asia     |              145 |      2,919 |                 4.2 |                 17.7 | ▲ surging (congestion watch) |
| New York    | Americas |              161 |      2,868 |                 4.2 |                 -8.8 | !  softening                 |
| Felixstowe  | Europe   |              127 |      2,492 |                 3.6 |                -10.5 | !! declining traffic         |
| Busan       | Asia     |               96 |      2,176 |                 3.2 |                 -3.7 | !  softening                 |
| Mersin      | MEA      |              109 |      2,061 |                 3   |                -11.2 | !! declining traffic         |
| Gdansk      | Europe   |               80 |      1,521 |                 2.2 |                 -6.5 | !  softening                 |
| Alexandria  | MEA      |               80 |      1,521 |                 2.2 |                -14.5 | !! declining traffic         |
| Singapore   | Asia     |               66 |      1,264 |                 1.8 |                 -3.7 | !  softening                 |
| Jebel Ali   | MEA      |               45 |        832 |                 1.2 |                -90.3 | !! declining traffic         |


## 13 · CHOKEPOINT EXPOSURE — HOW MUCH OF OUR BOOK SAILS THROUGH EACH STRAIT?

*Source: `analytics/13_chokepoint_exposure.sql`*

| chokepoint           |   lanes |   shipments_180d |   cbm_180d |   share_of_book_pct |   transits_per_day |   transits_yoy_pct | real_world_signal                      |
|:---------------------|--------:|-----------------:|-----------:|--------------------:|-------------------:|-------------------:|:---------------------------------------|
| Dover Strait         |       9 |             1287 |     24,585 |                71.3 |               35.2 |               -5.7 | stable                                 |
| Gibraltar Strait     |       8 |             1126 |     21,717 |                63   |               31.4 |               -6.1 | stable                                 |
| Suez Canal           |       7 |              941 |     18,038 |                52.3 |                8.4 |               -6.5 | stable                                 |
| Bab el-Mandeb Strait |       7 |              941 |     18,038 |                52.3 |                5.5 |              -16.6 | !  transits falling                    |
| Malacca Strait       |       5 |              751 |     14,288 |                41.4 |               60.2 |               -3.6 | stable                                 |
| Bosporus Strait      |       3 |              292 |      4,985 |                14.5 |               10.2 |                0.9 | stable                                 |
| Oresund Strait       |       2 |              236 |      4,510 |                13.1 |                5.3 |               -5.9 | stable                                 |
| Strait of Hormuz     |       2 |              190 |      3,750 |                10.9 |                1.4 |              -93.3 | !! transits collapsing — re-route risk |


## 13_door_to_door_routing

*Source: `door_to_door/13_door_to_door_routing.sql`*

| request         |   rank | route                                   | gateway   | inland_mode   |   total_days |   usd_per_cbm |   real_data_buffer_d |   score |
|:----------------|-------:|:----------------------------------------|:----------|:--------------|-------------:|--------------:|---------------------:|--------:|
| CNSHA → Kyiv    |      1 | CNSHA → EGALY → UAODS ⇒ Kyiv            | UAODS     | truck         |           28 |         115.9 |                    0 |   157.9 |
| CNSHA → Kyiv    |      2 | CNSHA → EGALY → TRMER → UAODS ⇒ Kyiv    | UAODS     | truck         |           31 |         124.3 |                    0 |   170.8 |
| CNSHA → Kyiv    |      3 | CNSHA → SGSIN → EGALY → UAODS ⇒ Kyiv    | UAODS     | truck         |           32 |         129.6 |                    0 |   177.6 |
| CNSHA → Poltava |      1 | CNSHA → EGALY → UAODS ⇒ Poltava         | UAODS     | truck         |           28 |         120.9 |                    0 |   162.9 |
| CNSHA → Poltava |      2 | CNSHA → EGALY → TRMER → UAODS ⇒ Poltava | UAODS     | truck         |           31 |         129.3 |                    0 |   175.8 |
| CNSHA → Poltava |      3 | CNSHA → SGSIN → EGALY → UAODS ⇒ Poltava | UAODS     | truck         |           32 |         134.6 |                    0 |   182.6 |
| CNSZX → Poltava |      1 | CNSZX → SGSIN → EGALY → UAODS ⇒ Poltava | UAODS     | truck         |           30 |         129.3 |                    0 |   174.3 |
| CNSZX → Poltava |      2 | CNSZX → CNSHA → EGALY → UAODS ⇒ Poltava | UAODS     | truck         |           33 |         128.9 |                    0 |   178.4 |
| CNSZX → Poltava |      3 | CNSZX → SGSIN → DEHAM → PLGDN ⇒ Poltava | PLGDN     | rail          |           38 |         127.3 |                    1 |   184.3 |


## 14 · DOOR-TO-DOOR ROUTING — MULTIMODAL PATHFINDING (OPTIONAL EXTENSION)

*Source: `door_to_door/14_door_to_door_routing.sql`*

| request         |   rank | route                                   | gateway   | inland_mode   |   total_days |   usd_per_cbm |   real_data_buffer_d |   score |
|:----------------|-------:|:----------------------------------------|:----------|:--------------|-------------:|--------------:|---------------------:|--------:|
| CNSHA → Kyiv    |      1 | CNSHA → EGALY → UAODS ⇒ Kyiv            | UAODS     | truck         |           28 |         115.9 |                    0 |   157.9 |
| CNSHA → Kyiv    |      2 | CNSHA → EGALY → TRMER → UAODS ⇒ Kyiv    | UAODS     | truck         |           31 |         124.3 |                    0 |   170.8 |
| CNSHA → Kyiv    |      3 | CNSHA → SGSIN → EGALY → UAODS ⇒ Kyiv    | UAODS     | truck         |           32 |         129.6 |                    0 |   177.6 |
| CNSHA → Poltava |      1 | CNSHA → EGALY → UAODS ⇒ Poltava         | UAODS     | truck         |           28 |         120.9 |                    0 |   162.9 |
| CNSHA → Poltava |      2 | CNSHA → EGALY → TRMER → UAODS ⇒ Poltava | UAODS     | truck         |           31 |         129.3 |                    0 |   175.8 |
| CNSHA → Poltava |      3 | CNSHA → SGSIN → EGALY → UAODS ⇒ Poltava | UAODS     | truck         |           32 |         134.6 |                    0 |   182.6 |
| CNSZX → Poltava |      1 | CNSZX → SGSIN → EGALY → UAODS ⇒ Poltava | UAODS     | truck         |           30 |         129.3 |                    0 |   174.3 |
| CNSZX → Poltava |      2 | CNSZX → CNSHA → EGALY → UAODS ⇒ Poltava | UAODS     | truck         |           33 |         128.9 |                    0 |   178.4 |
| CNSZX → Poltava |      3 | CNSZX → SGSIN → DEHAM → PLGDN ⇒ Poltava | PLGDN     | rail          |           38 |         127.3 |                    1 |   184.3 |
