# `seq_operator_questionnaire` 테이블 설명

`seq_operator_questionnaire`는 DOCX 질문지 1건을 MariaDB에 정규화해서 저장하는 메인 테이블이다.

이 테이블은 질문지의 원문 응답과 구조화된 결과를 함께 담아, 이후 tag 생성과 운영 분석의 기준점이 되도록 설계되어 있다.

## 역할

- 질문지 1건의 최종 저장본 역할을 한다.
- 답변 원문과 선택값을 함께 보관한다.
- tag 후보 생성의 기준 데이터가 된다.
- 문서가 다시 들어오면 UPSERT로 최신 상태를 유지한다.

## 저장 성격

이 테이블은 단순 원문 저장소가 아니다.

다음 정보가 함께 들어간다.

- 파싱된 텍스트 답변
- 선택형 항목의 원문/코드성 값
- footer 메타데이터
- 원본 파일 정보
- 파생된 tag 목록 요약
- 미매핑 라벨

## 주요 컬럼 묶음

### 기본 식별 정보

- `id`: 내부 식별자
- `seq_name`: SEQ 식별 이름, 유일키
- `business_name`: 업무명
- `owner`: 담당 부서/담당자

### 실행 주기 / 중요도 / 시작 조건

- `execution_cycle_raw`
- `execution_cycle_json`
- `operational_importance_raw`
- `operational_importance_code`
- `start_condition_raw`
- `start_condition_json`
- `parallel_execution_raw`
- `parallel_execution_code`

### 실행 흐름 / 의존성

- `start_condition_detail`
- `main_processing_flow`
- `parallel_branch_detail`
- `external_dependency`
- `co_operated_seq_business`
- `downstream_business_usage`
- `normal_completion_criteria`

### 장애 / 재처리 / 운영 작업

- `job_failure_action_raw`
- `job_failure_action_json`
- `failure_action_detail`
- `auto_retry_raw`
- `auto_retry_code`
- `retry_criteria`
- `reprocessing_method_raw`
- `reprocessing_method_json`
- `reprocessing_detail`
- `manual_operation`
- `pre_reprocessing_check`
- `post_reprocessing_check`
- `skip_reject_handling`

### 파라미터 / 알림 / 예외

- `main_parameters`
- `file_data_wait`
- `success_failure_notification`
- `exception_execution_rule`
- `non_regular_execution_reason`
- `operation_check_screen_log`

### 운영상 중요 정보

- `most_attention_section`
- `current_operation_pain_point`
- `must_keep_after_transition`
- `interview_additional_check`
- `delay_failure_impact`
- `business_critical_result`

### 검증 정보

- `verification_timing`
- `verification_method_raw`
- `verification_method_json`
- `comparison_reference_raw`
- `comparison_reference_json`
- `main_verification_target`
- `null_duplicate_missing_check`
- `difference_tolerance_raw`
- `difference_tolerance_code`
- `allowed_difference_normal_exception`
- `master_reference_raw`
- `master_reference_code`
- `historical_master_available_raw`
- `historical_master_available_code`
- `history_comparable_period`
- `past_date_rerun_result_raw`
- `past_date_rerun_result_code`
- `verification_failure_action`

### 부가 메타데이터

- `available_materials_json`
- `completed_date`
- `author`
- `derived_tags_json`
- `raw_answers_json`
- `unmapped_labels_json`
- `source_file`
- `source_path`
- `source_sha256`
- `imported_at`
- `updated_at`

## 생성 과정

```text
DOCX 파싱
  -> answers / selected / metadata 생성
  -> parsed_to_row()
  -> seq_operator_questionnaire upsert
  -> questionnaire_id 획득
  -> seq_operator_questionnaire_tag 재생성
```

## UPSERT 동작

이 테이블은 `seq_name` 기준으로 UPSERT된다.

즉:

- 같은 `seq_name`이 다시 들어오면 기존 행을 업데이트한다.
- 새 문서가 들어오면 새 행이 아니라 동일 SEQ의 최신 스냅샷으로 갱신한다.

이 방식은 같은 업무를 재적재할 때 중복 레코드를 남기지 않기 위한 것이다.

## `parsed_to_row()`가 하는 일

`parsed_to_row()`는 파싱 결과를 DB 컬럼 형태로 평탄화한다.

예:

- `answers.execution_cycle` -> `execution_cycle_raw`
- `selected.execution_cycle` -> `execution_cycle_json`
- `selected.verification_method` -> `verification_method_json`
- `parsed.tags` -> `derived_tags_json`
- `parsed.unmapped_labels` -> `unmapped_labels_json`

## `raw` 와 `json` 컬럼의 차이

- `*_raw`: 문서에 적힌 원문 텍스트
- `*_json`: 선택된 값이나 구조화된 리스트를 JSON 문자열로 저장한 값

이 둘을 같이 두면 원문 보존과 구조화 검색을 동시에 할 수 있다.

## 활용 포인트

- 질문지 최신본 확인
- 동일 SEQ 재적재 비교
- tag 후보 생성의 기준 데이터 관리
- 원문과 구조화 결과의 동시 추적
- 문서 변경에 따른 영향 분석

## 관련 테이블과 관계

```text
seq_operator_questionnaire
  └── seq_operator_questionnaire_tag
```

- `seq_operator_questionnaire`는 원본 스냅샷이다.
- `seq_operator_questionnaire_tag`는 그 스냅샷에서 파생된 의미 단위다.

## 정리

이 테이블은 질문지 1건의 "정본" 역할을 한다.

원문, 구조화 값, 메타데이터, tag 요약을 함께 보관해
후속 분석과 전환 설계의 기준점이 되도록 만든다.
