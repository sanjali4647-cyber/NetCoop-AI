# Offline scenarios

`scenario_data.py` generates deterministic, explicitly synthetic inputs only for automated checks and the command-line demonstration. These fixtures are not inserted into the live dashboard or its database.

Run the automated scenario checks with:

```powershell
python -m unittest discover -s tests -v
```

Run one offline scenario and print the agent trace plus JSON report:

```powershell
python demo.py link_congestion
```

Other scenarios: `normal`, `weak_wifi`, `interface_fault`, `dns_failure`, `dhcp_failure`, `server_downtime`, `database_failure`, `connection_pool_exhaustion`, and `missing`.
