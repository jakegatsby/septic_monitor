from diagrams import Diagram
from diagrams.programming.flowchart import Database
from diagrams.programming.language import Python
from diagrams.programming.framework import Vue

with Diagram(show=False, filename="topology"):
    Vue("Dashboard") >> Python("FastAPI") >> Python("Storage API") >> Database("TimescaleDB")
