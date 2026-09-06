# `seq_docx_to_mariadb_V3.py` 처리 프로세스

`seq_docx_to_mariadb_V3.py`는 DataStage SEQ 운영자 사전질문지 DOCX를 읽어서 MariaDB에 저장하고, 전환/분석에 쓸 수 있는 tag 후보를 함께 생성하는 도구다.

## 개요

이 스크립트의 핵심 목적은 다음과 같다.

1. DOCX의 표와 Content Control 값을 안정적으로 읽는다.
2. 질문지 답변을 구조화된 JSON/컬럼 형태로 정리한다.
3. 규칙 기반으로 tag 후보를 생성한다.
4. MariaDB에 질문지 1건과 tag 후보를 함께 저장한다.

## 전체 흐름

```text
DOCX 입력
  -> DOCX 내부 OOXML 파싱
  -> 질문 라벨 기준 응답 수집
  -> 체크박스/선택값 해석
  -> footer 메타데이터 추출
  -> tag 후보 생성
  -> dry-run 출력 또는 MariaDB 적재
```

## 입력

입력은 다음 중 하나다.

- `.docx` 파일 1개
- DOCX가 들어있는 디렉터리
- glob 패턴

선택 옵션은 다음을 지원한다.

- `--recursive`: 디렉터리 하위까지 탐색
- `--dry-run`: DB에 저장하지 않고 파싱 결과만 출력
- `--allow-missing-seq`: `seq_name`이 비어 있을 때 파일명 기반 임시값 허용
- `--env-file`: MariaDB 접속용 `.env` 파일 지정

## 처리 순서

### 1. 환경 로드

`load_environment()`가 `.env`를 읽어 프로세스 환경변수에 반영한다.

- OS/컨테이너 환경변수가 `.env`보다 우선한다.
- `dry-run`이 아니면 DB 접속용 핵심 변수 `MARIADB_USER`, `MARIADB_PASSWORD`, `MARIADB_DATABASE`가 필요하다.

### 2. DOCX 수집

`iter_docx_inputs()`가 입력을 다음 순서로 해석한다.

1. 실제 파일이면 바로 사용
2. 디렉터리면 `.docx`를 탐색
3. 그 외에는 glob으로 확장

Word 임시파일 `~$...`은 제외한다.

### 3. 문서 파싱

`parse_questionnaire()`가 실제 본문을 읽는다.

#### 3-1. 표 기반 매핑

문서의 2열 표를 순회하면서 왼쪽 셀의 라벨을 기준으로 오른쪽 값을 읽는다.

```text
라벨 셀 -> FIELD_BY_LABEL -> answers/selected 갱신
```

여기서 중요한 점은 행 순서가 아니라 **라벨 자체**를 기준으로 매핑한다는 점이다.

#### 3-2. 선택형 값 해석

선택형 항목은 `parse_choices()`가 해석한다.

- `☒`, `☑`, `✅` 같은 체크 표시를 인식
- 일반적인 `[]`, `()` 스타일 체크도 인식
- 체크 표시가 없어도 단일 옵션만 남아 있으면 허용

#### 3-3. 텍스트 정리

`clean_text_answer()`와 `normalize_whitespace()`가 다음을 정리한다.

- 공백 정리
- 줄바꿈 정규화
- placeholder 문구 제거
- `YYYY-MM-DD` 같은 안내 문구 제거

#### 3-4. footer 메타데이터 추출

`parse_footer_metadata()`는 문서의 `작성 완료일`, `작성자`를 찾는다.

- 완료일은 `YYYY-MM-DD` 등으로 정규화
- 날짜로 해석되지 않으면 저장하지 않음

#### 3-5. 누락 라벨 추적

스키마에 없는 라벨은 `unmapped_labels`에 따로 남긴다.

이 값은 문서 변경 감지나 파서 보완에 유용하다.

## tag 후보 생성

`generate_tag_candidates()`는 구조화된 응답을 바탕으로 후보 tag를 만든다.

### 생성 기준 예시

- `execution_cycle` -> `cycle_daily`, `cycle_weekly` 등
- `start_condition` -> `trigger_schedule`, `trigger_file`, `run_manual` 등
- `external_dependency` -> `external_dependency`
- `reprocessing_method` -> `reprocess_full`, `reprocess_failed` 등
- `verification_method` -> `verify_count`, `verify_sum`, `verify_file` 등
- `difference_tolerance` -> `policy_strict`, `policy_conditional` 등

### 태그 생성 특징

- 조건에 맞는 항목만 생성한다.
- 같은 `tag_name`이 여러 규칙에서 나오면 최초 1개만 남긴다.
- `requires_review`가 필요한 후보도 별도로 표시한다.

## DB 적재

### 메인 테이블

`seq_operator_questionnaire`

- 질문지 1건의 정규화된 스냅샷을 저장한다.
- `seq_name`은 유일키다.
- `imported_at`, `updated_at`을 유지한다.

### 태그 테이블

`seq_operator_questionnaire_tag`

- 메인 질문지 1건에 대해 여러 tag 후보를 저장한다.
- `(questionnaire_id, tag_name)` 조합이 유일하다.
- 메인 레코드가 갱신되면 태그도 재생성된다.

### 적재 순서

```text
메인 row upsert
  -> 기존 tag 삭제
  -> 새 tag 후보 insert
  -> commit
```

`LAST_INSERT_ID(id)`를 사용해서 INSERT/UPDATE 모두에서 동일하게 `questionnaire_id`를 얻는다.

## dry-run 동작

`--dry-run`은 DB를 사용하지 않는다.

출력 내용:

- `source_file`
- `seq_name`
- `answers`
- `selected`
- `available_materials`
- `completion_date`
- `author`
- `tags`
- `unmapped_labels`

## 오류 처리

- 입력 파일이 없으면 종료 코드 2를 반환한다.
- `seq_name`이 비어 있으면 기본적으로 적재를 중단한다.
- DB 적재 중 에러가 나면 해당 건만 롤백하고 다음 문서를 계속 처리한다.

## 처리 요약

```text
1. 환경 로드
2. 입력 DOCX 수집
3. 질문지 파싱
4. tag 후보 생성
5. dry-run 출력 또는 MariaDB 적재
6. 결과 로그 출력
```

## 확인 포인트

- 표 라벨이 바뀌어도 파싱이 유지되는지
- 체크박스가 `☒/☐`로 올바르게 해석되는지
- `seq_name`이 유일키로 잘 동작하는지
- tag 후보가 문서 변경에 따라 재생성되는지
- `unmapped_labels`에 신규 라벨이 남는지
