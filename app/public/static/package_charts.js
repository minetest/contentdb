"use strict";


const labelColor = "#bbb";
const gridColor = "#333";


const chartColors = [
	"#7eb26d",
	"#eab839",
	"#6ed0e0",
	"#e24d42",
	"#1f78c1",
	"#ba43a9",
];


function hexToRgb(hex) {
	var bigint = parseInt(hex, 16);
	var r = (bigint >> 16) & 255;
	var g = (bigint >> 8) & 255;
	var b = bigint & 255;

	return r + "," + g + "," + b;
}


const chartColorsBg = chartColors.map(color => `rgba(${hexToRgb(color.slice(1))}, 0.2)`);


async function load_data() {
	const root = document.getElementById("stats-root");
	const source = root.getAttribute("data-source");
	const response = await fetch(source);
	const json = await response.json();

	document.getElementById("loading").style.display = "none";

	if (json == null) {
		document.getElementById("empty-view").style.display = "block";
		return;
	}

	const jsonOther = json.platform_minetest.map((value, i) =>
			value + json.platform_other[i]
				- json.reason_new[i] - json.reason_dependency[i]
				- json.reason_update[i]);

	root.style.display = "block";

	function getData(list) {
		return list.map((value, i) => ({ x: json.dates[i], y: value }));
	}

	function sum(list) {
		return list.reduce((acc, x) => acc + x, 0);
	}

	{
		const ctx = document.getElementById("chart-platform").getContext("2d");
		const data = {
			datasets: [
				{ label: "Web / other", data: getData(json.platform_other) },
				{ label: "Minetest", data: getData(json.platform_minetest) },
			],
		};
		setup_chart(ctx, data);
	}

	{
		const ctx = document.getElementById("chart-reason").getContext("2d");
		const data = {
			datasets: [
				{ label: "Other / Unknown", data: getData(jsonOther) },
				{ label: "Update", data: getData(json.reason_update) },
				{ label: "Dependency", data: getData(json.reason_dependency) },
				{ label: "New Install", data: getData(json.reason_new) },
			],
		};
		setup_chart(ctx, data);
	}

	{
		const ctx = document.getElementById("chart-reason-pie").getContext("2d");
		const data = {
			labels: [
				"New Install",
				"Dependency",
				"Update",
				"Other / Unknown",
			],
			datasets: [{
				label: "My First Dataset",
				data: [
					sum(json.reason_new),
					sum(json.reason_dependency),
					sum(json.reason_update),
					sum(jsonOther),
				],
				backgroundColor: chartColors,
				hoverOffset: 4,
				borderWidth: 0,
			}]
		};
		const config = {
			type: "doughnut",
			data: data,
			options: {
				responsive: true,
				plugins: {
					legend: {
						labels: {
							color: labelColor,
						},
					},
				},
			}
		};
		new Chart(ctx, config);
	}
}


function setup_chart(ctx, data) {
	data.datasets = data.datasets.map((set, i) => {
		const colorIdx = data.datasets.length - i - 1;
		return {
			fill: true,
			backgroundColor: chartColorsBg[colorIdx],
			borderColor: chartColors[colorIdx],
			pointBackgroundColor: chartColors[colorIdx],
			...set,
		};
	});

	const config = {
		type: "line",
		data: data,
		options: {
			responsive: true,
			plugins: {
				tooltip: {
					mode: "index"
				},

				legend: {
					reverse: true,
					labels: {
						color: labelColor,
					}
				}
			},
			interaction: {
				mode: "nearest",
				axis: "x",
				intersect: false
			},
			scales: {
				x: {
					type: "time",
					time: {
						// min: start,
						// max: end,
						unit: "day",
					},
					ticks: {
						color: labelColor,
					},
					grid: {
						color: gridColor,
					}
				},
				y: {
					stacked: true,
					min: 0,
					precision: 0,
					ticks: {
						color: labelColor,
					},
					grid: {
						color: gridColor,
					}
				},
			}
		}
	};

	new Chart(ctx, config);
}


$(load_data);
