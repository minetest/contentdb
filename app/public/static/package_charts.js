"use strict";


const labelColor = "#bbb";
const annotationColor = "#bbb";
const annotationLabelBgColor = "#444";
const gridColor = "#333";


const chartColors = [
	"#7eb26d",
	"#eab839",
	"#6ed0e0",
	"#e24d42",
	"#1f78c1",
	"#ba43a9",
];


const annotationNov5 = {
	type: 'line',
	borderColor: annotationColor,
	borderWidth: 1,
	click: function({chart, element}) {
		document.location = "https://fosstodon.org/@rubenwardy/109303281233703275";
	},
	label: {
		backgroundColor: annotationLabelBgColor,
		content: "YouTube Video",
		display: true,
		position: "end",
		color: "#00bc8c",
	},
	scaleID: 'x',
	value: "2022-11-05",
};


function hexToRgb(hex) {
	var bigint = parseInt(hex, 16);
	var r = (bigint >> 16) & 255;
	var g = (bigint >> 8) & 255;
	var b = bigint & 255;

	return r + "," + g + "," + b;
}


function sum(list) {
	return list.reduce((acc, x) => acc + x, 0);
}


const chartColorsBg = chartColors.map(color => `rgba(${hexToRgb(color.slice(1))}, 0.2)`);

const SECONDS_IN_A_DAY = 1000 * 3600 * 24;

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

	const startDate = new Date(json.start);
	const endDate = new Date(json.end);
	const numberOfDays = Math.round((endDate.valueOf() - startDate.valueOf()) / SECONDS_IN_A_DAY) + 1;
	const dates = [...Array(numberOfDays)].map((_, i) => {
		const date = new Date(startDate.valueOf() + i*SECONDS_IN_A_DAY);
		return date.toISOString().split('T')[0];
	});

	const total7 = sum(json.platform_minetest.slice(-7)) + sum(json.platform_other.slice(-7));
	document.getElementById("downloads_total7d").textContent = total7;
	document.getElementById("downloads_avg7d").textContent = (total7 / 7).toFixed(0);

	if (json.platform_minetest.length >= 30) {
		const total30 = sum(json.platform_minetest.slice(-30)) + sum(json.platform_other.slice(-30));
		document.getElementById("downloads_total30d").textContent = total30;
		document.getElementById("downloads_avg30d").textContent = (total30 / 30).toFixed(0);
	} else {
		document.getElementById("downloads30").style.display = "none";
	}

	const jsonOther = json.platform_minetest.map((value, i) =>
			value + json.platform_other[i]
				- json.reason_new[i] - json.reason_dependency[i]
				- json.reason_update[i]);

	root.style.display = "block";

	function getData(list) {
		return list.map((value, i) => ({ x: dates[i], y: value }));
	}

	if (json.package_downloads) {
		const packageRecentDownloads = Object.fromEntries(Object.entries(json.package_downloads)
			.map(([label, values]) => [label, sum(values.slice(-30))]));

		document.getElementById("downloads-by-package").classList.remove("d-none");
		const ctx = document.getElementById("chart-packages").getContext("2d");

		const data = {
			datasets: Object.entries(json.package_downloads)
				.sort((a, b) => packageRecentDownloads[a[0]] - packageRecentDownloads[b[0]])
				.map(([label, values]) => ({ label, data: getData(values) })),
		};
		setup_chart(ctx, data);
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
			backgroundColor: chartColorsBg[colorIdx] ?? chartColorsBg[0],
			borderColor: chartColors[colorIdx] ?? chartColors[0],
			pointBackgroundColor: chartColors[colorIdx] ?? chartColors[0],
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
				},

				annotation: {
					annotations: {
						annotationNov5,
					},
				},
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
