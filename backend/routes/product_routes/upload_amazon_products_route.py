from flask import Blueprint, request, jsonify
from sqlalchemy import text, create_engine
from config import config

amazon_bp = Blueprint('amazon_bp', __name__)

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=280,
)

@amazon_bp.route('/fetch-data', methods=['GET'])
def fetch_amazon_data():
    try:
        page     = request.args.get('page', 1, type=int)
        limit    = request.args.get('limit', 50, type=int)
        search   = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()

        offset = (page - 1) * limit

        # Build WHERE clause
        conditions = []
        params = {'limit': limit, 'offset': offset}

        if search:
            conditions.append("title LIKE :search")
            params['search'] = f"%{search}%"

        if category:
            conditions.append("categoryName LIKE :category")
            params['category'] = f"%{category}%"

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        with engine.connect() as conn:
            total = conn.execute(
                text(f"SELECT COUNT(*) FROM amazon_products {where}"),
                params
            ).scalar()

            rows = conn.execute(
                text(f"""
                    SELECT id, asin, title, stars, reviews, price, listPrice,
                           categoryName, isBestSeller, boughtInLastMonth,
                           imgUrl, productUrl
                    FROM amazon_products
                    {where}
                    ORDER BY id DESC
                    LIMIT :limit OFFSET :offset
                """),
                params
            ).mappings().fetchall()

        data = []
        for r in rows:
            data.append({
                "id":               r["id"],
                "asin":             r["asin"] or "",
                "title":            r["title"] or "",
                "stars":            float(r["stars"]) if r["stars"] else None,
                "reviews":          r["reviews"] or 0,
                "price":            float(r["price"]) if r["price"] else None,
                "listPrice":        float(r["listPrice"]) if r["listPrice"] else None,
                "categoryName":     r["categoryName"] or "",
                "isBestSeller":     bool(r["isBestSeller"]),
                "boughtInLastMonth":r["boughtInLastMonth"] or 0,
                "imgUrl":           r["imgUrl"] or "",
                "productUrl":       r["productUrl"] or "",
            })

        total_pages = max(1, (total + limit - 1) // limit)

        return jsonify({
            "status":       "success",
            "data":         data,
            "total_count":  total,
            "total_pages":  total_pages,
            "current_page": page,
        }), 200

    except Exception as e:
        import traceback
        print(f"Amazon Route Error: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500