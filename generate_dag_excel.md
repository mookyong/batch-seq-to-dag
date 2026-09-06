# `generate_dag_excel.py` 옵션 설명

`generate_dag_excel.py`는 `seq_operator_questionnaire`와 `seq_operator_questionnaire_tag`를 읽어서 DAG 자동 생성용 Excel 워크북을 만드는 스크립트다.

## 목적

- 질문지와 태그 정보를 사람이 보정 가능한 Excel 입력으로 만든다.
- DAG generator가 읽을 표준 입력 파일을 생성한다.
- 필요하면 `seq_name`별로 개별 워크북도 생성한다.

## 입력

기본 입력은 MariaDB에 저장된 두 테이블이다.

- `seq_operator_questionnaire`
- `seq_operator_questionnaire_tag`

## 출력

- 기본: 단일 `.xlsx` 워크북
- 옵션 사용 시: `seq_name`별 개별 `.xlsx` 파일

## 옵션

| 옵션 | 설명 | 예시 |
|---|---|---|
| `--output` | 단일 워크북 출력 파일 경로 | `dag_generation_input.xlsx` |
| `--split-by-seq` | `seq_name`별 개별 파일 생성 | `--split-by-seq` |
| `--output-dir` | 개별 파일 출력 디렉터리 | `dag_split_out` |
| `--seq-name` | 대상 `seq_name` 지정 | `--seq-name SEQ_PRODUCT_MASTER` |
| `--env-file` | MariaDB 환경변수 파일 경로 | `.env` |
| `--overwrite` | 기존 출력 파일/디렉터리 덮어쓰기 | `--overwrite` |

## 실행 예시

### 단일 워크북 생성

```bash
python generate_dag_excel.py --output dag_generation_input.xlsx --overwrite
```

### 개별 워크북 생성

```bash
python generate_dag_excel.py --split-by-seq --output-dir dag_split_out --overwrite
```

### 특정 `seq_name`만 생성

```bash
python generate_dag_excel.py --seq-name SEQ_PRODUCT_MASTER --output product_master.xlsx --overwrite
```

## 생성되는 시트

- `DAG_Mapping`
- `Sensor_Notify`
- `Validation_Policy`
- `Review_Log`

## 동작 개요

```text
DB 조회
  -> 질문지/태그 읽기
  -> 자동 추론값 계산
  -> 시트별 행 생성
  -> Excel 서식 적용
  -> .xlsx 저장
```

## 주의사항

- 출력 파일이 이미 존재하면 기본적으로 중단한다.
- `--overwrite`를 주면 덮어쓴다.
- `--split-by-seq`는 파일 단위 관리가 필요할 때 유용하다.
