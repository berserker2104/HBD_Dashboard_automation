from flask import Flask,request,jsonify,Blueprint
from tasks.products_task.upload_jio_mart_task import process_jio_mart_products_task
from werkzeug.utils import secure_filename
import os 
from utils.storage import get_upload_base_dir

from model.product_model.additional_products import JioMart

jiomart_bp = Blueprint("jiomart_bp",__name__)

@jiomart_bp.route('/fetch-data', methods=['GET'])
def fetch_jiomart_data():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '')
        category = request.args.get('category', '')

        query = JioMart.query
        
        if search:
            query = query.filter(JioMart.title.ilike(f"%{search}%"))
        if category:
            query = query.filter(JioMart.categoryName.ilike(f"%{category}%"))
        
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

@jiomart_bp.route("/upload/jio-mart-data",methods=["POST"])
def upload_jio_mart_products_route():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error":"No files provided"}),400
    UPLOAD_DIR = get_upload_base_dir()/"jio-mart"
    UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
    paths = []
    for f in files:
        filename = secure_filename(f.filename)
        filepath = UPLOAD_DIR/filename
        f.save(filepath)
        paths.append(str(filepath))
    try:
        task = process_jio_mart_products_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id":task.id
            }),202
    except Exception as e:
        return jsonify({
            "error":str(e)
        }),500