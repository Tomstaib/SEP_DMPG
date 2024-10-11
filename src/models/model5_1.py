from src.util.global_imports import random
from src.core.source import Source
from src.core.server import Server
from src.core.sink import Sink
from src.util.simulations import run_simulation, run_replications
from src.util.visualization import visualize_system
from src.core.model import Model


def setup_model5_1(env):
    source = Source(env, "Source", (random.expovariate, 1 / 6))
    placement = Server(env, "Placement", (random.triangular, 3, 4, 5))
    inspection = Server(env, "Inspection", (random.uniform, 2, 4))
    good_parts = Sink(env, "Goodparts")
    bad_parts = Sink(env, "Badparts")

    source.connect(placement)
    placement.connect(inspection)
    inspection.connect(good_parts, 92)
    inspection.connect(bad_parts, 8)


def main():
    # 1200 hours
    run_simulation(model=setup_model5_1, minutes=72000)
    visualize_system()

    run_replications(model=setup_model5_1, minutes=7200, num_replications=10, multiprocessing=True)

    print(Model().get_components())


if __name__ == '__main__':
    main()
