#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Equipment Matcher Service - CMMS Equipment Matching & Creation

Matches user input to existing CMMS equipment or creates new equipment records.
Implements equipment-first architecture with fuzzy matching to prevent duplicates.

Usage:
    from agent_factory.services.equipment_matcher import EquipmentMatcher

    matcher = EquipmentMatcher(db)
    equipment_id, is_new = await matcher.match_or_create_equipment(
        manufacturer="Siemens",
        model_number="G120C",
        serial_number="SR123456",
        equipment_type="VFD",
        location="Building A, Floor 2",
        user_id="telegram_8445149012"
    )
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class EquipmentMatcher:
    """Match user input to existing CMMS equipment or create new."""

    def __init__(self, db):
        """
        Initialize equipment matcher.

        Args:
            db: Database connection (DatabaseManager or similar)
        """
        self.db = db

    async def match_or_create_equipment(
        self,
        manufacturer: Optional[str],
        model_number: Optional[str],
        serial_number: Optional[str],
        equipment_type: Optional[str],
        location: Optional[str],
        user_id: str,
        machine_id: Optional[UUID] = None
    ) -> Tuple[UUID, bool]:
        """
        Match to existing equipment or create new.

        3-Step Matching Algorithm:
        1. Exact match on serial number (if provided)
        2. Fuzzy match on manufacturer + model (85%+ similarity)
        3. Match via user's machine library (machine_id)
        4. Create new equipment if no match found

        Args:
            manufacturer: Equipment manufacturer (e.g., "Siemens")
            model_number: Model number (e.g., "G120C")
            serial_number: Serial number (e.g., "SR123456")
            equipment_type: Type of equipment (e.g., "VFD", "PLC")
            location: Physical location (e.g., "Building A, Floor 2")
            user_id: User who reported this equipment
            machine_id: Optional link to user's machine library

        Returns:
            Tuple of (equipment_id, is_new_equipment)
            - equipment_id: UUID of matched or created equipment
            - is_new_equipment: True if equipment was created, False if matched

        Example:
            >>> equipment_id, is_new = await matcher.match_or_create_equipment(
            ...     manufacturer="Siemens",
            ...     model_number="G120C",
            ...     serial_number="SR123456",
            ...     equipment_type="VFD",
            ...     location="Building A, Floor 2",
            ...     user_id="telegram_8445149012"
            ... )
            >>> print(f"Equipment ID: {equipment_id}, New: {is_new}")
        """

        # Step 1: Try exact match on serial number (if provided)
        if serial_number:
            equipment = await self._match_by_serial(serial_number)
            if equipment:
                logger.info(
                    f"Matched equipment by serial: {equipment['equipment_number']} "
                    f"(serial: {serial_number})"
                )
                return (equipment["id"], False)

        # Step 2: Try fuzzy match on manufacturer + model
        if manufacturer and model_number:
            equipment = await self._fuzzy_match(manufacturer, model_number)
            if equipment:
                logger.info(
                    f"Matched equipment by fuzzy: {equipment['equipment_number']} "
                    f"({manufacturer} {model_number})"
                )
                return (equipment["id"], False)

        # Step 3: Try match via user's machine library
        if machine_id:
            equipment = await self._match_by_machine_id(machine_id)
            if equipment:
                logger.info(
                    f"Matched equipment by machine_id: {equipment['equipment_number']} "
                    f"(machine_id: {machine_id})"
                )
                return (equipment["id"], False)

        # Step 4: No match found → Create new equipment
        equipment_id = await self._create_equipment(
            manufacturer=manufacturer or "Unknown",
            model_number=model_number,
            serial_number=serial_number,
            equipment_type=equipment_type,
            location=location,
            owned_by_user_id=user_id,
            machine_id=machine_id
        )

        logger.info(
            f"Created new equipment: {equipment_id} "
            f"({manufacturer} {model_number})"
        )

        return (equipment_id, True)

    async def _match_by_serial(self, serial_number: str) -> Optional[Dict]:
        """
        Exact match on serial number.

        Args:
            serial_number: Serial number to match

        Returns:
            Equipment record if found, None otherwise
        """
        try:
            result = await self.db.execute_query("""
                SELECT id, manufacturer, model_number, equipment_number
                FROM cmms_equipment
                WHERE serial_number = $1
                LIMIT 1
            """, (serial_number,))

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error matching by serial: {e}")
            return None

    async def _fuzzy_match(
        self,
        manufacturer: str,
        model_number: str,
        threshold: float = 0.85
    ) -> Optional[Dict]:
        """
        Fuzzy match on manufacturer + model.

        Uses SequenceMatcher for similarity scoring.
        Threshold: 85%+ similarity required to prevent false matches.

        Example:
            "Siemens G120C" matches "SIEMENS G-120-C" (0.89 similarity)
            "Siemens G120C" does NOT match "Siemens S7-1200" (0.45 similarity)

        Args:
            manufacturer: Manufacturer name
            model_number: Model number
            threshold: Similarity threshold (default 0.85 = 85%)

        Returns:
            Best matching equipment record if above threshold, None otherwise
        """
        try:
            # Get all equipment from same manufacturer
            candidates = await self.db.execute_query("""
                SELECT id, manufacturer, model_number, equipment_number
                FROM cmms_equipment
                WHERE LOWER(manufacturer) = LOWER($1)
            """, (manufacturer,))

            if not candidates:
                return None

            best_match = None
            best_score = 0.0

            for candidate in candidates:
                # Calculate similarity score
                score = SequenceMatcher(
                    None,
                    model_number.lower(),
                    candidate["model_number"].lower() if candidate["model_number"] else ""
                ).ratio()

                if score > best_score:
                    best_score = score
                    best_match = candidate

            # Return match if above threshold
            if best_score >= threshold:
                logger.debug(
                    f"Fuzzy match found: {best_match['equipment_number']} "
                    f"({manufacturer} {model_number} matched "
                    f"{best_match['manufacturer']} {best_match['model_number']} "
                    f"with {best_score:.2%} similarity)"
                )
                return best_match

            logger.debug(
                f"No fuzzy match above threshold ({threshold:.0%}). "
                f"Best score: {best_score:.2%}"
            )
            return None

        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")
            return None

    async def _match_by_machine_id(self, machine_id: UUID) -> Optional[Dict]:
        """
        Match via user's machine library.

        Args:
            machine_id: UUID of machine in user_machines table

        Returns:
            Equipment record if found, None otherwise
        """
        try:
            result = await self.db.execute_query("""
                SELECT id, manufacturer, model_number, equipment_number
                FROM cmms_equipment
                WHERE machine_id = $1
                LIMIT 1
            """, (machine_id,))

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error matching by machine_id: {e}")
            return None

    async def _create_equipment(
        self,
        manufacturer: str,
        model_number: Optional[str],
        serial_number: Optional[str],
        equipment_type: Optional[str],
        location: Optional[str],
        owned_by_user_id: str,
        machine_id: Optional[UUID]
    ) -> UUID:
        """
        Create new equipment in CMMS.

        Args:
            manufacturer: Equipment manufacturer
            model_number: Model number (optional)
            serial_number: Serial number (optional)
            equipment_type: Type of equipment (optional)
            location: Physical location (optional)
            owned_by_user_id: User who first reported this equipment
            machine_id: Optional link to user's machine library

        Returns:
            UUID of newly created equipment

        Raises:
            Exception if creation fails
        """
        try:
            result = await self.db.execute_query("""
                INSERT INTO cmms_equipment (
                    manufacturer,
                    model_number,
                    serial_number,
                    equipment_type,
                    location,
                    owned_by_user_id,
                    machine_id,
                    first_reported_by,
                    work_order_count
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 0)
                RETURNING id, equipment_number
            """,
                (manufacturer,
                model_number,
                serial_number,
                equipment_type,
                location,
                owned_by_user_id,
                machine_id,
                owned_by_user_id)
            )

            equipment_id = result[0]["id"]
            equipment_number = result[0]["equipment_number"]

            logger.info(
                f"Created equipment {equipment_number}: "
                f"{manufacturer} {model_number or 'Unknown Model'}"
            )

            return equipment_id

        except Exception as e:
            logger.error(f"Failed to create equipment: {e}")
            raise

    async def update_equipment_stats(
        self,
        equipment_id: UUID,
        fault_code: Optional[str] = None
    ) -> None:
        """
        Update equipment statistics after work order creation.

        Note: work_order_count and last_work_order_at are auto-updated
        by the database trigger. This method handles optional fault_code update.

        Args:
            equipment_id: UUID of equipment to update
            fault_code: Optional fault code to record
        """
        try:
            if fault_code:
                await self.db.execute_query("""
                    UPDATE cmms_equipment
                    SET
                        last_reported_fault = $2,
                        updated_at = NOW()
                    WHERE id = $1
                """, (equipment_id, fault_code))

                logger.debug(
                    f"Updated equipment {equipment_id} with fault code: {fault_code}"
                )

        except Exception as e:
            logger.error(f"Failed to update equipment stats: {e}")
            # Don't raise - this is non-critical

    async def get_equipment_by_id(self, equipment_id: UUID) -> Optional[Dict]:
        """
        Get equipment details by ID.

        Args:
            equipment_id: UUID of equipment

        Returns:
            Equipment record if found, None otherwise
        """
        try:
            result = await self.db.execute_query("""
                SELECT
                    id,
                    equipment_number,
                    manufacturer,
                    model_number,
                    serial_number,
                    equipment_type,
                    location,
                    work_order_count,
                    last_reported_fault,
                    last_work_order_at,
                    created_at
                FROM cmms_equipment
                WHERE id = $1
            """, (equipment_id,))

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error fetching equipment: {e}")
            return None

    async def list_equipment_by_user(
        self,
        user_id: str,
        limit: int = 50
    ) -> list[Dict]:
        """
        List equipment owned by user.

        Args:
            user_id: User ID to filter by
            limit: Maximum number of results (default 50)

        Returns:
            List of equipment records
        """
        try:
            results = await self.db.execute_query("""
                SELECT
                    id,
                    equipment_number,
                    manufacturer,
                    model_number,
                    serial_number,
                    equipment_type,
                    location,
                    work_order_count,
                    last_reported_fault,
                    created_at
                FROM cmms_equipment
                WHERE owned_by_user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, (user_id, limit))

            return results or []

        except Exception as e:
            logger.error(f"Error listing equipment: {e}")
            return []
