# Excel 시트별 템플릿

`seq_operator_questionnaire`와 `seq_operator_questionnaire_tag`를 바탕으로 DAG 자동 생성용 입력을 사람이 보정할 수 있도록 만든 중간 Excel 템플릿이다.

## 사용 목적

- 자동 추론된 값을 사람이 최종 확정한다.
- 모호한 운영 문구를 실행 가능한 규칙으로 바꾼다.
- DAG generator가 읽을 표준 입력을 만든다.

## 시트 구성

- `DAG_Mapping`
- `Sensor_Notify`
- `Validation_Policy`
- `Review_Log`

## 1. `DAG_Mapping`

| 컬럼 | 설명 | 입력 주체 | 예시 | 비고 |
|---|---|---|---|---|
| `seq_name` | DAG 기준 식별자 | 자동 | `SEQ_PRODUCT_MASTER` | 유일키 기준 |
| `business_name` | 업무명 | 자동 | `상품 기준정보 갱신` | 표시명 생성에 사용 |
| `dag_id` | 최종 DAG ID | 자동/조정 | `seq_product_master` | 정규화 필요 |
| `dag_name` | 표시 이름 | 자동 | `SEQ_PRODUCT_MASTER - 상품 기준정보 갱신` | UI 표기용 |
| `schedule_type` | 스케줄 유형 | 자동+사람 | `daily` | `manual`, `event` 가능 |
| `schedule_interval` | cron 또는 preset | 사람 | `0 1 * * *` | 승인 필요 |
| `priority` | 우선순위 | 자동+사람 | `high` | 운영 중요도 반영 |
| `dbt_group` | dbt 그룹명 | 자동+사람 | `product_master` | 업무별 그룹화 |
| `dbt_selector` | dbt selector | 자동+사람 | `tag:product_master` | `dbt build` 입력용 |
| `model_mapping` | 업무-모델 매핑 | 사람 | `stg -> int -> fct` | 최종 edge에 영향 |

## 2. `Sensor_Notify`

| 컬럼 | 설명 | 입력 주체 | 예시 | 비고 |
|---|---|---|---|---|
| `seq_name` | DAG 기준 식별자 | 자동 | `SEQ_PRODUCT_MASTER` | 상위 키 |
| `start_mode` | 시작 방식 | 자동+사람 | `file_sensor` | `manual`, `time_based` 가능 |
| `sensor_type` | 사용할 Sensor | 사람 | `FileSensor` | 구현체 확정 |
| `sensor_target` | 대기 대상 | 사람 | `/inbound/*.dat` | 파일/이벤트 경로 |
| `external_dependency` | 외부 의존성 | 자동+사람 | `상품관리 시스템` | 대기 판단 근거 |
| `notify_on_success` | 성공 알림 여부 | 사람 | `Y` | 정책 필요 |
| `notify_on_failure` | 실패 알림 여부 | 사람 | `Y` | 정책 필요 |
| `notify_channel` | 알림 채널 | 사람 | `Slack` | Email/Callback 가능 |
| `notify_recipients` | 수신자 | 사람 | `data-ops` | 배포 대상 |
| `failure_policy` | 실패 시 처리 | 자동+사람 | `stop` | `continue`, `manual_review` 가능 |

## 3. `Validation_Policy`

| 컬럼 | 설명 | 입력 주체 | 예시 | 비고 |
|---|---|---|---|---|
| `seq_name` | DAG 기준 식별자 | 자동 | `SEQ_PRODUCT_MASTER` | 상위 키 |
| `validation_mode` | 검증 방식 | 자동+사람 | `dbt_test` | `count`, `sample` 가능 |
| `validation_timing` | 검증 시점 | 사람 | `after_dbt` | 실행 순서에 영향 |
| `comparison_reference` | 비교 기준 | 자동+사람 | `existing_dw` | 원천/기존DW/보고서 |
| `retry_policy` | 재시도 정책 | 자동+사람 | `3 times / 5 min` | task/group 기준 선택 |
| `exception_rule` | 예외 실행 규칙 | 사람 | `월말만 추가 실행` | 운영 정책 |
| `verification_comment` | 검증 설명 | 사람 | `건수와 샘플 확인` | 자유서술 |
| `review_status` | 검토 상태 | 사람 | `needs_review` | 승인 흐름 |

