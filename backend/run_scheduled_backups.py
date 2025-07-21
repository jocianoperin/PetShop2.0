#!/usr/bin/env python
"""
Script to run scheduled tenant backups.
This script is designed to be run by a cron job or similar scheduler.
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
import django
django.setup()

from django.utils import timezone
from django.conf import settings
from django.core.management import call_command

from tenants.models import Tenant, TenantConfiguration


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(settings.BASE_DIR, 'logs', 'scheduled_backups.log'))
    ]
)
logger = logging.getLogger('scheduled_backups')


def run_scheduled_backups():
    """Run scheduled backups for tenants"""
    logger.info("Starting scheduled backup check")
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.join(settings.BASE_DIR, 'logs'), exist_ok=True)
    
    # Get all active tenants
    tenants = Tenant.objects.filter(is_active=True)
    
    backups_run = 0
    errors = 0
    
    for tenant in tenants:
        try:
            # Get backup schedule
            schedule_config = TenantConfiguration.get_config(tenant, 'backup_schedule')
            next_backup = TenantConfiguration.get_config(tenant, 'next_scheduled_backup')
            
            if not schedule_config or not schedule_config.get('enabled', False):
                continue
            
            # Check if it's time for backup
            if next_backup:
                try:
                    next_backup_time = datetime.datetime.fromisoformat(next_backup)
                    now = timezone.now()
                    
                    if next_backup_time <= now:
                        # Time to run backup
                        logger.info(f"Running scheduled backup for tenant: {tenant.name}")
                        
                        # Determine backup directory
                        backup_dir = getattr(settings, 'BACKUP_DIR', None)
                        if backup_dir is None:
                            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
                        
                        # Run backup command
                        call_command(
                            'backup_tenant',
                            tenant_id=str(tenant.id),
                            output_dir=backup_dir,
                            compress=True
                        )
                        
                        # Calculate next backup time
                        next_backup_time = calculate_next_backup_time(schedule_config)
                        
                        # Update next backup time
                        TenantConfiguration.set_config(
                            tenant=tenant,
                            key='next_scheduled_backup',
                            value=next_backup_time.isoformat(),
                            config_type='string'
                        )
                        
                        logger.info(f"Backup completed for tenant: {tenant.name}")
                        logger.info(f"Next backup scheduled for: {next_backup_time.isoformat()}")
                        
                        backups_run += 1
                        
                        # Clean up old backups based on retention policy
                        retention_days = schedule_config.get('retention_days', 30)
                        clean_old_backups(tenant, retention_days)
                        
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid next_backup format for tenant {tenant.name}: {str(e)}")
                    errors += 1
        except Exception as e:
            logger.error(f"Error processing tenant {tenant.name}: {str(e)}", exc_info=True)
            errors += 1
    
    logger.info(f"Scheduled backup check completed. Backups run: {backups_run}, Errors: {errors}")


def calculate_next_backup_time(schedule):
    """
    Calculate the next backup time based on schedule
    
    Args:
        schedule: Backup schedule configuration
        
    Returns:
        datetime: Next backup time
    """
    now = timezone.now()
    frequency = schedule.get('frequency', 'daily')
    time_str = schedule.get('time', '03:00')
    
    # Parse time
    hour, minute = map(int, time_str.split(':'))
    
    # Start with today at the specified time
    next_backup = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If that time has already passed today, start from tomorrow
    if next_backup <= now:
        next_backup += datetime.timedelta(days=1)
    
    # Adjust based on frequency
    if frequency == 'weekly' and 'day_of_week' in schedule:
        # Convert day_of_week (1-7, Monday=1) to Python's weekday (0-6, Monday=0)
        target_weekday = schedule['day_of_week'] - 1
        current_weekday = next_backup.weekday()
        
        # Calculate days to add to reach target weekday
        days_to_add = (target_weekday - current_weekday) % 7
        if days_to_add == 0 and next_backup <= now:
            days_to_add = 7  # Next week if today's weekday but time has passed
            
        next_backup += datetime.timedelta(days=days_to_add)
        
    elif frequency == 'monthly' and 'day_of_month' in schedule:
        target_day = min(schedule['day_of_month'], 28)  # Cap at 28 to handle February
        
        # If current day is past target day, move to next month
        if next_backup.day > target_day or (next_backup.day == target_day and next_backup <= now):
            # Move to first day of next month
            if next_backup.month == 12:
                next_backup = next_backup.replace(year=next_backup.year + 1, month=1, day=1)
            else:
                next_backup = next_backup.replace(month=next_backup.month + 1, day=1)
        
        # Set to target day
        try:
            next_backup = next_backup.replace(day=target_day)
        except ValueError:
            # Handle case where target day doesn't exist in this month (e.g., Feb 30)
            # Use last day of month instead
            if next_backup.month == 12:
                next_month = 1
                next_year = next_backup.year + 1
            else:
                next_month = next_backup.month + 1
                next_year = next_backup.year
            
            last_day = (datetime.datetime(next_year, next_month, 1) - datetime.timedelta(days=1)).day
            next_backup = next_backup.replace(day=min(target_day, last_day))
    
    return next_backup


def clean_old_backups(tenant, retention_days):
    """
    Clean up old backups based on retention policy
    
    Args:
        tenant: Tenant instance
        retention_days: Number of days to retain backups
    """
    try:
        # Determine backup directory
        backup_dir = getattr(settings, 'BACKUP_DIR', None)
        if backup_dir is None:
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        
        tenant_backup_dir = os.path.join(backup_dir, tenant.schema_name)
        if not os.path.exists(tenant_backup_dir):
            return
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - datetime.timedelta(days=retention_days)
        
        # Find and delete old backup files
        deleted_count = 0
        for filename in os.listdir(tenant_backup_dir):
            file_path = os.path.join(tenant_backup_dir, filename)
            
            # Skip directories and non-backup files
            if os.path.isdir(file_path) or not (filename.endswith('.json') or filename.endswith('.json.gz')):
                continue
            
            # Extract timestamp from filename (format: schema_name_YYYYMMDD_HHMMSS.json[.gz])
            try:
                # Parse timestamp from filename
                parts = filename.split('_')
                if len(parts) >= 3:
                    timestamp_str = parts[-2] + '_' + parts[-1].split('.')[0]
                    file_date = datetime.datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    
                    # Check if file is older than retention period
                    if file_date < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
            except (ValueError, IndexError):
                # Skip files with invalid naming format
                continue
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backup files for tenant {tenant.name}")
            
    except Exception as e:
        logger.error(f"Error cleaning old backups for tenant {tenant.name}: {str(e)}")


if __name__ == '__main__':
    run_scheduled_backups()