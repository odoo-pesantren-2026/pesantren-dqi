# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration script to link existing cdn.jenis_pegawai records to XML IDs.
    This prevents UniqueViolation errors when the module is upgraded.
    """
    if not version:
        return

    _logger.info(
        "Running pre-migration script to link cdn.jenis_pegawai records...")

    # Check if table exists before querying.
    # This prevents UndefinedTable errors during the module's first installation
    # or if the table hasn't been created yet in the database.
    cr.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = 'cdn_jenis_pegawai'")
    if not cr.fetchone():
        _logger.info(
            "Table 'cdn_jenis_pegawai' does not exist yet. Skipping pre-migration linking.")
        return

    # Mapping of XML IDs to their corresponding codes
    # These must match pesantren_base/data/jenis_pegawai_data.xml
    roles_to_handle = [
        ('jenis_pegawai_musyrif', 'musyrif'),
        ('jenis_pegawai_guru', 'guru'),
        ('jenis_pegawai_guruquran', 'guruquran'),
        ('jenis_pegawai_keamanan', 'keamanan'),
        ('jenis_pegawai_superadmin', 'superadmin'),
    ]

    for xml_id, code in roles_to_handle:
        # Check if record exists in the table using raw SQL
        cr.execute("SELECT id FROM cdn_jenis_pegawai WHERE code = %s", (code,))
        row = cr.fetchone()
        if row:
            res_id = row[0]
            # Check if XML ID already exists in ir_model_data
            cr.execute(
                "SELECT id FROM ir_model_data WHERE module = 'pesantren_base' AND name = %s", (xml_id,))
            if not cr.fetchone():
                _logger.info(
                    "Linking existing record for role '%s' (ID: %s) to XML ID 'pesantren_base.%s'", code, res_id, xml_id)
                # Link existing record to XML ID
                cr.execute("""
                    INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
                    VALUES ('pesantren_base', %s, 'cdn.jenis_pegawai', %s, true)
                """, (xml_id, res_id))
            else:
                _logger.debug(
                    "XML ID 'pesantren_base.%s' already exists for role '%s'", xml_id, code)
        else:
            _logger.debug(
                "No existing record found for role '%s', Odoo will create it normally.", code)

    _logger.info("Pre-migration script for cdn.jenis_pegawai completed.")
