import sqlalchemy.types as sqltypes

from sqlalchemy.dialects.postgresql.base import ENUM
from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
from sqlalchemy.engine import reflection
from sqlalchemy import util, exc
from sqlalchemy.types import VARCHAR, NullType
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable, ClauseElement
from sqlalchemy.sql.expression import BindParameter


class RedshiftDialect(PGDialect_psycopg2):
    name = 'redshift'

    def initialize(self, connection):
        #super(PGDialect, self).initialize(connection)
        #can't call super as that has the error
        #we also need t to replicate DefaultDialect's functionality since
        # we are not utilizing the inheritence of this correctly.
        try:
            self.server_version_info = \
                            self._get_server_version_info(connection)
        except NotImplementedError:
            self.server_version_info = None
        try:
            self.default_schema_name = \
                            self._get_default_schema_name(connection)
        except NotImplementedError:
            self.default_schema_name = None

        try:
            self.default_isolation_level = \
                        self.get_isolation_level(connection.connection)
        except NotImplementedError:
            self.default_isolation_level = None

        self.returns_unicode_strings = self._check_unicode_returns(connection)

        if self.description_encoding is not None and \
            self._check_unicode_description(connection):
            self._description_decoder = self.description_encoding = None

        self.do_rollback(connection.connection)


        self.implicit_returning = self.server_version_info > (8, 2) and \
                            self.__dict__.get('implicit_returning', True)
        self.supports_native_enum = self.server_version_info >= (8, 3)
        if not self.supports_native_enum:
            self.colspecs = self.colspecs.copy()
            # pop base Enum type
            self.colspecs.pop(sqltypes.Enum, None)
            # psycopg2, others may have placed ENUM here as well
            self.colspecs.pop(ENUM, None)

        # http://www.postgresql.org/docs/9.3/static/release-9-2.html#AEN116689
        self.supports_smallserial = self.server_version_info >= (9, 2)

        #PGDialect has
        #self._backslash_escapes = connection.scalar(
        #                            "show standard_conforming_strings"
        #                            ) == 'off'
        # which fails for us so we set it like
        self._backslash_escapes = False
        #we also can't utilize anything in PGDialect_psycopg2 so
        # we don't have to call it or reimplement it


    @reflection.cache
    def get_pk_constraint(self, connection, table_name, schema=None, **kw):
        """
        Constraints in redshift are informational only. This allows reflection to work
        """
        return {'constrained_columns': [], 'name': ''}

    @reflection.cache
    def get_indexes(self, connection, table_name, schema, **kw):
        """
        Redshift does not use traditional indexes.
        """
        return []

    #def set_isolation_level(self, connection, level):
    #    from psycopg2 import extensions
    #    connection.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    @util.memoized_property
    def _isolation_lookup(self):
        extensions = __import__('psycopg2.extensions').extensions
        return {
            'READ COMMITTED': extensions.ISOLATION_LEVEL_READ_COMMITTED,
            'READ UNCOMMITTED': extensions.ISOLATION_LEVEL_READ_UNCOMMITTED,
            'REPEATABLE READ': extensions.ISOLATION_LEVEL_REPEATABLE_READ,
            'SERIALIZABLE': extensions.ISOLATION_LEVEL_SERIALIZABLE,
            'AUTOCOMMIT': extensions.ISOLATION_LEVEL_AUTOCOMMIT
        }

    def set_isolation_level(self, connection, level):
        try:
            level = self._isolation_lookup[level.replace('_', ' ')]
        except KeyError:
            raise exc.ArgumentError(
                "Invalid value '%s' for isolation_level. "
                "Valid isolation levels for %s are %s" %
                (level, self.name, ", ".join(self._isolation_lookup))
            )

        connection.set_isolation_level(level)

    def _get_column_info(self, name, format_type, default,
                         notnull, domains, enums, schema):
        column_info = super(RedshiftDialect, self)._get_column_info(name, format_type, default, notnull, domains, enums, schema)
        if isinstance(column_info['type'], VARCHAR) and column_info['type'].length is None:
            column_info['type'] = NullType()
        return column_info


class UnloadFromSelect(Executable, ClauseElement):
    ''' Prepares a RedShift unload statement to drop a query to Amazon S3
    http://docs.aws.amazon.com/redshift/latest/dg/r_UNLOAD_command_examples.html
    '''
    def __init__(self, select, bucket, access_key, secret_key):
        ''' Initializes an UnloadFromSelect instance

        Args:
            self: An instance of UnloadFromSelect
            select: The select statement to be unloaded
            bucket: The Amazon S3 bucket where the result will be stored
            access_key: The Amazon Access Key ID
            secret_key: The Amazon Secret Access Key
        '''
        self.select = select
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key


@compiles(UnloadFromSelect)
def visit_unload_from_select(element, compiler, **kw):
    ''' Returns the actual sql query for the UnloadFromSelect class
    '''
    return "unload ('%(query)s') to '%(bucket)s' credentials 'aws_access_key_id=%(access_key)s;aws_secret_access_key=%(secret_key)s' delimiter ',' addquotes allowoverwrite" % {
        'query': compiler.process(element.select, unload_select=True, literal_binds=True),
        'bucket': element.bucket,
        'access_key': element.access_key,
        'secret_key': element.secret_key,
    }

@compiles(BindParameter)
def visit_bindparam(bindparam, compiler, **kw):
    #print bindparam
    res = compiler.visit_bindparam(bindparam, **kw)
    if 'unload_select' in kw:
        #process param and return
        res = res.replace("'", "\\'")
        res = res.replace('%', '%%')
        return res
    else:
        return res
