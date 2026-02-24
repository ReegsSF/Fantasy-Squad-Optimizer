import streamlit as st
import pandas as pd
import tempfile
import os

from optimizer_fantasy import run_optimizer

# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(
    page_title="SuperFantasy – AFL Fantasy Optimizer",
    layout="wide"
)

st.title("🔥 AFL Fantasy Optimizer")
st.write("Upload your AFL Fantasy CSV and run the optimizer.")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload your Fantasy input CSV",
    type=["csv"]
)

if uploaded_file is not None:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_csv_path = tmp.name

    st.success("CSV uploaded successfully")

    if st.button("🚀 Run Optimizer"):

        with st.spinner("Optimizing Fantasy squad..."):
            try:
                squad = run_optimizer(temp_csv_path)

                st.success("Optimization complete!")

                # -----------------------------
                # ON FIELD DISPLAY (SORT BY PRICE)
                # -----------------------------
                st.subheader("🏆 ON FIELD")

                on_field = (
                    squad[squad["role"] == "On Field"]
                    .sort_values("price")   # ✅ SORT HERE
                )

                for pos in ["DEF", "MID", "RUC", "FWD"]:
                    st.markdown(f"### {pos}")

                    rows = on_field[on_field["line"] == pos]

                    if rows.empty:
                        st.write("_No players_")
                        continue

                    for _, r in rows.iterrows():
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${r['price']:,} | "
                            f"Adj Avg: {round(r['adjusted_avg'], 1)}"
                        )

                # -----------------------------
                # BENCH DISPLAY (SORT BY PRICE)
                # -----------------------------
                st.subheader("🪑 BENCH")

                bench = (
                    squad[squad["role"] == "Bench"]
                    .sort_values("price")   # ✅ SORT HERE
                )

                for pos in ["DEF", "MID", "RUC", "FWD", "UTIL"]:
                    st.markdown(f"### {pos}")

                    rows = bench[bench["line"] == pos]

                    if rows.empty:
                        st.write("_No players_")
                        continue

                    for _, r in rows.iterrows():
                        st.write(
                            f"**{r['name']}** ({r['position']}) — "
                            f"${r['price']:,} | "
                            f"Adj Avg: {round(r['adjusted_avg'], 1)}"
                        )

                # -----------------------------
                # SUMMARY
                # -----------------------------
                st.subheader("📊 SUMMARY")

                st.write(
                    f"**Total Squad Price:** ${int(squad['price'].sum()):,}"
                )
                st.write(
                    f"**Total Adjusted Avg:** {round(squad['adjusted_avg'].sum(), 2)}"
                )

                # -----------------------------
                # DOWNLOAD CSV
                # -----------------------------
                csv_out = squad.to_csv(index=False).encode("utf-8")

                st.download_button(
                    "⬇️ Download Fantasy Squad CSV",
                    csv_out,
                    file_name="AFLFantasy2026_Squad.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error("Optimizer failed")
                st.exception(e)

    os.unlink(temp_csv_path)

