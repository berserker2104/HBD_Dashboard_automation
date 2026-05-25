import os
import re
import traceback
import pandas as pd
import pdfplumber
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import text, create_engine
from config import config

listing_upload_bp = Blueprint('listing_upload_bp', __name__)

engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=280,
    pool_size=5,
    max_overflow=10,
)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'listing_files')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'xls', 'xlsx'}
MAX_ROWS_PER_UPLOAD = 5000


# ─────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def safe_str(val):
    """Convert a value to string, returning '' for None/NaN."""
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ''
    except Exception:
        pass
    return str(val).strip()


def extract_pincode(text_val):
    m = re.search(r'\b\d{6}\b', str(text_val))
    return m.group(0) if m else ''


# ─────────────────────────────────────────────────────────────
# Column name normalisation
# ─────────────────────────────────────────────────────────────

COLUMN_MAP = {
    'business_name': [
        'business name', 'entity name', 'asc name', 'icp name',
        'name', 'center name', 'shop name', 'company name',
    ],
    'contact': [
        'contact number', 'contact no', 'contact no.', 'mobile no',
        'mobile no.', 'phone no', 'phone no.', 'phone', 'mobile',
    ],
    'email':   ['email', 'email id', 'official email id'],
    'address': ['address', 'full address', 'location'],
    'category':['category', 'business category', 'type'],
    'city':    ['city'],
    'state':   ['state'],
    'pincode': ['pincode', 'pin code', 'post code', 'zip'],
}


def normalize_row(row_dict):
    norm = {k: '' for k in COLUMN_MAP}
    for raw_key, raw_val in row_dict.items():
        if not isinstance(raw_key, str):
            continue
        key_low = raw_key.strip().lower()
        val = safe_str(raw_val)
        for field, aliases in COLUMN_MAP.items():
            if key_low in aliases:
                if not norm[field]:   # first match wins
                    norm[field] = val
                break

    if not norm['pincode'] and norm['address']:
        norm['pincode'] = extract_pincode(norm['address'])

    return norm


# ─────────────────────────────────────────────────────────────
# File extractors
# ─────────────────────────────────────────────────────────────

def extract_from_csv(filepath):
    df = pd.read_csv(filepath, dtype=str).fillna('')
    return df.to_dict('records')


def extract_from_excel(filepath):
    df = pd.read_excel(filepath, dtype=str).fillna('')
    return df.to_dict('records')


def extract_from_pdf(filepath):
    """
    Extract rows from a multi-page PDF table.

    Key fix: The PDF has real column headers ONLY on page 1.
    Pages 2+ continue the same table without repeating headers.
    So we capture headers from page 1, then for all other pages
    we treat EVERY row (including the first) as a data row.
    """
    records = []
    global_headers = None  # shared header across all pages

    with pdfplumber.open(filepath) as pdf:
        for page_num, page in enumerate(pdf.pages):
            tbl = page.extract_table()

            if tbl and len(tbl) >= 1:
                if global_headers is None:
                    # Page 1: first row is the real header
                    global_headers = [
                        str(h).strip().lower() if h else f'col_{i}'
                        for i, h in enumerate(tbl[0])
                    ]
                    data_rows = tbl[1:]   # skip header row on page 1
                else:
                    # Pages 2+: NO header row — all rows are data
                    data_rows = tbl

                for row in data_rows:
                    # Pad short rows to match header length
                    padded = [str(c) if c else '' for c in row]
                    while len(padded) < len(global_headers):
                        padded.append('')
                    records.append(dict(zip(global_headers, padded[:len(global_headers)])))

            else:
                # No table detected — plain text fallback
                raw = page.extract_text()
                if raw:
                    for line in raw.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        # Try to map to known headers if we have them
                        if global_headers and '\t' in line:
                            parts = line.split('\t')
                            padded = parts + [''] * (len(global_headers) - len(parts))
                            records.append(dict(zip(global_headers, padded[:len(global_headers)])))
                        else:
                            parts = line.split(' - ', 1)
                            if len(parts) > 1:
                                records.append({
                                    'business name': parts[0].strip(),
                                    'address': parts[1].strip(),
                                })

    return records



# ─────────────────────────────────────────────────────────────
# Location master – load once, match in Python
# ─────────────────────────────────────────────────────────────

