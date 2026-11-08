# 기존 자산 감사 — 2026-11-08

실제 `the local Projects directory`의 두 프로젝트를 읽기 전용으로 조사했다. 이 디렉터리에는 이 둘 외에 다른 프로젝트 폴더가 없었다. 원본 코드와 데이터는 변경하지 않았다. 아래 경로는 각각 실제 프로젝트 루트 기준이다. 원본 전체 저장소를 새 연구에 의존시키지 않는다.

## A. 재사용 코드·수정 범위

| 기능 | 실제 파일·함수/클래스 | 재사용 범위와 필요한 수정 | 자료 의미 |
|---|---|---|---|
| 거래소 연결·수집 | `Liquidation_gravity/src/liquidation_microstructure/api/hyperliquid.py`: `subscriptions`, `open_market_socket`, `subscribe`; `collectors/market.py`: `MarketRecorder`, `RecorderOptions` | 기존 mainnet 수집 기록을 사용. 새 수집 인프라 불필요. 후속 수집 시 단일 BTC/bbo 구독만 선택 | 공개 호가·체결 채널을 구분하는 실제 API 코드. socket 주입 테스트는 합성 가능 |
| CEX 연결 | 같은 루트 `api/cex.py`: `UniverseClient`; `collectors/cex.py`: `plans`, `frame_identity`, `CexRecorder` | Binance bookTicker/depth20, Bybit orderbook.50 지원. 동적 다자산 수집기는 이번 MVP에 과대 | native_frames에는 호가·체결·mark·청산이 섞여 있으므로 채널 필터 필수 |
| Bid/Ask 가격·수량 | `collectors/orderbook.py`: `_level`, `parse_bbo` | `bid_px/ask_px/bid_sz/ask_sz`, 원문·세션·양쪽 시각 스키마 재사용. 이미 정규화되어 파서 추출 불필요 | 실제 표시 호가 잔량. 청산 포지션이나 거래량 아님 |
| L2 snapshot·delta | `collectors/orderbook.py`: `parse_l2`; `research/cex_inputs.py`: `BookState.update`, `BookState.sample` | Hyperliquid 전체 L2 snapshot; CEX Binance 부분깊이 snapshot / Bybit snapshot+delta 복원. 이번에는 BBO만 사용하므로 제외. 향후 세션 reset, 역순·중복·baseline 검증 유지 필요 | 호가 레벨. 개별 주문/queue 정보 아님 |
| Mid·Spread·Depth·OBI | `microstructure/orderbook.py`: `book_features`; `market-microstructure-toolkit/src/market_microstructure/orderbook.py`: `bid_ask_spread`, `order_book_imbalance`, `notional_depth` | **LG 원본 함수 한 파일을 `src/obi_research/legacy_book.py`로 그대로 추출**, OBI/spread_bps/log_depth 직접 호출. wrapper에서 양쪽 수량 >0 강화, mid·relative spread·microprice 추가. Toolkit은 비교·계약 참고만 | log_depth는 최우선 양쪽 표시 명목잔량의 log1p이며 전체 시장 유동성 아님 |
| Timestamp·as-of·resampling | LG `research/inputs.py`: `Timeline.at`, `Timeline.between`, `_read`; `research/cex_inputs.py`: `derive_contract`; Toolkit `asof.py`: `select_asof` | 수신 시각 이전 최신 상태와 정수 ns 방식 재사용. 계정/선정 registry 의존은 제외하고 작은 BBO 전용 1초 격자 구현. 이전 정상값 fallback 금지 | 거래소 시각과 로컬 가용 시각을 구분 |
| 시계열 특징·지표 | LG `microstructure/volatility.py`: `price_features`; `microstructure/order_flow.py`: `trade_imbalance`; `models/baseline.py`: `fit_logistic`, `matrix`, `prior_probabilities` | 기존 training-only scaler/단순 logistic 패턴 참조. 청산용 특징·거래량·다중모델 프레임워크 미추출 | trade imbalance는 체결 방향의 불균형이며 OBI와 다름 |
| 저장·파이프라인 | LG `storage/parquet.py`: `ParquetWriter.write`; `research/inputs.py`: `capture_manifest`, `_read`; `research/cex_inputs.py`: `file_record`, `verified`, `build_dataset`; Toolkit `historical_io.py` | Arrow 정수 ns와 SHA-256 전후 검증 방식 적용. 새 writer framework 대신 로컬 결과 파일만 저장. 기존 replay schema는 계정·청산 연구 의존성이 커 제외 | raw/processed/diagnostics를 구분. processed 합성 산출물은 실증 입력 아님 |
| 통계·시각화 | LG `models/evaluation.py`: `expanding_splits`, `block_interval`, `classification_metrics`; Toolkit `event_study_io.py`: `render_report`, `run_study` | purging·고정 시간 block bootstrap 아이디어 참조. LG 3분류 손실/청산 gate, Toolkit 장벽/HTML 보고는 부적합. 2분류 평가와 Matplotlib 4개 그림만 신규 | 합성 예제 수치를 실증 결과로 옮기지 않음 |

