"""
Management command to schedule automatic backups for tenants.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from tenants.models import Tenant, TenantConfiguration


logger = logging.getLogger('tenants.backup')


class Command(BaseCommand):
    help = 'Schedule automatic backups for tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            dest='tenant_id',
            help='ID or subdomain of the tenant to schedule (omit for all tenants)'
        )
        parser.add_argument(
            '--frequency',
            dest='frequency',
            choices=['daily', 'weekly', 'monthly'],
            default='daily',
            help='Backup frequency (default: daily)'
        )
        parser.add_argument(
            '--time',
            dest='time',
            default='03:00',
            help='Time of day for backup in 24h format (default: 03:00)'
        )
        parser.add_argument(
            '--day',
            dest='day',
            type=int,
            help='Day of week (1-7) for weekly backups or day of month (1-31) for monthly backups'
        )
        parser.add_argument(
            '--retention',
            dest='retention',
            type=int,
            default=30,
            help='Number of days to retain backups (default: 30)'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            dest='list_schedules',
            default=False,
            help='List current backup schedules'
        )
        parser.add_argument(
            '--disable',
            action='store_true',
            dest='disable',
            default=False,
            help='Disable scheduled backups for specified tenant(s)'
        )

    def handle(self, *args, **options):
        tenant_id = options['tenant_id']
        frequency = options['frequency']
        time = options['time']
        day = options['day']
        retention = options['retention']
        list_schedules = options['list_schedules']
        disable = options['disable']

        # Validate time format
        try:
            hour, minute = map(int, time.split(':'))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
        except ValueError:
            raise CommandError("Time must be in 24h format (HH:MM)")

        # Validate day based on frequency
        if frequency == 'weekly' and day is not None:
            if day < 1 or day > 7:
                raise CommandError("Day of week must be between 1 (Monday) and 7 (Sunday)")
        elif frequency == 'monthly' and day is not None:
            if day < 1 or day > 31:
                raise CommandError("Day of month must be between 1 and 31")

        # Get tenant(s)
        if tenant_id:
            try:
                # Try to get by ID first
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                except (Tenant.DoesNotExist, ValueError):
                    # If not found or not a valid UUID, try by subdomain
                    tenant = Tenant.objects.get(subdomain=tenant_id)
                tenants = [tenant]
            except Tenant.DoesNotExist:
                raise CommandError(f"Tenant with ID or subdomain '{tenant_id}' not found")
        else:
            # All active tenants
            tenants = Tenant.objects.filter(is_active=True)
            if not tenants.exists():
                self.stdout.write(self.style.WARNING("No active tenants found"))
                return

        # List schedules if requested
        if list_schedules:
            self._list_backup_schedules(tenants)
            return

        # Disable schedules if requested
        if disable:
            self._disable_backup_schedules(tenants)
            return

        # Schedule backups
        for tenant in tenants:
            try:
                self._schedule_tenant_backup(tenant, frequency, time, day, retention)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Scheduled {frequency} backup for tenant '{tenant.name}' at {time}"
                    )
                )
            except Exception as e:
                logger.error(f"Error scheduling backup for tenant {tenant.name}: {str(e)}", exc_info=True)
                self.stdout.write(
                    self.style.ERROR(f"Failed to schedule backup for tenant '{tenant.name}': {str(e)}")
                )

    def _schedule_tenant_backup(self, tenant, frequency, time, day, retention):
        """
        Schedule automatic backup for a tenant
        
        Args:
            tenant: Tenant instance
            frequency: Backup frequency (daily, weekly, monthly)
            time: Time of day for backup (HH:MM)
            day: Day of week/month (depends on frequency)
            retention: Number of days to retain backups
        """
        # Create backup schedule configuration
        schedule = {
            'enabled': True,
            'frequency': frequency,
            'time': time,
            'retention_days': retention
        }
        
        if frequency == 'weekly' and day is not None:
            schedule['day_of_week'] = day
        elif frequency == 'monthly' and day is not None:
            schedule['day_of_month'] = day
        
        # Save schedule in tenant configuration
        TenantConfiguration.set_config(
            tenant=tenant,
            key='backup_schedule',
            value=json.dumps(schedule),
            config_type='json'
        )
        
        # Set next backup time
        next_backup = self._calculate_next_backup_time(schedule)
        
        TenantConfiguration.set_config(
            tenant=tenant,
            key='next_scheduled_backup',
            value=next_backup.isoformat(),
            config_type='string'
        )

    def _disable_backup_schedules(self, tenants):
        """
        Disable backup schedules for tenants
        
        Args:
            tenants: List of tenant instances
        """
        for tenant in tenants:
            try:
                # Get existing schedule
                schedule_config = TenantConfiguration.get_config(tenant, 'backup_schedule')
                
                if schedule_config:
                    # Update schedule to disabled
                    schedule = schedule_config.copy() if isinstance(schedule_config, dict) else {}
                    schedule['enabled'] = False
                    
                    # Save updated schedule
                    TenantConfiguration.set_config(
                        tenant=tenant,
                        key='backup_schedule',
                        value=json.dumps(schedule),
                        config_type='json'
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"Disabled backup schedule for tenant '{tenant.name}'")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"No backup schedule found for tenant '{tenant.name}'")
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to disable backup for tenant '{tenant.name}': {str(e)}")
                )

    def _list_backup_schedules(self, tenants):
        """
        List backup schedules for tenants
        
        Args:
            tenants: List of tenant instances
        """
        self.stdout.write("\nCurrent Backup Schedules:")
        self.stdout.write("-" * 80)
        self.stdout.write(f"{'Tenant':<30} {'Status':<10} {'Frequency':<10} {'Time':<10} {'Next Backup':<20}")
        self.stdout.write("-" * 80)
        
        for tenant in tenants:
            try:
                # Get schedule configuration
                schedule_config = TenantConfiguration.get_config(tenant, 'backup_schedule')
                next_backup = TenantConfiguration.get_config(tenant, 'next_scheduled_backup')
                
                if schedule_config:
                    status = "Enabled" if schedule_config.get('enabled', False) else "Disabled"
                    frequency = schedule_config.get('frequency', 'N/A')
                    time = schedule_config.get('time', 'N/A')
                    
                    # Format day information if applicable
                    if frequency == 'weekly' and 'day_of_week' in schedule_config:
                        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        day_idx = schedule_config['day_of_week'] - 1
                        if 0 <= day_idx < len(day_names):
                            frequency = f"{frequency} ({day_names[day_idx]})"
                    elif frequency == 'monthly' and 'day_of_month' in schedule_config:
                        frequency = f"{frequency} (day {schedule_config['day_of_month']})"
                    
                    # Format next backup time
                    next_backup_str = "Not scheduled"
                    if next_backup:
                        try:
                            dt = datetime.fromisoformat(next_backup)
                            next_backup_str = dt.strftime('%Y-%m-%d %H:%M')
                        except (ValueError, TypeError):
                            next_backup_str = str(next_backup)
                    
                    self.stdout.write(
                        f"{tenant.name:<30} {status:<10} {frequency:<10} {time:<10} {next_backup_str:<20}"
                    )
                else:
                    self.stdout.write(
                        f"{tenant.name:<30} {'Not set':<10} {'-':<10} {'-':<10} {'-':<20}"
                    )
            except Exception as e:
                self.stdout.write(
                    f"{tenant.name:<30} {'ERROR':<10} {str(e):<40}"
                )
        
        self.stdout.write("-" * 80)

    def _calculate_next_backup_time(self, schedule):
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
            next_backup += timedelta(days=1)
        
        # Adjust based on frequency
        if frequency == 'weekly' and 'day_of_week' in schedule:
            # Convert day_of_week (1-7, Monday=1) to Python's weekday (0-6, Monday=0)
            target_weekday = schedule['day_of_week'] - 1
            current_weekday = next_backup.weekday()
            
            # Calculate days to add to reach target weekday
            days_to_add = (target_weekday - current_weekday) % 7
            if days_to_add == 0 and next_backup <= now:
                days_to_add = 7  # Next week if today's weekday but time has passed
                
            next_backup += timedelta(days=days_to_add)
            
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
                
                last_day = (datetime(next_year, next_month, 1) - timedelta(days=1)).day
                next_backup = next_backup.replace(day=min(target_day, last_day))
        
        return next_backup