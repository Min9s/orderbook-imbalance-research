# Full BBO inventory — before external outcomes

682,024 observed BBO rows, 3,173 Parquet files, **28 session IDs across only2 UTC dates**. One session spans midnight, so per-date session appearances sum to29. These are not28 independent trading days. All682,024 rows contain finite positive bid/ask prices and sizes and no crossed quotes. Clock/admission quality is materially worse than numeric quote completeness.

| UTC date | Raw BBO | Session appearances | Clock states | Valid states |
|---|---:|---:|---:|---:|
| 2026-10-07 | 447,443 | 12 | 65,335 | 55,164 |
| 2026-10-08 | 234,581 | 17 | 29,085 | 27,406 |

Across all sessions: 67,059 negative exchange→receive differences, 6,036 differences>2s,5 adjacent exchange-timestamp reversals,221 receive gaps>2s. No duplicate event IDs, duplicate receipt timestamps, exchange timestamp field mismatches, or overlapping session time ranges were found. Negative clock differences do not imply true negative network latency. Primary rules invalidate such observations; they are not repaired by shifting timestamps.

Wall span is last minus first receipt. Valid-grid seconds count usable one-second observation states; they are not a guarantee of continuously observed exchange activity. A long quiet BBO interval is not automatically packet loss. No inter-session interpolation is used. Row-level valid quantities do not make clock-invalid rows eligible. The full-session grid contains94,420 states, of which82,570 satisfy the existing rules. Reserved/pilot exclusions reduce the external study further.

## Every session

| Session | Start UTC | End UTC | Wall min | BBO | Valid grid / total | Negative lag | Lag>2s | Gap>2s | Role |
|---|---|---|---:|---:|---|---:|---:|---:|---|
| `f1d0c0b3bd1f4c7b844074508477be4c` | 2026-10-07T05:14:56.346948+00:00 | 2026-10-07T05:15:40.684687+00:00 | 0.74 | 325 | 44/44 | 0 | 0 | 0 | robustness |
| `e29a1088ea904b0f83335013adb7c384` | 2026-10-07T05:17:17.181025+00:00 | 2026-10-07T07:44:11.358403+00:00 | 146.90 | 55,310 | 8,806/8,814 | 0 | 0 | 19 | pilot_session_excluded |
| `61ad52b42c094b1dafbc9fc5c1e29102` | 2026-10-07T07:46:01.791937+00:00 | 2026-10-07T07:47:23.757069+00:00 | 1.37 | 711 | 30/82 | 0 | 441 | 1 | robustness |
| `a0460445c46d4fa0885ef42cfc842006` | 2026-10-07T07:48:01.232045+00:00 | 2026-10-07T07:48:19.259039+00:00 | 0.30 | 122 | 18/18 | 0 | 0 | 0 | robustness |
| `e092d868777d4b77bbb9aaa9838bce63` | 2026-10-07T07:49:52.280443+00:00 | 2026-10-07T07:49:59.065756+00:00 | 0.11 | 63 | 7/7 | 0 | 0 | 0 | robustness |
| `6d21d8afdf8b4d5290ba079778895b88` | 2026-10-07T08:18:56.176787+00:00 | 2026-10-07T08:21:19.083367+00:00 | 2.38 | 1,254 | 143/143 | 0 | 0 | 0 | robustness |
| `bf0a38528fe54bd9953042336d082753` | 2026-10-07T08:22:37.252054+00:00 | 2026-10-07T11:22:53.983432+00:00 | 180.28 | 80,587 | 10,801/10,816 | 0 | 120 | 8 | robustness |
| `e25bf6d83b7045eb84fba4f1876b8e89` | 2026-10-07T11:22:56.824937+00:00 | 2026-10-07T14:19:57.131379+00:00 | 177.01 | 90,157 | 10,621/10,621 | 0 | 0 | 1 | robustness |
| `1f8bc06730564ab0ab8ae4e5ba6daa51` | 2026-10-07T14:19:59.721195+00:00 | 2026-10-07T17:21:16.555003+00:00 | 181.28 | 88,121 | 10,875/10,877 | 0 | 3 | 4 | robustness |
| `fa8185efa43e4b6daae26552be8930c0` | 2026-10-07T17:21:20.064938+00:00 | 2026-10-07T20:14:30.432279+00:00 | 173.17 | 66,386 | 1,609/10,390 | 54,235 | 0 | 27 | robustness |
| `8d46cf66bef94c26bdd9a6b666e00394` | 2026-10-07T20:14:33.642417+00:00 | 2026-10-07T23:05:01.917702+00:00 | 170.47 | 48,403 | 8,936/10,228 | 6,291 | 0 | 92 | robustness |
| `00a32f7bcd4e421a8540d5cbd0fdabe7` | 2026-10-07T23:05:04.857899+00:00 | 2026-10-08T01:56:11.556643+00:00 | 171.11 | 60,896 | 10,239/10,267 | 0 | 0 | 57 | robustness |
| `95a74716c1c140eb8e896cb11f924151` | 2026-10-08T01:56:14.396905+00:00 | 2026-10-08T02:39:50.017688+00:00 | 43.59 | 16,945 | 2,614/2,616 | 0 | 0 | 4 | first_external |
| `f84a23a19e4640afaea55db02b298d96` | 2026-10-08T03:09:36.948737+00:00 | 2026-10-08T04:01:46.838107+00:00 | 52.16 | 23,789 | 3,129/3,130 | 0 | 7 | 4 | robustness |
| `f6411dec62e64c7bbafad54f92756460` | 2026-10-08T04:31:49.114820+00:00 | 2026-10-08T04:48:40.593951+00:00 | 16.86 | 9,633 | 1,011/1,011 | 0 | 0 | 0 | robustness |
| `c666f085288a4b6d97852a41605383c5` | 2026-10-08T05:05:14.365398+00:00 | 2026-10-08T05:05:19.105922+00:00 | 0.08 | 47 | 5/5 | 0 | 0 | 0 | robustness |
| `3f2232407e7e4c629486bd1f1142d562` | 2026-10-08T06:10:27.086373+00:00 | 2026-10-08T06:10:27.917736+00:00 | 0.01 | 15 | 0/0 | 0 | 0 | 0 | robustness |
| `30c11f8b470f4025ab29efa373c45090` | 2026-10-08T06:21:23.332820+00:00 | 2026-10-08T06:56:38.956689+00:00 | 35.26 | 15,062 | 2,115/2,115 | 0 | 0 | 0 | robustness |
| `d71a6296b750428c928b1db3ff980339` | 2026-10-08T06:59:10.877230+00:00 | 2026-10-08T06:59:16.798094+00:00 | 0.10 | 31 | 6/6 | 0 | 0 | 0 | robustness |
| `132178fdc51c4501b24acea81871fa5a` | 2026-10-08T08:21:02.963447+00:00 | 2026-10-08T08:21:06.855930+00:00 | 0.06 | 36 | 4/4 | 0 | 0 | 0 | robustness |
| `d5e4f076679b46be98947996d5397589` | 2026-10-08T10:00:12.704734+00:00 | 2026-10-08T11:29:43.471473+00:00 | 89.51 | 40,931 | 4,254/5,371 | 6,327 | 198 | 1 | robustness |
| `aba1fc356d75465088617f88c5016c89` | 2026-10-08T11:32:24.054468+00:00 | 2026-10-08T11:32:54.661077+00:00 | 0.51 | 271 | 14/30 | 97 | 0 | 0 | robustness |
| `bf87b53c4aab4739aae7c6a2db1a5860` | 2026-10-08T11:33:56.163768+00:00 | 2026-10-08T11:36:37.919870+00:00 | 2.70 | 1,358 | 31/161 | 109 | 995 | 1 | robustness |
| `1b1961b8bc54492a962972f0d38adc35` | 2026-10-08T14:08:12.584853+00:00 | 2026-10-08T14:08:40.141314+00:00 | 0.46 | 274 | 28/28 | 0 | 0 | 0 | robustness |
| `de574dbd54dc4bc9bed8d45e02779b19` | 2026-10-08T14:27:22.488327+00:00 | 2026-10-08T14:33:26.079910+00:00 | 6.06 | 3,506 | 117/364 | 0 | 2,431 | 2 | robustness |
| `f2e394cfb3cc4baba411ada736c6e338` | 2026-10-08T14:49:48.943382+00:00 | 2026-10-08T14:50:31.951977+00:00 | 0.72 | 373 | 43/43 | 0 | 0 | 0 | robustness |
| `0f972725979643149fcacf1c203cedb4` | 2026-10-08T15:08:41.824800+00:00 | 2026-10-08T15:09:10.019754+00:00 | 0.47 | 275 | 29/29 | 0 | 0 | 0 | robustness |
| `df37f36553464010ae9c34cd83d0eeac` | 2026-10-08T15:15:56.594595+00:00 | 2026-10-08T17:15:56.455088+00:00 | 120.00 | 77,143 | 7,041/7,200 | 0 | 1,841 | 0 | reserved_final |

