CREATE TABLE Modell (
                        modell_id INTEGER PRIMARY KEY,
                        name VARCHAR(255)
);

CREATE TABLE Szenario (
                          scenario_id INTEGER PRIMARY KEY,
                          scenario_name VARCHAR(255),
                          replication INTEGER,
                          status VARCHAR(255),
                          Seed INTEGER,
                          modell_id INTEGER,
                          FOREIGN KEY (modell_id) REFERENCES Modell(modell_id)
);

CREATE TABLE Source (
                         source_id INTEGER PRIMARY KEY,
                         name VARCHAR(255),
                         creation_time_dwp TIME(7),
                         entities_created INTEGER,
                         number_exited INTEGER,
                         scenario_id INTEGER,
                         FOREIGN KEY (scenario_id) REFERENCES Szenario(scenario_id),
);

CREATE TABLE Sink (
                      sink_id INTEGER PRIMARY KEY,
                      name VARCHAR(255),
                      entities_processed INTEGER,
                      total_time_in_system TIME(7),
                      min_time_in_system TIME(7),
                      number_entered INTEGER,
                      scenario_id INTEGER,
                      Szenariomodell_id INTEGER,
                      FOREIGN KEY (scenario_id) REFERENCES Szenario(scenario_id),
                      FOREIGN KEY (Szenariomodell_id) REFERENCES Modell(modell_id)
);

CREATE TABLE Server (
                        server_id INTEGER PRIMARY KEY,
                        name VARCHAR(255),
                        processing_time_dwp TIME(7),
                        time_between_maschine_breakdowns TIME(7),
                        maschine_breakdown_duration TIME(7),
                        entities_processed INTEGER,
                        total_processing_time TIME(7),
                        number_entered INTEGER,
                        number_exited INTEGER,
                        units_allocated INTEGER,
                        units_utilized INTEGER,
                        start_processing_time TIMESTAMP(7),
                        total_downtime TIME(7),
                        number_downtime INTEGER,
                        uptime Time,
                        total_uptime TIME(7),
                        number_uptimes INTEGER,
                        queue_order_id INTEGER,
                        scenario_id INTEGER,
                        FOREIGN KEY (queue_order_id) REFERENCES QueueOrders(queue_order_id),
                        FOREIGN KEY (scenario_id) REFERENCES Szenario(scenario_id),
);

CREATE TABLE Path (
                      path_id INTEGER PRIMARY KEY,
                      name VARCHAR(255),
                      length INTEGER,
                      scenario_id INTEGER,
                      FOREIGN KEY (scenario_id) REFERENCES Szenario(scenario_id),
);

CREATE TABLE QueueOrder (
                             queue_order_id INTEGER PRIMARY KEY,
                             procedure VARCHAR(255)
);

CREATE TABLE Entity (
                        entity_id INTEGER PRIMARY KEY,
                        name VARCHAR(255),
                        creation_time TIME(7),
                        destruction_time TIME(7),
                        source_id INTEGER,
                        FOREIGN KEY (source_id) REFERENCES Sources(source_id),
);
