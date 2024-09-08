"""
The util directory hosts utility modules and functions that support the simulation framework.

    date_time.py: This module offers utilities for managing date and time-related functionalities within the simulation environment. It facilitates tasks like computing time intervals and formatting timestamps to suit the simulation's requirements. The core functionalities include setting the initial date and time, retrieving the current date and time, mapping time components to different units (such as seconds, minutes, or hours), and calculating delta times relative to the initial date. By encapsulating these operations, the module enhances the simulation framework's flexibility and adaptability to various time-based scenarios.

    global_imports.py: The code sets up configurations for a simulation framework. It imports necessary modules, defines custom logging levels, initializes a random seed, and configures logging. It also defines a class Stats as a Singleton to store detailed statistics for simulation runs.

    helper.py: The Helper module serves as a repository for diverse helper functions and utilities crucial for common tasks within the simulation framework. It encapsulates functionalities ranging from generating random numbers to conducting statistical calculations, enhancing the overall efficiency and versatility of the simulation process. This module integrates essential components like probability validation, logging customization, value rounding, and distribution parameter retrieval, facilitating seamless operation and management of simulation entities and processes.

    simulations.py: This module serves as a repository for predefined simulation scenarios or experiments within the simulation framework. Here, users can access ready-to-use simulation setups designed to leverage the core components of the framework. These simulations are crafted to cater to various testing or analysis needs, offering a convenient platform for researchers and practitioners to explore and experiment with different system configurations and parameters.

    singleton.py: The Singleton module provides an implementation of the Singleton design pattern, ensuring that specific classes within the simulation have only one instance throughout the runtime. This is achieved using a custom metaclass Singleton, which controls the instantiation process, ensuring that only a single instance of the class is created and reused whenever needed.

    visualization.py: This module hosts utilities for creating visual representations of simulation results or system dynamics.  It has tools to create different kinds visualizations, ranging from scatterplots and histograms to boxplots and violin plots.
"""
