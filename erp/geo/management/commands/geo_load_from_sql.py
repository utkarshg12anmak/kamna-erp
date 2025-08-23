"""
One-time DB loader for geo data from SQL files.

Usage:
    python manage.py geo_load_from_sql --sql-file path/to/geo_data.sql [--dry-run]

Features:
- Loads State→City→Pincode data from SQL INSERT statements
- Parses SQL and extracts data safely (no SQL execution)
- Dry-run mode for validation without database changes
- Respects existing data (no duplicates)
- Progress tracking and error reporting
- Uses model normalization and validation
"""
import re
import os
from typing import Dict, List, Tuple, Optional
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from geo.models import State, City, Pincode

User = get_user_model()


class Command(BaseCommand):
    help = 'Load geo data from SQL file (one-time loader)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sql-file',
            type=str,
            required=True,
            help='Path to SQL file containing INSERT statements'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and validate data without saving to database'
        )
        parser.add_argument(
            '--created-by',
            type=str,
            default='system',
            help='Username for audit trail (default: system)'
        )

    def handle(self, *args, **options):
        sql_file = options['sql_file']
        dry_run = options['dry_run']
        created_by_username = options['created_by']
        
        # Validate SQL file exists
        if not os.path.exists(sql_file):
            raise CommandError(f"SQL file not found: {sql_file}")
        
        # Get or create user for audit trail
        try:
            created_by_user = User.objects.get(username=created_by_username)
        except User.DoesNotExist:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"User '{created_by_username}' not found. "
                        "In actual run, you'll need a valid user for audit trail."
                    )
                )
                created_by_user = None
            else:
                raise CommandError(
                    f"User '{created_by_username}' not found. "
                    "Create user first or specify existing username with --created-by"
                )
        
        # Parse SQL file
        self.stdout.write(f"Parsing SQL file: {sql_file}")
        geo_data = self._parse_sql_file(sql_file)
        
        # Display statistics
        states_count = len(geo_data)
        cities_count = sum(len(cities) for cities in geo_data.values())
        pincodes_count = sum(
            len(pincodes) 
            for cities in geo_data.values() 
            for pincodes in cities.values()
        )
        
        self.stdout.write(
            f"Parsed: {states_count} states, {cities_count} cities, {pincodes_count} pincodes"
        )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS("DRY RUN - No data saved to database")
            )
            return
        
        # Load data to database
        self.stdout.write("Loading data to database...")
        with transaction.atomic():
            stats = self._load_to_database(geo_data, created_by_user)
        
        # Display results
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully loaded: "
                f"{stats['states_created']} states, "
                f"{stats['cities_created']} cities, "
                f"{stats['pincodes_created']} pincodes"
            )
        )
        
        if stats['skipped'] > 0:
            self.stdout.write(
                self.style.WARNING(f"Skipped {stats['skipped']} existing records")
            )

    def _parse_sql_file(self, sql_file: str) -> Dict[str, Dict[str, List[str]]]:
        """
        Parse SQL file and extract geo data.
        
        Expected format patterns:
        - INSERT INTO states (...) VALUES ('UP', 'Uttar Pradesh');
        - INSERT INTO cities (...) VALUES ('UP', 'Agra');
        - INSERT INTO pincodes (...) VALUES ('UP', 'Agra', '282001');
        
        Returns:
        {
            'state_code': {
                'state_name': state_name,
                'cities': {
                    'city_name': ['pincode1', 'pincode2', ...]
                }
            }
        }
        """
        geo_data = {}
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove comments and normalize whitespace
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = ' '.join(content.split())
        
        # Parse INSERT statements
        # Pattern for INSERT INTO table_name (...) VALUES (...);
        insert_pattern = r'INSERT\s+INTO\s+(\w+)\s*\([^)]*\)\s*VALUES\s*\(([^)]+)\)'
        
        for match in re.finditer(insert_pattern, content, re.IGNORECASE):
            table_name = match.group(1).lower()
            values_str = match.group(2)
            
            # Parse values (handle quoted strings)
            values = self._parse_values(values_str)
            
            if table_name in ['state', 'states'] and len(values) >= 2:
                state_code, state_name = values[0], values[1]
                state_code = state_code.strip().upper()
                state_name = state_name.strip()
                
                if state_code not in geo_data:
                    geo_data[state_code] = {
                        'state_name': state_name,
                        'cities': {}
                    }
            
            elif table_name in ['city', 'cities'] and len(values) >= 2:
                state_code, city_name = values[0], values[1]
                state_code = state_code.strip().upper()
                city_name = city_name.strip()
                
                if state_code not in geo_data:
                    geo_data[state_code] = {
                        'state_name': state_code,  # Fallback if state not defined
                        'cities': {}
                    }
                
                if city_name not in geo_data[state_code]['cities']:
                    geo_data[state_code]['cities'][city_name] = []
            
            elif table_name in ['pincode', 'pincodes'] and len(values) >= 3:
                state_code, city_name, pincode = values[0], values[1], values[2]
                state_code = state_code.strip().upper()
                city_name = city_name.strip()
                pincode = pincode.strip()
                
                if state_code not in geo_data:
                    geo_data[state_code] = {
                        'state_name': state_code,
                        'cities': {}
                    }
                
                if city_name not in geo_data[state_code]['cities']:
                    geo_data[state_code]['cities'][city_name] = []
                
                if pincode not in geo_data[state_code]['cities'][city_name]:
                    geo_data[state_code]['cities'][city_name].append(pincode)
        
        return geo_data

    def _parse_values(self, values_str: str) -> List[str]:
        """Parse VALUES string and extract individual values."""
        values = []
        current_value = ''
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(values_str):
            char = values_str[i]
            
            if not in_quotes and char in ["'", '"']:
                in_quotes = True
                quote_char = char
            elif in_quotes and char == quote_char:
                # Check for escaped quote
                if i + 1 < len(values_str) and values_str[i + 1] == quote_char:
                    current_value += char
                    i += 1  # Skip next quote
                else:
                    in_quotes = False
                    quote_char = None
            elif not in_quotes and char == ',':
                values.append(current_value.strip())
                current_value = ''
            else:
                current_value += char
            
            i += 1
        
        # Add last value
        if current_value.strip():
            values.append(current_value.strip())
        
        # Clean up values (remove quotes, handle NULL)
        cleaned_values = []
        for value in values:
            value = value.strip()
            if value.upper() == 'NULL':
                cleaned_values.append('')
            elif value.startswith(("'", '"')) and value.endswith(("'", '"')):
                cleaned_values.append(value[1:-1])
            else:
                cleaned_values.append(value)
        
        return cleaned_values

    def _load_to_database(
        self, 
        geo_data: Dict[str, Dict], 
        created_by_user
    ) -> Dict[str, int]:
        """Load parsed data to database with progress tracking."""
        stats = {
            'states_created': 0,
            'cities_created': 0,
            'pincodes_created': 0,
            'skipped': 0
        }
        
        total_items = len(geo_data)
        processed_items = 0
        
        for state_code, state_info in geo_data.items():
            processed_items += 1
            self.stdout.write(f"Processing {state_code} ({processed_items}/{total_items})")
            
            # Create or get state
            state, created = State.objects.get_or_create(
                code=state_code,
                defaults={
                    'name': state_info['state_name'],
                    'is_active': True,
                    'created_by': created_by_user,
                    'updated_by': created_by_user
                }
            )
            if created:
                stats['states_created'] += 1
            else:
                stats['skipped'] += 1
            
            # Create cities and pincodes
            for city_name, pincodes in state_info['cities'].items():
                # Create or get city
                city, created = City.objects.get_or_create(
                    state=state,
                    name=city_name,
                    defaults={
                        'is_active': True,
                        'created_by': created_by_user,
                        'updated_by': created_by_user
                    }
                )
                if created:
                    stats['cities_created'] += 1
                else:
                    stats['skipped'] += 1
                
                # Create pincodes
                for pincode_code in pincodes:
                    # Validate pincode format
                    if not re.match(r'^\d{6}$', pincode_code):
                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipping invalid pincode: {pincode_code}"
                            )
                        )
                        continue
                    
                    pincode, created = Pincode.objects.get_or_create(
                        code=pincode_code,
                        defaults={
                            'state': state,
                            'city': city,
                            'is_active': True,
                            'created_by': created_by_user,
                            'updated_by': created_by_user
                        }
                    )
                    if created:
                        stats['pincodes_created'] += 1
                    else:
                        stats['skipped'] += 1
        
        return stats
