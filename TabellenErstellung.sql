CREATE TABLE Model (
                       ModelID INTEGER PRIMARY KEY,
                       ModelName VARCHAR(255),
                       UserID INTEGER,
                       FOREIGN KEY (UserID) REFERENCES HSUser(UserID)
);

CREATE TABLE HSUser  (
                      UserID INTEGER PRIMARY KEY,
                      UserName VARCHAR(255),
                      NumberStartedSimulations INTEGER
);

CREATE TABLE Scenario (
                          ScenarioID INTEGER PRIMARY KEY,
                          ScenarioName VARCHAR(255),
                          NumberInSystem INTEGER,
                          AvgTimeInSystem FLOAT,
                          MaxTimeInSystem FLOAT,
                          MinTimeInSystem FLOAT,
                          NumberCreated INTEGER,
                          NumberDestroyed INTEGER,
                          Seed INTEGER
);

CREATE TABLE Model_Scenario (
                                ModelID INTEGER,
                                ScenarioID INTEGER,
                                PRIMARY KEY (ModelID, ScenarioID),
                                FOREIGN KEY (ModelID) REFERENCES Model(ModelID),
                                FOREIGN KEY (ScenarioID) REFERENCES Scenario(ScenarioID)
);

CREATE TABLE Source (
                        SourceID INTEGER,
                        ScenarioID INTEGER,
                        SourceName VARCHAR(255),
                        NumberCreated INTEGER,
                        NumberExited INTEGER,
                        CreationTimeDistributionWithParameters FLOAT,
                        PRIMARY KEY (SourceID, ScenarioID),
                        FOREIGN KEY (ScenarioID) REFERENCES Scenario(ScenarioID)
);

CREATE TABLE Server (
                        ServerID INTEGER,
                        ScenarioID INTEGER,
                        ServerName VARCHAR(255),
                        ScheduledUtilization FLOAT,
                        UnitsUtilized INTEGER,
                        AvgTimeProcessing FLOAT,
                        TotalTimeProcessing FLOAT,
                        NumberEntered INTEGER,
                        NumberExited INTEGER,
                        NumberDowntimes INTEGER,
                        TotalDowntime FLOAT,
                        QueueOrder VARCHAR(4),
                        ProcessingTimeDistributionWithParameters FLOAT,
                        TimeBetweenMaschineBreakdowns FLOAT,
                        MaschineBreakdownDuration FLOAT,
                        EntitiesProcessed INTEGER,
                        TotalUptime FLOAT,
                        NumberUptimes INTEGER,
                        PRIMARY KEY (ServerID, ScenarioID),
                        FOREIGN KEY (ScenarioID) REFERENCES Scenario(ScenarioID)
);

CREATE TABLE Sink (
                      SinkID INTEGER,
                      ScenarioID INTEGER,
                      SinkName VARCHAR(255),
                      EntitiesProcessed INTEGER,
                      TotalTimeInSystem FLOAT,
                      NumberEntered INTEGER,
                      MaxTimeInSystem FLOAT,
                      MinTimeInSystem FLOAT,
                      PRIMARY KEY (SinkID, ScenarioID),
                      FOREIGN KEY (ScenarioID) REFERENCES Scenario(ScenarioID)
);

CREATE TABLE Connection (
                            ConnectionID INTEGER,
                            ScenarioID INTEGER,
                            ConnectionName VARCHAR(255),
                            EntitiesProcessed INTEGER,
                            NumberEntered INTEGER,
                            ProcessingDuration FLOAT,
                            Availability FLOAT,
                            PRIMARY KEY (ConnectionID, ScenarioID),
                            FOREIGN KEY (ScenarioID) REFERENCES Scenario(ScenarioID)
);

CREATE TABLE Entity (
                        EntityID INTEGER,
                        ScenarioID INTEGER,
                        EntityName VARCHAR(255),
                        CreationTime FLOAT,
                        PRIMARY KEY (EntityID, ScenarioID),
                        FOREIGN KEY (ScenarioID) REFERENCES Scenario(ScenarioID)
);
