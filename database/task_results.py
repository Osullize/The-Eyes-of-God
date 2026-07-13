from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import re
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import CrawlResult, ProfilePackage, TaskRun
from database.queries import _isoformat


CRAWL_RESULT_COLUMNS: list[tuple[str, str]] = [
    ("domain", "域名"),
    ("company_name", "公司名称"),
    ("website", "官网"),
    ("status", "抓取状态"),
    ("emails", "邮箱"),
    ("phones", "电话"),
    ("possible_address", "可能地址"),
    ("description", "简介"),
    ("crawled_pages", "抓取页数"),
    ("error", "错误"),
    ("country", "国家"),
    ("industry", "行业"),
    ("keyword", "搜索关键词"),
    ("matched_keywords", "匹配关键词"),
    ("profile_package_id", "画像包ID"),
    ("profile_page_count", "画像页数"),
    ("created_at", "入库时间"),
]


def get_task_run_results(
    session: Session,
    task_run_id: int,
    *,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any] | None:
    task_run = session.get(TaskRun, task_run_id)
    if task_run is None:
        return None

    if task_run.task_type != "crawl":
        return {
            "task_run_id": task_run.id,
            "task_type": task_run.task_type,
            "task_name": task_run.name,
            "status": task_run.status,
            "result_type": "unsupported",
            "message": "当前版本先支持查看抓官网任务结果。",
            "items": [],
            "count": 0,
            "total": 0,
            "limit": min(max(limit, 1), 500),
            "offset": max(offset, 0),
        }

    return list_crawl_task_results(session, task_run, limit=limit, offset=offset)


def list_crawl_task_results(
    session: Session,
    task_run: TaskRun,
    *,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    safe_limit = min(max(limit, 1), 500)
    safe_offset = max(offset, 0)
    source_names = crawl_source_names(task_run)
    stmt = (
        select(CrawlResult)
        .join(CrawlResult.domain_record)
        .where(CrawlResult.source_file.in_(source_names))
        .order_by(CrawlResult.created_at.desc(), CrawlResult.id.desc())
    )
    total = len(session.scalars(stmt).all())
    rows = session.scalars(stmt.offset(safe_offset).limit(safe_limit)).all()
    profile_by_crawl_result_id = profile_packages_by_crawl_result_id(session, task_run.id)
    return {
        "task_run_id": task_run.id,
        "task_type": task_run.task_type,
        "task_name": task_run.name,
        "status": task_run.status,
        "result_type": "crawl",
        "items": [serialize_crawl_task_result(row, profile_by_crawl_result_id.get(row.id)) for row in rows],
        "count": len(rows),
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
    }


def build_crawl_task_results_xlsx(session: Session, task_run_id: int) -> tuple[str, bytes] | None:
    task_run = session.get(TaskRun, task_run_id)
    if task_run is None:
        return None
    if task_run.task_type != "crawl":
        return (xlsx_filename(task_run_id), build_xlsx(CRAWL_RESULT_COLUMNS, []))

    result = list_crawl_task_results(session, task_run, limit=500, offset=0)
    return (xlsx_filename(task_run_id), build_xlsx(CRAWL_RESULT_COLUMNS, result["items"]))


def build_selected_crawl_results_xlsx(session: Session, crawl_result_ids: list[int]) -> tuple[str, bytes]:
    unique_ids = list(dict.fromkeys(crawl_result_ids))
    if not unique_ids:
        return ("crawl-results-selected.xlsx", build_xlsx(CRAWL_RESULT_COLUMNS, []))

    rows = session.scalars(
        select(CrawlResult)
        .join(CrawlResult.domain_record)
        .where(CrawlResult.id.in_(unique_ids))
    ).all()
    row_by_id = {row.id: row for row in rows}
    ordered_rows = [row_by_id[row_id] for row_id in unique_ids if row_id in row_by_id]
    profile_by_crawl_result_id = latest_profile_packages_by_crawl_result_id(session, unique_ids)
    serialized_rows = [
        serialize_crawl_task_result(row, profile_by_crawl_result_id.get(row.id))
        for row in ordered_rows
    ]
    return ("crawl-results-selected.xlsx", build_xlsx(CRAWL_RESULT_COLUMNS, serialized_rows))


def crawl_source_names(task_run: TaskRun) -> list[str]:
    source_names = [f"task:crawl:{task_run.id}"]
    output_file = str((task_run.params_json or {}).get("output_file") or "").strip()
    if output_file:
        source_names.append(output_file)
    return source_names


def profile_packages_by_crawl_result_id(session: Session, task_run_id: int) -> dict[int, ProfilePackage]:
    packages = session.scalars(
        select(ProfilePackage)
        .where(ProfilePackage.crawl_task_run_id == task_run_id, ProfilePackage.crawl_result_id.is_not(None))
        .order_by(ProfilePackage.updated_at.desc(), ProfilePackage.id.desc())
    ).all()
    result: dict[int, ProfilePackage] = {}
    for package in packages:
        if package.crawl_result_id is not None and package.crawl_result_id not in result:
            result[package.crawl_result_id] = package
    return result


def latest_profile_packages_by_crawl_result_id(session: Session, crawl_result_ids: list[int]) -> dict[int, ProfilePackage]:
    packages = session.scalars(
        select(ProfilePackage)
        .where(ProfilePackage.crawl_result_id.in_(crawl_result_ids))
        .order_by(ProfilePackage.updated_at.desc(), ProfilePackage.id.desc())
    ).all()
    result: dict[int, ProfilePackage] = {}
    for package in packages:
        if package.crawl_result_id is not None and package.crawl_result_id not in result:
            result[package.crawl_result_id] = package
    return result


def serialize_crawl_task_result(row: CrawlResult, profile_package: ProfilePackage | None) -> dict[str, Any]:
    return {
        "id": row.id,
        "domain_id": row.domain_id,
        "domain": row.domain_record.domain,
        "keyword": row.keyword,
        "company_name": row.company_name,
        "website": row.website,
        "emails": row.emails,
        "phones": row.phones,
        "possible_address": row.possible_address,
        "description": row.description,
        "crawled_pages": row.crawled_pages,
        "status": row.status,
        "error": row.error,
        "country": row.country,
        "industry": row.industry,
        "matched_keywords": row.matched_keywords,
        "profile_package_id": profile_package.id if profile_package else None,
        "profile_page_count": profile_package.page_count if profile_package else None,
        "created_at": _isoformat(row.created_at),
    }


def xlsx_filename(task_run_id: int) -> str:
    return f"crawl-task-{task_run_id}-results.xlsx"


def build_xlsx(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> bytes:
    workbook = BytesIO()
    with ZipFile(workbook, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml())
        archive.writestr("_rels/.rels", root_relationships_xml())
        archive.writestr("docProps/app.xml", app_xml())
        archive.writestr("docProps/core.xml", core_xml())
        archive.writestr("xl/workbook.xml", workbook_xml())
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_relationships_xml())
        archive.writestr("xl/styles.xml", styles_xml())
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml(columns, rows))
    return workbook.getvalue()


