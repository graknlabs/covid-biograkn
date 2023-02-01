from typedb.client import *


def initialise_database(client, database, force=False):
    if client.databases().contains(database):
        if force:
            client.databases().get(database).delete()
        else:
            raise ValueError("database {} already exists, use --force True to overwrite")
    client.databases().create(database)
    session = client.session(database, SessionType.SCHEMA)
    print('.....')
    print('Inserting schema...')
    print('.....')
    with open("Schema/schema.tql", "r") as typeql_file:
        schema = typeql_file.read()
    with session.transaction(TransactionType.WRITE) as write_transaction:
        write_transaction.query().define(schema)
        write_transaction.commit()
    print('.....')
    print('Successfully committed schema!')
    print('.....')
    session.close()