## 4. `Review_Log`

| 컬럼 | 설명 | 입력 주체 | 예시 | 비고 |
|---|---|---|---|---|
| `seq_name` | DAG 기준 식별자 | 자동 | `SEQ_PRODUCT_MASTER` | 추적용 |
| `review_status` | 검토 상태 | 사람 | `approved` | 승인/반려 |
| `review_comment` | 판단 근거 | 사람 | `파일 대기 필요함` | 변경 사유 기록 |
| `owner` | 검토자 | 사람 | `data-ops` | 책임자 |
| `reviewed_at` | 검토 시각 | 자동/사람 | `2026-09-05 14:30:00` | 감사용 |

## 자동 채움 / 수동 입력 기준

### 자동 채움

- `seq_name`
- `business_name`
- `tag 기반 분류`
- `초안 policy`
- `priority` 초안
- `dbt_group` 초안

### 수동 입력

- `sensor_type`
- `sensor_target`
- `model_mapping`
- `notify_recipients`
- `exception_rule`
- `schedule_interval`

### 사람 승인 필요

- `schedule_interval`
- `final edge`
- `운영 예외`
- `검증 기준`

## 권장 작성 순서

1. `DAG_Mapping`에 기본 식별과 DAG 성격을 채운다.
2. `Sensor_Notify`에 시작/알림 정책을 적는다.
3. `Validation_Policy`에 검증/재시도 기준을 정한다.
4. `Review_Log`로 승인 여부와 근거를 남긴다.

## 생성 파이프라인과의 관계

```text
seq_operator_questionnaire
  -> seq_operator_questionnaire_tag
  -> Excel 시트별 템플릿
  -> DAG generator
  -> Airflow / dbt 산출물
```

## 실제 `.xlsx` 생성 방향

이 템플릿은 `openpyxl`을 사용해 실제 `.xlsx` 파일로 생성하는 방식이 가장 잘 맞는다.

### 권장 구조

- 1개 workbook
- 4개 sheet 생성
- 각 sheet의 1행은 헤더로 고정
- 컬럼 폭 자동 조정
- 입력 주체별 색상 구분
- `자동 채움 / 수동 입력 / 사람 승인 필요`를 색상 또는 드롭다운으로 표시

### 생성 흐름

```text
Excel시트별템플릿.md
  -> 템플릿 정의 읽기
  -> workbook 생성
  -> sheet별 헤더/샘플행 작성
  -> 서식 적용
  -> .xlsx 저장
```

### 구현 선택지

| 방식 | 장점 | 단점 |
|---|---|---|
| `openpyxl` | 시트, 서식, 드롭다운, 검증까지 유연 | 코드가 조금 길어짐 |
| `xlsxwriter` | 작성 성능이 좋음 | 읽기/수정에는 불리 |
| CSV 여러 개 | 단순함 | 시트 구조와 서식 표현이 약함 |

### 추천

- 현재 템플릿 구조에는 `openpyxl`이 가장 잘 맞는다.
- 이유는 시트가 여러 개이고, 나중에 드롭다운/색상/검증 규칙을 붙일 가능성이 크기 때문이다.

### 실무적으로 넣으면 좋은 요소

- `freeze panes`
- 헤더 필터
- 입력 칸 색상 분리
- `review_status` 드롭다운
- `schedule_type`, `start_mode`, `notify_channel` 같은 선택형 드롭다운
- 예시 행 1줄

### 개별 파일 출력

`generate_dag_excel.py`는 다음 두 가지 방식으로 출력할 수 있다.

- 단일 워크북: 모든 질문지를 하나의 `.xlsx`에 합친다.
- 개별 워크북: `--split-by-seq` 옵션으로 `seq_name`별 `.xlsx` 파일을 따로 생성한다.

개별 파일 출력은 다음과 같은 상황에 유용하다.

- 질문지별 검토를 독립적으로 수행하고 싶을 때
- 업무별 전달/승인이 분리되어 있을 때
- 대량 생성 시 파일 단위 관리가 필요할 때

예:

```bash
python generate_dag_excel.py --split-by-seq --output-dir dag_split_out --overwrite
```