def worksheet_xml(columns: list[tuple[str, str]], rows: list[dict[str, Any]]) -> str:
    sheet_rows = [excel_row(1, [label for _, label in columns], style="1")]
    for index, row in enumerate(rows, start=2):
        sheet_rows.append(excel_row(index, [row.get(key, "") for key, _ in columns]))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        f'<dimension ref="A1:{column_name(len(columns))}{max(len(rows) + 1, 1)}"/>'
        '<sheetFormatPr defaultRowHeight="18"/>'
        f"<cols>{columns_xml(len(columns))}</cols>"
        f"<sheetData>{''.join(sheet_rows)}</sheetData>"
        f'<autoFilter ref="A1:{column_name(len(columns))}{max(len(rows) + 1, 1)}"/>'
        "</worksheet>"
    )


def excel_row(row_index: int, values: list[Any], *, style: str = "") -> str:
    cells = []
    for column_index, value in enumerate(values, start=1):
        cell_ref = f"{column_name(column_index)}{row_index}"
        style_attr = f' s="{style}"' if style else ""
        cells.append(f'<c r="{cell_ref}" t="inlineStr"{style_attr}><is><t>{escape_xml(value)}</t></is></c>')
    return f'<row r="{row_index}">{"".join(cells)}</row>'


def columns_xml(count: int) -> str:
    widths = []
    for index in range(1, count + 1):
        width = 34 if index in {3, 8, 14} else 18
        widths.append(f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>')
    return "".join(widths)


def column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def escape_xml(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def content_types_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )


def root_relationships_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def workbook_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        "<sheets><sheet name=\"抓官网结果\" sheetId=\"1\" r:id=\"rId1\"/></sheets>"
        "</workbook>"
    )


def workbook_relationships_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        "</Relationships>"
    )


def styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="2"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><name val="Arial"/></font></fonts>'
        '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        "</styleSheet>"
    )


def app_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>The Eyes of God Lead Console</Application></Properties>"
    )


def core_xml() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        "<dc:creator>The Eyes of God Lead Console</dc:creator>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>'
        "</cp:coreProperties>"
    )
