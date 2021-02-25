title: Prometheus Metrics

## What is Prometheus?

[Prometheus](https://prometheus.io) is an "open-source monitoring system with a
dimensional data model, flexible query language, efficient time series database
and modern alerting approach".

Prometheus Metrics can be accessed at [/metrics](/metrics), or you can view them
on the Grafana instance below.

<p>
    <a class="btn btn-primary" href="https://monitor.rubenwardy.com/d/3ELzFy3Wz/contentdb">
        View ContentDB on Grafana
    </a>
</p>

## Metrics

* `contentdb_packages` - Total packages (counter).
* `contentdb_users` - Number of registered users (counter).
* `contentdb_downloads` - Total downloads (counter).
* `contentdb_score` - Total package score (gauge).
