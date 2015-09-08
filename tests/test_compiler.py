from sqlalchemy import func, select
from redshift_sqlalchemy.dialect import RedshiftDialect


def test_func_now():
    dialect = RedshiftDialect()
    s = select([func.NOW().label("time")])
    compiled = s.compile(dialect=dialect)
    assert str(compiled) == "SELECT SYSDATE AS time"
