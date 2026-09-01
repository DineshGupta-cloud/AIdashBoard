import { useEffect, useState } from "react";
import HighchartsReactOfficial from "highcharts-react-official";

const HighchartsReact =
  HighchartsReactOfficial.default || HighchartsReactOfficial;
import Highcharts from "highcharts";
import { getChartData } from "../API/api";

export default function OpenInterestChart() {
  const [options, setOptions] = useState(null);

  const load = async () => {
    try {
      const res = await getChartData();
      console.log("Open Interest Chart Data:", res);

      const data = res?.chartData || res || [];

      const categories = data.map((d) => d.strike);
      const ceOi = data.map((d) => d.ceOi);
      const peOi = data.map((d) => d.peOi);

      const chartOptions = {
        chart: {
          type: "column",
          backgroundColor: "#0f172a",
          height: 420, // ✅ FIX: required for rendering
        },

        title: {
          text: "Open Interest (CE vs PE)",
          style: { color: "#fff" },
        },

        xAxis: {
          categories,
          labels: { style: { color: "#cbd5e1" } },
        },

        yAxis: {
          title: {
            text: "Open Interest",
            style: { color: "#cbd5e1" },
          },
          labels: { style: { color: "#cbd5e1" } },
          gridLineColor: "#1e293b",
        },

        tooltip: {
          shared: true,
        },

        legend: {
          itemStyle: { color: "#fff" },
        },

        series: [
          {
            name: "Call OI (CE)",
            data: ceOi,
            color: "#ef4444",
          },
          {
            name: "Put OI (PE)",
            data: peOi,
            color: " #38aa5e",
          },
        ],

        credits: {
          enabled: false,
        },
      };

      setOptions(chartOptions);
    } catch (err) {
      console.error("OpenInterestChart error:", err);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (!options) {
    return (
      <div className="text-white p-4 bg-slate-900">
        Loading Open Interest Chart...
      </div>
    );
  }

  return (
    <div className="p-4 bg-slate-900 rounded-xl">
      <HighchartsReact highcharts={Highcharts} options={options} />
    </div>
  );
}