import Highcharts from "highcharts";
import HighchartsReactOfficial from "highcharts-react-official";

const HighchartsReact =
  HighchartsReactOfficial.default || HighchartsReactOfficial;

export default function Chart({ analysis }) {
  const rows = [...analysis.support, ...analysis.resistance];

  const options = {
    chart: {
      type: "column",
      backgroundColor: "transparent",
    },
    title: {
      text: "CE vs PE Open Interest",
      style: { color: "#ffffff" },
    },
    xAxis: {
      categories: rows.map((r, i) => `${r.strike}-${i}`),
      labels: { style: { color: "#cbd5e1" } },
    },
    yAxis: {
      title: {
        text: "OI",
        style: { color: "#cbd5e1" },
      },
      labels: { style: { color: "#cbd5e1" } },
    },
    series: [
      {
        type: "column",
        name: "CE",
        data: rows.map((r) => Number(r.ceOi || 0)),
      },
      {
        type: "column",
        name: "PE",
        data: rows.map((r) => Number(r.peOi || 0)),
      },
    ],
    credits: { enabled: false },
  };

  return (
    <div className="rounded-2xl bg-slate-900 p-4">
      <HighchartsReact
        highcharts={Highcharts}
        options={options}
        containerProps={{ style: { height: "420px", width: "100%" } }}
      />
    </div>
  );
}