// Import necessary libraries
const axios = require("axios");

const KIBANA_URL = "http://localhost:5601";
const KIBANA_API_KEY = "your-api-key"; // Generate this in Kibana

async function createKibanaDashboards() {
  const headers = {
    "kbn-xsrf": "true",
    Authorization: `ApiKey ${KIBANA_API_KEY}`,
    "Content-Type": "application/json",
  };

  // 1. Create Index Patterns
  const indexPatterns = [
    {
      name: "mysql-slow",
      pattern: "mysql-slow-*",
      timeFieldName: "@timestamp",
    },
    {
      name: "nginx-access",
      pattern: "nginx-access-*",
      timeFieldName: "@timestamp",
    },
    {
      name: "system-metrics",
      pattern: "system-metrics-*",
      timeFieldName: "@timestamp",
    },
  ];

  for (const pattern of indexPatterns) {
    await axios.post(
      `${KIBANA_URL}/api/index_patterns/index_pattern`,
      {
        index_pattern: {
          title: pattern.pattern,
          timeFieldName: pattern.timeFieldName,
        },
      },
      { headers }
    );
  }

  // 2. Create MySQL Dashboard Visualizations
  const mysqlVisualizations = [
    {
      name: "mysql-query-time",
      type: "line",
      title: "Average Query Time Over Time",
      params: {
        index_pattern: "mysql-slow-*",
        metrics: [{ type: "avg", field: "query_time" }],
        time_field: "@timestamp",
        interval: "auto",
      },
    },
    {
      name: "mysql-slow-queries",
      type: "table",
      title: "Top Slow Queries",
      params: {
        index_pattern: "mysql-slow-*",
        metrics: [
          { type: "avg", field: "query_time" },
          { type: "avg", field: "lock_time" },
          { type: "sum", field: "rows_examined" },
        ],
        group_by: ["query"],
        order_by: [{ field: "query_time", order: "desc" }],
        size: 10,
      },
    },
    {
      name: "mysql-lock-time",
      type: "heatmap",
      title: "Query Lock Time Distribution",
      params: {
        index_pattern: "mysql-slow-*",
        metrics: [{ type: "count" }],
        group_by: ["lock_time", "@timestamp"],
      },
    },
  ];

  // 3. Create Nginx Dashboard Visualizations
  const nginxVisualizations = [
    {
      name: "nginx-status-codes",
      type: "pie",
      title: "HTTP Status Code Distribution",
      params: {
        index_pattern: "nginx-access-*",
        metrics: [{ type: "count" }],
        group_by: ["status"],
      },
    },
    {
      name: "nginx-request-time",
      type: "line",
      title: "Average Request Time",
      params: {
        index_pattern: "nginx-access-*",
        metrics: [{ type: "avg", field: "request_time" }],
        time_field: "@timestamp",
        interval: "auto",
      },
    },
    {
      name: "nginx-top-ips",
      type: "table",
      title: "Top Client IPs",
      params: {
        index_pattern: "nginx-access-*",
        metrics: [{ type: "count" }],
        group_by: ["remote_addr"],
        size: 10,
      },
    },
  ];

  // 4. Create System Metrics Dashboard Visualizations
  const systemVisualizations = [
    {
      name: "system-cpu-gauge",
      type: "gauge",
      title: "CPU Usage",
      params: {
        index_pattern: "system-metrics-*",
        metrics: [{ type: "avg", field: "cpu_usage" }],
        ranges: [
          { from: 0, to: 60, color: "green" },
          { from: 60, to: 80, color: "yellow" },
          { from: 80, to: 100, color: "red" },
        ],
      },
    },
    {
      name: "system-memory-gauge",
      type: "gauge",
      title: "Memory Usage",
      params: {
        index_pattern: "system-metrics-*",
        metrics: [{ type: "avg", field: "memory_usage" }],
        ranges: [
          { from: 0, to: 60, color: "green" },
          { from: 60, to: 80, color: "yellow" },
          { from: 80, to: 100, color: "red" },
        ],
      },
    },
    {
      name: "system-network",
      type: "area",
      title: "Network Traffic",
      params: {
        index_pattern: "system-metrics-*",
        metrics: [
          { type: "avg", field: "network_in" },
          { type: "avg", field: "network_out" },
        ],
        time_field: "@timestamp",
        interval: "auto",
      },
    },
  ];

  // 5. Create Dashboards
  const dashboards = [
    {
      name: "mysql-monitoring",
      title: "MySQL Slow Query Monitor",
      visualizations: mysqlVisualizations,
      refreshInterval: "1m",
    },
    {
      name: "nginx-monitoring",
      title: "Nginx Access Log Monitor",
      visualizations: nginxVisualizations,
      refreshInterval: "30s",
    },
    {
      name: "system-monitoring",
      title: "System Metrics Monitor",
      visualizations: systemVisualizations,
      refreshInterval: "10s",
    },
  ];

  for (const dashboard of dashboards) {
    // Create visualizations for the dashboard
    const visualizationIds = [];
    for (const viz of dashboard.visualizations) {
      const response = await axios.post(
        `${KIBANA_URL}/api/saved_objects/visualization/${viz.name}`,
        {
          attributes: {
            title: viz.title,
            visState: JSON.stringify(viz.params),
            uiStateJSON: "{}",
            description: "",
            version: 1,
            kibanaSavedObjectMeta: {
              searchSourceJSON: JSON.stringify({
                index: viz.params.index_pattern,
                query: { query: "", language: "kuery" },
                filter: [],
              }),
            },
          },
        },
        { headers }
      );
      visualizationIds.push(response.data.id);
    }

    // Create dashboard and add visualizations
    await axios.post(
      `${KIBANA_URL}/api/saved_objects/dashboard/${dashboard.name}`,
      {
        attributes: {
          title: dashboard.title,
          hits: 0,
          description: "",
          panelsJSON: JSON.stringify(
            visualizationIds.map((id, index) => ({
              gridData: {
                x: (index % 2) * 24,
                y: Math.floor(index / 2) * 15,
                w: 24,
                h: 15,
                i: String(index),
              },
              version: "8.0.0",
              type: "visualization",
              id,
            }))
          ),
          optionsJSON: JSON.stringify({
            hidePanelTitles: false,
            useMargins: true,
            syncColors: false,
            refreshInterval: {
              pause: false,
              value: dashboard.refreshInterval,
            },
          }),
          timeRestore: true,
          timeFrom: "now-24h",
          timeTo: "now",
          refreshInterval: {
            pause: false,
            value: dashboard.refreshInterval,
          },
        },
      },
      { headers }
    );
  }
}

// Execute the dashboard creation
createKibanaDashboards().catch(console.error);
