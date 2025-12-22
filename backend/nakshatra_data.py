# backend/nakshatra_data.py
"""
Nakshatra database with all 27 lunar mansions
Each nakshatra spans 13°20' (13.333°)
Mapping: Longitude / 13.333 = Nakshatra number (0-26)
"""

NAKSHATRAS = [
    {
        'number': 0,
        'name': 'Ashwini',
        'lord': 'Ketu',
        'element': 'Fire',
        'symbol': '🐴 Horse',
        'deity': 'Ashwini Kumars',
        'traits': ['Quick', 'Energetic', 'Enterprising', 'Fearless'],
        'color': 'Red',
        'lucky_day': 'Wednesday',
        'lucky_number': 1,
        'profession': ['Medicine', 'Surgery', 'Driving', 'Mechanics'],
        'love': ['Quick to fall', 'Passionate', 'Independent'],
        'challenge': 'Impatience, recklessness',
        'remedy': 'Chant Gayatri Mantra',
        'range': '0°00\' - 13°20\''
    },
    {
        'number': 1,
        'name': 'Bharani',
        'lord': 'Venus',
        'element': 'Water',
        'symbol': '🔺 Triangle',
        'deity': 'Yama',
        'traits': ['Nurturing', 'Creative', 'Sensual', 'Protective'],
        'color': 'Red',
        'lucky_day': 'Friday',
        'lucky_number': 2,
        'profession': ['Cooking', 'Art', 'Music', 'Childcare'],
        'love': ['Devoted', 'Family-oriented', 'Loyal'],
        'challenge': 'Possessiveness, stubbornness',
        'remedy': 'Wear Pearl or Ruby',
        'range': '13°20\' - 26°40\''
    },
    {
        'number': 2,
        'name': 'Krittika',
        'lord': 'Sun',
        'element': 'Fire',
        'symbol': '🔥 Flame',
        'deity': 'Agni',
        'traits': ['Sharp', 'Penetrating', 'Critical', 'Courageous'],
        'color': 'Golden',
        'lucky_day': 'Sunday',
        'lucky_number': 3,
        'profession': ['Military', 'Surgery', 'Engineering', 'Teaching'],
        'love': ['Fiercely protective', 'Intense', 'Authoritative'],
        'challenge': 'Aggression, pride',
        'remedy': 'Worship Sun, wear Ruby',
        'range': '26°40\' - 40°00\''
    },
    {
        'number': 3,
        'name': 'Rohini',
        'lord': 'Moon',
        'element': 'Earth',
        'symbol': '🚗 Chariot',
        'deity': 'Brahma',
        'traits': ['Stable', 'Fertile', 'Creative', 'Materialistic'],
        'color': 'White',
        'lucky_day': 'Monday',
        'lucky_number': 4,
        'profession': ['Finance', 'Real Estate', 'Agriculture', 'Art'],
        'love': ['Sensual', 'Grounded', 'Loyal', 'Loves comfort'],
        'challenge': 'Stubbornness, attachment',
        'remedy': 'Wear Pearl, meditate on Moon',
        'range': '40°00\' - 53°20\''
    },
    {
        'number': 4,
        'name': 'Mrigashira',
        'lord': 'Mars',
        'element': 'Air',
        'symbol': '🦌 Deer Head',
        'deity': 'Soma (Moon god)',
        'traits': ['Curious', 'Intelligent', 'Shy', 'Inquisitive'],
        'color': 'Light Green',
        'lucky_day': 'Tuesday',
        'lucky_number': 5,
        'profession': ['Research', 'Travel', 'Communication', 'Hunting'],
        'love': ['Romantic', 'Seeks novelty', 'Restless'],
        'challenge': 'Fickleness, scattered',
        'remedy': 'Wear Red Coral, Mars rituals',
        'range': '53°20\' - 66°40\''
    },
    {
        'number': 5,
        'name': 'Ardra',
        'lord': 'Rahu',
        'element': 'Air',
        'symbol': '💧 Teardrop',
        'deity': 'Rudra (Shiva)',
        'traits': ['Intense', 'Sensitive', 'Intelligent', 'Secretive'],
        'color': 'Smoky',
        'lucky_day': 'Saturday',
        'lucky_number': 6,
        'profession': ['Science', 'Technology', 'Law', 'Psychology'],
        'love': ['Complex emotions', 'Deep bonding', 'Manipulative tendency'],
        'challenge': 'Turbulence, negative thinking',
        'remedy': 'Chant Maha Mrityunjaya Mantra',
        'range': '66°40\' - 80°00\''
    },
    {
        'number': 6,
        'name': 'Punarvasu',
        'lord': 'Jupiter',
        'element': 'Air',
        'symbol': '🏠 Bow & Arrow',
        'deity': 'Aditi',
        'traits': ['Optimistic', 'Spiritual', 'Generous', 'Restless'],
        'color': 'Yellow',
        'lucky_day': 'Thursday',
        'lucky_number': 7,
        'profession': ['Teaching', 'Philosophy', 'Travel', 'Religion'],
        'love': ['Idealistic', 'Spiritual bond', 'Seeks truth'],
        'challenge': 'Restlessness, impulsiveness',
        'remedy': 'Wear Topaz, Jupiter worship',
        'range': '80°00\' - 93°20\''
    },
    {
        'number': 7,
        'name': 'Pushya',
        'lord': 'Saturn',
        'element': 'Water',
        'symbol': '🐄 Udder',
        'deity': 'Brihaspati',
        'traits': ['Nourishing', 'Responsible', 'Protective', 'Dependable'],
        'color': 'Blue',
        'lucky_day': 'Saturday',
        'lucky_number': 8,
        'profession': ['Nursing', 'Social Work', 'Counseling', 'Teaching'],
        'love': ['Caring', 'Devoted', 'Family values'],
        'challenge': 'Rigidity, over-responsibility',
        'remedy': 'Wear Blue Sapphire, Saturn rituals',
        'range': '93°20\' - 106°40\''
    },
    {
        'number': 8,
        'name': 'Ashlesha',
        'lord': 'Mercury',
        'element': 'Water',
        'symbol': '🐍 Serpent',
        'deity': 'Sarpas (serpents)',
        'traits': ['Intuitive', 'Secretive', 'Manipulative', 'Magnetic'],
        'color': 'Green',
        'lucky_day': 'Wednesday',
        'lucky_number': 9,
        'profession': ['Occult', 'Medicine', 'Investigation', 'Psychology'],
        'love': ['Mysterious', 'Controlling', 'Healing potential'],
        'challenge': 'Jealousy, vindictiveness',
        'remedy': 'Wear Emerald, Mercury worship',
        'range': '106°40\' - 120°00\''
    },
    {
        'number': 9,
        'name': 'Magha',
        'lord': 'Ketu',
        'element': 'Fire',
        'symbol': '👑 Throne',
        'deity': 'Pitris (Ancestors)',
        'traits': ['Regal', 'Proud', 'Authoritative', 'Honorable'],
        'color': 'Deep Red',
        'lucky_day': 'Sunday',
        'lucky_number': 1,
        'profession': ['Leadership', 'Authority', 'Administration', 'History'],
        'love': ['Dominant', 'Traditional', 'Values legacy'],
        'challenge': 'Arrogance, obsession with status',
        'remedy': 'Ancestor worship, charity',
        'range': '120°00\' - 133°20\''
    },
    {
        'number': 10,
        'name': 'Purva Phalguni',
        'lord': 'Venus',
        'element': 'Fire',
        'symbol': '🌳 Swing',
        'deity': 'Aryaman',
        'traits': ['Creative', 'Playful', 'Sensual', 'Artistic'],
        'color': 'Bright Yellow',
        'lucky_day': 'Friday',
        'lucky_number': 2,
        'profession': ['Entertainment', 'Art', 'Performance', 'Design'],
        'love': ['Playful', 'Romantic', 'Loves pleasure'],
        'challenge': 'Laziness, overindulgence',
        'remedy': 'Wear Diamond, Venus worship',
        'range': '133°20\' - 146°40\''
    },
    {
        'number': 11,
        'name': 'Uttara Phalguni',
        'lord': 'Sun',
        'element': 'Earth',
        'symbol': '📖 Bed',
        'deity': 'Aryaman',
        'traits': ['Dutiful', 'Responsible', 'Generous', 'Modest'],
        'color': 'Golden',
        'lucky_day': 'Sunday',
        'lucky_number': 3,
        'profession': ['Management', 'Service', 'Medicine', 'Charity'],
        'love': ['Devoted', 'Responsibility', 'Traditional'],
        'challenge': 'Self-sacrifice, being taken for granted',
        'remedy': 'Sun worship, service work',
        'range': '146°40\' - 160°00\''
    },
    {
        'number': 12,
        'name': 'Hasta',
        'lord': 'Mercury',
        'element': 'Earth',
        'symbol': '✋ Hand',
        'deity': 'Savitar',
        'traits': ['Skillful', 'Intelligent', 'Practical', 'Adaptable'],
        'color': 'Green',
        'lucky_day': 'Wednesday',
        'lucky_number': 4,
        'profession': ['Crafts', 'Technology', 'Communication', 'Trade'],
        'love': ['Playful', 'Witty', 'Dexterous'],
        'challenge': 'Restlessness, lack of depth',
        'remedy': 'Wear Emerald, Mercury worship',
        'range': '160°00\' - 173°20\''
    },
    {
        'number': 13,
        'name': 'Chitra',
        'lord': 'Mars',
        'element': 'Fire',
        'symbol': '✨ Jewel',
        'deity': 'Twashtar',
        'traits': ['Creative', 'Unique', 'Determined', 'Attractive'],
        'color': 'Multi-colored',
        'lucky_day': 'Tuesday',
        'lucky_number': 5,
        'profession': ['Art', 'Design', 'Architecture', 'Creativity'],
        'love': ['Magnetic', 'Creative expression', 'Unconventional'],
        'challenge': 'Perfectionism, stubbornness',
        'remedy': 'Wear Red Coral, Mars rituals',
        'range': '173°20\' - 186°40\''
    },
    {
        'number': 14,
        'name': 'Swati',
        'lord': 'Rahu',
        'element': 'Air',
        'symbol': '🌬️ Sword',
        'deity': 'Vayu',
        'traits': ['Independent', 'Intelligent', 'Diplomatic', 'Restless'],
        'color': 'Black & White',
        'lucky_day': 'Saturday',
        'lucky_number': 6,
        'profession': ['Diplomacy', 'Air travel', 'Sales', 'Trade'],
        'love': ['Independent', 'Freedom-seeker', 'Values space'],
        'challenge': 'Indecision, being uprooted',
        'remedy': 'Chant Rahu mantras',
        'range': '186°40\' - 200°00\''
    },
    {
        'number': 15,
        'name': 'Vishakha',
        'lord': 'Jupiter',
        'element': 'Fire',
        'symbol': '🌳 Trident',
        'deity': 'Indra & Agni',
        'traits': ['Ambitious', 'Determined', 'Passionate', 'Conflicted'],
        'color': 'Golden & Red',
        'lucky_day': 'Thursday',
        'lucky_number': 7,
        'profession': ['Leadership', 'Debate', 'War Strategy', 'Law'],
        'love': ['Passionate', 'Ambitious partner', 'Competitive'],
        'challenge': 'Conflict, argumentative',
        'remedy': 'Wear Topaz, Jupiter worship',
        'range': '200°00\' - 213°20\''
    },
    {
        'number': 16,
        'name': 'Anuradha',
        'lord': 'Saturn',
        'element': 'Air',
        'symbol': '💫 Garland',
        'deity': 'Mitra',
        'traits': ['Devoted', 'Loyal', 'Focused', 'Deep'],
        'color': 'Green',
        'lucky_day': 'Saturday',
        'lucky_number': 8,
        'profession': ['Friendship', 'Bonds', 'Psychology', 'Service'],
        'love': ['Deeply devoted', 'Stable bond', 'Values loyalty'],
        'challenge': 'Jealousy in relationships',
        'remedy': 'Wear Blue Sapphire, Saturn rituals',
        'range': '213°20\' - 226°40\''
    },
    {
        'number': 17,
        'name': 'Jyeshtha',
        'lord': 'Mercury',
        'element': 'Air',
        'symbol': '👑 Thunderbolt',
        'deity': 'Indra',
        'traits': ['Courageous', 'Protective', 'Mysterious', 'Authoritative'],
        'color': 'Copper',
        'lucky_day': 'Wednesday',
        'lucky_number': 9,
        'profession': ['Leadership', 'Command', 'Medical', 'Occult'],
        'love': ['Protective', 'Magnetic', 'Intense'],
        'challenge': 'Arrogance, secretive',
        'remedy': 'Wear Emerald, Mercury worship',
        'range': '226°40\' - 240°00\''
    },
    {
        'number': 18,
        'name': 'Mula',
        'lord': 'Ketu',
        'element': 'Earth',
        'symbol': '🔪 Whip',
        'deity': 'Nirrti',
        'traits': ['Destructive', 'Transformative', 'Philosophical', 'Radical'],
        'color': 'Black',
        'lucky_day': 'Sunday',
        'lucky_number': 1,
        'profession': ['Occult', 'Research', 'Exploration', 'Change agent'],
        'love': ['Seeks truth', 'Transformative', 'Non-traditional'],
        'challenge': 'Destructiveness, obsession',
        'remedy': 'Meditation, Ketu worship',
        'range': '240°00\' - 253°20\''
    },
    {
        'number': 19,
        'name': 'Purva Ashadha',
        'lord': 'Venus',
        'element': 'Fire',
        'symbol': '🏹 Fan',
        'deity': 'Apas',
        'traits': ['Confident', 'Fearless', 'Independent', 'Sensual'],
        'color': 'Golden',
        'lucky_day': 'Friday',
        'lucky_number': 2,
        'profession': ['Adventure', 'Travel', 'Art', 'Leadership'],
        'love': ['Confident lover', 'Independence valued', 'Sensual'],
        'challenge': 'Over-confidence, instability',
        'remedy': 'Wear Diamond, Venus worship',
        'range': '253°20\' - 266°40\''
    },
    {
        'number': 20,
        'name': 'Uttara Ashadha',
        'lord': 'Sun',
        'element': 'Earth',
        'symbol': '🐘 Elephant Tusk',
        'deity': 'Vishvadevas',
        'traits': ['Dignified', 'Patient', 'Steadfast', 'Righteous'],
        'color': 'Golden',
        'lucky_day': 'Sunday',
        'lucky_number': 3,
        'profession': ['Administration', 'Government', 'Teaching', 'Law'],
        'love': ['Steadfast', 'Respectful', 'Mature love'],
        'challenge': 'Rigidity, being overbearing',
        'remedy': 'Sun worship, righteous action',
        'range': '266°40\' - 280°00\''
    },
    {
        'number': 21,
        'name': 'Shravana',
        'lord': 'Moon',
        'element': 'Air',
        'symbol': '👂 Ear',
        'deity': 'Vishnu',
        'traits': ['Obedient', 'Humble', 'Learned', 'Devoted'],
        'color': 'Golden',
        'lucky_day': 'Monday',
        'lucky_number': 4,
        'profession': ['Education', 'Communication', 'Listening', 'Teaching'],
        'love': ['Obedient', 'Devoted', 'Spiritual connection'],
        'challenge': 'Over-dependence, servility',
        'remedy': 'Wear Pearl, Moon worship',
        'range': '280°00\' - 293°20\''
    },
    {
        'number': 22,
        'name': 'Dhanishta',
        'lord': 'Mars',
        'element': 'Air',
        'symbol': '🥁 Drum',
        'deity': 'Vasus',
        'traits': ['Energetic', 'Musical', 'Rich', 'Powerful'],
        'color': 'Blue',
        'lucky_day': 'Tuesday',
        'lucky_number': 5,
        'profession': ['Music', 'Wealth', 'Power', 'Business'],
        'love': ['Energetic', 'Musical nature', 'Materialistic'],
        'challenge': 'Restlessness, arrogance',
        'remedy': 'Wear Red Coral, Mars rituals',
        'range': '293°20\' - 306°40\''
    },
    {
        'number': 23,
        'name': 'Shatabhisha',
        'lord': 'Rahu',
        'element': 'Air',
        'symbol': '🌊 100 Flowers',
        'deity': 'Varuna',
        'traits': ['Mysterious', 'Independent', 'Scientific', 'Unconventional'],
        'color': 'Dark Blue',
        'lucky_day': 'Saturday',
        'lucky_number': 6,
        'profession': ['Science', 'Occult', 'Medicine', 'Technology'],
        'love': ['Detached', 'Friendship-based', 'Unconventional'],
        'challenge': 'Isolation, misunderstanding',
        'remedy': 'Chant Rahu mantras',
        'range': '306°40\' - 320°00\''
    },
    {
        'number': 24,
        'name': 'Purva Bhadrapada',
        'lord': 'Jupiter',
        'element': 'Water',
        'symbol': '⚡ Two-faced',
        'deity': 'Aja Ekapad',
        'traits': ['Fierce', 'Intelligent', 'Spiritual', 'Explosive'],
        'color': 'Black & Gold',
        'lucky_day': 'Thursday',
        'lucky_number': 7,
        'profession': ['Occult', 'Spirituality', 'Healing', 'Research'],
        'love': ['Intense', 'Spiritual', 'Transformative'],
        'challenge': 'Aggression, obsession',
        'remedy': 'Wear Topaz, Jupiter worship',
        'range': '320°00\' - 333°20\''
    },
    {
        'number': 25,
        'name': 'Uttara Bhadrapada',
        'lord': 'Saturn',
        'element': 'Water',
        'symbol': '😴 Twin Stars',
        'deity': 'Ahir Budhnya',
        'traits': ['Gentle', 'Wise', 'Spiritual', 'Diplomatic'],
        'color': 'Blue',
        'lucky_day': 'Saturday',
        'lucky_number': 8,
        'profession': ['Spirituality', 'Counseling', 'Charity', 'Teaching'],
        'love': ['Gentle', 'Spiritual bond', 'Healing'],
        'challenge': 'Excessive passivity, sadness',
        'remedy': 'Wear Blue Sapphire, Saturn rituals',
        'range': '333°20\' - 346°40\''
    },
    {
        'number': 26,
        'name': 'Revati',
        'lord': 'Mercury',
        'element': 'Earth',
        'symbol': '🐟 Fish',
        'deity': 'Pushan',
        'traits': ['Prosperous', 'Protective', 'Nurturing', 'Musical'],
        'color': 'Golden',
        'lucky_day': 'Wednesday',
        'lucky_number': 9,
        'profession': ['Trade', 'Music', 'Protection', 'Nurturing'],
        'love': ['Nurturing', 'Protective', 'Seeks security'],
        'challenge': 'Over-protectiveness, dependence',
        'remedy': 'Wear Emerald, Mercury worship',
        'range': '346°40\' - 360°00\''
    }
]

