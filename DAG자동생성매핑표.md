# DAG 자동 생성 매핑표

`dag_generation_input.xlsx`의 컬럼을 읽어 DAG Python 코드를 자동 생성할 때의 매핑 규칙을 정리한 문서다.

## 1. `DAG_Mapping`

| Excel 컬럼 | 생성 대상 | 규칙 |
|---|---|---|
| `seq_name` | `dag_id`, `group_id`, 파일명 | 필수. `seq_` 제거 후 snake_case 정규화 |
| `business_name` | `dag_display_name`, `description` | DAG 표시명과 설명에 포함 |
| `dag_id` | `dag_id` | 있으면 우선 사용, 없으면 `seq_name`에서 생성 |
| `dag_name` | `dag_display_name` | 그대로 사용 |
| `schedule_type` | `schedule` | `daily/weekly/monthly/manual/event`로 분기 |
| `schedule_interval` | `schedule` | 값이 있으면 그대로 사용, 비면 `schedule_type` 기반 기본 cron 사용 |
| `priority` | `priority_weight`, `pool` | `high/medium/low`로 매핑 |
| `dbt_group` | `DbtTaskGroup.group_id` | dbt task group 이름으로 사용 |
| `dbt_selector` | `RenderConfig(select=...)` | `dbt build --select` 또는 Cosmos `select`에 사용 |
| `model_mapping` | `TaskGroup` / 주석 / TODO | 있으면 task edge 세분화, 없으면 dbt graph에 위임 |

## 2. `Sensor_Notify`

| Excel 컬럼 | 생성 대상 | 규칙 |
|---|---|---|
| `seq_name` | 연결 키 | DAG 식별자와 일치해야 함 |
| `start_mode` | 시작 task 흐름 | `file_sensor/manual/dependency_sensor/time_based/event` 분기 |
| `sensor_type` | `Sensor` 클래스 | `FileSensor`, `ExternalTaskSensor`, `CustomSensor` 등으로 매핑 |
| `sensor_target` | sensor 인자 | 파일 경로, 외부 DAG/Task, 이벤트 대상값으로 사용 |
| `external_dependency` | sensor 설명 / 주석 | 대기 사유, 센서 조건 설명에 사용 |
| `notify_on_success` | success callback/task | `Y`면 성공 알림 생성 |
| `notify_on_failure` | failure callback/task | `Y`면 실패 알림 생성 |
| `notify_channel` | 알림 구현 | `Slack/Email/Callback/Teams`로 분기 |
| `notify_recipients` | 알림 대상 | 채널별 수신자 문자열로 사용 |
| `failure_policy` | retry / trigger_rule / branch | `stop/continue/manual_review`로 처리 |

## 3. `Validation_Policy`

| Excel 컬럼 | 생성 대상 | 규칙 |
|---|---|---|
| `seq_name` | 연결 키 | DAG 식별자와 일치 |
| `validation_mode` | 검증 task | `count/sample/report/file/dbt_test/manual`로 분기 |
| `validation_timing` | 검증 위치 | `dbt 후`, `전달 전`, `마감 직후` 등으로 task 배치 |
| `comparison_reference` | validation 로직 | 비교 기준 문자열 또는 태그로 반영 |
| `retry_policy` | retry 설정 | `retries`, `retry_delay` 또는 validation 재시도 정책 |
| `exception_rule` | 브랜치 / 주석 / TODO | 예외 실행 규칙으로 문서화 또는 branch 조건화 |
| `verification_comment` | 검증 task 설명 | validation task docstring / 주석 / TODO에 사용 |
| `review_status` | 생성 차단 여부 | `approved` 아니면 scaffold만 만들고 TODO 남김 |

## 4. `Review_Log`

| Excel 컬럼 | 생성 대상 | 규칙 |
|---|---|---|
| `seq_name` | 연결 키 | DAG 식별자와 일치 |
| `review_status` | 생성 허용 여부 | `approved`일 때만 본 생성, 아니면 초안만 |
| `review_comment` | 주석 / TODO | 코드 주석 또는 별도 review note 생성 |
| `owner` | `default_args.owner` | DAG owner 반영 |
| `reviewed_at` | 메타데이터 | 생성 시각 / 검토 시각 기록 |

## 생성 우선순위

1. `review_status != approved`면 최종 DAG가 아니라 초안 생성
2. `dag_id`, `seq_name`, `business_name`은 필수
3. `start_mode`와 `dbt_selector`가 있으면 실행 그래프 생성 가능
4. `sensor_type` 또는 `schedule_interval`이 비면 자동 추론 규칙 사용
5. `model_mapping`이 비면 dbt model dependency에 위임

## 생성 순서

```text
DAG_Mapping
  -> 기본 DAG skeleton
Sensor_Notify
  -> Sensor / Notify / Branch
Validation_Policy
  -> validation task / retry
Review_Log
  -> 승인 상태 반영
```

## 한 줄 요약

- `DAG_Mapping`은 **DAG 뼈대**
- `Sensor_Notify`는 **시작 / 알림**
- `Validation_Policy`는 **검증 / 재시도**
- `Review_Log`는 **최종 승인 게이트**
