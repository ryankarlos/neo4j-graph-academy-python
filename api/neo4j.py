from flask import Flask, current_app

# tag::import[]
from neo4j import GraphDatabase
# end::import[]


# tag::initDriver[]
def init_driver(uri, username, password):
    """
    Initiate the Neo4j Driver.
    Verifies that the connection details are correct before returning the
    newly created driver instance. If the connection cannot be made for any
    reason, an Exception will be thrown.
    """
    current_app.driver = GraphDatabase.driver(uri, auth=(username, password))
    current_app.driver.verify_connectivity()
    return current_app.driver
# end::initDriver[]



# tag::getDriver[]
def get_driver():
    """
    Get the instance of the Neo4j Driver created in the `initDriver` function
    """
    return current_app.driver

# end::getDriver[]


# tag::closeDriver[]
def close_driver():
    """
    close the driver and all remaining open sessions
    """
    if current_app.driver != None:
        current_app.driver.close()
        current_app.driver = None

        return current_app.driver
# end::closeDriver[]
