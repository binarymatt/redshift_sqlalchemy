__version__ = '0.5.1a'

from sqlalchemy.dialects import registry

registry.register("redshift", "redshift_sqlalchemy.dialect", "RedshiftDialect")
registry.register("redshift+psycopg2", "redshift_sqlalchemy.dialect", "RedshiftDialect")
