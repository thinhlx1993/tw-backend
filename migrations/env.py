from __future__ import with_statement
from alembic import context
import logging
from logging.config import fileConfig
from src import app
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool, MetaData, Table, ForeignKeyConstraint, Index

load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from flask import current_app
config.set_main_option( 
    'sqlalchemy.url', current_app.config.get(
        'SQLALCHEMY_DATABASE_URI').replace('%', '%%'))
# base migrations on this schema
prototype_schema = current_app.config['PROTOTYPE_SCHEMA']
# table names that belong in 'public', not tenant schemas
public_schema_tables = current_app.config['PUBLIC_SCHEMA_TABLES']
# query that returns a list of tenant schemas
get_schemas_query = current_app.config['GET_SCHEMAS_QUERY']
target_metadata = current_app.extensions['migrate'].db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def include_schemas(names):
    # produce an include object function that filters on the given schemas
    def include_object(object, name, type_, reflected, compare_to):
        if type_ == "table":
            return object.schema in names
        return True
    return include_object


def lookup_correct_schema(name):
    if name in public_schema_tables:
        return 'public'
    else:
        return prototype_schema


def _get_table_key(name, schema):
    if schema is None:
        return name
    else:
        return schema + "." + name


def tometadata(table, metadata, schema):
    key = _get_table_key(table.name, schema)
    if key in metadata.tables:
        return metadata.tables[key]

    args = []
    for c in table.columns:
        args.append(c.copy(schema=schema))
    new_table = Table(
        table.name, metadata, schema=schema,
        *args, **table.kwargs
    )
    for c in table.constraints:
        if isinstance(c, ForeignKeyConstraint):
            constraint_schema = lookup_correct_schema(
                c.elements[0].column.table.name)
        else:
            constraint_schema = schema
        new_table.append_constraint(
            c.copy(schema=constraint_schema, target_table=new_table))
        
    for index in table.indexes:
        # skip indexes that would be generated
        # by the 'index' flag on Column
        if len(index.columns) == 1 and \
                list(index.columns)[0].index:
            continue
        Index(index.name,
              unique=index.unique,
              *[new_table.c[col] for col in index.columns.keys()],
              **index.kwargs)
    return table._schema_item_copy(new_table)


meta = current_app.extensions['migrate'].db.metadata
meta_schemax = MetaData()
for table in meta.tables.values():
    tometadata(table, meta_schemax, lookup_correct_schema(table.name))
target_metadata = meta_schemax

# target_metadata = current_app.extensions['migrate'].db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from alembic.operations import ops

    def process_revision_directives(context, revision, directives):
        script = directives[0]

        # process both "def upgrade()", "def downgrade()"
        for directive in (script.upgrade_ops_list, script.downgrade_ops_list):

            # make a set of tables that are being dropped within
            # the migration function
            tables_dropped = set()
            for op in directive:
                if isinstance(op, ops.DropTableOp):
                    tables_dropped.add((op.table_name, op.schema))

            # now rewrite the list of "ops" such that DropIndexOp
            # is removed for those tables.   Needs a recursive function.
            directive = list(
                _filter_drop_indexes(directive, tables_dropped)
            )
    
    def _filter_drop_indexes(directives, tables_dropped):
        # given a set of (tablename, schemaname) to be dropped, filter
        # out DropIndexOp from the list of directives and yield the result.

        for directive in directives:
            # ModifyTableOps is a container of ALTER TABLE types of
            # commands.  process those in place recursively.
            if isinstance(directive, ops.ModifyTableOps) and \
                    (directive.table_name, directive.schema) in tables_dropped:
                directive = list(
                    _filter_drop_indexes(directive.ops, tables_dropped)
                )

                # if we emptied out the directives, then skip the
                # container altogether.
                if not directive:
                    continue
            elif isinstance(directive, ops.DropIndexOp) and \
                    (directive.table_name, directive.schema) in tables_dropped:
                # we found a target DropIndexOp.   keep looping
                continue

            # otherwise if not filtered, yield out the directive
            yield directive


    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool)

    schemas = set([prototype_schema, None])

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
        include_schemas=True,  # schemas,
        include_object=include_schemas([None, prototype_schema, 'public'])
    )

    try:
        # get the schema names
        tenant_schemas = [row[0] for row in connection.execute(get_schemas_query)]
        app.logger.info(get_schemas_query)
        app.logger.info(tenant_schemas)
        for schema in tenant_schemas:
            app.logger.info(schema)
            app.logger.info(get_schemas_query)
            connection.execute(
                'set search_path to "{}", public'.format(schema))
            with context.begin_transaction():
                context.run_migrations()
    except Exception as err:
        print(str(err))
    finally:
        connection.close()


    # with connectable.connect() as connection:
    #     context.configure(
    #         connection=connection,
    #         target_metadata=target_metadata,
    #         process_revision_directives=process_revision_directives,
    #         **current_app.extensions['migrate'].configure_args
    #     )

    #     with context.begin_transaction():
    #         context.run_migrations()


if context.is_offline_mode():
    print ("Can't run migrations offline")
    # run_migrations_offline()
else:
    run_migrations_online()
