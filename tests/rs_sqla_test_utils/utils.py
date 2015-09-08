__author__ = 'haleemur'

import re
from redshift_sqlalchemy import dialect


def clean(query):
    return re.sub(r'\s+', ' ', query).strip()


def compile_query(q):
    return str(q.compile(
        dialect=dialect.RedshiftDialect(),
        compile_kwargs={'literal_binds': True})
    )