def load_location_master(conn):
    rows = conn.execute(
        text("SELECT state_full_name, city_name, area_name FROM Location_Master_India")
    ).fetchall()
    locs = []
    for r in rows:
        locs.append({
            'state':   r[0] or '',
            'city':    r[1] or '',
            'area':    r[2] or '',
            'state_l': (r[0] or '').lower().strip(),
            'city_l':  (r[1] or '').lower().strip(),
            'area_l':  (r[2] or '').lower().strip(),
        })
    return locs


def detect_location(norm, locations):
    """
    Returns (det_state, det_city, det_area, is_matched:bool)
    Priority: area > city+state > city > address scan
    """
    city_in  = norm.get('city',  '').lower().strip()
    state_in = norm.get('state', '').lower().strip()
    addr_l   = norm.get('address', '').lower()

    # P1: city + state exact match
    if city_in and state_in:
        cands = [l for l in locations if l['city_l'] == city_in and l['state_l'] == state_in]
        if cands:
            base = cands[0]
            for loc in cands:
                if loc['area_l'] and loc['area_l'] in addr_l:
                    return loc['state'], loc['city'], loc['area'], True
            return base['state'], base['city'], '', False

    # P2: city only
    if city_in:
        cands = [l for l in locations if l['city_l'] == city_in]
        if cands:
            base = cands[0]
            for loc in cands:
                if loc['area_l'] and loc['area_l'] in addr_l:
                    return loc['state'], loc['city'], loc['area'], True
            return base['state'], base['city'], '', False

    # P3: scan address for city name
    for loc in locations:
        if loc['city_l'] and loc['city_l'] in addr_l:
            if loc['area_l'] and loc['area_l'] in addr_l:
                return loc['state'], loc['city'], loc['area'], True
            return loc['state'], loc['city'], '', False

    # P4: scan address for area name
    for loc in locations:
        if loc['area_l'] and loc['area_l'] in addr_l:
            return loc['state'], loc['city'], loc['area'], False

    return '', '', '', False


# ─────────────────────────────────────────────────────────────
# master_table column inspector
# ─────────────────────────────────────────────────────────────

