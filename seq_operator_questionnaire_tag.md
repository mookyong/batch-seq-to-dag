# `seq_operator_questionnaire_tag` 테이블 설명

`seq_operator_questionnaire_tag`는 질문지 1건에서 파생된 tag 후보를 행 단위로 저장하는 테이블이다.

이 테이블은 원문 답변을 그대로 보관하는 곳이 아니라, 질문지 내용을 전환/분석/검증에 유용한 의미 단위로 정리한 결과를 담는다.

## 역할

- 질문지 1건에서 여러 개의 tag 후보를 저장한다.
- 각 tag가 어떤 규칙으로 만들어졌는지 남긴다.
- Airflow 전환, 운영 정책 분석, 검증 설계에 활용한다.

## 저장 구조

주요 컬럼은 다음과 같다.

- `questionnaire_id`: 원본 질문지와의 연결 키
- `tag_category`: tag의 상위 분류
- `tag_name`: 실제 tag 이름
- `source_field`: tag 생성에 사용된 원본 필드
- `source_value`: 원본 응답 값
- `rule_code`: 생성 규칙 코드
- `confidence`: 생성 신뢰도
- `requires_review`: 사람 검토 필요 여부
- `created_at`: 생성 시각

## 생성 과정

```text
DOCX 파싱
  -> answers / selected 생성
  -> generate_tag_candidates()
  -> category + tag_name 결정
  -> seq_operator_questionnaire_tag insert
```

### 예시 흐름

- `execution_cycle = 일배치` -> `tag_category = cycle`, `tag_name = cycle_daily`
- `start_condition = 파일 도착` -> `tag_category = trigger`, `tag_name = trigger_file`
- `reprocessing_method = 전체 재실행` -> `tag_category = operation`, `tag_name = reprocess_full`
- `verification_method = 건수` -> `tag_category = verification`, `tag_name = verify_count`

## `tag_category`의 의미

`tag_category`는 자유 입력값이 아니라, 코드 내부 규칙이 정한 분류값이다.

자주 쓰는 분류는 다음과 같다.

- `cycle`
- `trigger`
- `run`
- `operation`
- `verification`
- `verification_reference`
- `verification_policy`
- `data`

즉, `tag_category`는 "이 tag가 어떤 성격인가"를 나타내는 상위 분류다.

## `tag_name` 생성 방식

`tag_name`은 답변값을 직접 넣는 것이 아니라, 규칙에 따라 표준화된 이름으로 바꾼 값이다.

예:

- `일배치` -> `cycle_daily`
- `수시` -> `cycle_adhoc`
- `정해진 시간` -> `trigger_schedule`
- `수동 실행` -> `run_manual`
- `완전 일치 필요` -> `policy_strict`

## 특징

- 같은 질문지에서 여러 tag가 생길 수 있다.
- `questionnaire_id + tag_name` 조합이 유일하다.
- 질문지 문서가 바뀌면 tag도 재생성된다.
- 일부 tag는 `requires_review=1`로 사람 검토가 필요할 수 있다.

## 활용 포인트

- 전환 대상 업무의 실행 특성 파악
- 운영 방식 분류
- 검증 정책 정리
- Airflow DAG 설계 시 trigger / run / verification 단서 확보

## 관련 테이블과 관계

```text
seq_operator_questionnaire
  └── seq_operator_questionnaire_tag
```

- `seq_operator_questionnaire`는 원본 질문지 1건의 스냅샷이다.
- `seq_operator_questionnaire_tag`는 그 1건에서 파생된 tag 후보 집합이다.

## 정리

이 테이블은 질문지 내용을 구조화해 "의미 있는 운영 메타데이터"로 바꾸는 결과물이다.
즉, 원문 보관보다 **분류, 검색, 전환 설계, 검증 설계**에 더 초점이 있다.
