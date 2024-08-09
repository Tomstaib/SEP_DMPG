"""
The core directory contains essential components for the simulation framework.

    entity.py: This module defines the Entity class, which represents entities moving through the simulation system. Entities can have attributes and states that evolve over time as they interact with other components of the simulation. The Entity class is responsible for managing the lifecycle of entities, including their creation and, optionally, destruction times. Additionally, the EntityManager class tracks and manages collections of Entity instances, ensuring efficient management within the simulation framework.

    queue_orders.py: This module implements the QueueOrders class, which manages the order queue within the simulation. It handles the arrival and departure of entities from queues, maintaining the order in which entities are processed.

    server.py: The Server class defined in this module simulates processing stations or servers within the simulation. It manages the processing of entities, including service times, resource utilization, and potential machine breakdowns. The class includes methods for processing entities, maintaining queues, handling connections to other components based on specified probabilities, and logging simulation events. Additionally, it provides a string representation of server objects.

    sink.py: sink.py: This module implements the Sink class, which serves as the final destination for entities within the simulation. Upon completing their journey through the system, entities arrive at the sink, where relevant statistics regarding their processing are collected. The Sink class tracks important metrics such as the total number of entities processed, the time entities spent in the system, and the maximum and minimum durations of entity processing. Additionally, the Sink class offers functionality to reset its statistics and provides a method to process entities, updating the pertinent statistics and logging processing events.

    source.py: The Source class serves as the initial point for entity generation within the simulation framework. It orchestrates the creation of entities based on predefined arrival patterns and directs them into the system for further processing. The class encapsulates essential functionalities for managing entity generation, routing, and interaction with subsequent components in the simulation.
    """
