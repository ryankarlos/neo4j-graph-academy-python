Graph Academy Course: Building Neo4j Applications with Python

This repository is a copy of https://github.com/neo4j-graphacademy/app-python which
accompanies the [Graph Academy Course](https://graphacademy.neo4j.com/courses/app-python/)
My solution attempts to the exercises have been included in the respective scripts. The descriptions below
are copied from the Neo4j Graph Academy site. This is used in preparation for the Neo4j Professional Certification.

## Install requirements 

create a virtual environment named sandbox and active. Then pip install requirements and 
neo4j dependency for accessing the driver.


```
python -m venv sandbox
source sandbox/bin/activate
pip install -r requirements.txt
pip install neo4j
```

## Neo4j Driver
To connect to and query Neo4j from within a Python application, you use the Neo4j Python Driver.
The Neo4j Python Driver is one of five officially supported drivers, the others are Java, JavaScript, .NET, and Go.
There are also a wide range of Community Drivers available for other languages including PHP and Ruby.[1][3][2]

You should create a single instance of the Driver in your application per Neo4j cluster or DBMS, which can then be
shared across your application.

Each driver instance will connect to one DBMS, or Neo4j cluster, depending on the value provided in the connection string.
The neo4j package exports a GraphDatabase object. This object provides a driver() function for creating a new 
driver instance.

The `driver()` function requires one mandatory parameter, a connection string for the Neo4j cluster or DBMS - for 
example `neo4j://localhost:7687` or `neo4j+s://dbhash.databases.neo4j.io:7687`.

Additionally, you will also pass a named parameter auth to represent the Neo4j user credentials. You can provide 
basic username/password authentication by passing the username and password as a tuple.

You can verify that the connection details used during driver instantiation are correct by calling the 
`verifyConnectivity()` function. This function will raise a `Neo4jException` with a code property of 
`Neo.ClientError.Security.Unauthorized` if a connection could not be made.
If the connection has been successfully verified, the function will return an instance of the driver.[1][3][2]

```python
from neo4j import GraphDatabase

def init_driver(uri, username, password):
    # Create an instance of the driver
    current_app.driver = GraphDatabase.driver(uri, auth=(username, password))

    # Verify Connectivity
    current_app.driver.verify_connectivity()

    return current_app.driver
```

## Sessions

Through the Driver, we open **Sessions**. It is important to remember that sessions are not the same as 
database connections. When the Driver connects to the database, it opens up multiple TCP connections 
that can be borrowed by the session. A query may be sent over multiple connections, and results 
may be received by the driver over multiple connections.
Instead, sessions should be considered a client-side abstraction for grouping units of work, which also 
handle the underlying connections. The connections themselves are managed internally by the driver and are 
not directly exposed to the application.[1]

To open a new session, call the `session()` method on the driver.This session method takes an optional configuration 
argument, which can be used to set the database to run any queries against in a multi-database setup, and the 
default access mode for any queries run within the transaction.

Through a Session, we can run one or more **Transactions**: *Auto-commit Transactions*, *Read Transactions*, 
*Write Transactions*.


* **AutoCommit**:Auto-commit transactions are a single unit of work that are immediately executed against the 
  DBMS and acknowledged immediately. You can run an auto-commit transaction by calling the `run()` method on 
  the session object, passing in a Cypher statement as a string and optionally an object containing a set of parameters.
  In the event that there are any transient errors when running a query, the driver will not attempt to retry a 
  query when using session.run(). For this reason, these should only be used for one-off queries and shouldn’t 
  be used in production.[1][3]
  
```
  session.run(
    "MATCH (p:Person {name: $name}) RETURN p", # Query
    name="Tom Hanks" # Named parameters referenced
)                    # in Cypher by prefixing with a $
```

* **Read Transactions**: When you intend to read data from Neo4j, you should execute a Read Transaction. 
  In a clustered environment (including Neo4j Aura), read queries are distributed across the cluster. 
  The session provides a `read_transaction()` function, which expects a single parameter, a function that 
  represents the unit of work. The first argument passed to the function will be a transaction object, on which 
  you can call the `run()` function to execute a Cypher statement. As with the `session.run` example above, the 
  first argument for the `run()` function should be a Cypher statement, and any parameters in the Cypher statement 
  should be passed as named parameters. You do not need to explicitly commit a read transaction.[1][3]
  

```
# Define a Unit of work to run within a Transaction (`tx`)
def get_movies(tx, title):
    return tx.run("""
        MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
        WHERE m.title = $title // (1)
        RETURN p.name AS name
        LIMIT 10
    """, title=title)

# Execute get_movies within a Read Transaction
session.read_transaction(get_movies,
    title="Arthur" # (2)
)
```

* **Write Transactions**: If you intend to write data to the database, you should execute a Write Transaction. In clustered environments, 
  write queries are sent exclusively to the leader of the cluster. The leader of the cluster is then responsible 
  for processing the query and synchronising the transaction across the followers and read-replica servers in 
  the cluster. The process is identical to running a Read Transaction. If anything goes wrong within of the unit of 
  work or there is a problem on Neo4j’s side, the transaction will be automatically rolled back and the database will remain in its previous state. If the unit of work succeeds, 
  the transaction will be automatically committed.[1][3]

```
# Call tx.run() to execute the query to create a Person node
def create_person(tx, name):
    return tx.run(
        "CREATE (p:Person {name: $name})",
        name=name
    )


# Execute the `create_person` "unit of work" within a write transaction
session.write_transaction(create_person, name="Michael")

```


It is also possible to explicitly create a transaction object by calling the `begin_transaction()` function on 
the session. This returns a Transaction object identical to the one passed in to the unit of work function when calling 
`read_transaction()` or `write_transaction()`. This method differs from the read_transaction and `write_transaction()` 
functions, in that the transaction will have to be manually committed or rolled back depending on the outcome of 
the unit of work. You can commit a transaction by calling the `tx.commit()` function, or roll back the 
transaction by calling `tx.rollback()`.[1][3]

```
try:
    # Run a query
    tx.run(query, **params)

    # Commit the transaction
    tx.commit()
except:
    # If something goes wrong in the try block,
    # then rollback the transaction
    tx.rollback()
```

Once you are finished with your session, you call `session.close()` to release any database connections 
held by that session.[1][3]

The following code shows a full working example of creating a `Person` node in the `customers` database.
This defines a function that accepts a name parameter, then executes a write transaction to create a `:Person` node 
in the people database.


```
def create_person_work(tx, name):
    return tx.run("CREATE (p:Person {name: $name}) RETURN p",
        name=name).single()

def create_person(name):
    # Create a Session for the `people` database
    session = driver.session(database="people")

    # Create a node within a write transaction
    record = session.write_transaction(create_person_work,
                                        name=name)

    # Get the `p` value from the first record
    person = record["p"]

    # Close the session
    session.close()

    # Return the property from the node
    return person["name"]
```

## Processing Results 

Query results are typically consumed as a stream of records. The drivers provide a way to iterate through that stream.
When accessing a record, either within a loop, list comprehension or within a single record, you can use the [] bracket syntax.
The following example extracts the p value from each record in the result buffer.
If you wish to preview a result without consuming it, you can use the peek method.This can be used to preview the
first record in the result without removing it from the buffer.[1]

```
# Check the first record without consuming it
peek = result.peek()
print(peek)
```

To get the keys for each record in the result, you can call the `keys()` method.[1]

```
# Get all keys available in the result
print(result.keys()) # ["p", "roles"]
```

If you only expect a single record, you can use the single() method on the result to return the first record.
If more than one record is available from the result then a warning will be generated, but the first result will 
still be returned. If no results are available, then the method call will return None.[1]

```
def get_actors_single(tx, movie):
    result = tx.run("""
        MATCH (p:Person)-[:ACTED_IN]->(:Movie {title: $title})
        RETURN p
    """, title=movie)

    return result.single()

```

If you wish to extract a single value from the remaining list of results, you can use the `value()` method.
The first parameter is a key or index of the field to return for each remaining record, and returns a
list of single values. You can provide a default value to be used as the second parameter, 
if the value is None or unavailable.[1]

```
def get_actors_values(tx, movie):
    result = tx.run("""
        MATCH (p:Person)-[r:ACTED_IN]->(m:Movie {title: $title})
        RETURN p.name AS name, m.title AS title, r.roles AS roles
    """, title=movie)

    return result.value("name", False)
    # Returns the `name` value, or False if unavailable

```

If you need to extract more than item from each record, you can use the `values()` method. The method expects one 
parameter per item requested from the RETURN statement of the query. A list will be returned, with each entry containing 
values representing name, title, and roles.[1]

```
def get_actors_values(tx, movie):
    result = tx.run("""
        MATCH (p:Person)-[r:ACTED_IN]->(m:Movie {title: $title})
        RETURN p.name AS name, m.title AS title, r.roles AS roles
    """, title=movie)

    return result.values("name", "title", "roles")

```


The `consume()` method will consume the remainder of the results and return a Result Summary. The Result Summary 
contains a information about the server, the query, execution times and a counters object which provide statistics 
about the query. The counters object can be used to retrieve the number of nodes, relationships, properties or 
labels that were affected during a write transaction.[1]


```
def get_actors_consume(tx, name):
    result = tx.run("""
        MERGE (p:Person {name: $name})
        RETURN p
    """, name=name)

    info = result.consume()
    
    # The time it took for the server to have the result available. (milliseconds)
    print(info.result_available_after)

    # The time it took for the server to consume the result. (milliseconds)
    print(info.result_consumed_after)
    
    print("{0} nodes created".format(info.counters.nodes_created))
    print("{0} properties set".format(info.counters.properties_set))

```

The result object acts as a buffer for an iterable list of records and provides a number of options for accessing 
those records. When accessing a record, either within a loop, list comprehension or within a single record, 
you can use the `[]` bracket syntax. The following example extracts the p value from each record in the result buffer. Once a result is 
consumed, it is removed from the buffer.[1]

```
for record in result:
    print(record["p"]) # Person Node
```
You can also access a value using its index, as it relates to the value contained in the keys array:

```
# Get all keys available in the result
print(result.keys()) # ["p", "roles"]
```


## Handling Driver Errors

When executing a Cypher statement, certain exceptions and error cases may arise. One error could be a transient 
error that may be resolved if retried, for example a problem connecting to the database instance. Another type 
of error could be something more permanent, for example a Syntax Error or a Constraint Error.[1][4]

In the Neo4j Python Driver, an error extending the `neo4j.exceptions.Neo4jError` class will be thrown.
Please refer to https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.exceptions.Neo4jError for 
the list of exceptions.
You can catch the specific exception above within a try/catch block, or catch all Neo4jErrors instances [1][4]:

```
# Import the Exception classes from neo4j.exceptions
from neo4j.exceptions import Neo4jError, ConstraintError

# Attempt a query
try:
    tx.run(cypher, params)
except ConstraintError as err:
    print("Handle constaint violation")
    print(err.code) # (1)
    print(err.message) # (2)
except Neo4jError as err:
    print("Handle generic Neo4j Error")
    print(err.code) # (1)
    print(err.message) # (2)

```

Exceptions contain code (1) and message (2) properties to help you further diagnose the problem.

The Neo4jError includes a code property, which provides higher-level information about the query. 
Each status code follows the same format (`Neo.[Classification].[Category].[Title]`), and includes four parts [1][4]:

* Every Neo4j Error code is prefixed with Neo.
* The Classification provides a high-level classification of the error - for example, a client-side error or 
  an error with the database.
* The Category provides a higher-level category for the error - for example, a problem with clustering, a 
  procedure or the database schema.
* The Title provides specific information about the error that has occurred.


## References

1. [Graph Academy Building Neo4j Applications with Python Course](https://graphacademy.neo4j.com/courses/app-python/)
2. Original repository for the course: https://github.com/neo4j-graphacademy/app-python
3. [Neo4j Driver Session API Docs](https://neo4j.com/docs/python-manual/current/session-api/)
4. [Status Codes Documentation](https://neo4j.com/docs/status-codes/current/)
