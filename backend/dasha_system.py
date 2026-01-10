
from typing import Dict, List, Optional, Any
import swisseph as swe
from datetime import datetime, timedelta
# Pydantic models imported from schemas
from backend.schemas import DashaPeriod, CompleteDashaInfo, CurrentDashaState
from backend.logger import logger
from backend.config import KP_AYANAMSA

# ============================================================================
# CONSTANTS & CONFIG
# ============================================================================

DASHA_PERIODS = {
    'Ketu': 7,
    'Venus': 20,
    'Sun': 6,
    'Moon': 10,
    'Mars': 7,
    'Rahu': 18,
    'Jupiter': 16,
    'Saturn': 19,
    'Mercury': 17
}

PLANET_SEQUENCE = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
TOTAL_DASHA_YEARS = 120
DAYS_PER_YEAR = 365.25 # Julian Year average for simplicity in Dasha

class VimshottariDashaSystem:
    """
    Enhanced Recursive Vimshottari Dasha Calculator.
    Supports up to Level 5 (Prana Dasha).
    """
    
    def __init__(self):
        self.nakshatra_span = 360.0 / 27.0
        
    def _jd_to_date(self, jd: float) -> str:
        """Convert Julian Day to ISO Format Date String"""
        try:
            # swe.revjul returns (year, month, day, hour)
            y, m, d, h = swe.revjul(jd)
            # Adjust for float hours
            dt = datetime(y, m, d) + timedelta(hours=h)
            return dt.isoformat()
        except:
            return str(jd)

    def get_nakshatra_info(self, moon_lon: float):
        """Get nakshatra num (0-26), lord, and degree traversal"""
        # Normalize
        lon = moon_lon % 360
        nak_num = int(lon / self.nakshatra_span)
        deg_in_nak = lon % self.nakshatra_span
        
        # Determine Lord
        # Sequence cycles 3 times: 0-8, 9-17, 18-26
        seq_idx = nak_num % 9
        lord = PLANET_SEQUENCE[seq_idx]
        
        return nak_num, lord, deg_in_nak

    def calculate_birth_balance(self, moon_lon: float) -> Dict[str, Any]:
        """Calculate balance of Dasha at birth"""
        _, lord, deg_in_nak = self.get_nakshatra_info(moon_lon)
        fraction_remaining = 1.0 - (deg_in_nak / self.nakshatra_span)
        
        total_years = DASHA_PERIODS[lord]
        balance_years = total_years * fraction_remaining
        
        return {
            'lord': lord,
            'balance_years': balance_years,
            'balance_days': balance_years * DAYS_PER_YEAR,
            'fraction_remaining': fraction_remaining
        }

    def generate_timeline(self, moon_lon: float, birth_jd: float, 
                          years_duration: int = 120, max_level: int = 3) -> List[Dict]:
        """
        Generate Dasha timeline starting from birth.
        max_level: 1=Maha, 2=Antar, 3=Pratyantar...
        """
        timeline = []
        
        # 1. Start with Birth Dasha
        balance = self.calculate_birth_balance(moon_lon)
        start_lord = balance['lord']
        start_idx = PLANET_SEQUENCE.index(start_lord)
        
        curr_jd = birth_jd
        
        # Calculate FIRST Maha Dasha (Partial)
        # It runs for 'balance_years'
        first_duration_days = balance['balance_days']
        end_jd = curr_jd + first_duration_days
        
        first_maha = {
            'lord': start_lord,
            'level': 1,
            'start_jd': curr_jd,
            'end_jd': end_jd,
            'duration_years': balance['balance_years'],
            'sub_periods': []
        }
        
        # Recursive drill-down if needed
        # Note: Birth dasha starts in MIDDLE of sub-periods.
        # This is complex. Standard approach: Calculate FULL periods then trim?
        # Or calculate forward from current moment?
        
        # Detailed Implementation Strategy for "Birth Dasha" Sub-periods:
        # If Balance is 50%, we are in middle of Antar Dashas.
        # Simple MVP: Generate Full Timeline blocks, then filter/truncate start?
        # Better: Calculate "Elapsed" time in the cycle, find offset.
        
        if max_level > 1:
            # We need to find *where* in the hierarchy we are starting.
            # Fraction Remaining means we are at (1-Fraction) * Total Years into the period.
            elapsed_fraction = 1.0 - balance['fraction_remaining']
            # We can use _generate_sub_periods with an offset?
            first_maha['sub_periods'] = self._generate_sub_periods(
                start_lord, DASHA_PERIODS[start_lord], curr_jd, 
                max_level, current_level=2, start_fraction=elapsed_fraction
            )
            # The duration of sub_periods must sum to duration_years?
            # My _generate_sub_periods handles start_fraction logic.

        timeline.append(first_maha)
        curr_jd = end_jd
        
        # 2. Subsequent Maha Dashas
        # Cycle through sequence until 120 years covered
        years_covered = balance['balance_years']
        
        idx = (start_idx + 1) % 9
        
        while years_covered < years_duration:
            lord = PLANET_SEQUENCE[idx]
            duration = DASHA_PERIODS[lord]
            
            # If expanding exceeds limit, truncate?
            # Usually we just list full periods
            
            p_end_jd = curr_jd + (duration * DAYS_PER_YEAR)
            
            maha = {
                'lord': lord,
                'level': 1,
                'start_jd': curr_jd,
                'end_jd': p_end_jd,
                'duration_years': duration,
                'sub_periods': []
            }
            
            if max_level > 1:
                maha['sub_periods'] = self._generate_sub_periods(
                    lord, duration, curr_jd, max_level, current_level=2
                )
                
            timeline.append(maha)
            
            curr_jd = p_end_jd
            years_covered += duration
            idx = (idx + 1) % 9
            
        return timeline

    def _generate_sub_periods(self, parent_lord: str, parent_years: float, 
                              start_jd: float, max_level: int, current_level: int,
                              start_fraction: float = 0.0) -> List[Dict]:
        """
        Recursive generation.
        start_fraction: If > 0, we skip/truncate initial sub-periods (Birth case).
        """
        subs = []
        parent_idx = PLANET_SEQUENCE.index(parent_lord)
        
        # Sub-period sequence always starts with Parent Lord
        
        curr_jd = start_jd
        total_years = parent_years
        
        # Calculate sub-period durations standardly
        # Formula: SubYear = (ParentYear * PlanetYear) / 120
        
        # We need to skip 'start_fraction' of the TOTAL duration?
        # Yes. Calculate cumulative time, find start point.
        
        total_duration_days = total_years * DAYS_PER_YEAR
        elapsed_target_days = total_duration_days * start_fraction
        
        accumulated_days = 0.0
        
        for i in range(9):
            # Lord Sequence: Starts at Parent Lord
            lord = PLANET_SEQUENCE[(parent_idx + i) % 9]
            lord_years = DASHA_PERIODS[lord]
            
            sub_duration_years = (parent_years * lord_years) / 120.0
            sub_duration_days = sub_duration_years * DAYS_PER_YEAR
            
            # Check overlap with [elapsed_target, total]
            period_start_time = accumulated_days
            period_end_time = accumulated_days + sub_duration_days
            
            # Cases:
            # 1. Period is fully before start point -> Skip
            if period_end_time <= elapsed_target_days:
                accumulated_days += sub_duration_days
                continue
                
            # 2. Period partially overlaps start point -> Truncate start
            if period_start_time < elapsed_target_days < period_end_time:
                # Active at birth
                days_into_period = elapsed_target_days - period_start_time
                fraction_into_period = days_into_period / sub_duration_days
                
                real_duration = sub_duration_days - days_into_period
                
                sub_entry = {
                    'lord': lord,
                    'level': current_level,
                    'start_jd': curr_jd, # Starts NOW (at birth/start_jd provided)
                    'end_jd': curr_jd + real_duration,
                    'is_partial': True
                }
                
                # Recursive call needs to know we are partly done?
                if current_level < max_level:
                    sub_entry['sub_periods'] = self._generate_sub_periods(
                        lord, sub_duration_years, curr_jd, max_level, 
                        current_level + 1, start_fraction=fraction_into_period
                    )
                
                subs.append(sub_entry)
                curr_jd += real_duration
                accumulated_days += sub_duration_days
                continue
                
            # 3. Period is fully after start point -> Add fully
            sub_entry = {
                'lord': lord, 
                'level': current_level,
                'start_jd': curr_jd,
                'end_jd': curr_jd + sub_duration_days
            }
            
            if current_level < max_level:
                 sub_entry['sub_periods'] = self._generate_sub_periods(
                    lord, sub_duration_years, curr_jd, max_level, current_level + 1
                 )
            
            subs.append(sub_entry)
            curr_jd += sub_duration_days
            accumulated_days += sub_duration_days
            
        return subs

    def get_current_dasha_detailed(self, moon_lon: float, birth_jd: float, 
                                   target_jd: float) -> Dict[str, Any]:
        """Find the exact leaf node period for a target date."""
        # TODO: Optimize instead of generating full timeline
        # For now, generate full timeline (cached?)
        
        # Optimization: Calculate mathematically without iteration?
        # Balance at birth gives start offset.
        # Elapsed time = target - birth.
        # Add offset.
        # Total elapsed from [Start of First Maha Dasha of Cycle].
        
        _, lord, deg_in_nak = self.get_nakshatra_info(moon_lon)
        fraction_traversed = deg_in_nak / self.nakshatra_span
        
        # 1. Total Cycle Duration (120 years)
        # 2. Where are we in the cycle at birth?
        # Find position of Moon in the sequence of 120 years?
        # Sequence starts at Ketu.
        # Find PRECEEDING years before Current Nakshatra Lord.
        
        lord_idx = PLANET_SEQUENCE.index(lord)
        years_preceding = 0.0
        for i in range(lord_idx):
            years_preceding += DASHA_PERIODS[PLANET_SEQUENCE[i]]
            
        # Add fraction of current lord
        years_preceding += (DASHA_PERIODS[lord] * fraction_traversed)
        
        # Total years from "Cycle Start" (0 Aries Ketu start point equivalent)
        elapsed_since_birth_days = target_jd - birth_jd
        elapsed_years = elapsed_since_birth_days / DAYS_PER_YEAR
        
        total_cycle_years = years_preceding + elapsed_years
        
        # Modulo 120 for cycle
        effective_years = total_cycle_years % 120.0
        
        # Now drill down 5 levels using effective_years (0-120)
        
        return self._drill_down_dasha(effective_years)

    def calculate_complete_dasha(self, moon_lon: float, birth_jd: float, 
                                  current_jd: float) -> CompleteDashaInfo:
        """
        Main entry point for Enhanced Dasha System.
        """
        # 1. Get detailed current state (up to Prana)
        detailed_map = self.get_current_dasha_detailed(moon_lon, birth_jd, current_jd)
        
        # Convert map to CurrentDashaState
        # Maps keys 'maha', 'antar' etc to DashaPeriod objects
        # We need to construct DashaPeriod. We only have 'lord' and 'balance'.
        # We need start_jd, end_jd?
        # Drill down logic returns balance.
        # We should enhance drill_down to return full DashaPeriod objects?
        # Or Just minimal info for now. Schema allows defaults.
        
        # Helper to make dummy/minimal period
        def make_period(p_data: Dict, level: int):
            if not p_data: return None
            # Estimate start/end based on current_jd ??
            # Balance means time REMAINING.
            # End = Current + Balance.
            # Start = End - TotalDuration?
            # We don't have TotalDuration in simple map.
            # We can lookup standard duration relative to level.
            # But calculating exact start needs parent context.
            # For UI Display: "Balance: X Years" is critical.
            return DashaPeriod(
                lord=p_data['lord'],
                level=level,
                start_jd=current_jd, # Approx/Placeholder
                end_jd=current_jd + (p_data['balance'] * DAYS_PER_YEAR),
                duration_years=p_data['balance'], # Shows Remaining
                is_current=True
            )
            
        current_state = CurrentDashaState(
            maha_dasha=make_period(detailed_map.get('maha'), 1),
            antar_dasha=make_period(detailed_map.get('antar'), 2),
            pratyantar_dasha=make_period(detailed_map.get('pratyantar'), 3),
            sookshma_dasha=make_period(detailed_map.get('sookshma'), 4),
            prana_dasha=make_period(detailed_map.get('prana'), 5)
        )
        
        # 2. Complete Timeline (Cached or Generated)
        raw_timeline = self.generate_timeline(moon_lon, birth_jd, max_level=2)
        # Pydantic will parse list of dicts
        
        return CompleteDashaInfo(
            current_state=current_state,
            timeline=raw_timeline
        )

    def _drill_down_dasha(self, year_offset: float) -> Dict[str, Any]:
        """
        Drill down 5 levels for a given year offset (0-120).
        """
        result = {}
        lv_names = ['maha', 'antar', 'pratyantar', 'sookshma', 'prana']
        
        # Level 1: Maha
        parent_lord = ''
        parent_years = 0.0
        rem_years = year_offset
        
        for lord in PLANET_SEQUENCE:
            dur = DASHA_PERIODS[lord]
            if rem_years < dur:
                parent_lord = lord
                parent_years = dur
                result['maha'] = {'lord': lord, 'balance': dur - rem_years}
                break
            rem_years -= dur
            
        current_p_lord = parent_lord
        current_p_dur = parent_years
        current_rem = rem_years
        
        for level in range(1, 5): # Levels 2,3,4,5 (Antar to Prana)
            found_sub = False
            start_idx = PLANET_SEQUENCE.index(current_p_lord)
            
            for i in range(9):
                sub_lord = PLANET_SEQUENCE[(start_idx + i) % 9]
                sub_years = (current_p_dur * DASHA_PERIODS[sub_lord]) / 120.0
                
                if current_rem < sub_years:
                     result[lv_names[level]] = {'lord': sub_lord, 'balance': sub_years - current_rem}
                     current_p_lord = sub_lord
                     current_p_dur = sub_years
                     found_sub = True
                     break
                current_rem -= sub_years
                
            if not found_sub:
                break
                
        return result