Only15,295 rows temporally overlap the previously analyzed pilot interval, all in its original session. That full session has55,310 rows and spans146.9 minutes; the additional same-session data are not an independent validation. The reserved final has77,143 rows. The external evaluation pool therefore has549,571 raw rows in26 sessions; eligible forward labels and directional counts will be reported separately after the freeze.

Detailed exchange/receive quantiles, quote completeness, invalid ratios, timestamp checks and role decisions are available in [inventory.json](../results/oos/inventory.json), [session_inventory.csv](../results/oos/session_inventory.csv) and [date_inventory.csv](../results/oos/date_inventory.csv). All raw files stay outside this repository.

## Temporal-role review after registered evaluation

The role column above is the preserved pre-evaluation assignment. The first
44-second session was subsequently recognized as preceding the training period.
It remains a disclosed retrospective diagnostic, not a chronological validation.
[Protocol addendum](EXTERNAL_PROTOCOL_ADDENDUM.md) records this correction without
changing the inventory fingerprint or original registered results. Final forward-only
results use25 sessions /549,246 raw BBO /66,679 valid grid states. The primary
next-day session and the latest reserved session roles are unchanged.

Receive timestamps are stored wall-clock observations. Ordering by receive time
and finding no duplicates does not prove a clock-step-free physical arrival
sequence; arbitrary Parquet filenames are not a global event order. Independent
monotonic-clock/UTC evidence is not present in these historical BBO rows, so clock
jumps and true network delay cannot be fully separated. This limitation is not
removed by the valid-grid filter.
