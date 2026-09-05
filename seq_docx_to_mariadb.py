#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataStage SEQ 운영자 사전질문지 DOCX -> MariaDB 적재

필수 패키지:
    pip install lxml mariadb

환경변수:
    DB_HOST=127.0.0.1
    DB_PORT=3306
    DB_USER=seq_user
    DB_PASSWORD=your_password
    DB_NAME=seq_migration

사용 예:
    python seq_docx_to_mariadb.py ./responses --init-db
    python seq_docx_to_mariadb.py ./responses/SEQ_A.docx
    python seq_docx_to_mariadb.py ./responses --dry-run
"""

import argparse
import json
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import mariadb
from lxml import etree


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
}

# Word Content Control의 일반 텍스트 태그 -> DB 컬럼
TEXT_FIELD_MAP = {
    "SEQ_NAME": "SEQ_NAME",
    "BUSINESS_NAME": "BUSINESS_NAME",
    "OWNER": "OWNER",
    "TARGET_END_TIME": "TARGET_END_TIME",
    "START_DETAIL": "START_DETAIL",
    "MAIN_FLOW": "MAIN_FLOW",
    "BRANCH_PARALLEL_DETAIL": "BRANCH_PARALLEL_DETAIL",
    "EXTERNAL_DEPENDENCY": "EXTERNAL_DEPENDENCY",
    "FAIL_DETAIL": "FAIL_DETAIL",
    "RETRY_DETAIL": "RETRY_DETAIL",
    "RERUN_DETAIL": "RERUN_DETAIL",
    "MANUAL_OPERATION": "MANUAL_OPERATION",
    "PARAMETERS": "PARAMETERS",
    "WAIT_CONDITION": "WAIT_CONDITION",
    "NOTIFICATION": "NOTIFICATION",
    "EXCEPTION_RULE": "EXCEPTION_RULE",
    "RISK_POINT": "RISK_POINT",
    "CURRENT_PAIN": "CURRENT_PAIN",
    "MUST_KEEP": "MUST_KEEP",
    "INTERVIEW_CHECK": "INTERVIEW_CHECK",
    "COMPLETED_DATE": "COMPLETED_DATE",
    "COMPLETED_BY": "COMPLETED_BY",
}

# 체크박스 태그 -> (CATEGORY, OPTION_CODE)
OPTION_MAP = {
    "SCHEDULE_1": ("SCHEDULE", "DAILY"),
    "SCHEDULE_2": ("SCHEDULE", "WEEKLY"),
    "SCHEDULE_3": ("SCHEDULE", "MONTHLY"),
    "SCHEDULE_4": ("SCHEDULE", "ADHOC"),
    "SCHEDULE_5": ("SCHEDULE", "OTHER"),

    "CRITICALITY_1": ("CRITICALITY", "HIGH"),
    "CRITICALITY_2": ("CRITICALITY", "MEDIUM"),
    "CRITICALITY_3": ("CRITICALITY", "LOW"),

    "START_CONDITION_1": ("START_CONDITION", "SCHEDULED_TIME"),
    "START_CONDITION_2": ("START_CONDITION", "UPSTREAM_COMPLETE"),
    "START_CONDITION_3": ("START_CONDITION", "FILE_ARRIVAL"),
    "START_CONDITION_4": ("START_CONDITION", "DATA_READY"),
    "START_CONDITION_5": ("START_CONDITION", "MANUAL"),
    "START_CONDITION_6": ("START_CONDITION", "OTHER"),

    "PARALLEL_1": ("PARALLEL", "YES"),
    "PARALLEL_2": ("PARALLEL", "NO"),
    "PARALLEL_3": ("PARALLEL", "UNKNOWN"),

    "FAIL_ACTION_1": ("FAIL_ACTION", "STOP_SEQUENCE"),
    "FAIL_ACTION_2": ("FAIL_ACTION", "CONTINUE_NEXT"),
    "FAIL_ACTION_3": ("FAIL_ACTION", "RUN_ERROR_JOB"),
    "FAIL_ACTION_4": ("FAIL_ACTION", "OPERATOR_DECISION"),
    "FAIL_ACTION_5": ("FAIL_ACTION", "OTHER"),

    "RETRY_1": ("RETRY", "NONE"),
    "RETRY_2": ("RETRY", "YES"),
    "RETRY_3": ("RETRY", "VARIES_BY_JOB"),

    "RERUN_METHOD_1": ("RERUN_METHOD", "FULL"),
    "RERUN_METHOD_2": ("RERUN_METHOD", "FROM_FAILED_JOB"),
    "RERUN_METHOD_3": ("RERUN_METHOD", "FROM_SPECIFIC_POINT"),
    "RERUN_METHOD_4": ("RERUN_METHOD", "CASE_BY_CASE"),

    "ATTACHMENT_1": ("ATTACHMENT", "SEQ_SCREENSHOT"),
    "ATTACHMENT_2": ("ATTACHMENT", "DSX_XML"),
    "ATTACHMENT_3": ("ATTACHMENT", "OPERATIONS_MANUAL"),
    "ATTACHMENT_4": ("ATTACHMENT", "INCIDENT_RERUN_HISTORY"),
    "ATTACHMENT_5": ("ATTACHMENT", "SCHEDULE_DEPENDENCY_LIST"),
    "ATTACHMENT_6": ("ATTACHMENT", "OTHER"),
}

# 양식의 기본 안내문은 실제 답변으로 저장하지 않는다.
PLACEHOLDERS = {
    "클릭하여 입력",
    "예: 매일 07:30 이전",
    "대상/시간/조건을 입력해 주세요",
    "예: JOB_A → JOB_B → JOB_C",
    "동시 실행 Job 또는 분기 조건을 입력해 주세요",
    "다른 SEQ/Job, 파일, DB, 외부시스템 등을 입력해 주세요",
    "실패 시 실제 운영 절차를 입력해 주세요",
    "예: 3회 / 10분 간격 / 특정 오류만 재시도",
    "재실행 시 선행 확인사항과 시작 지점을 입력해 주세요",
    "수동 실행·중지·Skip·강제 종료·재기동 등을 입력해 주세요",
    "예: 기준일자, 경로, 시스템 구분, 재처리 여부",
    "대기 대상, 확인 주기, 타임아웃 기준을 입력해 주세요",
    "알림 조건, 방식, 대상자를 입력해 주세요",
    "월말/휴일/특정 요일/특정 데이터 조건 등을 입력해 주세요",
    "장애가 자주 발생하거나 운영 판단이 필요한 구간",
    "수동 확인, 반복 작업, 재처리 어려움 등을 입력해 주세요",
    "Airflow 전환 후에도 유지되어야 하는 운영 규칙",
    "사전 작성이 어려워 인터뷰에서 확인할 내용을 입력해 주세요",
    "YYYY-MM-DD",
}


DDL = [
    """
    CREATE TABLE IF NOT EXISTS SEQ_INTERVIEW (
        SEQ_ID BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        SEQ_NAME VARCHAR(200) NOT NULL,
        BUSINESS_NAME VARCHAR(200) NULL,
        OWNER VARCHAR(100) NULL,
        TARGET_END_TIME VARCHAR(100) NULL,
        START_DETAIL TEXT NULL,
        MAIN_FLOW TEXT NULL,
        BRANCH_PARALLEL_DETAIL TEXT NULL,
        EXTERNAL_DEPENDENCY TEXT NULL,
        FAIL_DETAIL TEXT NULL,
        RETRY_DETAIL TEXT NULL,
        RERUN_DETAIL TEXT NULL,
        MANUAL_OPERATION TEXT NULL,
        PARAMETERS TEXT NULL,
        WAIT_CONDITION TEXT NULL,
        NOTIFICATION TEXT NULL,
        EXCEPTION_RULE TEXT NULL,
        RISK_POINT TEXT NULL,
        CURRENT_PAIN TEXT NULL,
        MUST_KEEP TEXT NULL,
        INTERVIEW_CHECK TEXT NULL,
        COMPLETED_DATE DATE NULL,
        COMPLETED_BY VARCHAR(100) NULL,
        CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (SEQ_ID),
        KEY IX_SEQ_INTERVIEW_SEQ_NAME (SEQ_NAME)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS SEQ_INTERVIEW_OPTION (
        SEQ_ID BIGINT UNSIGNED NOT NULL,
        CATEGORY VARCHAR(50) NOT NULL,
        OPTION_CODE VARCHAR(50) NOT NULL,
        SELECTED TINYINT(1) NOT NULL DEFAULT 0,
        PRIMARY KEY (SEQ_ID, CATEGORY, OPTION_CODE),
        CONSTRAINT FK_SEQ_OPTION_INTERVIEW
            FOREIGN KEY (SEQ_ID)
            REFERENCES SEQ_INTERVIEW (SEQ_ID)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    """
    CREATE TABLE IF NOT EXISTS SEQ_INTERVIEW_RAW (
        RAW_ID BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        SEQ_ID BIGINT UNSIGNED NOT NULL,
        FILE_NAME VARCHAR(300) NOT NULL,
        RAW_JSON LONGTEXT NOT NULL,
        CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (RAW_ID),
        KEY IX_SEQ_RAW_SEQ_ID (SEQ_ID),
        CONSTRAINT FK_SEQ_RAW_INTERVIEW
            FOREIGN KEY (SEQ_ID)
            REFERENCES SEQ_INTERVIEW (SEQ_ID)
            ON DELETE CASCADE,
        CONSTRAINT CK_SEQ_RAW_JSON CHECK (JSON_VALID(RAW_JSON))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
]


def clean_text(value):
    if value is None:
        return None
    value = " ".join(value.replace("\xa0", " ").split()).strip()
    if not value or value in PLACEHOLDERS:
        return None
    return value


def parse_date(value):
    value = clean_text(value)
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"COMPLETED_DATE 날짜 형식 오류: {value}")


def checkbox_value(sdt):
    checked = sdt.xpath(
        "./w:sdtPr/w14:checkbox/w14:checked/@w14:val",
        namespaces=NS,
    )
    if not checked:
        return None
    return checked[0].lower() in ("1", "true", "on")


def parse_docx(path):
    """
    DOCX의 Word Content Control(w:sdt)의 w:tag 값을 Key로 사용해
    {TAG: value} 형태의 dict를 반환한다.
    """
    path = Path(path)

    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")

    root = etree.fromstring(xml)
    result = {}

    for sdt in root.xpath(".//w:sdt", namespaces=NS):
        tags = sdt.xpath("./w:sdtPr/w:tag/@w:val", namespaces=NS)
        if not tags:
            continue

        tag = tags[0]
        checked = checkbox_value(sdt)

        if checked is not None:
            result[tag] = checked
        else:
            text_parts = sdt.xpath(
                "./w:sdtContent//w:t/text()",
                namespaces=NS,
            )
            result[tag] = clean_text("".join(text_parts))

    return result


def validate_document(data, file_name):
    errors = []

    if not data.get("SEQ_NAME"):
        errors.append("SEQ_NAME이 입력되지 않았습니다.")

    unknown_tags = sorted(
        set(data.keys()) - set(TEXT_FIELD_MAP.keys()) - set(OPTION_MAP.keys())
    )
    if unknown_tags:
        errors.append(f"정의되지 않은 태그: {', '.join(unknown_tags)}")

    if errors:
        raise ValueError(f"{file_name}: " + " / ".join(errors))


def get_db_connection():
    required = ["DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [name for name in required if not os.getenv(name)]

    if missing:
        raise RuntimeError(
            "DB 환경변수가 없습니다: " + ", ".join(missing)
        )

    return mariadb.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        autocommit=False,
    )


def init_database(conn):
    cur = conn.cursor()
    try:
        for ddl in DDL:
            cur.execute(ddl)
        conn.commit()
    finally:
        cur.close()


def insert_interview(conn, data, file_name):
    """
    1) SEQ_INTERVIEW
    2) SEQ_INTERVIEW_OPTION
    3) SEQ_INTERVIEW_RAW
    순서로 하나의 트랜잭션에 저장한다.
    """
    validate_document(data, file_name)

    db_values = {}
    for tag, column in TEXT_FIELD_MAP.items():
        if tag == "COMPLETED_DATE":
            db_values[column] = parse_date(data.get(tag))
        else:
            db_values[column] = clean_text(data.get(tag))

    columns = list(db_values.keys())
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)

    insert_master_sql = f"""
        INSERT INTO SEQ_INTERVIEW ({column_sql})
        VALUES ({placeholders})
    """

    cur = conn.cursor()

    try:
        cur.execute(
            insert_master_sql,
            tuple(db_values[col] for col in columns),
        )
        seq_id = cur.lastrowid

        option_sql = """
            INSERT INTO SEQ_INTERVIEW_OPTION
                (SEQ_ID, CATEGORY, OPTION_CODE, SELECTED)
            VALUES (?, ?, ?, ?)
        """

        for tag, (category, option_code) in OPTION_MAP.items():
            selected = 1 if data.get(tag) is True else 0
            cur.execute(
                option_sql,
                (seq_id, category, option_code, selected),
            )

        raw_json = json.dumps(
            data,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )

        cur.execute(
            """
            INSERT INTO SEQ_INTERVIEW_RAW
                (SEQ_ID, FILE_NAME, RAW_JSON)
            VALUES (?, ?, ?)
            """,
            (seq_id, file_name, raw_json),
        )

        conn.commit()
        return seq_id

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()


def collect_docx(input_path):
    path = Path(input_path)

    if path.is_file():
        if path.suffix.lower() != ".docx":
            raise ValueError("입력 파일은 .docx 형식이어야 합니다.")
        return [path]

    if path.is_dir():
        # Word가 생성하는 임시 파일(~$...)은 제외
        return sorted(
            p for p in path.rglob("*.docx")
            if not p.name.startswith("~$")
        )

    raise FileNotFoundError(f"입력 경로가 없습니다: {path}")


def dry_run(files):
    success = 0
    failed = 0

    for path in files:
        try:
            data = parse_docx(path)
            validate_document(data, path.name)
            print(
                json.dumps(
                    {
                        "file": path.name,
                        "seq_name": data.get("SEQ_NAME"),
                        "data": data,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            success += 1
        except Exception as exc:
            failed += 1
            print(f"[ERROR] {path}: {exc}", file=sys.stderr)

    return success, failed


def load_to_database(files, init_db=False):
    conn = get_db_connection()
    success = 0
    failed = 0

    try:
        if init_db:
            init_database(conn)
            print("[OK] MariaDB 테이블 생성/확인 완료")

        for path in files:
            try:
                data = parse_docx(path)
                seq_id = insert_interview(conn, data, path.name)
                print(
                    f"[OK] {path.name} -> "
                    f"SEQ_ID={seq_id}, SEQ_NAME={data.get('SEQ_NAME')}"
                )
                success += 1

            except Exception as exc:
                failed += 1
                print(f"[ERROR] {path}: {exc}", file=sys.stderr)

    finally:
        conn.close()

    return success, failed


def main():
    parser = argparse.ArgumentParser(
        description="DataStage SEQ 운영자 사전질문지 DOCX를 MariaDB에 적재"
    )
    parser.add_argument(
        "input",
        help="DOCX 파일 또는 DOCX 파일들이 있는 폴더",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="필요한 MariaDB 테이블을 자동 생성",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="DB에 저장하지 않고 DOCX 파싱 결과만 JSON으로 출력",
    )

    args = parser.parse_args()

    try:
        files = collect_docx(args.input)

        if not files:
            print("처리할 DOCX 파일이 없습니다.")
            return 1

        print(f"대상 DOCX: {len(files)}개")

        if args.dry_run:
            success, failed = dry_run(files)
        else:
            success, failed = load_to_database(
                files,
                init_db=args.init_db,
            )

        print(
            f"완료: 성공={success}, 실패={failed}, 전체={len(files)}"
        )

        return 0 if failed == 0 else 2

    except Exception as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
