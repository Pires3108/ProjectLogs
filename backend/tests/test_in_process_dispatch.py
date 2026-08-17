from threading import Event

from app.jobs import dispatch


def test_in_process_dispatch_submits_job_without_blocking(monkeypatch) -> None:
    called = Event()
    monkeypatch.setattr(dispatch.process_job, "run", lambda job_id: called.set())

    dispatch.dispatch_in_process("synthetic-job")

    assert called.wait(timeout=2)
