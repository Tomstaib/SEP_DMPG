from src.util.global_imports import random
from src.core.source import RL_Source
from src.core.server import Server
from src.core.sink import Sink


def setup_model_pcb(env, params):
    # Create servers, sinks, and sources

    source1 = RL_Source(env, "Source", params)
    server1 = Server(env, "Server", (random.triangular, 8, 10, 12))
    sink1 = Sink(env, "Sink")

    source1.connect(server1)

    server1.connect(sink1)
