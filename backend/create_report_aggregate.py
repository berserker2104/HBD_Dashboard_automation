"""
Script to create and populate the report_aggregate table for the REPORT dashboard.
"""
import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='local_dashboard', password='darshit@1912', database='local_dashboard')
cursor = conn.cursor()

# Create the aggregate report table
cursor.execute("""
CREATE TABLE IF NOT EXISTS report_aggregate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    metric_key VARCHAR(500) NOT NULL,
    total_count INT DEFAULT 0,
    missing_count INT DEFAULT 0,
    match_count INT DEFAULT 0,
    unmatch_count INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_metric (metric_type, metric_key(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
print("Table created.")

# Clear and rebuild
cursor.execute("TRUNCATE TABLE report_aggregate")

# ========== 1. OVERALL SUMMARY ==========
cursor.execute("""
INSERT INTO report_aggregate (metric_type, metric_key, total_count, missing_count, match_count, unmatch_count)
SELECT 
    'summary' as metric_type,
    'overall' as metric_key,
    COUNT(*) as total_count,
    SUM(CASE WHEN (phone_number IS NULL OR phone_number = '') AND (website IS NULL OR website = '') THEN 1 ELSE 0 END) as missing_count,
    SUM(CASE WHEN phone_number IS NOT NULL AND phone_number != '' THEN 1 ELSE 0 END) as match_count,
    SUM(CASE WHEN phone_number IS NULL OR phone_number = '' THEN 1 ELSE 0 END) as unmatch_count
FROM g_map_master_table
""")
print("1. Summary done")

# ========== 2. TOP CITIES ==========
cursor.execute("""
INSERT INTO report_aggregate (metric_type, metric_key, total_count, missing_count, match_count, unmatch_count)
SELECT 
    'city' as metric_type,
    city as metric_key,
    COUNT(*) as total_count,
    SUM(CASE WHEN (phone_number IS NULL OR phone_number = '') AND (website IS NULL OR website = '') THEN 1 ELSE 0 END) as missing_count,
    SUM(CASE WHEN phone_number IS NOT NULL AND phone_number != '' THEN 1 ELSE 0 END) as match_count,
    SUM(CASE WHEN phone_number IS NULL OR phone_number = '' THEN 1 ELSE 0 END) as unmatch_count
FROM g_map_master_table
WHERE city IS NOT NULL AND city != ''
GROUP BY city
ORDER BY total_count DESC
LIMIT 50
""")
print("2. Cities done")

# ========== 3. TOP CATEGORIES ==========
cursor.execute("""
INSERT INTO report_aggregate (metric_type, metric_key, total_count, missing_count, match_count, unmatch_count)
SELECT 
    'category' as metric_type,
    category as metric_key,
    COUNT(*) as total_count,
    SUM(CASE WHEN (phone_number IS NULL OR phone_number = '') AND (website IS NULL OR website = '') THEN 1 ELSE 0 END) as missing_count,
    SUM(CASE WHEN phone_number IS NOT NULL AND phone_number != '' THEN 1 ELSE 0 END) as match_count,
    SUM(CASE WHEN phone_number IS NULL OR phone_number = '' THEN 1 ELSE 0 END) as unmatch_count
FROM g_map_master_table
WHERE category IS NOT NULL AND category != ''
GROUP BY category
ORDER BY total_count DESC
LIMIT 50
""")
print("3. Categories done")

# ========== 4. TOP GLOBAL RECORDS ==========
cursor.execute("""
INSERT INTO report_aggregate (metric_type, metric_key, total_count, missing_count, match_count, unmatch_count)
SELECT 
    'global_record' as metric_type,
    CONCAT(name, ' | ', COALESCE(city,''), ' | ', COALESCE(category,'')) as metric_key,
    COALESCE(reviews_count, 0) as total_count,
    CAST(COALESCE(reviews_avg, 0) * 10 AS UNSIGNED) as missing_count,
    CASE WHEN phone_number IS NOT NULL AND phone_number != '' THEN 1 ELSE 0 END as match_count,
    id as unmatch_count
FROM g_map_master_table
WHERE name IS NOT NULL AND name != '' AND reviews_count IS NOT NULL AND reviews_count > 50
ORDER BY reviews_count DESC, reviews_avg DESC
LIMIT 25
""")
print("4. Global records done")

conn.commit()

# Verify
cursor.execute("SELECT metric_type, COUNT(*) FROM report_aggregate GROUP BY metric_type")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} rows")

cursor.execute("SELECT total_count, missing_count, match_count, unmatch_count FROM report_aggregate WHERE metric_type='summary'")
s = cursor.fetchone()
print(f"  Summary -> Total: {s[0]:,} | Missing: {s[1]:,} | Match: {s[2]:,} | Unmatch: {s[3]:,}")

conn.close()
print("Aggregate table created and populated!")
