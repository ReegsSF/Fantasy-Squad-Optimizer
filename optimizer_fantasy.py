import pandas as pd
from pulp import *


def run_optimizer(input_csv_path):

    SALARY_CAP = 18_300_000
    BENCH_PRICE_LIMIT = 400_000

    # ------------------------
    # LOAD DATA
    # ------------------------
    df = pd.read_csv(input_csv_path)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    df["positions"] = df["position"].apply(lambda x: x.split("|"))

    # ------------------------
    # DETECT EARLY BYE
    # ------------------------
    def detect_early_bye(val):
        if isinstance(val, str) and "|" in val:
            return 1
        return 0

    df["early_bye"] = df["bye"].apply(detect_early_bye)

    # ------------------------
    # APPLY BYE ADJUSTMENT
    # ------------------------
    def apply_bye_adjustment(row):
        avg = row["expected_avg"]
        price = row["price"]

        if row["early_bye"] == 1:
            if price > 1_000_000:
                return avg - 6
            elif 700_000 <= price <= 999_999:
                return avg - 4
            elif 400_000 <= price <= 699_999:
                return avg
            else:
                return avg + 3
        return avg

    df["adjusted_avg"] = df.apply(apply_bye_adjustment, axis=1)

    players = df.index.tolist()
    field_positions = ["DEF", "MID", "RUC", "FWD"]
    bench_positions = ["DEF", "MID", "RUC", "FWD", "UTIL"]

    # ------------------------
    # MODEL
    # ------------------------
    model = LpProblem("AFL_Fantasy_2026", LpMaximize)

    x = LpVariable.dicts("squad", players, cat="Binary")
    y = LpVariable.dicts("onfield", [(p, pos) for p in players for pos in field_positions], cat="Binary")
    z = LpVariable.dicts("bench", [(p, pos) for p in players for pos in bench_positions], cat="Binary")

    # ------------------------
    # OBJECTIVE
    # ------------------------
    model += lpSum(x[p] * df.loc[p, "adjusted_avg"] for p in players)

    # ------------------------
    # SQUAD CONSTRAINTS
    # ------------------------
    model += lpSum(x[p] for p in players) == 30
    model += lpSum(x[p] * df.loc[p, "price"] for p in players) <= SALARY_CAP

    model += lpSum(x[p] for p in players if "DEF" in df.loc[p, "positions"]) >= 8
    model += lpSum(x[p] for p in players if "MID" in df.loc[p, "positions"]) >= 10
    model += lpSum(x[p] for p in players if "FWD" in df.loc[p, "positions"]) >= 8
    model += lpSum(x[p] for p in players if "RUC" in df.loc[p, "positions"]) == 3

    # ------------------------
    # STRUCTURE
    # ------------------------
    model += lpSum(y[(p, "DEF")] for p in players) == 6
    model += lpSum(y[(p, "MID")] for p in players) == 8
    model += lpSum(y[(p, "RUC")] for p in players) == 2
    model += lpSum(y[(p, "FWD")] for p in players) == 6

    model += lpSum(z[(p, "DEF")] for p in players) == 2
    model += lpSum(z[(p, "MID")] for p in players) == 2
    model += lpSum(z[(p, "RUC")] for p in players) == 1
    model += lpSum(z[(p, "FWD")] for p in players) == 2
    model += lpSum(z[(p, "UTIL")] for p in players) == 1

    # ------------------------
    # ASSIGNMENT RULES
    # ------------------------
    for p in players:

        for pos in field_positions:
            model += y[(p, pos)] <= x[p]
            if pos not in df.loc[p, "positions"]:
                model += y[(p, pos)] == 0

        for pos in bench_positions:
            model += z[(p, pos)] <= x[p]
            if pos != "UTIL" and pos not in df.loc[p, "positions"]:
                model += z[(p, pos)] == 0

        model += (
            lpSum(y[(p, pos)] for pos in field_positions)
            + lpSum(z[(p, pos)] for pos in bench_positions)
            <= 1
        )

        model += (
            lpSum(z[(p, pos)] for pos in bench_positions)
            * df.loc[p, "price"]
            <= BENCH_PRICE_LIMIT
        )

    # ------------------------
    # SOLVE
    # ------------------------
    model.solve()

    if LpStatus[model.status] != "Optimal":
        raise Exception("Infeasible solution")

    # ------------------------
    # OUTPUT (NO ORDERING)
    # ------------------------
    rows = []

    for p in players:
        for pos in field_positions:
            if y[(p, pos)].value() == 1:
                rows.append({
                    "name": df.loc[p, "name"],
                    "line": pos,
                    "position": df.loc[p, "position"],
                    "price": float(df.loc[p, "price"]),
                    "expected_avg": df.loc[p, "expected_avg"],
                    "adjusted_avg": df.loc[p, "adjusted_avg"],
                    "role": "On Field"
                })

        for pos in bench_positions:
            if z[(p, pos)].value() == 1:
                rows.append({
                    "name": df.loc[p, "name"],
                    "line": pos,
                    "position": df.loc[p, "position"],
                    "price": float(df.loc[p, "price"]),
                    "expected_avg": df.loc[p, "expected_avg"],
                    "adjusted_avg": df.loc[p, "adjusted_avg"],
                    "role": "Bench"
                })

    output = pd.DataFrame(rows)

# ✅ FORCE SORT ORDER HERE
output["price"] = pd.to_numeric(output["price"], errors="coerce")

output = output.sort_values(
    by=["role", "line", "price"],
    ascending=[True, True, True]
).reset_index(drop=True)

return output
