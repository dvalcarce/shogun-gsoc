
var URL = "svm.py?json";
var feature_type = "a";
var width = 640,
	height = 400;
var fill = d3.scale.category10();

var svg = d3.select("body").append("svg")
	.attr("width", width)
	.attr("height", height)
	.on("mousedown", mousedown);

svg.append("rect")
	.attr("width", width)
	.attr("height", height)
	.attr("class", "box");

function mousedown() {
	var point = d3.mouse(this);
	svg.append("circle")
		.attr("r", 5)
		.attr("transform", "translate(" + d3.mouse(this) + ")")
		.attr("class", feature_type)
		.attr("opacity", 0)
		.transition()
		.duration(500)
		.ease("linear")
		.attr("opacity", 1);
}

function change_features(feature) {
	feature_type = feature;
	d3.selectAll("button")
		.classed("button_on", 0)
		.classed("button", 1);
	d3.select("#" + feature + "_button")
		.classed("button", 0)
		.classed("button_on", 1);
}

function classify() {
	var points = {};

	svg.selectAll("circle")
		.each(function(d, i) {
			c = this.attributes[2]["value"];
			coordinates = this.attributes[1]["value"];
			if (c in points) {
				points[c].push(coordinates);
			} else {
				points[c] = [coordinates];
			}
		});

	request_clasify(points);
}

function request_clasify(data) {
	xhr = new XMLHttpRequest();
	xhr.aborted = false;
	xhr.open("POST", URL, true);
	xhr.setRequestHeader("X-Ajax-Request", "true");
	xhr.onreadystatechange = function() {
		if (xhr.readyState === 4 && xhr.status === 200) {
			recv(xhr.responseText);
		}
	};
	xhr.send(JSON.stringify(data));
}

function recv(data) {
	data = JSON.parse(data);

	if (data["status"] != "ok") {
		return;
	}

	// Grid data
	z = data["z"];

	// Generate contour
	var cliff = -100;
	z.push(d3.range(z[0].length).map(function() { return cliff; }));
	z.unshift(d3.range(z[0].length).map(function() { return cliff; }));
	z.forEach(function(d) {
		d.push(cliff);
		d.unshift(cliff);
	});

	var c = new Conrec(),
		xs = d3.range(0, z.length),
		ys = d3.range(0, z[0].length),
		zs = d3.range(data["min"], data["max"], 0.1),
		x = d3.scale.linear().range([0, width]).domain([0, z.length]),
		y = d3.scale.linear().range([0, height]).domain([0, z[0].length]),
		colours = d3.scale.linear().domain([-1, 1]).range(["blue", "red"]);

	c.contour(z, 0, xs.length-1, 0, ys.length-1, xs, ys, zs.length, zs);

	// Remove old paths
	d3.select("svg")
		.selectAll("path")
		.remove();
	// Create new paths
	d3.select("svg")
		.selectAll("path").data(c.contourList())
		.enter().append("svg:path")
		.style("fill", function(d) { return colours(d.level);})
		.attr("class", "path")
		.attr("d",d3.svg.line()
			.x(function(d) { return x(d.x); })
			.y(function(d) { return y(d.y); })
		);
	// Sort points
	d3.select("svg")
		.selectAll("circle")
		.each(function() {
			this.parentNode.appendChild(this);
		});

}

