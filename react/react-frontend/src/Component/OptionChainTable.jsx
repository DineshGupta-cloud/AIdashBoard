import { useEffect, useState } from "react";
import { fetchOptionChainTable } from "../API/api";

export default function OptionChainTable() {
  const [data, setData] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await fetchOptionChainTable();
      setData(res);
    } catch (err) {
      console.error("Error loading option chain", err);
    }
  };

  if (!data) {
    return (
      <div
        style={{
          backgroundColor: "#0d0d0d",
          minHeight: "100vh",
          padding: "20px",
          color: "#fff",
        }}
      >
        Loading...
      </div>
    );
  }

  const {
    spot,
    atmStrike,
    pcr,
    maxPain,
    trend,
    optionChainTable,
  } = data;

  // Convert spot to number
  const spotPrice = Number(spot) || 0;

  const styles = {
    page: {
      backgroundColor: "#0d0d0d",
      minHeight: "100vh",
      padding: "15px",
      color: "#e0e0e0",
      fontFamily: "Arial, sans-serif",
      overflowX: "auto",
    },

    header: {
      background: "#1a1a1a",
      padding: "12px",
      borderRadius: "8px",
      marginBottom: "15px",
      boxShadow: "0 0 10px rgba(0,0,0,0.6)",
    },

    title: {
      margin: 0,
      color: "#ffffff",
      fontSize: "20px",
    },

    rowInfo: {
      display: "flex",
      flexWrap: "wrap",
      gap: "25px",
      marginTop: "12px",
      fontSize: "14px",
    },

    tableContainer: {
      width: "100%",
      overflowX: "auto",
      borderRadius: "8px",
      boxShadow: "0 0 12px rgba(0,0,0,0.6)",
    },

    table: {
      width: "100%",
      minWidth: "1300px",
      borderCollapse: "collapse",
      backgroundColor: "#121212",
      overflow: "hidden",
    },

    th: {
      backgroundColor: "#1f1f1f",
      color: "#ffffff",
      padding: "10px 8px",
      borderBottom: "1px solid #333",
      borderRight: "1px solid #333",
      fontSize: "12px",
      whiteSpace: "nowrap",
      textAlign: "center",
    },

    td: {
      padding: "8px",
      textAlign: "center",
      borderBottom: "1px solid #222",
      borderRight: "1px solid #222",
      fontSize: "12px",
      whiteSpace: "nowrap",
    },

    atmRow: {
      backgroundColor: "#2e7d32",
      fontWeight: "bold",
      color: "#ffffff",
    },

    ceGreen: {
      color: "#00e676",
    },

    red: {
      color: "#ff5252",
    },

    yellow: {
      color: "#ffd740",
    },

    cyan: {
      color: "#40c4ff",
    },

    premiumHeader: {
      backgroundColor: "#263238",
      color: "#ffffff",
    },
  };

  return (
    <div style={styles.page}>

      {/* ================= HEADER ================= */}

      <div style={styles.header}>
        <h2 style={styles.title}>
          Option Chain Analysis
        </h2>

        <div style={styles.rowInfo}>
          <div>
            Spot:{" "}
            <b style={styles.cyan}>
              {spot}
            </b>
          </div>

          <div>
            ATM:{" "}
            <b style={styles.yellow}>
              {atmStrike}
            </b>
          </div>

          <div>
            PCR:{" "}
            <b>
              {pcr}
            </b>
          </div>

          <div>
            Max Pain:{" "}
            <b>
              {maxPain}
            </b>
          </div>

          <div>
            Trend:{" "}
            <b
              style={{
                color:
                  trend?.toLowerCase() === "bullish"
                    ? "#00e676"
                    : trend?.toLowerCase() === "bearish"
                    ? "#ff5252"
                    : "#ffd740",
              }}
            >
              {trend}
            </b>
          </div>
        </div>
      </div>

      {/* ================= TABLE ================= */}

      <div style={styles.tableContainer}>
        <table style={styles.table}>

          <thead>

            {/* FIRST HEADER ROW */}

            <tr>

              <th style={styles.th} colSpan="4">
                CALLS (CE)
              </th>

              <th style={styles.th} rowSpan="2">
                STRIKE
              </th>

              <th style={styles.th} colSpan="4">
                PUTS (PE)
              </th>

              <th
                style={{
                  ...styles.th,
                  ...styles.premiumHeader,
                }}
                colSpan="8"
              >
                PREMIUM ANALYSIS
              </th>

            </tr>

            {/* SECOND HEADER ROW */}

            <tr>

              {/* CE */}

              <th style={styles.th}>
                TYPE
              </th>

              <th style={styles.th}>
                OI
              </th>

              <th style={styles.th}>
                CHG OI
              </th>

              <th style={styles.th}>
                LTP
              </th>

              {/* PE */}

              <th style={styles.th}>
                LTP
              </th>

              <th style={styles.th}>
                CHG OI
              </th>

              <th style={styles.th}>
                OI
              </th>

              <th style={styles.th}>
                TYPE
              </th>

              {/* PREMIUM */}

              <th style={styles.th}>
                CE Intrinsic
              </th>

              <th style={styles.th}>
                CE Time Value
              </th>

              <th style={styles.th}>
                CE Breakeven
              </th>

              <th style={styles.th}>
                CE Move
              </th>

              <th style={styles.th}>
                PE Intrinsic
              </th>

              <th style={styles.th}>
                PE Time Value
              </th>

              <th style={styles.th}>
                PE Breakeven
              </th>

              <th style={styles.th}>
                PE Move
              </th>

            </tr>

          </thead>

          <tbody>

            {optionChainTable.map((row) => {

              const strike = Number(row.strike) || 0;

              const ceLtp = Number(row.ce?.ltp) || 0;

              const peLtp = Number(row.pe?.ltp) || 0;

              /* =====================================
                 CE CALCULATIONS
                 ===================================== */

              // CE intrinsic value
              const ceIntrinsic = Math.max(
                spotPrice - strike,
                0
              );

              // CE time value
              const ceTimeValue =
                ceLtp - ceIntrinsic;

              // CE breakeven
              const ceBreakeven =
                strike + ceLtp;

              // Spot movement required for CE
              const ceMove =
                ceBreakeven - spotPrice;

              /* =====================================
                 PE CALCULATIONS
                 ===================================== */

              // PE intrinsic value
              const peIntrinsic = Math.max(
                strike - spotPrice,
                0
              );

              // PE time value
              const peTimeValue =
                peLtp - peIntrinsic;

              // PE breakeven
              const peBreakeven =
                strike - peLtp;

              // Spot movement required for PE
              const peMove =
                spotPrice - peBreakeven;

              const isATM = row.isATM;

              return (
                <tr
                  key={row.strike}
                  style={
                    isATM
                      ? styles.atmRow
                      : {}
                  }
                >

                  {/* ================= CE ================= */}

                  <td style={styles.td}>
                    {row.ce?.oiState}
                  </td>

                  <td style={styles.td}>
                    {row.ce?.oi}
                  </td>

                  <td
                    style={{
                      ...styles.td,
                      ...(Number(row.ce?.changeOi) >= 0
                        ? styles.ceGreen
                        : styles.red),
                    }}
                  >
                    {row.ce?.changeOi}
                  </td>

                  <td style={styles.td}>
                    {ceLtp.toFixed(2)}
                  </td>

                  {/* ================= STRIKE ================= */}

                  <td
                    style={{
                      ...styles.td,
                      fontWeight: "bold",
                      fontSize: "13px",
                    }}
                  >
                    {row.strike}
                  </td>

                  {/* ================= PE ================= */}

                  <td style={styles.td}>
                    {peLtp.toFixed(2)}
                  </td>

                  <td
                    style={{
                      ...styles.td,
                      ...(Number(row.pe?.changeOi) >= 0
                        ? styles.ceGreen
                        : styles.red),
                    }}
                  >
                    {row.pe?.changeOi}
                  </td>

                  <td style={styles.td}>
                    {row.pe?.oi}
                  </td>

                  <td style={styles.td}>
                    {row.pe?.oiState}
                  </td>

                  {/* =================================================
                      PREMIUM ANALYSIS
                      ================================================= */}

                  {/* CE INTRINSIC */}

                  <td
                    style={{
                      ...styles.td,
                      color: "#40c4ff",
                    }}
                  >
                    {ceIntrinsic.toFixed(2)}
                  </td>

                  {/* CE TIME VALUE */}

                  <td
                    style={{
                      ...styles.td,
                      color:
                        ceTimeValue >= 0
                          ? "#00e676"
                          : "#ff5252",
                    }}
                  >
                    {ceTimeValue.toFixed(2)}
                  </td>

                  {/* CE BREAKEVEN */}

                  <td
                    style={{
                      ...styles.td,
                      color: "#ffd740",
                      fontWeight: "bold",
                    }}
                  >
                    {ceBreakeven.toFixed(2)}
                  </td>

                  {/* CE SPOT MOVE */}

                  <td
                    style={{
                      ...styles.td,
                      color:
                        ceMove > 0
                          ? "#ffab40"
                          : "#00e676",
                    }}
                  >
                    {ceMove > 0 ? "+" : ""}
                    {ceMove.toFixed(2)}
                  </td>

                  {/* PE INTRINSIC */}

                  <td
                    style={{
                      ...styles.td,
                      color: "#40c4ff",
                    }}
                  >
                    {peIntrinsic.toFixed(2)}
                  </td>

                  {/* PE TIME VALUE */}

                  <td
                    style={{
                      ...styles.td,
                      color:
                        peTimeValue >= 0
                          ? "#00e676"
                          : "#ff5252",
                    }}
                  >
                    {peTimeValue.toFixed(2)}
                  </td>

                  {/* PE BREAKEVEN */}

                  <td
                    style={{
                      ...styles.td,
                      color: "#ffd740",
                      fontWeight: "bold",
                    }}
                  >
                    {peBreakeven.toFixed(2)}
                  </td>

                  {/* PE SPOT MOVE */}

                  <td
                    style={{
                      ...styles.td,
                      color:
                        peMove > 0
                          ? "#ffab40"
                          : "#00e676",
                    }}
                  >
                    {peMove > 0 ? "-" : "+"}
                    {Math.abs(peMove).toFixed(2)}
                  </td>

                </tr>
              );
            })}

          </tbody>

        </table>
      </div>

    </div>
  );
}
