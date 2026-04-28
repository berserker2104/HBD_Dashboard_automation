from flask import Flask,request,jsonify,Blueprint
from tasks.products_task.upload_blinkit_task import process_blinkit_task
from werkzeug.utils import secure_filename
import os 
from utils.storage import get_upload_base_dir

from model.product_model.additional_products import Blinkit

blinkit_bp = Blueprint("blinkit_bp",__name__)

@blinkit_bp.route('/fetch-data', methods=['GET'])
def fetch_blinkit_data():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        category = request.args.get('category', '')

        query = Blinkit.query
        
        if search:
            query = query.filter(Blinkit.product.ilike(f"%{search}%"))
        if category:
            query = query.filter(Blinkit.category.ilike(f"%{category}%"))
        
        pagination = query.paginate(page=page, per_page=limit, error_out=False)
        return jsonify({
            "status": "success",
            "data": [item.to_dict() for item in pagination.items],
            "total_pages": pagination.pages,
            "total_count": pagination.total,
            "current_page": page
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@blinkit_bp.route("/upload/blinkit-data",methods=["POST"])
def upload_blinkit_route():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error":"No files provided"}),400
    UPLOAD_DIR = get_upload_base_dir()/"blinkit"
    UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
    paths = []
    for f in files:
        filename = secure_filename(f.filename)
        filepath = UPLOAD_DIR/filename
        f.save(filepath)
        paths.append(str(filepath))
    try:
        task = process_blinkit_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id":task.id
            }),202
    except Exception as e:
        return jsonify({
            "error":str(e)
        }),500