def get_nakshatra_by_longitude(longitude):
    """
    Calculate nakshatra from longitude (0-360°)
    Returns: nakshatra_dict, pada_number
    
    Logic: Each nakshatra = 13°20' = 13.333°
    Pada (quarter) = 3°20' = 3.333°
    """
    # Normalize to 0-360
    longitude = longitude % 360
    
    # Which nakshatra (0-26)
    nakshatra_num = int(longitude / 13.33333)
    if nakshatra_num >= 27:
        nakshatra_num = 26
    
    # Which pada (quarter) within nakshatra (1-4)
    position_in_nakshatra = longitude % 13.33333
    pada = int(position_in_nakshatra / 3.33333) + 1
    
    return NAKSHATRAS[nakshatra_num], pada

def get_nakshatra_details(nakshatra_dict, pada):
    """
    Returns formatted details for display
    """
    details = f"""
╔═══════════════════════════════════════════════════════╗
║  🌙 NAKSHATRA DETAILS: {nakshatra_dict['name'].upper()}
╚═══════════════════════════════════════════════════════╝

🔢 Number: {nakshatra_dict['number']+1}/27 (Range: {nakshatra_dict['range']})
👑 Lord: {nakshatra_dict['lord']}
🔥 Element: {nakshatra_dict['element']}
📍 Pada (Quarter): {pada}/4

🏛️ Deity: {nakshatra_dict['deity']}
🎨 Symbol: {nakshatra_dict['symbol']}
🎨 Color: {nakshatra_dict['color']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 PERSONALITY TRAITS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{', '.join(nakshatra_dict['traits'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 CAREER & PROFESSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{', '.join(nakshatra_dict['profession'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💕 IN LOVE & RELATIONSHIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{', '.join(nakshatra_dict['love'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CHALLENGES TO OVERCOME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{nakshatra_dict['challenge']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ REMEDY & RECOMMENDATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{nakshatra_dict['remedy']}
Lucky Day: {nakshatra_dict['lucky_day']} | Lucky Number: {nakshatra_dict['lucky_number']}
"""
    return details
