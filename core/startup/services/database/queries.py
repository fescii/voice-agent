"""
PostgreSQL query utilities for database service.
"""
from sqlalchemy import text

# Basic health check query
HEALTH_CHECK_QUERY = text("SELECT 1")

# Version information query
VERSION_QUERY = text("SELECT version()")

# Connection count query
CONNECTION_COUNT_QUERY = text("SELECT count(*) FROM pg_stat_activity")

# Database statistics query
DATABASE_STATS_QUERY = text("""
    SELECT 
        current_database() as database_name,
        pg_size_pretty(pg_database_size(current_database())) as database_size,
        (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()) as connections
""")

# Schema list query (excluding system schemas)
SCHEMA_LIST_QUERY = text("""
    SELECT schema_name 
    FROM information_schema.schemata 
    WHERE schema_name NOT LIKE 'pg_%' 
        AND schema_name != 'information_schema'
""")

# Table list query with column counts
TABLE_LIST_QUERY = text("""
    SELECT 
        table_schema, 
        table_name, 
        (SELECT count(*) FROM information_schema.columns 
         WHERE table_schema = t.table_schema AND table_name = t.table_name) as column_count
    FROM information_schema.tables t
    WHERE table_schema NOT LIKE 'pg_%' 
        AND table_schema != 'information_schema'
        AND table_type = 'BASE TABLE'
""")

# Table size information
TABLE_SIZE_QUERY = text("""
    SELECT 
        table_schema, 
        table_name, 
        pg_size_pretty(pg_total_relation_size('"' || table_schema || '"."' || table_name || '"')) as total_size
    FROM information_schema.tables
    WHERE table_schema NOT LIKE 'pg_%' 
        AND table_schema != 'information_schema'
        AND table_type = 'BASE TABLE'
    ORDER BY pg_total_relation_size('"' || table_schema || '"."' || table_name || '"') DESC
""")

# Index information
INDEX_INFO_QUERY = text("""
    SELECT
        schemaname as schema_name,
        relname as table_name,
        indexrelname as index_name,
        idx_scan as index_scans
    FROM pg_stat_all_indexes
    WHERE schemaname NOT LIKE 'pg_%'
        AND schemaname != 'information_schema'
    ORDER BY idx_scan DESC
""")
