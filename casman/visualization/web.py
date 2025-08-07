"""
Interactive web visualization for CAsMan.

This module provides a modern Flask-based web interface with interactive visualizations
using Chart.js and D3.js for network graphs, timeline views, and export capabilities.
"""

from flask import Flask, jsonify, render_template_string, request

from .enhanced import visualization_engine

app = Flask(__name__)


def get_template() -> str:
    """Get the enhanced HTML template."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAsMan Visualization Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 300;
        }

        .header p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        .controls {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }

        .controls h3 {
            margin-bottom: 1rem;
            color: #333;
        }

        .filter-group {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }

        .filter-group label {
            font-weight: 500;
            margin-right: 0.5rem;
        }

        .filter-group select, .filter-group input, .filter-group button {
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }

        .filter-group button {
            background: #667eea;
            color: white;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .filter-group button:hover {
            background: #5a6fd8;
        }

        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        .widget {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }

        .widget h3 {
            margin-bottom: 1rem;
            color: #333;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 0.5rem;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }

        .stat-item {
            text-align: center;
            padding: 1rem;
            background: #f8f9ff;
            border-radius: 8px;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }

        .stat-label {
            font-size: 0.9rem;
            color: #666;
            margin-top: 0.5rem;
        }

        .network-container {
            grid-column: span 2;
            height: 600px;
        }

        .network-svg {
            width: 100%;
            height: 100%;
            border: 1px solid #eee;
            border-radius: 8px;
        }

        .timeline-container {
            grid-column: span 2;
            height: 400px;
        }

        .export-section {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }

        .export-buttons {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .export-buttons button {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }

        .btn-json { background: #28a745; color: white; }
        .btn-csv { background: #17a2b8; color: white; }
        .btn-graphml { background: #ffc107; color: black; }
        .btn-dot { background: #dc3545; color: white; }

        .btn-json:hover { background: #218838; }
        .btn-csv:hover { background: #138496; }
        .btn-graphml:hover { background: #e0a800; }
        .btn-dot:hover { background: #c82333; }

        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }

        .node {
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }

        .link {
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 2px;
        }

        .link:hover {
            stroke: #333;
            stroke-width: 3px;
        }

        .node-label {
            font-size: 12px;
            text-anchor: middle;
            dominant-baseline: central;
            pointer-events: none;
        }

        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }

            .network-container,
            .timeline-container {
                grid-column: span 1;
            }

            .filter-group {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>CAsMan Visualization Dashboard</h1>
        <p>Interactive Assembly Connection Visualization</p>
    </div>

    <div class="container">
        <div class="controls">
            <h3>Filters & Controls</h3>
            <div class="filter-group">
                <label>Part Type:</label>
                <select id="partTypeFilter" multiple>
                    <option value="">All Types</option>
                    <option value="ANTENNA">ANTENNA</option>
                    <option value="LNA">LNA</option>
                    <option value="BACBOARD">BACBOARD</option>
                    <option value="COAX">COAX</option>
                    <option value="SNAP">SNAP</option>
                </select>

                <label>Date Range:</label>
                <input type="date" id="startDate">
                <input type="date" id="endDate">

                <label>View Mode:</label>
                <select id="viewMode">
                    <option value="network">Network Graph</option>
                    <option value="timeline">Timeline View</option>
                    <option value="both">Both Views</option>
                </select>

                <button onclick="refreshData()">Refresh</button>
                <button onclick="resetFilters()">Reset Filters</button>
            </div>
        </div>

        <div class="dashboard">
            <div class="widget">
                <h3>Network Statistics</h3>
                <div id="statsContainer" class="stats-grid">
                    <div class="loading">Loading statistics...</div>
                </div>
            </div>

            <div class="widget">
                <h3>Type Distribution</h3>
                <canvas id="typeChart" width="400" height="300"></canvas>
            </div>

            <div class="widget network-container">
                <h3>Network Visualization</h3>
                <svg id="networkSvg" class="network-svg"></svg>
            </div>

            <div class="widget timeline-container">
                <h3>Assembly Timeline</h3>
                <canvas id="timelineChart" width="600" height="300"></canvas>
            </div>
        </div>

        <div class="export-section">
            <h3>Export Data</h3>
            <div class="export-buttons">
                <button class="btn-json" onclick="exportData('json')">Export JSON</button>
                <button class="btn-csv" onclick="exportData('csv')">Export CSV</button>
                <button class="btn-graphml" onclick="exportData('graphml')">Export GraphML</button>
                <button class="btn-dot" onclick="exportData('dot')">Export DOT</button>
            </div>
        </div>
    </div>

    <script>
        let currentData = null;
        let networkSimulation = null;
        let typeChart = null;
        let timelineChart = null;

        // Color scheme for different part types
        const typeColors = {
            'ANTENNA': '#FF6B6B',
            'LNA': '#4ECDC4',
            'BACBOARD': '#45B7D1',
            'COAX': '#96CEB4',
            'SNAP': '#FECA57',
            'UNKNOWN': '#BDC3C7'
        };

        async function fetchData() {
            const filters = getFilters();
            const response = await fetch('/api/network_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(filters)
            });
            return await response.json();
        }

        async function fetchTimelineData() {
            const response = await fetch('/api/timeline_data');
            return await response.json();
        }

        function getFilters() {
            const partTypeSelect = document.getElementById('partTypeFilter');
            const selectedTypes = Array.from(partTypeSelect.selectedOptions).map(option => option.value).filter(v => v);

            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;

            return {
                filter_by_type: selectedTypes.length > 0 ? selectedTypes : null,
                filter_by_date: (startDate && endDate) ? [startDate, endDate] : null,
                include_metadata: true
            };
        }

        function resetFilters() {
            document.getElementById('partTypeFilter').selectedIndex = -1;
            document.getElementById('startDate').value = '';
            document.getElementById('endDate').value = '';
            refreshData();
        }

        async function refreshData() {
            try {
                currentData = await fetchData();
                updateStatistics();
                updateTypeChart();
                updateNetworkVisualization();

                if (document.getElementById('viewMode').value !== 'network') {
                    const timelineData = await fetchTimelineData();
                    updateTimelineChart(timelineData);
                }
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }

        function updateStatistics() {
            const stats = currentData.statistics;
            const container = document.getElementById('statsContainer');

            container.innerHTML = `
                <div class="stat-item">
                    <div class="stat-value">${stats.total_nodes}</div>
                    <div class="stat-label">Total Parts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.total_links}</div>
                    <div class="stat-label">Connections</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.longest_chain_length}</div>
                    <div class="stat-label">Longest Chain</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${stats.average_connections_per_node}</div>
                    <div class="stat-label">Avg Connections</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${(stats.density * 100).toFixed(1)}%</div>
                    <div class="stat-label">Network Density</div>
                </div>
            `;
        }

        function updateTypeChart() {
            const ctx = document.getElementById('typeChart').getContext('2d');
            const distribution = currentData.statistics.type_distribution;

            if (typeChart) {
                typeChart.destroy();
            }

            typeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(distribution),
                    datasets: [{
                        data: Object.values(distribution),
                        backgroundColor: Object.keys(distribution).map(type => typeColors[type] || typeColors.UNKNOWN),
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            });
        }

        function updateNetworkVisualization() {
            const svg = d3.select('#networkSvg');
            svg.selectAll('*').remove();

            const width = svg.node().clientWidth;
            const height = svg.node().clientHeight;

            // Create simulation
            networkSimulation = d3.forceSimulation(currentData.nodes)
                .force('link', d3.forceLink(currentData.links).id(d => d.id).distance(100))
                .force('charge', d3.forceManyBody().strength(-300))
                .force('center', d3.forceCenter(width / 2, height / 2))
                .force('collision', d3.forceCollide().radius(30));

            // Create links
            const link = svg.append('g')
                .selectAll('line')
                .data(currentData.links)
                .enter().append('line')
                .attr('class', 'link');

            // Create nodes
            const node = svg.append('g')
                .selectAll('circle')
                .data(currentData.nodes)
                .enter().append('circle')
                .attr('class', 'node')
                .attr('r', d => Math.sqrt((d.connections_count || 1) * 50))
                .attr('fill', d => typeColors[d.type] || typeColors.UNKNOWN)
                .call(d3.drag()
                    .on('start', dragstarted)
                    .on('drag', dragged)
                    .on('end', dragended));

            // Add labels
            const label = svg.append('g')
                .selectAll('text')
                .data(currentData.nodes)
                .enter().append('text')
                .attr('class', 'node-label')
                .text(d => d.label);

            // Add tooltips
            node.append('title')
                .text(d => `${d.label}\\nType: ${d.type}\\nConnections: ${d.connections_count || 0}`);

            // Update positions on simulation tick
            networkSimulation.on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);

                label
                    .attr('x', d => d.x)
                    .attr('y', d => d.y);
            });
        }

        function updateTimelineChart(timelineData) {
            const ctx = document.getElementById('timelineChart').getContext('2d');

            if (timelineChart) {
                timelineChart.destroy();
            }

            timelineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timelineData.timeline.map(item => item.time),
                    datasets: [{
                        label: 'Total Scans',
                        data: timelineData.timeline.map(item => item.total),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            display: true
                        }
                    }
                }
            });
        }

        // D3 drag functions
        function dragstarted(event, d) {
            if (!event.active) networkSimulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) networkSimulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        async function exportData(format) {
            try {
                const filters = getFilters();
                const response = await fetch(`/api/export_data/${format}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(filters)
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    a.download = `casman_visualization_${new Date().toISOString().split('T')[0]}.${format}`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    alert('Error exporting data');
                }
            } catch (error) {
                console.error('Export error:', error);
                alert('Error exporting data');
            }
        }

        // Initialize the dashboard
        document.addEventListener('DOMContentLoaded', () => {
            refreshData();
        });

        // Handle view mode changes
        document.getElementById('viewMode').addEventListener('change', (e) => {
            const networkContainer = document.querySelector('.network-container');
            const timelineContainer = document.querySelector('.timeline-container');

            switch (e.target.value) {
                case 'network':
                    networkContainer.style.display = 'block';
                    timelineContainer.style.display = 'none';
                    break;
                case 'timeline':
                    networkContainer.style.display = 'none';
                    timelineContainer.style.display = 'block';
                    break;
                case 'both':
                    networkContainer.style.display = 'block';
                    timelineContainer.style.display = 'block';
                    break;
            }
            refreshData();
        });
    </script>
</body>
</html>
    """


