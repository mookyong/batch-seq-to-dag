# DAG Python 생성 규칙표

`dag_generation_input.xlsx`를 읽어서 Airflow DAG Python 코드를 생성할 때의 변환 규칙을 정리한 문서다.

## 목적

- Excel 입력을 Python 코드로 변환한다.
- DAG 뼈대, Sensor, dbt, 검증, 알림, 승인 게이트를 일관되게 생성한다.
- 사람이 확정한 Excel 값을 최종 코드에 반영한다.

## 기본 구조

```text
start
  -> branch
  -> sensor(optional)
  -> dbt_task_group
  -> validation
  -> notify_success / notify_failure
  -> end
```

## 규칙표

| 단계 | 입력 시트/컬럼 | 생성 규칙 | Python 코드 반영 |
|---|---|---|---|
| 1. DAG 기본값 | `DAG_Mapping.seq_name`, `business_name`, `dag_id`, `dag_name` | `dag_id`는 우선 사용, 없으면 `seq_name`에서 snake_case 생성 | `DAG(...)`, `dag_id`, `dag_display_name`, `description` |
| 2. 스케줄 | `DAG_Mapping.schedule_type`, `schedule_interval` | `schedule_interval`이 있으면 우선 사용, 없으면 `schedule_type` 기반 cron 사용 | `schedule=` |
| 3. 기본 args | `Review_Log.owner`, `Validation_Policy.retry_policy`, `DAG_Mapping.priority` | owner, retries, retry_delay, priority 설정 | `default_args` |
| 4. 시작 분기 | `Sensor_Notify.start_mode` | `manual/file_sensor/dependency_sensor/time_based/event`로 분기 | `BranchPythonOperator` |
| 5. Sensor | `Sensor_Notify.sensor_type`, `sensor_target`, `external_dependency` | Sensor 타입별로 인스턴스 생성 | `FileSensor`, `ExternalTaskSensor`, custom sensor |
| 6. dbt 실행 | `DAG_Mapping.dbt_group`, `dbt_selector`, `model_mapping` | `dbt_selector`를 Cosmos `RenderConfig`에 반영 | `DbtTaskGroup` |
| 7. 검증 | `Validation_Policy.validation_mode`, `validation_timing`, `comparison_reference` | 검증 모드에 따라 `dbt test` 또는 validation task 생성 | `BashOperator`, validation task |
| 8. 알림 | `Sensor_Notify.notify_on_success`, `notify_on_failure`, `notify_channel`, `notify_recipients` | 채널별 notify task/callback 생성 | `PythonOperator`, callback, notifier |
| 9. 실패 정책 | `Sensor_Notify.failure_policy`, `Validation_Policy.retry_policy` | stop/continue/manual_review로 분기 | `trigger_rule`, `retries`, `retry_delay` |
| 10. 승인 게이트 | `Review_Log.review_status`, `review_comment` | `approved` 아니면 최종 생성 대신 초안/TODO | scaffold only / warnings |

## 실무 규칙

- `Review_Log.review_status != approved`면 최종 DAG가 아니라 초안만 생성한다.
- `model_mapping`이 있으면 task edge 세분화, 없으면 dbt graph에 위임한다.
- `sensor_type`이 비면 `start_mode`와 `external_dependency`로 추론한다.
- `notify_channel`이 비면 notify task 생성 대신 TODO를 남긴다.
- `validation_mode=dbt_test`면 Cosmos dbt task와 `dbt test`를 연결한다.

## Python 코드 생성 순서

1. DAG 기본 정보 생성
2. `default_args` 생성
3. 시작 분기/센서 생성
4. `DbtTaskGroup` 생성
5. 검증 task 생성
6. 알림 task 생성
7. 실패 정책과 `trigger_rule` 반영
8. 승인 상태에 따른 scaffold/TODO 처리

## 한 줄 요약

- Excel은 **입력**
- 이 규칙표는 **변환 로직**
- DAG Python은 **최종 산출물**