청산 관련 `liquidation/gravity.py`, Toolkit `gravity.py`의 imbalance는 청산 노출 불균형이다. 실제 bid/ask 수량의 OBI로 대체할 수 없다. Toolkit `simulated_venue.py`, `synthetic_fix.py`, 실행 예제와 테스트 입력은 명시적으로 합성이며 전부 제외했다. Toolkit에 실제 데이터를 수용할 코드가 있다는 사실은 실제 입력이 배포되었다는 뜻이 아니다.

## B. 실제 사용 가능 데이터

| 실제 경로 | 확인한 내용 | 연구 사용 판단 |
|---|---|---|
| `Liquidation_gravity/data/raw/hyperliquid/bbo/BTC/2026-10-07/05/*.parquet` | 95파일·15,620행. 실제 양쪽 가격/수량·order count·exchange ms·수신 ns·원문 JSON·event hash·session | **선택 입력**. 단일 BTC perpetual, 최우선 호가. USDT 계약으로 명명하지 않음 |
| `data/raw/hyperliquid/bbo/BTC/{2026-10-07,2026-10-08}/…` | BTC BBO 파일 총 3,173개를 발견. 전체 범위 품질은 이번에 검증하지 않음 | 확장 가능 후보이며 여러 날 독립 검증을 완료했다고 주장하지 않음 |
| `data/raw/hyperliquid/l2_snapshots/BTC/…`, `data/raw/hyperliquid/l2/BTC/…` | header 3,171파일 발견. 표본 원문에 bid/ask 각각20레벨과 px/sz/n 존재 | 실제 L2 후보. header-child 결합·연속성 추가 검증 후 사용 가능. MVP에서 미사용 |
| `data/cex/raw/binance/native_frames/BTC/{2026-10-08,2026-10-09,2026-10-10}/…` | 23,008파일 발견. 표본 BTCUSDT bookTicker에 b/B/a/A 및 T/E/u 존재 | 실제 CEX 후보. 전체 검증은 미실시. 단일 소스 원칙상 미사용 |
| `data/raw/hyperliquid/trades`, `liquidation_ws_messages`, `wallet_position_snapshots` | 별도 체결·청산 메시지·참가자 포지션 계층 | BBO 대체 불가; 이번 연구 미사용 |
| `data/processed/live_raw_finite/20261018_verified_synthetic/…`, Toolkit examples/tests | synthetic/test 계층 또는 생성 입력 | 실증 자료로 제외 |

원문과 연결된 수집 기록:
`data/interim/market_recorder/d7830102b0a24e6c9d27bc2ec21d8910/{status.json,events.jsonl}`.
status에 source=hyperliquid, `wss://api.hyperliquid.xyz/ws`, raw_root와 accepted/written bbo가 있다. events의 session 연결 시각은 05:17:16.799531 UTC. 선택 행은 05:17:17.181025–05:59:59.788403 UTC에 수신되었다. 같은 세션의 07:45 후속 장애 로그는 분석 구간 밖이다. 원문과 정규화 필드 및 event SHA-256은 모든 선택 행에서 대조했다. 이 로컬 계보는 독립적인 거래소 서명이나 호스트 UTC 정확성 인증은 아니다.

최초 세션은 44초뿐이라 모델 분할에 부족했다. 수익률 확인 전 첫 시간대의 가장 긴 세션을 선택했다. 이 선택은 별도 날짜 OOS를 대체하지 않는다.

## C. 최소 신규 구현

`features.py`: BBO 검증·Microprice·receipt-causal 1초 표본·gap 검열·미래 로그수익률·purging.
`statistics.py`: binary metrics와 paired fixed-time block bootstrap.
`research/run.py`: manifest, 고정 60/20/20 실험, logistic 두 개, 결과 CSV/JSON·4개 PNG.
기존 LG 특성 함수 외에는 좁은 목적의 신규 구현이며, 계보와 방법을 참조한 코드를 원문 복사라고 표시하지 않는다.

## D. 최소 프로젝트 및 진행 판단

실제 L1 잔량과 42분 단일 세션이 있어 **실증 파일럿은 가능**하다. 실거래 수익성·여러 시장 상태 일반화 연구를 완료하기에는 부족하다. 새 수집은 하지 않았다. L2 복원·OMS·대시보드·신경망은 만들지 않는다.

후속 최소 확보 방법은 동일 거래소의 BTC `bbo` 공개 WebSocket을 기존 수집기로 별도 날짜에 짧게 저장하는 것이다. REST 현재 snapshot 반복 수집은 이 이벤트 스트림과 샘플링이 다르며 과거 시계열을 복구하지 못한다. 여러 날의 독립 세션을 확보한 뒤 분석 설계를 고정해 다시 평가한다.

공식 API는 bbo에 coin/time/bbo 가격·수량 구조를 제공한다: [Subscriptions](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions). 확인일 2026-11-08. 공개 API 접근과 데이터 재배포 권한은 별개다. 원시 자료의 재배포 허가를 확인한 것은 아니므로 원문 데이터는 새 저장소에 복사하지 않았다. 로컬 파생 parquet와 절대 경로 manifest는 .gitignore 대상이다. 공개 예제나 무관한 LOB 공급자 탐색은 이미 충분한 로컬 입력이 있어 불필요했다.
