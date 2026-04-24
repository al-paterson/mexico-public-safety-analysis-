import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os

os.makedirs("output/charts", exist_ok=True)

conn = sqlite3.connect("data/mexico_safety.db")
QRO = "Querétaro"

# ── load all four datasets ────────────────────────────────────────────────────

yearly = pd.read_sql("""
    SELECT i.year, SUM(i.incidents) AS total_incidents
    FROM incidents i
    INNER JOIN state_lookup s ON i.state_code = s.state_code
    WHERE s.state_name = ?
    GROUP BY i.year
    ORDER BY i.year
""", conn, params=[QRO])

top_crimes = pd.read_sql("""
    SELECT i.crime_type, SUM(i.incidents) AS total_incidents
    FROM incidents i
    INNER JOIN state_lookup s ON i.state_code = s.state_code
    WHERE s.state_name = ?
    GROUP BY i.crime_type
    ORDER BY total_incidents DESC
    LIMIT 10
""", conn, params=[QRO])

monthly = pd.read_sql("""
    SELECT i.month, SUM(i.incidents) AS total_incidents
    FROM incidents i
    INNER JOIN state_lookup s ON i.state_code = s.state_code
    WHERE s.state_name = ?
    GROUP BY i.month
    ORDER BY i.month
""", conn, params=[QRO])

vs_national = pd.read_sql("""
    SELECT
        i.year,
        SUM(i.incidents) AS qro_total,
        ROUND((SELECT SUM(incidents) / 32.0 FROM incidents WHERE year = i.year), 2)
            AS national_avg_per_state
    FROM incidents i
    INNER JOIN state_lookup s ON i.state_code = s.state_code
    WHERE s.state_name = ?
    GROUP BY i.year
    ORDER BY i.year
""", conn, params=[QRO])

conn.close()

# 2026 is partial data (Jan–Feb only) — drop from trend charts
yearly = yearly[yearly["year"] <= 2025]
vs_national = vs_national[vs_national["year"] <= 2025]

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ── Chart 1: Incidents by year (line) ────────────────────────────────────────

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(yearly["year"], yearly["total_incidents"], marker="o",
        linewidth=2.5, color="#2563EB", markersize=6)
ax.fill_between(yearly["year"], yearly["total_incidents"], alpha=0.08, color="#2563EB")

ax.set_title("Reported Crime Incidents in Querétaro (2015–2025)", fontsize=14, fontweight="bold", pad=14)
ax.set_xlabel("Year")
ax.set_ylabel("Total Incidents")
ax.set_xticks(yearly["year"])
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout()
plt.savefig("output/charts/chart1_yearly_trend.png", dpi=150)
plt.close()
print("Saved chart1_yearly_trend.png")

# ── Chart 2: Top 10 crime types (horizontal bar) ──────────────────────────────

fig, ax = plt.subplots(figsize=(10, 6))
colors = ["#2563EB"] + ["#93C5FD"] * 9
ax.barh(top_crimes["crime_type"][::-1], top_crimes["total_incidents"][::-1], color=colors[::-1])

ax.set_title("Top 10 Crime Types in Querétaro (2015–2025)", fontsize=14, fontweight="bold", pad=14)
ax.set_xlabel("Total Incidents")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", linestyle="--", alpha=0.4)

plt.tight_layout()
plt.savefig("output/charts/chart2_top_crimes.png", dpi=150)
plt.close()
print("Saved chart2_top_crimes.png")

# ── Chart 3: Incidents by month (bar) ────────────────────────────────────────

fig, ax = plt.subplots(figsize=(10, 5))
bar_colors = ["#DC2626" if v == monthly["total_incidents"].max()
              else "#93C5FD" if v == monthly["total_incidents"].min()
              else "#2563EB"
              for v in monthly["total_incidents"]]

ax.bar(MONTH_LABELS, monthly["total_incidents"], color=bar_colors)

ax.set_title("Seasonal Crime Patterns in Querétaro (All Years Combined)", fontsize=14, fontweight="bold", pad=14)
ax.set_xlabel("Month")
ax.set_ylabel("Total Incidents")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.4)

ax.annotate("Peak: Oct", xy=(9, monthly["total_incidents"].iloc[9]),
            xytext=(9, monthly["total_incidents"].iloc[9] + 500),
            ha="center", fontsize=9, color="#DC2626")

plt.tight_layout()
plt.savefig("output/charts/chart3_seasonal.png", dpi=150)
plt.close()
print("Saved chart3_seasonal.png")

# ── Chart 4: Querétaro vs national average (line) ────────────────────────────

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(vs_national["year"], vs_national["qro_total"], marker="o",
        linewidth=2.5, color="#2563EB", markersize=6, label="Querétaro")
ax.plot(vs_national["year"], vs_national["national_avg_per_state"], marker="s",
        linewidth=2.5, color="#DC2626", linestyle="--", markersize=6, label="National avg per state")

ax.set_title("Querétaro vs National Average per State (2015–2025)", fontsize=14, fontweight="bold", pad=14)
ax.set_xlabel("Year")
ax.set_ylabel("Total Incidents")
ax.set_xticks(vs_national["year"])
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.legend(frameon=False)
ax.grid(axis="y", linestyle="--", alpha=0.4)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout()
plt.savefig("output/charts/chart4_vs_national.png", dpi=150)
plt.close()
print("Saved chart4_vs_national.png")
