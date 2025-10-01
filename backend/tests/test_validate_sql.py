from database import validate_sql

def test_valid_select_query():
    sql = 'SELECT ssp5_10yr FROM "FloodRisk" LIMIT 10;'
    assert validate_sql(sql) is True

def test_invalid_update_query():
    sql = 'UPDATE "FloodRisk" SET ssp5_10yr = 0;'
    assert validate_sql(sql) is False

def test_invalid_table_name():
    sql = 'SELECT * FROM "HackTable";'
    assert validate_sql(sql) is False
