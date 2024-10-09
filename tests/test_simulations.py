import sys
import os
import unittest
import simpy
import pandas as pd
import numpy as np
import logging

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../Laufzeitprognose/src')
))

from util.simulations import run_simulation, run_replications
from core.source import Source
from core.server import Server
from core.sink import Sink
from core.entity import EntityManager
from models.model4_1 import setup_model4_1
from util.global_imports import Stats, RANDOM_SEED, random

class TestSimulationIntegration(unittest.TestCase):
    EXPECTED_NUMBER_CREATED = 15
    EXPECTED_NUMBER_ENTERED_SINK1 = 11
    EXPECTED_SERVER_UTILIZATION = 80.0
    SERVER_UTILIZATION_DELTA = 20.0

    def setUp(self):
        random.seed(RANDOM_SEED)
        logging.basicConfig(level=logging.DEBUG)
        
        Source.reset_all()
        Server.reset_all()
        Sink.reset_all()
        
        EntityManager.destroy_all_entities()
        
        if Stats.all_detailed_stats is not None:
            Stats.all_detailed_stats = []
    
    def test_simulation_end_to_end_model4_1(self):
        """Integrationstest für model4_1 - Überprüfung der wichtigsten Statistiken"""

        simulation_time = 20

        pivot_table = run_simulation(setup_model4_1, minutes=simulation_time)

        self.assertIsNotNone(pivot_table, "Pivot-Tabelle ist None")
        self.assertFalse(pivot_table.empty, "Pivot-Tabelle ist leer")

        logging.debug(f"Pivot Table:\n{pivot_table}")


        entity_stats = pivot_table.loc[('Entity', 'Entity')]
        number_created = entity_stats.loc[('NumberCreated'), 'Value']
        logging.debug(f"Number Created: {number_created}, Expected: {self.EXPECTED_NUMBER_CREATED}")

        self.assertEqual(number_created, self.EXPECTED_NUMBER_CREATED,
                         msg=f"Anzahl erstellter Entitäten {number_created} weicht von erwartetem Wert {self.EXPECTED_NUMBER_CREATED} ab")

        sink_stats = pivot_table.loc[('Sink', 'Sink1')]
        number_entered_sink1 = sink_stats.loc[('NumberEntered'), 'Value']
        logging.debug(f"Number Entered Sink1: {number_entered_sink1}, Expected: {self.EXPECTED_NUMBER_ENTERED_SINK1}")

        self.assertEqual(number_entered_sink1, self.EXPECTED_NUMBER_ENTERED_SINK1,
                         msg=f"Anzahl der in Sink1 angekommenen Entitäten {number_entered_sink1} weicht von der Anzahl erstellter Entitäten {number_created} ab")

        server_stats = pivot_table.loc[('Server', 'Server1')]
        utilization_server1 = server_stats.loc[('ScheduledUtilization'), 'Value']
        logging.debug(f"Server1 Utilization: {utilization_server1}%")
        self.assertAlmostEqual(utilization_server1, self.EXPECTED_SERVER_UTILIZATION, delta=self.SERVER_UTILIZATION_DELTA,
                               msg=f"Server1 Auslastung {utilization_server1}% liegt außerhalb des erwarteten Bereichs")
    
    def test_run_replications_model4_1(self):
        """Integrationstest mit mehreren Replikationen für model4_1"""

        simulation_time = 20
        num_replications = 5

        pivot_table = run_replications(setup_model4_1, minutes=simulation_time, num_replications=num_replications, multiprocessing=False)

        self.assertIsNotNone(pivot_table, "Pivot-Tabelle ist None")
        self.assertFalse(pivot_table.empty, "Pivot-Tabelle ist leer")

        self.assertEqual(len(Stats.all_detailed_stats), num_replications,
                         f"Anzahl der detaillierten Statistiken {len(Stats.all_detailed_stats)} entspricht nicht der Anzahl der Replikationen {num_replications}")

        server_stats = pivot_table.loc[('Server', 'Server1')]
        utilization = server_stats.loc[('ScheduledUtilization'), 'Average']
        self.assertAlmostEqual(utilization, self.EXPECTED_SERVER_UTILIZATION, delta=self.SERVER_UTILIZATION_DELTA,
                               msg=f"Durchschnittliche Server1 Auslastung {utilization}% liegt außerhalb des erwarteten Bereichs")

        sink_stats = pivot_table.loc[('Sink', 'Sink1')]
        avg_time_in_system = sink_stats.loc[('AvgTimeInSystem'), 'Average']
        self.assertGreaterEqual(avg_time_in_system, 0, "Durchschnittliche Zeit im System für Sink1 ist negativ")

if __name__ == '__main__':
    unittest.main()
