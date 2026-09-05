# SEQ 질문지 DOCX → MariaDB

## 1. 환경변수 설정

`.env.example`을 `.env`로 복사하고 비밀번호를 변경합니다.

```bash
cp .env.example .env
```

MariaDB 컨테이너 초기화와 Python 접속정보가 동일한 `.env`를 사용합니다.

## 2. MariaDB 시작

```bash
docker compose up -d mariadb
docker compose ps
```

## 3. Python 패키지 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. 질문지 파싱 확인

```bash
python seq_docx_to_mariadb.py ./answers --recursive --dry-run
```

## 5. MariaDB 적재

```bash
python seq_docx_to_mariadb.py ./answers --recursive
```

다른 env 파일을 쓰려면:

```bash
python seq_docx_to_mariadb.py ./answers --recursive --env-file .env.dev
```

DB 비밀번호는 CLI 인자로 받지 않습니다. OS 환경변수가 `.env`보다 우선합니다.

## 6. DB 확인

```bash
docker compose exec mariadb mariadb \
  -u"$MARIADB_USER" -p"$MARIADB_PASSWORD" "$MARIADB_DATABASE"
```

주요 테이블:
- `seq_operator_questionnaire`
- `seq_operator_questionnaire_tag`
