import pandas as pd


def safe_int(val, default=0):
    try:
        if isinstance(val, (bytes, bytearray)):
            return int.from_bytes(val, byteorder="little", signed=False)
        if isinstance(val, str):
            return int(val.strip())
        return int(val)
    except Exception:
        return default


def generate_criteria_html(details):
    rows = ""
    cat_order = ["must_have_skills", "experience", "domain_knowledge", "nice_to_have_skills", "education_requirements", "soft_skills"]
    sorted_details = sorted(details, key=lambda x: cat_order.index(x.get("category")) if x.get("category") in cat_order else 99)

    for item in sorted_details:
        if not item:
            continue
        status = item.get("status", "Unknown")
        cat = item.get("category", "").replace("_", " ").upper()

        color = "color: #333; background-color: #e0e0e0;"
        if "Met" in status:
            color = "color: #0f5132; background-color: #d1e7dd;"
        elif "Missing" in status:
            color = "color: #842029; background-color: #f8d7da;"
        elif "Partial" in status:
            color = "color: #664d03; background-color: #fff3cd;"

        rows += (
            f'<tr><td style="font-size:10px; font-weight:bold; color:#666;">{cat}</td>'
            f'<td>{item.get("requirement", "")}</td><td>{item.get("evidence", "")}</td>'
            f'<td><span class="status-badge" style="{color}">{status}</span></td></tr>'
        )

    return f"""
    <style>
        .match-table {{width: 100%; border-collapse: collapse; font-family: sans-serif; margin-top: 10px;}}
        .match-table th {{background-color: #f0f2f6; padding: 12px 15px; text-align: left; border-bottom: 2px solid #e0e0e0; font-weight: 600; color: #31333F;}}
        .match-table td {{padding: 10px 15px; border-bottom: 1px solid #e0e0e0; vertical-align: top; font-size: 13px; color: #31333F;}}
        .match-table tr:hover {{background-color: #f9f9f9;}}
        .status-badge {{padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; display: inline-block;}}
    </style>
    <table class="match-table">
        <thead><tr><th>Category</th><th>Requirement</th><th>Evidence Found</th><th>Status</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
    """


