from src.util.global_imports import random
from src.core.source import Source
from src.core.server import Server
from src.core.sink import Sink


def setup_model_pcb(env):
    # Create servers, sinks, and sources
    source1 = Source(env, "PCB", (random.expovariate, 1 / 6))

    server1 = Server(env, "Placement", (random.triangular, 3, 5, 4))
    server2 = Server(env, "FinePitchFast", (random.triangular, 8, 10, 9))
    server3 = Server(env, "FinePitchMedium", (random.triangular, 18, 22, 20))
    server4 = Server(env, "FinePitchSlow", (random.triangular, 22, 26, 24))
    server5 = Server(env, "Inspection", (random.uniform, 2, 4))
    server6 = Server(env, "Rework", (random.triangular, 2, 6, 4))

    sink1 = Sink(env, "GoodParts")
    sink2 = Sink(env, "BadParts")

    # Set up connections with routing probabilities for servers
    source1.connect(server1)

    server1.connect(server2)
    server1.connect(server3)
    server1.connect(server4)
    server2.connect(server5)
    server3.connect(server5)
    server4.connect(server5)
    server6.connect(server1)

    server5.connect(sink1, 66)      # 66% probability to route to Sink1
    server5.connect(sink2, 8)       # 8% probability to route to Sink1
    server5.connect(server6, 26)    # 26% probability to route to Rework
