(function () {
    const { useEffect, useMemo, useRef, useState } = React;

    function fmtTime(seconds) {
        if (!seconds) return "Never";
        return new Date(seconds * 1000).toLocaleTimeString();
    }

    function titleCase(value) {
        return String(value || "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    }

    function StatusDot({ online }) {
        return React.createElement("span", {
            className: "telemetry-dot " + (online ? "is-online" : "is-offline"),
            title: online ? "Connected" : "Disconnected",
        });
    }

    function StatCard({ label, value, tone }) {
        return React.createElement("div", { className: "telemetry-stat " + (tone || "") },
            React.createElement("span", null, label),
            React.createElement("strong", null, value)
        );
    }

    function LineChart({ device, field }) {
        const canvasRef = useRef(null);
        const chartRef = useRef(null);

        useEffect(() => {
            let stopped = false;
            async function load() {
                const res = await fetch(`/api/telemetry/series?device=${encodeURIComponent(device)}&field=${encodeURIComponent(field)}`);
                const data = await res.json();
                if (stopped || !canvasRef.current) return;
                const labels = data.points.map((p) => new Date(p.x * 1000).toLocaleTimeString());
                const values = data.points.map((p) => p.y);
                if (!chartRef.current) {
                    chartRef.current = new Chart(canvasRef.current, {
                        type: "line",
                        data: {
                            labels,
                            datasets: [{
                                label: titleCase(field),
                                data: values,
                                borderColor: "#2563eb",
                                backgroundColor: "rgba(37, 99, 235, .12)",
                                pointRadius: 0,
                                tension: 0.35,
                                fill: true,
                            }],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            animation: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                x: { grid: { display: false }, ticks: { maxTicksLimit: 5 } },
                                y: { beginAtZero: false },
                            },
                        },
                    });
                } else {
                    chartRef.current.data.labels = labels;
                    chartRef.current.data.datasets[0].data = values;
                    chartRef.current.update();
                }
            }
            load();
            const timer = setInterval(load, 3000);
            return () => {
                stopped = true;
                clearInterval(timer);
                if (chartRef.current) chartRef.current.destroy();
                chartRef.current = null;
            };
        }, [device, field]);

        return React.createElement("div", { className: "telemetry-chart" }, React.createElement("canvas", { ref: canvasRef }));
    }

    function Gauge({ value, field, unit }) {
        const safeValue = Number.isFinite(value) ? value : 0;
        const max = unit === "C" ? 50 : 100;
        const pct = Math.max(0, Math.min(100, (safeValue / max) * 100));
        return React.createElement("div", { className: "telemetry-gauge" },
            React.createElement("div", { className: "telemetry-gauge-ring", style: { "--value": `${pct * 3.6}deg` } },
                React.createElement("div", null,
                    React.createElement("strong", null, safeValue.toFixed(1)),
                    React.createElement("span", null, unit || titleCase(field))
                )
            )
        );
    }

    function Widget({ device, field, latest, type, onType }) {
        const value = latest && typeof latest === "object" ? Number(latest[field]) : NaN;
        const unit = latest && typeof latest === "object" ? latest.unit : "";
        return React.createElement("div", { className: "card telemetry-widget" },
            React.createElement("div", { className: "card-header telemetry-widget-head" },
                React.createElement("div", null,
                    React.createElement("span", null, titleCase(field)),
                    React.createElement("small", null, device)
                ),
                React.createElement("select", { className: "form-select form-select-sm telemetry-widget-select", value: type, onChange: (e) => onType(device, field, e.target.value) },
                    React.createElement("option", { value: "chart" }, "Chart"),
                    React.createElement("option", { value: "gauge" }, "Gauge"),
                    React.createElement("option", { value: "card" }, "Card")
                )
            ),
            React.createElement("div", { className: "card-body" },
                type === "gauge" ? React.createElement(Gauge, { value, field, unit }) :
                type === "card" ? React.createElement("div", { className: "telemetry-value-card" },
                    React.createElement("strong", null, Number.isFinite(value) ? value.toFixed(2) : "-"),
                    React.createElement("span", null, unit || titleCase(field))
                ) :
                React.createElement(LineChart, { device, field })
            )
        );
    }

    function App() {
        const [data, setData] = useState({ devices: [], messages: [], widgets: {}, collector: {} });
        const [selected, setSelected] = useState("");
        const [query, setQuery] = useState("");

        async function refresh() {
            const res = await fetch("/api/telemetry");
            setData(await res.json());
        }

        useEffect(() => {
            refresh();
            const timer = setInterval(refresh, 3000);
            return () => clearInterval(timer);
        }, []);

        const filteredDevices = useMemo(() => {
            const q = query.trim().toLowerCase();
            if (!q) return data.devices;
            return data.devices.filter((item) =>
                item.device.toLowerCase().includes(q) ||
                item.topics.join(" ").toLowerCase().includes(q)
            );
        }, [data.devices, query]);

        const onlineCount = data.devices.filter((item) => item.online).length;
        const topicCount = new Set(data.devices.flatMap((item) => item.topics)).size;
        const activeDevice = selected || (filteredDevices[0] && filteredDevices[0].device) || "";
        const device = data.devices.find((item) => item.device === activeDevice);
        const latestPayload = device && typeof device.last_payload === "object" ? device.last_payload : {};
        const widgets = useMemo(() => {
            if (!device) return [];
            return device.fields.map((field) => ({
                device: device.device,
                field,
                type: data.widgets[`${device.device}:${field}`] || "gauge",
            }));
        }, [device, data.widgets]);

        async function setWidgetType(device, field, type) {
            await fetch("/api/telemetry/widgets", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ device, field, type }),
            });
            refresh();
        }

        return React.createElement(React.Fragment, null,
            data.collector.error && React.createElement("div", { className: "alert alert-warning" }, data.collector.error),
            React.createElement("div", { className: "telemetry-summary" },
                React.createElement(StatCard, { label: "Online Devices", value: `${onlineCount}/${data.devices.length}`, tone: onlineCount ? "good" : "" }),
                React.createElement(StatCard, { label: "Topics Seen", value: topicCount }),
                React.createElement(StatCard, { label: "Messages", value: data.messages.length }),
                React.createElement(StatCard, { label: "Collector", value: data.collector.error ? "Issue" : "Running", tone: data.collector.error ? "bad" : "good" })
            ),
            React.createElement("div", { className: "telemetry-layout" },
                React.createElement("section", { className: "card telemetry-panel" },
                    React.createElement("div", { className: "card-header" },
                        React.createElement("div", null, "Devices"),
                        React.createElement("input", { className: "form-control form-control-sm", placeholder: "Search", value: query, onChange: (e) => setQuery(e.target.value) })
                    ),
                    React.createElement("div", { className: "list-group list-group-flush" },
                        filteredDevices.length ? filteredDevices.map((item) =>
                            React.createElement("button", { key: item.device, className: "list-group-item list-group-item-action telemetry-device " + (item.device === activeDevice ? "active" : ""), onClick: () => setSelected(item.device) },
                                React.createElement("span", null, React.createElement(StatusDot, { online: item.online }), item.device),
                                React.createElement("small", null, `${item.topics.length} topic(s) | ${fmtTime(item.last_seen)}`)
                            )
                        ) : React.createElement("div", { className: "empty-state m-3" }, "Waiting for telemetry messages.")
                    )
                ),
                React.createElement("section", { className: "telemetry-main" },
                    device ? React.createElement(React.Fragment, null,
                        React.createElement("div", { className: "card telemetry-device-detail" },
                            React.createElement("div", { className: "card-body" },
                                React.createElement("div", null,
                                    React.createElement("div", { className: "small text-secondary" }, "Selected Device"),
                                    React.createElement("h2", null, React.createElement(StatusDot, { online: device.online }), device.device)
                                ),
                                React.createElement("div", { className: "telemetry-meta" },
                                    React.createElement("span", null, `Status: ${device.online ? "Connected" : "Disconnected"}`),
                                    React.createElement("span", null, `Last seen: ${fmtTime(device.last_seen)}`),
                                    React.createElement("span", null, `Fields: ${device.fields.length}`)
                                )
                            )
                        ),
                        React.createElement("div", { className: "telemetry-topic-strip" },
                            device.topics.map((topic) => React.createElement("span", { key: topic }, topic))
                        ),
                        React.createElement("div", { className: "telemetry-widget-grid" },
                            widgets.length ? widgets.map((widget) => React.createElement(Widget, { key: `${widget.device}:${widget.field}`, latest: device.last_payload, onType: setWidgetType, ...widget })) :
                            React.createElement("div", { className: "empty-state" }, "This device has no numeric fields yet.")
                        ),
                        React.createElement("div", { className: "card telemetry-payload" },
                            React.createElement("div", { className: "card-header" }, "Latest Payload"),
                            React.createElement("div", { className: "card-body" },
                                Object.keys(latestPayload).map((key) =>
                                    React.createElement("div", { key, className: "telemetry-payload-row" },
                                        React.createElement("span", null, titleCase(key)),
                                        React.createElement("strong", null, String(latestPayload[key]))
                                    )
                                )
                            )
                        )
                    ) : React.createElement("div", { className: "empty-state" }, "Select a device once data arrives.")
                )
            ),
            React.createElement("div", { className: "card mt-4 telemetry-log" },
                React.createElement("div", { className: "card-header" }, "Recent Messages"),
                React.createElement("div", { className: "table-responsive" },
                    React.createElement("table", { className: "table table-sm align-middle mb-0" },
                        React.createElement("thead", null, React.createElement("tr", null, React.createElement("th", null, "Time"), React.createElement("th", null, "Device"), React.createElement("th", null, "Topic"), React.createElement("th", null, "Payload"))),
                        React.createElement("tbody", null, data.messages.slice(0, 25).map((msg, index) =>
                            React.createElement("tr", { key: index },
                                React.createElement("td", null, fmtTime(msg.timestamp)),
                                React.createElement("td", null, msg.device),
                                React.createElement("td", null, msg.topic),
                                React.createElement("td", { className: "small telemetry-payload-cell" }, msg.payload_text)
                            )
                        ))
                    )
                )
            )
        );
    }

    const root = document.getElementById("telemetry-root");
    if (root && window.React && window.ReactDOM && window.Chart) {
        ReactDOM.createRoot(root).render(React.createElement(App));
    }
})();
