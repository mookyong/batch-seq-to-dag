# SEQ 질문지 DOCX → MariaDB

SEQ 운영자 사전질문지 DOCX를 파싱해 MariaDB에 적재하는 도구입니다.
현재 권장 스크립트는 `seq_docx_to_mariadb_V3.py`입니다.

## 준비

1. `.env.example`을 `.env`로 복사하고 비밀번호를 변경합니다.

```bash
cp .env.example .env
```

2. 가상환경과 패키지를 준비합니다.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. MariaDB를 시작합니다.

```bash
docker compose up -d mariadb
```

## 실행

파싱 결과만 확인:

```bash
python seq_docx_to_mariadb_V3.py ./answers --recursive --dry-run
```

MariaDB에 적재:

```bash
python seq_docx_to_mariadb_V3.py ./answers --recursive
```

필요하면 임시 SEQ명을 허용할 수 있습니다.

```bash
python seq_docx_to_mariadb_V3.py ./answers --recursive --allow-missing-seq
```

다른 env 파일을 쓰려면:

```bash
python seq_docx_to_mariadb_V3.py ./answers --recursive --env-file .env.dev
```

## 환경변수

- `MARIADB_HOST`
- `MARIADB_PORT`
- `MARIADB_USER`
- `MARIADB_PASSWORD`
- `MARIADB_DATABASE`
- `MARIADB_CONNECT_TIMEOUT`

`.env`에 적힌 값보다 OS 환경변수가 우선합니다.

## 확인

```bash
docker compose exec mariadb mariadb -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE"
```

주요 테이블:

- `SEQ_INTERVIEW`
- `SEQ_INTERVIEW_OPTION`
- `SEQ_INTERVIEW_RAW`