@app.route("/")
def index() -> str:
    """Render the main dashboard page."""
    return render_template_string(get_template())


@app.route("/api/network_data", methods=["POST"])
def api_network_data():
    """API endpoint for network visualization data."""
    try:
        filters = request.json or {}
        data = visualization_engine.get_network_data(**filters)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/timeline_data")
def api_timeline_data():
    """API endpoint for timeline visualization data."""
    try:
        bin_size = request.args.get("bin_size", "day")
        data = visualization_engine.get_timeline_data(bin_size=bin_size)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/export_data/<format_type>", methods=["POST"])
def api_export_data(format_type: str):
    """API endpoint for exporting visualization data."""
    try:
        filters = request.json or {}
        export_data = visualization_engine.export_data(format_type, **filters)

        # Set appropriate content type
        content_types = {
            "json": "application/json",
            "csv": "text/csv",
            "graphml": "application/xml",
            "dot": "text/plain"
        }

        content_type = content_types.get(format_type, "text/plain")

        return export_data, 200, {
            "Content-Type": content_type,
            "Content-Disposition": f"attachment; filename=casman_export.{format_type}"
        }
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main() -> None:
    """Run the enhanced visualization web application."""
    print("Starting CAsMan Enhanced Visualization Dashboard...")
    print("Navigate to http://localhost:5000 to view the dashboard")
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main()