def generate_candidate_list_html(df, threshold=75, is_deep=False, threshold_map=None):
    if df.empty:
        return "<p style='color: #666;'>No results found.</p>"
    rows = ""
    for _, row in df.iterrows():
        score = safe_int(row["match_score"], 0)
        job_name = row.get("job_name", "Unknown Role")
        decision = row.get("decision", "Reject")

        if decision in ("Parsing Error", "Error"):
            decision_label = "⚠️ Parsing Failed"
            badge_color = "color: #721c24; background-color: #f8d7da;"
            score_color = "#dc3545"
        elif is_deep:
            decision_label = decision
            if decision == "Move Forward":
                badge_color = "color: #0f5132; background-color: #d1e7dd;"
                score_color = "#0f5132"
            elif decision == "Review":
                badge_color = "color: #664d03; background-color: #fff3cd;"
                score_color = "#856404"
            else:
                decision_label = "Reject"
                badge_color = "color: #842029; background-color: #f8d7da;"
                score_color = "#842029"
        else:
            if score < 50:
                decision_label = "Reject (Low Fit)"
                badge_color = "color: #842029; background-color: #f8d7da;"
                score_color = "#842029"
            elif score < threshold:
                decision_label = "Potential (Below Threshold)"
                badge_color = "color: #555; background-color: #e2e3e5;"
                score_color = "#555"
            else:
                decision_label = "Ready for Deep Scan"
                badge_color = "color: #084298; background-color: #cfe2ff;"
                score_color = "#084298"

        std_score_display = ""
        if "standard_score" in row and pd.notna(row["standard_score"]) and row["strategy"] == "Deep":
            deep_th = None
            if threshold_map and "id" in row and row["id"] in threshold_map:
                deep_th = threshold_map.get(row["id"])
            if deep_th is None:
                deep_th = threshold
            if deep_th is not None:
                std_score_display = (
                    f"<br><span style='font-size: 10px; color: #666;'>"
                    f"Pass 1: {safe_int(row['standard_score'])}% (Deep Match Th: {safe_int(deep_th)}%)"
                    f"</span>"
                )
            else:
                std_score_display = f"<br><span style='font-size: 10px; color: #666;'>Pass 1: {safe_int(row['standard_score'])}%</span>"

        job_display = (
            f"<br><span style='font-size: 11px; color: #007bff; font-weight:bold;'>Job: {job_name}</span>"
            if "job_name" in df.columns and df["job_name"].nunique() > 1
            else ""
        )

        rows += (
            f'<tr><td style="font-weight: 600;">{row["candidate_name"]}<br><span style="font-size: 11px; color: #666;">'
            f'{row["res_name"]}</span>{job_display}</td><td style="color: {score_color}; font-weight: bold; font-size: 16px;">'
            f'{score}%{std_score_display}</td><td><span class="status-badge" style="{badge_color}">{decision_label}</span></td>'
            f'<td style="font-size: 13px; color: #444;">{row["reasoning"]}</td></tr>'
        )

    return (
        "<style>.candidate-table {width: 100%; border-collapse: collapse; margin-bottom: 20px;}"
        ".candidate-table th {background-color: #f8f9fa; padding: 12px; text-align: left;}"
        ".candidate-table td {padding: 12px; border-bottom: 1px solid #dee2e6; vertical-align: top;}"
        ".status-badge {padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;}</style>"
        f"<table class='candidate-table'><thead><tr><th>Candidate</th><th>Score</th><th>Decision</th><th>Reasoning</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def generate_matrix_view(df, view_mode="All"):
    if df.empty:
        return

    if view_mode == "Deep Match Only":
        df_filtered = df[df["strategy"] == "Deep"]
    elif view_mode == "Standard Match Only":
        df_filtered = df[df["strategy"] != "Deep"]
    else:
        df_filtered = df

    if df_filtered.empty:
        return

    pivot_df = df_filtered.pivot_table(index="candidate_name", columns="job_name", values="match_score", aggfunc="max")
    pivot_df["Best Score"] = pivot_df.max(axis=1)
    pivot_df = pivot_df.sort_values(by="Best Score", ascending=False)

    headers = ["Candidate"] + list(pivot_df.columns[:-1]) + ["Best Score"]
    header_html = "".join(
        [f"<th style='background-color:#f0f2f6; padding:10px; border-bottom:2px solid #ccc; text-align:center;'>{h}</th>" for h in headers]
    )

    rows_html = ""
    for cand, row in pivot_df.iterrows():
        cells = f"<td style='padding:10px; font-weight:bold; border-bottom:1px solid #eee;'>{cand}</td>"
        for col in pivot_df.columns[:-1]:
            score = row[col]
            if pd.isna(score):
                cell_style = "color:#ccc; background-color:#f9f9f9;"
                val = "-"
            else:
                s = safe_int(score, 0)
                if s >= 75:
                    bg = "#d1e7dd"
                    color = "#0f5132"
                elif s >= 50:
                    bg = "#fff3cd"
                    color = "#664d03"
                else:
                    bg = "#f8d7da"
                    color = "#842029"
                cell_style = f"background-color:{bg}; color:{color}; font-weight:bold;"
                val = f"{s}%"
            cells += f"<td style='padding:10px; text-align:center; border-bottom:1px solid #eee; {cell_style}'>{val}</td>"

        best = int(row["Best Score"])
        cells += (
            "<td style='padding:10px; text-align:center; border-bottom:1px solid #eee; font-weight:bold; "
            f"font-size:1.1em; background-color:#f8f9fa;'>{best}%</td>"
        )
        rows_html += f"<tr>{cells}</tr>"

    return (
        "<div style='overflow-x:auto;'><table style='width:100%; border-collapse:collapse; font-family:sans-serif; font-size:0.9em;'>"
        f"<thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></div>"
    )
