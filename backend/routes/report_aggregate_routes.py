"""
Aggregate Report API — reads from remote genuinedashboardtest database.
Tables: top_cities, top_categories, report_summery
Handles connection failures gracefully with detailed error reporting.
"""
from flask import Blueprint, jsonify
from database.report_db_session import get_report_db_session, test_report_db_connection
from database.session import get_db_session
from sqlalchemy import text
import traceback

report_aggregate_bp = Blueprint("report_aggregate", __name__)


@report_aggregate_bp.route("/api/report/aggregate", methods=["GET"])
def get_report_aggregate():
    """Main aggregate report endpoint — pulls data from remote DB tables."""
    session = None
    is_remote = False
    
    # Check local first for speed and availability
    try:
        session = get_db_session()
        # Verify if local summary table exists
        tables_res = session.execute(text("SHOW TABLES LIKE 'dashboard_summary'")).fetchone()
        if tables_res:
            print("[Report] Using Local Database (dashboard_summary found)")
            is_remote = False
        else:
            # Fallback to remote if local summary doesn't exist
            session.close()
            session = get_report_db_session()
            is_remote = True
            print("[Report] Using Remote Database")
    except Exception as e:
        print(f"[Report] Database detection error: {e}")
        # Final fallback attempt
        try:
            session = get_db_session()
            is_remote = False
        except:
            return jsonify({"status": "ERROR", "message": "Database connection failed"}), 500

    try:
        # ─── Discover available tables ──────────────────────────────────
        available_tables = []
        try:
            tables_result = session.execute(text("SHOW TABLES")).fetchall()
            available_tables = [row[0] for row in tables_result]
            print(f"[Report] Tables found: {available_tables}")
        except Exception as e:
            print(f"[WARN] Could not list tables: {e}")

        # ─── 1. Report Summary (from report_summery table) ───────────────
        summary = {}
        all_summary = []
        summary_table = _find_table(available_tables, ["dashboard_summary", "report_summery", "report_summary", "report_summaries"])
        
        if summary_table:
            try:
                summary_rows = session.execute(text(f"SELECT * FROM `{summary_table}`")).fetchall()
                if summary_rows:
                    first = dict(summary_rows[0]._mapping)
                    summary = {
                        "total_records": _extract(first, ["total_records", "total_count", "total", "count", "total_master_data"]),
                        "total_states":  _extract(first, ["total_states", "total_location_master_states"]),
                        "matched_states": _extract(first, ["matched_states", "matched_master_states"]),
                        "unmatched_states": _extract(first, ["unmatched_states", "unmatched_master_states"]),
                        "total_cities":  _extract(first, ["total_cities", "total_location_master_cities"]),
                        "matched_cities": _extract(first, ["matched_cities", "matched_master_cities"]),
                        "unmatched_cities": _extract(first, ["unmatched_cities", "unmatched_master_cities"]),
                        "total_areas":   _extract(first, ["total_areas", "total_location_master_areas"]),
                        "matched_areas": _extract(first, ["matched_areas", "matched_master_areas"]),
                        "unmatched_areas": _extract(first, ["unmatched_areas", "unmatched_master_areas"]),
                        "total_categories": _extract(first, ["total_categories", "total_master_categories"]),
                        "matched_categories": _extract(first, ["matched_categories", "matched_categories_master"]),
                        "unmatched_categories": _extract(first, ["unmatched_categories", "unmatched_category_master"]),
                        "pending_data":  _extract(first, ["pending_data", "missing_count", "pending_master_data"]),
                        # Compatibility keys for older frontend
                        "total_count":   _extract(first, ["total_count", "total_records", "total", "total_master_data"]),
                        "match_count":   _extract(first, ["match_count", "matched_cities", "matched_master_cities"]),
                        "unmatch_count": _extract(first, ["unmatch_count", "unmatched_cities", "unmatched_master_cities"]),
                        "_raw": first,
                    }
                    # Automatically copy any other keys from first into summary for direct access by frontend
                    for k, v in first.items():
                        if k not in summary and k != 'created_at':  # avoid datetime serialization issues implicitly
                            summary[k] = v
                all_summary = [dict(r._mapping) for r in summary_rows]
            except Exception as e:
                print(f"[WARN] Error reading {summary_table}: {e}")
                all_summary = []
        else:
            print("[WARN] No report_summery/report_summary table found")

        # ─── 2. Top Cities (from top_cities table) ──────────────────────
        cities = []
        cities_table = _find_table(available_tables, ["top_cities", "cities", "top_city"])
        
        if cities_table:
            try:
                cities_rows = session.execute(
                    text(f"SELECT * FROM `{cities_table}` ORDER BY 1")
                ).fetchall()
                for row in cities_rows:
                    d = dict(row._mapping)
                    cities.append({
                        "name":          _extract_str(d, ["city", "name", "city_name", "City", "Name"]),
                        "total_count":   _extract(d, ["total_count", "total", "count", "total_records", "Total", "Total_Count"]),
                        "missing_count": _extract(d, ["missing_count", "missing", "missing_records", "Missing", "Missing_Count"]),
                        "match_count":   _extract(d, ["match_count", "matched", "matched_count", "Match", "Match_Count"]),
                        "unmatch_count": _extract(d, ["unmatch_count", "unmatched", "unmatched_count", "Unmatch", "Unmatch_Count"]),
                        "_raw": d,
                    })
            except Exception as e:
                print(f"[WARN] Error reading {cities_table}: {e}")
        else:
            print("[WARN] No top_cities/cities table found")

        # ─── 3. Top Categories (from top_categories or categories table) ─
        categories = []
        cat_table = _find_table(available_tables, ["top_categories", "categories", "top_category", "category"])
        
        if cat_table:
            try:
                cat_rows = session.execute(
                    text(f"SELECT * FROM `{cat_table}` ORDER BY 1")
                ).fetchall()
                for row in cat_rows:
                    d = dict(row._mapping)
                    categories.append({
                        "name":          _extract_str(d, ["category", "name", "category_name", "Category", "Name"]),
                        "total_count":   _extract(d, ["total_count", "total", "count", "total_records", "Total", "Total_Count"]),
                        "missing_count": _extract(d, ["missing_count", "missing", "missing_records", "Missing", "Missing_Count"]),
                        "match_count":   _extract(d, ["match_count", "matched", "matched_count", "Match", "Match_Count"]),
                        "unmatch_count": _extract(d, ["unmatch_count", "unmatched", "unmatched_count", "Unmatch", "Unmatch_Count"]),
                        "_raw": d,
                    })
            except Exception as e:
                print(f"[WARN] Error reading {cat_table}: {e}")
        else:
            print("[WARN] No top_categories/categories table found")

        # ─── 4. Schema info (Disabled for performance) ──────────────────
        schema_info = {}
        # Avoid describing all tables as it was causing timeouts
        for tbl in [summary_table, cities_table, cat_table]:
            if tbl:
                try:
                    cols = session.execute(text(f"DESCRIBE `{tbl}`")).fetchall()
                    schema_info[tbl] = [{"field": r[0], "type": str(r[1])} for r in cols]
                except Exception:
                    schema_info[tbl] = "could not describe"

        # ─── 5. Top Cities Rank (from Top_cities_rank table) ──────────────
        top_cities_business_data = []
        try:
            # Check if table exists
            if _find_table(available_tables, ["top_cities_rank"]):
                top_cities_rank_rows = session.execute(
                    text("SELECT city_name, state_name, business_count, city_rank FROM `Top_cities_rank` ORDER BY city_rank ASC")
                ).fetchall()
                for row in top_cities_rank_rows:
                    top_cities_business_data.append({
                        "city_name": row[0],
                        "state_name": row[1],
                        "business_count": row[2],
                        "city_rank": row[3]
                    })
        except Exception as e:
            print(f"[WARN] Error reading Top_cities_rank: {e}")

        return jsonify({
            "status": "COMPLETED",
            "is_remote": is_remote,
            "summary": summary,
            "all_summary_rows": all_summary,
            "cities": cities,
            "categories": categories,
            "top_cities_business_data": top_cities_business_data,
            "schema_info": schema_info,
            "tables_found": available_tables,
            "tables_used": {
                "summary": summary_table,
                "cities": cities_table,
                "categories": cat_table,
            }
        })

    except Exception as e:
        traceback.print_exc()
        print(f"[ERROR] Aggregate Report Error: {str(e)}")
        return jsonify({
            "status": "ERROR",
            "message": str(e),
            "hint": "Database may be unreachable or table structure may have changed."
        }), 500
    finally:
        try:
            session.close()
        except Exception:
            pass


