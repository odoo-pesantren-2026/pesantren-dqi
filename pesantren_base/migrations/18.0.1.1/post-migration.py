# -*- coding: utf-8 -*-
"""
Post-migration script for migrating jns_pegawai from Selection to Many2many.

This script:
1. Ensures all role master records exist
2. Migrates existing employee jns_pegawai values to jns_pegawai_ids
3. Validates the migration

Run this after upgrading the module to version 18.0.1.1
"""

import logging
from odoo import api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migrate employee roles from Selection field to Many2many relationship.
    
    :param cr: Database cursor
    :param version: Module version being migrated to
    """
    if version is None:
        return
    
    _logger.info("Starting migration of jns_pegawai from Selection to Many2many...")
    
    # Get environment from cursor
    env = api.Environment(cr, 1, {})
    
    try:
        # Get all employees with jns_pegawai set (use raw SQL to avoid computed field)
        cr.execute("""
            SELECT id, name, jns_pegawai 
            FROM hr_employee 
            WHERE jns_pegawai IS NOT NULL AND jns_pegawai != ''
        """)
        employees_data = cr.fetchall()
        
        if not employees_data:
            _logger.info("No employees found with jns_pegawai set. Migration skipped.")
            return
        
        _logger.info(f"Found {len(employees_data)} employees to migrate.")
        
        # Get role master records
        role_records = env['cdn.jenis_pegawai'].search([])
        role_by_code = {role.code: role.id for role in role_records}
        
        migrated_count = 0
        error_count = 0
        
        for emp_id, emp_name, jns_pegawai_value in employees_data:
            try:
                if not jns_pegawai_value:
                    continue
                
                # Parse comma-separated role codes
                codes = [c.strip() for c in jns_pegawai_value.split(',') if c.strip()]
                
                # Find corresponding role IDs
                role_ids = []
                missing_codes = []
                
                for code in codes:
                    if code in role_by_code:
                        role_ids.append(role_by_code[code])
                    else:
                        missing_codes.append(code)
                
                if missing_codes:
                    _logger.warning(
                        f"Employee {emp_name} (ID: {emp_id}) has roles without master records: {missing_codes}"
                    )
                
                # Assign roles to employee via M2M junction table
                if role_ids:
                    # Clear existing relationships
                    cr.execute("""
                        DELETE FROM hr_employee_jenis_pegawai_rel 
                        WHERE employee_id = %s
                    """, (emp_id,))
                    
                    # Insert new relationships
                    for role_id in role_ids:
                        cr.execute("""
                            INSERT INTO hr_employee_jenis_pegawai_rel 
                            (employee_id, jenis_pegawai_id) 
                            VALUES (%s, %s)
                        """, (emp_id, role_id))
                    
                    migrated_count += 1
                    role_names = [r.name for code, r in role_records.mapped(lambda x: (x.code, x)) if code in codes]
                    _logger.debug(
                        f"Migrated employee {emp_name} (ID: {emp_id}): "
                        f"{jns_pegawai_value} -> roles: {role_ids}"
                    )
                else:
                    _logger.warning(
                        f"Employee {emp_name} (ID: {emp_id}) has no valid roles to migrate"
                    )
                    error_count += 1
                    
            except Exception as e:
                _logger.error(
                    f"Error migrating employee {emp_name} (ID: {emp_id}): {str(e)}"
                )
                error_count += 1
        
        cr.commit()
        
        _logger.info(
            f"Migration completed: {migrated_count} employees migrated successfully, "
            f"{error_count} errors"
        )
        
    except Exception as e:
        _logger.error(f"Migration failed with error: {str(e)}")
        cr.rollback()
        raise

