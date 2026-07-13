from __future__ import annotations

import os
from typing import Any, Callable, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session, sessionmaker

from config.env import load_project_env

load_project_env()

from api.schemas import (
    AIProfileTaskRequest,
    CrawlTaskRequest,
    ImportExistingDataRequest,
    KeywordGroupCreateRequest,
    KeywordGroupUpdateRequest,
    SearchTaskRequest,
)
from database.keyword_groups import (
    create_keyword_group,
    delete_keyword_group,
    list_keyword_groups,
    update_keyword_group,
)
from database.candidate_groups import get_candidate_group_detail, list_candidate_groups
from database.queries import (
    get_company_library_stats,
    get_database_stats,
    get_domain_detail,
    get_profile_source_group,
    list_domains,
    list_profile_source_groups,
    list_raw_ai_profile_results,
    list_raw_crawl_results,
    list_raw_domains,
    list_raw_search_results,
    list_stage_a_companies,
    list_stage_b_companies,
    list_stage_c_companies,
)
from database.session import DEFAULT_DATABASE_URL, create_engine_from_url, create_session_factory
from database.task_batches import get_task_run_detail, list_task_runs, request_task_run_cancel
from database.task_results import build_crawl_task_results_xlsx, build_selected_crawl_results_xlsx, get_task_run_results
from tasks.handlers import run_ai_profile_task, run_crawl_task, run_import_existing_data_task, run_search_task
from tasks.runner import run_task
from tasks.celery_tasks import execute_task as celery_execute_task


TaskHandler = Callable[[dict[str, Any]], dict[str, Any]]
ExecutionMode = Literal["inline", "celery"]


def execution_mode_from_env(env: dict[str, str] | None = None) -> ExecutionMode:
    values = env if env is not None else os.environ
    mode = values.get("TASK_EXECUTION_MODE", "inline").strip().lower()
    if mode == "celery":
        return "celery"
    return "inline"