def get_master_columns(conn):
    rows = conn.execute(text("DESCRIBE master_table")).fetchall()
    return {r[0] for r in rows}


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@listing_upload_bp.route('', methods=['POST'])
def upload_listing_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: pdf, csv, xls, xlsx'}), 400

    source_name = request.form.get('source_name', 'Unknown Source')
    filename    = secure_filename(file.filename)
    filepath    = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    file_type = filename.rsplit('.', 1)[1].lower()

    upload_id = None
    try:
        # 1. Create history record
        with engine.begin() as conn:
            res = conn.execute(text("""
                INSERT INTO uploaded_listing_files
                    (file_name, source_name, file_type, upload_status)
                VALUES (:fn, :sn, :ft, 'processing')
            """), {'fn': filename, 'sn': source_name, 'ft': file_type})
            upload_id = res.lastrowid

        # 2. Extract rows
        if file_type == 'csv':
            raw_rows = extract_from_csv(filepath)
        elif file_type in ['xls', 'xlsx']:
            raw_rows = extract_from_excel(filepath)
        elif file_type == 'pdf':
            raw_rows = extract_from_pdf(filepath)
        else:
            raw_rows = []

        raw_rows = raw_rows[:MAX_ROWS_PER_UPLOAD]

        # 3. Load location master ONCE
        with engine.connect() as lc:
            locations = load_location_master(lc)

        # 4. Get master_table columns ONCE
        with engine.connect() as mc:
            master_cols = get_master_columns(mc)

        # 5. Process & insert
        total = inserted = updated = duplicates = loc_matched = loc_unmatched = 0

        with engine.begin() as conn:
            for raw in raw_rows:
                norm = normalize_row(raw)
                if not norm['business_name'] and not norm['address']:
                    continue

                total += 1

                det_state, det_city, det_area, is_loc_matched = detect_location(norm, locations)
                if is_loc_matched:
                    loc_matched += 1
                else:
                    loc_unmatched += 1

                bname   = norm['business_name']
                contact = norm['contact']
                addr    = norm['address']

                # Duplicate check: business_name + address (+ contact if present)
                if contact:
                    dup_row = conn.execute(text("""
                        SELECT id FROM master_table
                        WHERE LOWER(TRIM(business_name)) = :b
                          AND LOWER(TRIM(address))       = :a
                          AND LOWER(TRIM(primary_phone)) = :p
                        LIMIT 1
                    """), {
                        'b': bname.strip().lower(),
                        'a': addr.strip().lower(),
                        'p': contact.strip().lower(),
                    }).fetchone()
                else:
                    dup_row = conn.execute(text("""
                        SELECT id FROM master_table
                        WHERE LOWER(TRIM(business_name)) = :b
                          AND LOWER(TRIM(address))       = :a
                        LIMIT 1
                    """), {
                        'b': bname.strip().lower(),
                        'a': addr.strip().lower(),
                    }).fetchone()

                if dup_row:
                    # Optional: fill NULL fields on existing record
                    existing_id = dup_row[0]
                    existing = conn.execute(text(
                        "SELECT primary_phone, email, state, city, area, pincode FROM master_table WHERE id = :id"
                    ), {'id': existing_id}).mappings().fetchone()

                    update_parts = []
                    update_params = {'id': existing_id}

                    def queue_update(col, new_val, existing_val):
                        if new_val and not existing_val:
                            update_parts.append(f"{col} = :{col}")
                            update_params[col] = new_val

                    queue_update('primary_phone', contact,           existing['primary_phone'])
                    queue_update('email',         norm['email'],     existing['email'])
                    queue_update('state',         det_state,         existing['state'])
                    queue_update('city',          det_city,          existing['city'])
                    queue_update('area',          det_area,          existing['area'])
                    queue_update('pincode',       norm['pincode'],   existing['pincode'])

                    if update_parts:
                        conn.execute(text(
                            f"UPDATE master_table SET {', '.join(update_parts)} WHERE id = :id"
                        ), update_params)
                        updated += 1
                    else:
                        duplicates += 1
                    continue

                # Build INSERT dynamically using only columns that exist
                field_map = {
                    'business_name':  bname,
                    'primary_phone':  contact,
                    'email':          norm['email'],
                    'address':        addr,
                    'pincode':        norm['pincode'],
                    'state':          det_state,
                    'city':           det_city,
                    'area':           det_area,
                    'business_category': norm['category'] or 'Service Center',
                    'data_source':    source_name,
                }
                insert_cols   = {c: v for c, v in field_map.items() if c in master_cols and v}
                if not insert_cols:
                    continue

                col_list  = ', '.join(insert_cols.keys())
                val_list  = ', '.join(f':{c}' for c in insert_cols.keys())
                conn.execute(
                    text(f"INSERT INTO master_table ({col_list}) VALUES ({val_list})"),
                    insert_cols
                )
                inserted += 1

            # 6. Mark upload completed
            conn.execute(text("""
                UPDATE uploaded_listing_files SET
                    upload_status           = 'completed',
                    total_rows              = :tot,
                    inserted_rows           = :ins,
                    updated_rows            = :upd,
                    duplicate_rows          = :dup,
                    matched_location_rows   = :lm,
                    unmatched_location_rows = :lu
                WHERE id = :id
            """), {
                'tot': total, 'ins': inserted, 'upd': updated,
                'dup': duplicates, 'lm': loc_matched, 'lu': loc_unmatched,
                'id': upload_id,
            })

        return jsonify({
            'message':               'File uploaded and imported successfully',
            'upload_file_id':        upload_id,
            'total_rows':            total,
            'inserted_rows':         inserted,
            'updated_rows':          updated,
            'duplicate_rows':        duplicates,
            'matched_location_rows': loc_matched,
            'unmatched_location_rows': loc_unmatched,
        }), 200

    except Exception as e:
        print(f"[listing_upload] FATAL: {traceback.format_exc()}")
        if upload_id:
            try:
                with engine.begin() as fail_conn:
                    fail_conn.execute(text("""
                        UPDATE uploaded_listing_files
                        SET upload_status = 'failed', error_message = :err
                        WHERE id = :id
                    """), {'err': str(e)[:1000], 'id': upload_id})
            except Exception as fe:
                print(f"[listing_upload] Could not mark failed: {fe}")
        return jsonify({'error': 'Upload failed', 'details': str(e)}), 500


@listing_upload_bp.route('/history', methods=['GET'])
def get_history():
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, file_name, source_name, file_type, upload_status,
                   total_rows, inserted_rows, updated_rows, duplicate_rows,
                   matched_location_rows, unmatched_location_rows,
                   error_message, created_at
            FROM uploaded_listing_files
            ORDER BY id DESC
        """)).mappings().all()
        result = []
        for r in rows:
            row = dict(r)
            if row.get('created_at'):
                row['created_at'] = str(row['created_at'])
            result.append(row)
        return jsonify(result)