@report_aggregate_bp.route("/api/report/health", methods=["GET"])
def report_health_check():
    """Health check endpoint for the report database connection."""
    ok, info = test_report_db_connection()
    if ok:
        return jsonify({"status": "healthy", "details": info}), 200
    else:
        return jsonify({
            "status": "unhealthy",
            "error": info,
            "hint": "Port 3306 may be blocked by firewall. The database must allow connections from this server's IP."
        }), 503


# ─── Helper Functions ────────────────────────────────────────────────────────

def _find_table(available, candidates):
    """
    Given a list of available table names and a priority list of candidate names,
    return the first match (case-insensitive).
    """
    available_lower = {t.lower(): t for t in available}
    for c in candidates:
        if c.lower() in available_lower:
            return available_lower[c.lower()]
    return None


def _extract(d, keys, default=0):
    """
    Given a dict and a list of possible key names,
    return the value of the first matching key found.
    """
    for k in keys:
        if k in d:
            val = d[k]
            if val is None:
                return default
            try:
                return int(val) if float(val) == int(float(val)) else float(val)
            except (ValueError, TypeError):
                return val
    return default


def _extract_str(d, keys, default="—"):
    """
    Like _extract but returns the value as a string (for name fields).
    """
    for k in keys:
        if k in d:
            val = d[k]
            if val is None or str(val).strip() == "":
                continue
            return str(val)
    return default
