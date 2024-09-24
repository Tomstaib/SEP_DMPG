CREATE VIEW accumulated_pivot_for_scenario AS
SELECT
    s.ScenarioID,
    s.ScenarioName,
    pt.Type,
    pt.Name,
    pt.Stat,
    SUM(pt.Average * sim.num_replications) / SUM(sim.num_replications) AS weighted_avg_average,
    MIN(pt.Minimum) AS min_value,
    MAX(pt.Maximum) AS max_value,
    SUM(pt.Half_Width * sim.num_replications) / SUM(sim.num_replications) AS weighted_avg_half_width,
    SUM(sim.num_replications) AS total_replications
FROM
    Scenario s
        JOIN
    Simulation sim ON s.ScenarioID = sim.ScenarioID
        JOIN
    PivotTable pt ON sim.SimulationID = pt.SimulationID
GROUP BY
    s.ScenarioID, s.ScenarioName, pt.Type, pt.Name, pt.Stat;