def create_app(
    handlers: dict[str, TaskHandler] | None = None,
    execution_mode: ExecutionMode = "inline",
    celery_task: Any = celery_execute_task,
    database_url: str | None = None,
    session_factory: sessionmaker[Session] | None = None,
) -> FastAPI:
    app = FastAPI(title="The Eyes of God Lead Backend")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_from_env(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    task_handlers = {
        "search": run_search_task,
        "crawl": run_crawl_task,
        "ai_profile": run_ai_profile_task,
        "import_existing_data": run_import_existing_data_task,
    }
    if handlers:
        task_handlers.update(handlers)
    db_session_factory = session_factory
    if db_session_factory is None:
        resolved_database_url = database_url or os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
        db_session_factory = create_session_factory(create_engine_from_url(resolved_database_url))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/runtime")
    def runtime() -> dict[str, str]:
        return {"task_execution_mode": execution_mode}

    @app.get("/database/stats")
    def database_stats() -> dict[str, int]:
        with db_session_factory() as session:
            return get_database_stats(session)

    @app.get("/company-library/stats")
    def company_library_stats() -> dict[str, int]:
        with db_session_factory() as session:
            return get_company_library_stats(session)

    @app.get("/company-library/stage-a")
    def company_library_stage_a(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
        country: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_stage_a_companies(session, limit=limit, offset=offset, q=q, country=country)

    @app.get("/company-library/stage-b")
    def company_library_stage_b(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
        country: str = "",
        status: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_stage_b_companies(session, limit=limit, offset=offset, q=q, country=country, status=status)

    @app.get("/company-library/stage-c")
    def company_library_stage_c(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
        country: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_stage_c_companies(session, limit=limit, offset=offset, q=q, country=country)

    @app.get("/keyword-groups")
    def keyword_groups(include_inactive: bool = True) -> list[dict[str, Any]]:
        with db_session_factory() as session:
            return list_keyword_groups(session, include_inactive=include_inactive)

    @app.get("/task-runs")
    def task_runs(
        limit: int = 50,
        offset: int = 0,
        task_type: str = "",
        status: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_task_runs(session, limit=limit, offset=offset, task_type=task_type, status=status)

    @app.get("/task-runs/{task_run_id}")
    def task_run_detail(task_run_id: int) -> dict[str, Any]:
        with db_session_factory() as session:
            detail = get_task_run_detail(session, task_run_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Task run not found")
        return detail

    @app.get("/task-runs/{task_run_id}/results")
    def task_run_results(task_run_id: int, limit: int = 200, offset: int = 0) -> dict[str, Any]:
        with db_session_factory() as session:
            detail = get_task_run_results(session, task_run_id, limit=limit, offset=offset)
        if detail is None:
            raise HTTPException(status_code=404, detail="Task run not found")
        return detail

    @app.get("/task-runs/{task_run_id}/results/export.xlsx")
    def export_task_run_results_xlsx(task_run_id: int) -> Response:
        with db_session_factory() as session:
            export = build_crawl_task_results_xlsx(session, task_run_id)
        if export is None:
            raise HTTPException(status_code=404, detail="Task run not found")
        filename, content = export
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/raw-tables/crawl-results/export.xlsx")
    def export_selected_crawl_results_xlsx(ids: str = "") -> Response:
        crawl_result_ids = parse_id_list(ids)
        if not crawl_result_ids:
            raise HTTPException(status_code=400, detail="Select at least one crawl result")
        if len(crawl_result_ids) > 1000:
            raise HTTPException(status_code=400, detail="Cannot export more than 1000 crawl results at once")
        with db_session_factory() as session:
            filename, content = build_selected_crawl_results_xlsx(session, crawl_result_ids)
        return Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/task-runs/{task_run_id}/cancel")
    def cancel_task_run(task_run_id: int) -> dict[str, Any]:
        with db_session_factory() as session:
            try:
                request_task_run_cancel(session, task_run_id)
            except ValueError as error:
                raise HTTPException(status_code=404, detail=str(error)) from error
            session.commit()
            detail = get_task_run_detail(session, task_run_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Task run not found")
        return detail

    @app.get("/candidate-groups")
    def candidate_groups(
        limit: int = 50,
        offset: int = 0,
        status: str = "active",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_candidate_groups(session, limit=limit, offset=offset, status=status)

    @app.get("/candidate-groups/{candidate_group_id}")
    def candidate_group_detail(candidate_group_id: int) -> dict[str, Any]:
        with db_session_factory() as session:
            detail = get_candidate_group_detail(session, candidate_group_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Candidate group not found")
        return detail

    @app.get("/profile-source-groups")
    def profile_source_groups(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_profile_source_groups(session, limit=limit, offset=offset, q=q)

    @app.get("/profile-source-groups/{crawl_task_run_id}")
    def profile_source_group_detail(crawl_task_run_id: int) -> dict[str, Any]:
        with db_session_factory() as session:
            detail = get_profile_source_group(session, crawl_task_run_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Profile source group not found")
        return detail

    @app.post("/keyword-groups")
    def create_keyword_group_endpoint(request: KeywordGroupCreateRequest) -> dict[str, Any]:
        with db_session_factory() as session:
            group = create_keyword_group(session, request.model_dump())
            session.commit()
            return serialize_created_keyword_group(session, group.id)

    @app.put("/keyword-groups/{group_id}")
    def update_keyword_group_endpoint(group_id: int, request: KeywordGroupUpdateRequest) -> dict[str, Any]:
        with db_session_factory() as session:
            try:
                group = update_keyword_group(session, group_id, request.model_dump(exclude_none=True))
            except ValueError as error:
                raise HTTPException(status_code=404, detail=str(error)) from error
            session.commit()
            return group

    @app.delete("/keyword-groups/{group_id}")
    def delete_keyword_group_endpoint(group_id: int) -> dict[str, bool]:
        with db_session_factory() as session:
            deleted = delete_keyword_group(session, group_id)
            session.commit()
            return {"deleted": deleted}

    @app.get("/domains")
    def domains(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
        country: str = "",
        status: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_domains(
                session,
                limit=limit,
                offset=offset,
                q=q,
                country=country,
                status=status,
            )

    @app.get("/domains/{domain_name}")
    def domain_detail(domain_name: str) -> dict[str, Any]:
        with db_session_factory() as session:
            detail = get_domain_detail(session, domain_name)
        if detail is None:
            raise HTTPException(status_code=404, detail="Domain not found")
        return detail

    @app.get("/raw-tables/domains")
    def raw_domains(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
        status: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_raw_domains(session, limit=limit, offset=offset, q=q, status=status)

    @app.get("/raw-tables/search-results")
    def raw_search_results(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
        country: str = "",
        engine: str = "",
        keyword: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_raw_search_results(
                session,
                limit=limit,
                offset=offset,
                q=q,
                country=country,
                engine=engine,
                keyword=keyword,
            )

    @app.get("/raw-tables/crawl-results")
    def raw_crawl_results(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
        country: str = "",
        status: str = "",
        keyword: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_raw_crawl_results(
                session,
                limit=limit,
                offset=offset,
                q=q,
                country=country,
                status=status,
                keyword=keyword,
            )

    @app.get("/raw-tables/ai-profile-results")
    def raw_ai_profile_results(
        limit: int = 50,
        offset: int = 0,
        q: str = "",
        status: str = "",
        priority: str = "",
        model_name: str = "",
        prompt_version: str = "",
    ) -> dict[str, Any]:
        with db_session_factory() as session:
            return list_raw_ai_profile_results(
                session,
                limit=limit,
                offset=offset,
                q=q,
                status=status,
                priority=priority,
                model_name=model_name,
                prompt_version=prompt_version,
            )

    @app.post("/tasks/search")
    def start_search_task(request: SearchTaskRequest) -> dict[str, Any]:
        return submit_task("search", task_handlers["search"], request.model_dump(exclude_none=True))

    @app.post("/tasks/crawl")
    def start_crawl_task(request: CrawlTaskRequest) -> dict[str, Any]:
        return submit_task("crawl", task_handlers["crawl"], request.model_dump(exclude_none=True))

    @app.post("/tasks/import-existing-data")
    def start_import_existing_data_task(request: ImportExistingDataRequest) -> dict[str, Any]:
        return submit_task(
            "import_existing_data",
            task_handlers["import_existing_data"],
            request.model_dump(exclude_none=True),
        )

    @app.post("/tasks/ai-profile")
    def start_ai_profile_task(request: AIProfileTaskRequest) -> dict[str, Any]:
        return submit_task("ai_profile", task_handlers["ai_profile"], request.model_dump(exclude_none=True))

    @app.get("/tasks/{task_id}")
    def get_task_status(task_id: str) -> dict[str, Any]:
        if execution_mode != "celery":
            raise HTTPException(status_code=404, detail="Task status is only available in celery mode")
        result = celery_task.AsyncResult(task_id)
        return {
            "task_id": result.id,
            "status": result.state,
            "result": result.result,
        }

    def submit_task(task_type: str, handler: TaskHandler, params: dict[str, Any]) -> dict[str, Any] | JSONResponse:
        if execution_mode == "celery":
            async_result = celery_task.delay(task_type, params)
            return JSONResponse(
                status_code=202,
                content={
                    "task_id": async_result.id,
                    "task_type": task_type,
                    "status": "queued",
                },
            )
        return execute_inline_task(task_type, handler, params)

    return app


def serialize_created_keyword_group(session: Session, group_id: int) -> dict[str, Any]:
    for group in list_keyword_groups(session):
        if group["id"] == group_id:
            return group
    raise HTTPException(status_code=404, detail="Keyword group not found after create")


def execute_inline_task(task_type: str, handler: TaskHandler, params: dict[str, Any]) -> dict[str, Any]:
    result = run_task(task_type, handler, params)
    return result.to_dict()


def cors_origins_from_env(env: dict[str, str] | None = None) -> list[str]:
    values = env if env is not None else os.environ
    raw_origins = values.get("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def parse_id_list(raw: str) -> list[int]:
    ids: list[int] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        try:
            value = int(text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid crawl result id") from exc
        if value <= 0:
            raise HTTPException(status_code=400, detail="Invalid crawl result id")
        ids.append(value)
    return list(dict.fromkeys(ids))


app = create_app(execution_mode=execution_mode_from_env())
