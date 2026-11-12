import pytest
from src.sql_engine import get_named_queries, run_select_query


def test_analytical_queries_execute():
    queries = get_named_queries()
    assert len(queries) == 3
    for q in queries.values():
        df = run_select_query(q)
        assert len(df) > 0


def test_sql_injection_write_blocked():
    with pytest.raises(ValueError):
        run_select_query("DROP TABLE wafers;")
