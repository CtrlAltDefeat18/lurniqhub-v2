"""
LurniqHub seed data: fleet ranks, the nautical-mile economy, and the full
course catalogue (modules, lessons, quizzes and bridge-simulation missions).

Content is written for South African high school learners (Grades 9-12) and
references the local maritime economy: SAMSA, Transnet, Operation Phakisa,
the ports of Durban, Cape Town and Richards Bay, and the Agulhas/Benguela
current systems.

This module is pure data + tiny pure helpers. It performs no I/O and opens
no database connections; app.py imports it and seeds Mongo on first request.
"""

# ---------------------------------------------------------------------------
# Nautical-mile economy
# ---------------------------------------------------------------------------

NM_ENROLL = 10          # first enrolment in a course
NM_LESSON = 15          # each lesson completed (once per lesson)
NM_DAILY_LOGIN = 5      # first login of each UTC day
NM_COURSE_COMPLETE = 25 # bonus when a course reaches 100%

# ---------------------------------------------------------------------------
# Fleet ranks (ordered, ascending)
# ---------------------------------------------------------------------------

RANKS = [
    {
        'level': 1, 'name': 'Deckhand', 'min_nm': 0, 'icon': 'anchor',
        'motto': 'Every voyage begins with a single watch.',
        'description': 'You have stepped aboard. Learn the ropes, keep the decks clear, and log your first miles.',
    },
    {
        'level': 2, 'name': 'Ordinary Seaman', 'min_nm': 50, 'icon': 'sailing',
        'motto': 'Steady hands, open eyes.',
        'description': 'You can stand a watch. The basics of seamanship are becoming second nature.',
    },
    {
        'level': 3, 'name': 'Able Seaman', 'min_nm': 120, 'icon': 'waves',
        'motto': 'Trusted at the helm.',
        'description': 'A certified all-rounder. You take the wheel and the crew trusts your judgement.',
    },
    {
        'level': 4, 'name': 'Bosun', 'min_nm': 220, 'icon': 'engineering',
        'motto': 'The crew follows your lead.',
        'description': 'Senior deck crew. You run operations on deck and mentor newer sailors.',
    },
    {
        'level': 5, 'name': 'Navigation Officer', 'min_nm': 350, 'icon': 'explore',
        'motto': 'You chart the course.',
        'description': 'An officer of the watch. Charts, bearings and passage plans are your domain.',
    },
    {
        'level': 6, 'name': 'Chief Mate', 'min_nm': 500, 'icon': 'military_tech',
        'motto': 'Second in command, first to act.',
        'description': 'The captain\'s right hand. Cargo, stability and the entire deck department answer to you.',
    },
    {
        'level': 7, 'name': 'Captain', 'min_nm': 650, 'icon': 'workspace_premium',
        'motto': 'The ship, the crew, the call — all yours.',
        'description': 'Master of the vessel. Every decision at sea carries your name.',
    },
    {
        'level': 8, 'name': 'Fleet Admiral', 'min_nm': 800, 'icon': 'stars',
        'motto': 'Legend of the LurniqHub fleet.',
        'description': 'The summit. You have mastered every course and mission on the platform.',
    },
]


def rank_for_miles(nm):
    """Return (current_rank, next_rank_or_None, pct_progress_to_next)."""
    nm = max(0, int(nm or 0))
    current = RANKS[0]
    nxt = None
    for i, r in enumerate(RANKS):
        if nm >= r['min_nm']:
            current = r
            nxt = RANKS[i + 1] if i + 1 < len(RANKS) else None
    if nxt is None:
        return current, None, 100
    span = nxt['min_nm'] - current['min_nm']
    pct = int(round(100 * (nm - current['min_nm']) / span)) if span else 100
    return current, nxt, max(0, min(100, pct))


# ---------------------------------------------------------------------------
# Course catalogue
# ---------------------------------------------------------------------------
# Course shape:
#   slug, title, tagline, description, category, grade_level, difficulty,
#   icon (material icon), theme {from, to} (hex, applied inline),
#   modules: [ {id, title, lessons: [lesson]} ]
#   lesson: {id, title, minutes, intro, sections:[{heading, body}],
#            key_points:[str], quiz:{question, options:[], answer, explanation}}
#   simulation: {type:'helm', title, briefing, pass_score, max_nm, config}
#
# Simulation config is consumed by static/js/simulator.js (world units are
# abstract chart units; the engine scales to the canvas).

SEED_COURSES = [
    # ------------------------------------------------------------------ 1
    {
        'slug': 'coastal-navigation',
        'title': 'Coastal Navigation Fundamentals',
        'tagline': 'Charts, compasses and the art of knowing exactly where you are.',
        'description': (
            'Master the foundations every navigator is built on: reading nautical charts, '
            'working with the magnetic compass, plotting positions and courses, and '
            'understanding the tides and currents that shape passage planning along the '
            'South African coast.'
        ),
        'category': 'Navigation',
        'grade_level': 'Grade 10–12',
        'difficulty': 'Beginner',
        'icon': 'explore',
        'theme': {'from': '#1976D2', 'to': '#0E4D92'},
        'modules': [
            {
                'id': 'm1',
                'title': 'Charts & the Compass',
                'lessons': [
                    {
                        'id': 'm1l1',
                        'title': 'Reading Nautical Charts',
                        'minutes': 12,
                        'intro': (
                            'A nautical chart is the road map of the sea — except the road moves, '
                            'the surface hides obstacles, and getting it wrong can put a ship on the '
                            'rocks. Charts encode depth, hazards, navigation aids and the coastline '
                            'into a single picture a navigator can read at a glance.'
                        ),
                        'sections': [
                            {
                                'heading': 'What a chart shows',
                                'body': (
                                    'Soundings (small numbers scattered across the water) give the depth at '
                                    'low tide, usually in metres. Contour lines join points of equal depth, '
                                    'exactly like elevation lines on a topographic map. Symbols mark wrecks, '
                                    'rocks, buoys and lighthouses — the South African Navy Hydrographic '
                                    'Office publishes the official charts for our 3 900 km coastline.'
                                ),
                            },
                            {
                                'heading': 'Scale and detail',
                                'body': (
                                    'A harbour chart of Durban might use a scale of 1:10 000 where every '
                                    'jetty is visible, while a passage chart from Cape Town to Port '
                                    'Elizabeth could be 1:750 000. Navigators switch between scales the way '
                                    'you zoom a map app — wide for planning, tight for pilotage.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Soundings show depth at the lowest astronomical tide — the safe minimum.',
                            'Depth contours reveal underwater terrain shape.',
                            'Chart symbols are standardised internationally (INT-1 catalogue).',
                            'Use small-scale charts to plan, large-scale charts to navigate close in.',
                        ],
                        'quiz': {
                            'question': 'The small numbers scattered across the water area of a chart show…',
                            'options': [
                                'Distance to the nearest port in kilometres',
                                'Water depth at low tide, usually in metres',
                                'The recommended speed limit in knots',
                                'Magnetic variation for that area',
                            ],
                            'answer': 1,
                            'explanation': 'Those are soundings — depths reduced to chart datum (roughly the lowest tide), so the real depth is almost always at least that value.',
                        },
                    },
                    {
                        'id': 'm1l2',
                        'title': 'The Magnetic Compass & Bearings',
                        'minutes': 12,
                        'intro': (
                            'Long before GPS, sailors crossed oceans with a magnetised needle. The '
                            'compass is still mandatory equipment on every ship, because satellites '
                            'can fail — magnetism doesn\'t. The catch: a compass doesn\'t quite point '
                            'at true north.'
                        ),
                        'sections': [
                            {
                                'heading': 'True north vs magnetic north',
                                'body': (
                                    'Charts are drawn around true north (the geographic pole), but the '
                                    'compass needle aligns with the magnetic pole, which sits in a slightly '
                                    'different place and slowly wanders. The difference is called '
                                    'variation. Around the South African coast variation is currently about '
                                    '25° west — large by world standards, so local navigators can never '
                                    'ignore it.'
                                ),
                            },
                            {
                                'heading': 'Taking and using bearings',
                                'body': (
                                    'A bearing is simply the direction to an object measured in degrees '
                                    'from north (000° to 359°). Sight a lighthouse at 045°M, convert to '
                                    'true by applying variation, draw the line on the chart — your ship is '
                                    'somewhere on that line. Cross it with a second bearing and you have a '
                                    'fix: your position.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Variation = the angle between true north and magnetic north.',
                            'South African waters have a large westerly variation (~25°W).',
                            'A single bearing gives a position line; two or more give a fix.',
                            'Memory aid: "Error West, Compass Best" — magnetic reads higher than true.',
                        ],
                        'quiz': {
                            'question': 'Why must South African navigators always correct compass bearings?',
                            'options': [
                                'Because GPS is illegal to use within harbours',
                                'Because the local magnetic variation is large (about 25°W)',
                                'Because compasses only work in the northern hemisphere',
                                'Because charts here are drawn around magnetic north',
                            ],
                            'answer': 1,
                            'explanation': 'Variation near the SA coast is roughly 25° west — among the largest in the inhabited world. Ignore it and a 10 nm leg puts you over 4 nm off track.',
                        },
                    },
                    {
                        'id': 'm1l3',
                        'title': 'Latitude, Longitude & Position',
                        'minutes': 10,
                        'intro': (
                            'Every point on Earth has an address: latitude and longitude. Durban sits '
                            'near 29°52\'S, 31°02\'E. Learn to read, plot and communicate positions '
                            'and you can tell anyone, anywhere, exactly where you are — essential in '
                            'an emergency.'
                        ),
                        'sections': [
                            {
                                'heading': 'The grid of the world',
                                'body': (
                                    'Latitude lines run parallel to the equator, measured 0–90° north or '
                                    'south. Longitude lines run pole to pole, measured 0–180° east or west '
                                    'of Greenwich. Each degree splits into 60 minutes — and one minute of '
                                    'latitude is exactly one nautical mile, which is why the nautical mile '
                                    'exists at all.'
                                ),
                            },
                            {
                                'heading': 'Plotting a position',
                                'body': (
                                    'On a chart, latitude is read from the side scales and longitude from '
                                    'the top/bottom scales. With dividers and a parallel ruler you transfer '
                                    'the numbers onto the chart to mark a fix, then label it with the time. '
                                    'A neat plot is a legal record — official logbooks are admissible in '
                                    'maritime inquiries.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Latitude: 0–90° N/S of the equator. Longitude: 0–180° E/W of Greenwich.',
                            '1 minute of latitude = 1 nautical mile = 1.852 km.',
                            'Always read latitude from the side scale of the chart, never the top.',
                            'Positions are written lat first: 29°52\'S 31°02\'E.',
                        ],
                        'quiz': {
                            'question': 'One minute of latitude equals…',
                            'options': [
                                'One kilometre',
                                'One statute mile',
                                'One nautical mile',
                                'Sixty nautical miles',
                            ],
                            'answer': 2,
                            'explanation': 'The nautical mile is defined from the Earth itself: 1 minute of latitude ≈ 1 852 m. That is why distance and position share the same units at sea.',
                        },
                    },
                ],
            },
            {
                'id': 'm2',
                'title': 'Practical Passage Skills',
                'lessons': [
                    {
                        'id': 'm2l1',
                        'title': 'Plotting a Course',
                        'minutes': 14,
                        'intro': (
                            'A passage plan turns "we want to sail to East London" into a sequence of '
                            'safe, checkable legs. Professional crews plan berth-to-berth before '
                            'letting go a single line — it is required by international law (SOLAS '
                            'Chapter V).'
                        ),
                        'sections': [
                            {
                                'heading': 'Course lines and waypoints',
                                'body': (
                                    'Draw a line from departure to destination that clears every hazard '
                                    'with margin. Where the line must bend, you create a waypoint. For each '
                                    'leg you record the true course, the distance, and the expected time at '
                                    'planned speed: distance ÷ speed = time, the most-used formula in '
                                    'navigation.'
                                ),
                            },
                            {
                                'heading': 'Allowing for set and drift',
                                'body': (
                                    'Water moves. If the current sets you east at 2 knots and you steer '
                                    'straight at your waypoint, you will arrive somewhere else. Navigators '
                                    'aim upstream — like a swimmer crossing a river — by applying a course '
                                    'correction calculated from the current\'s set (direction) and drift '
                                    '(speed). You will feel this first-hand in this course\'s simulation.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Plan berth to berth; every leg gets course, distance and ETA.',
                            'Waypoints mark every alteration of course.',
                            'Time = Distance ÷ Speed (in hours, with distance in nm and speed in knots).',
                            'Steer into the current to stay on track — never chase the waypoint.',
                        ],
                        'quiz': {
                            'question': 'A leg is 24 nm long and your speed is 8 knots. How long will it take?',
                            'options': ['2 hours', '3 hours', '4 hours', '8 hours'],
                            'answer': 1,
                            'explanation': 'Time = Distance ÷ Speed = 24 ÷ 8 = 3 hours. This single formula underpins every ETA at sea.',
                        },
                    },
                    {
                        'id': 'm2l2',
                        'title': 'Tides, Currents & the Agulhas',
                        'minutes': 12,
                        'intro': (
                            'South Africa\'s coast is ruled by one of the most powerful ocean currents '
                            'on Earth. Understanding moving water is not optional here — it decides '
                            'your speed, your fuel bill and sometimes your survival.'
                        ),
                        'sections': [
                            {
                                'heading': 'The Agulhas Current',
                                'body': (
                                    'The Agulhas sweeps down the east coast at up to 5 knots — one of the '
                                    'fastest currents in the world. Ride it southbound from Durban and a '
                                    'ship gains a free 100+ nm a day. But when a south-westerly gale blows '
                                    'against it, the current builds freak waves up to 20 m that have broken '
                                    'ships in two. Mariners treat the 200 m depth contour off the Wild '
                                    'Coast with deep respect.'
                                ),
                            },
                            {
                                'heading': 'Tides and tidal streams',
                                'body': (
                                    'Tides are the vertical rise and fall of the sea (about 2 m range on '
                                    'the SA coast); tidal streams are the horizontal flows they cause, '
                                    'strongest in harbour entrances. Tide tables — published annually by '
                                    'the SA Navy Hydrographic Office — tell you the depth available over a '
                                    'harbour sill at any time, which can decide when a ship may enter port.'
                                ),
                            },
                        ],
                        'key_points': [
                            'The Agulhas Current can exceed 5 knots — a moving conveyor belt.',
                            'Wind against current off the Wild Coast creates dangerous freak waves.',
                            'Tide = vertical movement; tidal stream = horizontal movement.',
                            'Tide tables are official documents used to time port entries.',
                        ],
                        'quiz': {
                            'question': 'Why is "wind against current" so dangerous off South Africa\'s east coast?',
                            'options': [
                                'It causes compasses to give false readings',
                                'It makes the Agulhas Current reverse direction',
                                'Opposing forces steepen the seas into freak waves',
                                'It produces dense fog over the shipping lanes',
                            ],
                            'answer': 2,
                            'explanation': 'A SW gale pushing against the 5-knot Agulhas shortens and steepens the swell. Waves of 15–20 m have been recorded — enough to overwhelm large ships.',
                        },
                    },
                    {
                        'id': 'm2l3',
                        'title': 'Buoyage & the Rules of the Road',
                        'minutes': 12,
                        'intro': (
                            'The sea has traffic signs and traffic rules. Buoys mark the safe water; '
                            'the International Collision Regulations (COLREGs) decide who gives way. '
                            'Both are pure memorisation — and both are tested in every maritime exam '
                            'on the planet.'
                        ),
                        'sections': [
                            {
                                'heading': 'IALA Region A buoyage',
                                'body': (
                                    'South Africa uses IALA Region A: entering harbour from seaward, keep '
                                    'the red can buoys to port (left) and the green cones to starboard '
                                    '(right). Cardinal buoys — yellow and black — tell you which side of a '
                                    'danger is safe, named for the compass point to pass on: a north '
                                    'cardinal means pass to the north of it.'
                                ),
                            },
                            {
                                'heading': 'Who gives way?',
                                'body': (
                                    'The COLREGs are blunt: power gives way to sail (usually), everyone '
                                    'gives way to a vessel they are overtaking, and when two power vessels '
                                    'cross, the one that has the other on her starboard side keeps clear. '
                                    'When two meet head-on, both alter to starboard — pass port-to-port, '
                                    'just like driving on the right at sea even though we drive left ashore.'
                                ),
                            },
                        ],
                        'key_points': [
                            'IALA Region A: red to port, green to starboard when entering from sea.',
                            'Cardinal buoys are named for the safe side: pass north of a north cardinal.',
                            'Crossing power vessels: give way if the other ship is to starboard.',
                            'Head-on: both ships alter course to starboard.',
                        ],
                        'quiz': {
                            'question': 'Entering Durban harbour from seaward (IALA Region A), you should keep…',
                            'options': [
                                'Green buoys to port, red to starboard',
                                'Red buoys to port, green to starboard',
                                'All buoys to starboard',
                                'All buoys to port',
                            ],
                            'answer': 1,
                            'explanation': 'Region A (Africa, Europe, most of Asia and Oceania): returning from sea, red cans stay on your left, green cones on your right.',
                        },
                    },
                ],
            },
        ],
        'simulation': {
            'type': 'helm',
            'title': 'Harbour Approach: Port of Durban',
            'briefing': (
                'You have the conn of the coaster MV Umngeni inbound to Durban — Africa\'s '
                'busiest port. A south-flowing current is setting you off the leads. Steer '
                'the marked channel in order: fairway buoy, the harbour entrance, then your '
                'berth. Stay off the sandbanks — groundings cost points and pride.'
            ),
            'pass_score': 60,
            'max_nm': 60,
            'config': {
                'world': {'w': 1600, 'h': 1000},
                'start': {'x': 1450, 'y': 850, 'heading': 300},
                'vessel': {'max_speed': 5.2, 'turn_rate': 70},
                'current': {'x': -0.35, 'y': 0.55},
                'time_par': 95,
                'time_limit': 240,
                'waypoints': [
                    {'x': 1150, 'y': 620, 'r': 52, 'label': 'Fairway Buoy'},
                    {'x': 820, 'y': 460, 'r': 48, 'label': 'Channel Entrance'},
                    {'x': 520, 'y': 330, 'r': 46, 'label': 'North Breakwater'},
                    {'x': 250, 'y': 210, 'r': 50, 'label': 'Berth 14'},
                ],
                'hazards': [
                    {'x': 1010, 'y': 330, 'r': 120, 'label': 'Aliwal Bank'},
                    {'x': 620, 'y': 640, 'r': 130, 'label': 'Sand Spit'},
                    {'x': 300, 'y': 470, 'r': 90, 'label': 'Dredger Works'},
                ],
            },
        },
    },

    # ------------------------------------------------------------------ 2
    {
        'slug': 'marine-engineering',
        'title': 'Marine Engineering Essentials',
        'tagline': 'The beating heart below decks — engines, power and propulsion.',
        'description': (
            'Go below the waterline and learn what actually moves a ship: marine diesel '
            'engines, propellers, shipboard electrical systems and the cooling, lubrication '
            'and fuel systems that keep tens of thousands of kilowatts running for weeks '
            'without stopping.'
        ),
        'category': 'Engineering',
        'grade_level': 'Grade 10–12',
        'difficulty': 'Intermediate',
        'icon': 'settings_suggest',
        'theme': {'from': '#E65100', 'to': '#BF360C'},
        'modules': [
            {
                'id': 'm1',
                'title': 'Power at Sea',
                'lessons': [
                    {
                        'id': 'm1l1',
                        'title': 'How Marine Diesel Engines Work',
                        'minutes': 14,
                        'intro': (
                            'The largest reciprocating engines ever built live inside ships. A big '
                            'container ship\'s main engine can stand four storeys tall, produce over '
                            '80 000 kW, and run non-stop from Durban to Singapore. Yet it works on '
                            'the same four principles as a bakkie\'s diesel.'
                        ),
                        'sections': [
                            {
                                'heading': 'Suck, squeeze, bang, blow',
                                'body': (
                                    'Intake: air is drawn (or forced by a turbocharger) into the cylinder. '
                                    'Compression: the piston squeezes it to around 1/16th of its volume, '
                                    'heating it past 500 °C. Power: fuel injected into that hot air ignites '
                                    'by itself — no spark plugs — and drives the piston down. Exhaust: the '
                                    'burnt gas leaves, often spinning the turbocharger on its way out.'
                                ),
                            },
                            {
                                'heading': 'Two-stroke giants, four-stroke workhorses',
                                'body': (
                                    'Large ships favour slow two-stroke engines turning at just 80–100 rpm, '
                                    'coupled directly to the propeller — no gearbox at all. Ferries, tugs '
                                    'and generators use faster four-strokes. Slow and enormous wins on fuel '
                                    'efficiency, which is why the biggest engines burn fuel measured in '
                                    'tonnes per hour, not litres.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Diesel ignites by compression heat — no spark plugs.',
                            'The four phases: intake, compression, power, exhaust.',
                            'Big ships use slow-turning two-strokes bolted straight to the prop shaft.',
                            'Turbochargers recycle exhaust energy to force in more air.',
                        ],
                        'quiz': {
                            'question': 'What ignites the fuel in a diesel engine?',
                            'options': [
                                'A spark plug timed by the camshaft',
                                'The heat of highly compressed air',
                                'A glow wire inside the injector',
                                'Friction from the piston rings',
                            ],
                            'answer': 1,
                            'explanation': 'Compressing air to ~1/16th of its volume heats it beyond diesel\'s ignition point (~210 °C). Inject fuel into that and it explodes on contact — compression ignition.',
                        },
                    },
                    {
                        'id': 'm1l2',
                        'title': 'Propellers & Thrust',
                        'minutes': 11,
                        'intro': (
                            'A propeller is a screw that drives through water — early engineers '
                            'literally called it a "screw propeller". How a spinning bronze sculpture '
                            'pushes 200 000 tonnes of steel across an ocean is a beautiful piece of '
                            'physics.'
                        ),
                        'sections': [
                            {
                                'heading': 'How blades make thrust',
                                'body': (
                                    'Each blade is a twisted wing. As it rotates it accelerates water '
                                    'backwards; Newton\'s third law pushes the ship forwards. Blade angle '
                                    '(pitch) is the gearing of the sea: coarse pitch for speed, fine pitch '
                                    'for pulling power — which is why a harbour tug\'s propeller looks '
                                    'nothing like a liner\'s.'
                                ),
                            },
                            {
                                'heading': 'Cavitation — the propeller\'s enemy',
                                'body': (
                                    'Spin a prop too hard and the pressure on the back of the blades drops '
                                    'so low that water boils cold, forming vapour bubbles that collapse '
                                    'with hammer-blow violence. Cavitation eats blades, causes vibration '
                                    'and noise, and is the reason naval architects obsess over propeller '
                                    'design. Some modern ships add azimuth thrusters that rotate 360° — '
                                    'propulsion and steering in one unit.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Thrust is Newton\'s third law: throw water backwards, ship goes forwards.',
                            'Pitch is the propeller\'s "gear ratio".',
                            'Cavitation = cold boiling that erodes blades and causes vibration.',
                            'Azimuth thrusters rotate fully, replacing the rudder.',
                        ],
                        'quiz': {
                            'question': 'Cavitation damages propellers because…',
                            'options': [
                                'Salt crystals form on the blade tips',
                                'Vapour bubbles collapse violently against the blades',
                                'The blades overheat and soften',
                                'Seaweed wraps around the hub',
                            ],
                            'answer': 1,
                            'explanation': 'Low pressure makes water vaporise; the bubbles implode against the blade surface with enormous local force, pitting solid bronze over time.',
                        },
                    },
                    {
                        'id': 'm1l3',
                        'title': 'Shipboard Electrical Systems',
                        'minutes': 11,
                        'intro': (
                            'A modern ship is a floating town: navigation electronics, cargo cranes, '
                            'galley ovens, reefer containers and emergency systems all need power, '
                            'hundreds of kilometres from the nearest plug.'
                        ),
                        'sections': [
                            {
                                'heading': 'Generators and the main switchboard',
                                'body': (
                                    'Diesel generator sets — usually three or four — feed a main '
                                    'switchboard that distributes 440 V three-phase power around the ship. '
                                    'Critical loads (steering gear, navigation lights, radios) also have an '
                                    'emergency generator and batteries on a separate circuit, by law, so a '
                                    'blackout never leaves the ship blind and unsteerable.'
                                ),
                            },
                            {
                                'heading': 'The cold chain at sea',
                                'body': (
                                    'South Africa exports citrus, wine and frozen fish in refrigerated '
                                    '"reefer" containers that each draw power like a small house. A reefer '
                                    'vessel out of Cape Town manages megawatts of refrigeration alone — '
                                    'one reason marine electricians are among the most employable trades in '
                                    'the maritime sector.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Multiple generator sets share load via the main switchboard.',
                            'Emergency power for steering, lights and radio is a legal requirement.',
                            'Reefer containers make ships major mobile consumers of electricity.',
                            'Marine electrician is a scarce, in-demand trade in SA ports.',
                        ],
                        'quiz': {
                            'question': 'Why do ships carry an emergency generator on a separate circuit?',
                            'options': [
                                'To power the galley during meal times',
                                'So critical systems survive a main switchboard blackout',
                                'To recharge the crew\'s personal devices',
                                'Because diesel generators cannot run at night',
                            ],
                            'answer': 1,
                            'explanation': 'SOLAS requires independent emergency power so steering, navigation lights and communications keep working even if the main electrical plant fails completely.',
                        },
                    },
                ],
            },
            {
                'id': 'm2',
                'title': 'Keeping the Ship Alive',
                'lessons': [
                    {
                        'id': 'm2l1',
                        'title': 'Cooling, Lubrication & Fuel Systems',
                        'minutes': 12,
                        'intro': (
                            'An engine producing 50 000 kW also produces ferocious heat and friction. '
                            'Three fluid systems — cooling water, lube oil and fuel — form the '
                            'life-support loop that lets it survive weeks at full power.'
                        ),
                        'sections': [
                            {
                                'heading': 'Two loops of cooling water',
                                'body': (
                                    'Seawater is corrosive, so it never touches the engine. Instead, clean '
                                    'fresh water circulates through the engine block, then passes through a '
                                    'heat exchanger where seawater carries the heat overboard. Two loops, '
                                    'one handshake — the same principle as a car radiator, scaled up a '
                                    'thousand times.'
                                ),
                            },
                            {
                                'heading': 'Oil and fuel treatment',
                                'body': (
                                    'Lube oil is pumped to every bearing, then filtered, cooled and '
                                    'centrifuged to strip out soot and water before going around again. '
                                    'Heavy fuel oil is so thick it must be heated to about 130 °C just to '
                                    'flow and be purified before injection. Engineers spend more time '
                                    'caring for fluids than for metal — dirty oil kills engines faster '
                                    'than hard running ever will.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Fresh water cools the engine; seawater cools the fresh water.',
                            'Lube oil is continuously filtered and centrifuged, not replaced.',
                            'Heavy fuel oil must be heated and purified before it can burn.',
                            'Fluid care is the heart of preventive maintenance.',
                        ],
                        'quiz': {
                            'question': 'Why does seawater never circulate directly through the engine block?',
                            'options': [
                                'It is too cold and would crack the block',
                                'Salt water is corrosive and would destroy the engine internals',
                                'Pumping seawater is illegal inside harbours',
                                'Seawater cannot absorb heat effectively',
                            ],
                            'answer': 1,
                            'explanation': 'Hot salt water is brutally corrosive. Ships use a closed fresh-water loop inside the engine and dump its heat to seawater through a heat exchanger.',
                        },
                    },
                    {
                        'id': 'm2l2',
                        'title': 'Watchkeeping & Maintenance',
                        'minutes': 11,
                        'intro': (
                            'Engine rooms run 24/7, watched in rotating shifts. The engineer of the '
                            'watch reads hundreds of temperatures and pressures, hears problems before '
                            'gauges show them, and follows the planned maintenance system like '
                            'scripture.'
                        ),
                        'sections': [
                            {
                                'heading': 'The watch system',
                                'body': (
                                    'Traditional watches run four hours on, eight off (the 4–8, 8–12 and '
                                    '12–4). Modern automated ships may run an unmanned engine room at '
                                    'night — sensors alarm the duty engineer\'s cabin — but someone is '
                                    'always responsible. Logbook entries every watch create the legal '
                                    'record of the machinery\'s health.'
                                ),
                            },
                            {
                                'heading': 'Planned maintenance',
                                'body': (
                                    'Every pump, valve and filter has a maintenance schedule by running '
                                    'hours — overhaul this purifier every 8 000 h, renew that bearing at '
                                    '16 000 h. Engineers at the Transnet Maritime School of Excellence in '
                                    'Durban train on full-size engine simulators before ever touching a '
                                    'real plant, exactly the way pilots train in flight simulators.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Watches keep the engine room continuously supervised.',
                            'Logbooks are legal documents recording machinery condition.',
                            'Maintenance is scheduled by running hours, not by breakdowns.',
                            'SA engineers train on engine-room simulators in Durban.',
                        ],
                        'quiz': {
                            'question': 'A planned maintenance system schedules work based on…',
                            'options': [
                                'Whenever something breaks down',
                                'Equipment running hours and fixed intervals',
                                'The chief engineer\'s mood',
                                'Only what class surveyors demand each year',
                            ],
                            'answer': 1,
                            'explanation': 'Preventive maintenance replaces parts on schedule — by running hours — before failure. Breakdown maintenance at sea is dangerous and ruinously expensive.',
                        },
                    },
                ],
            },
        ],
        'simulation': {
            'type': 'helm',
            'title': 'Precision Docking: Cape Town Dry Dock',
            'briefing': (
                'The tug Enseleni must shepherd a damaged trawler into Cape Town\'s Sturrock '
                'Dry Dock. This is slow, surgical work: tight gates, moored vessels either '
                'side, and a westerly setting you onto the caisson. Low speed, small '
                'corrections — engineers feel the ship, they don\'t fight it.'
            ),
            'pass_score': 60,
            'max_nm': 60,
            'config': {
                'world': {'w': 1600, 'h': 1000},
                'start': {'x': 180, 'y': 160, 'heading': 135},
                'vessel': {'max_speed': 3.6, 'turn_rate': 85},
                'current': {'x': 0.45, 'y': 0.15},
                'time_par': 110,
                'time_limit': 260,
                'waypoints': [
                    {'x': 520, 'y': 360, 'r': 46, 'label': 'Outer Basin'},
                    {'x': 860, 'y': 470, 'r': 42, 'label': 'Tanker Basin Gate'},
                    {'x': 1130, 'y': 640, 'r': 40, 'label': 'Dock Approach'},
                    {'x': 1400, 'y': 820, 'r': 42, 'label': 'Sturrock Dry Dock'},
                ],
                'hazards': [
                    {'x': 780, 'y': 250, 'r': 110, 'label': 'Moored Bulker'},
                    {'x': 1080, 'y': 870, 'r': 120, 'label': 'Repair Quay'},
                    {'x': 1320, 'y': 430, 'r': 100, 'label': 'Caisson Wall'},
                ],
            },
        },
    },

    # ------------------------------------------------------------------ 3
    {
        'slug': 'ocean-science',
        'title': 'Ocean Science & the Blue Economy',
        'tagline': 'Two great currents, one extraordinary coastline — and an economy beneath the waves.',
        'description': (
            'South Africa sits at the meeting point of two oceans and two mighty current '
            'systems. Explore the science of the Agulhas and Benguela, the ecosystems they '
            'power, and how Operation Phakisa aims to turn our ocean territory into jobs '
            'and sustainable growth.'
        ),
        'category': 'Marine Science',
        'grade_level': 'Grade 9–12',
        'difficulty': 'Beginner',
        'icon': 'water',
        'theme': {'from': '#00897B', 'to': '#00574B'},
        'modules': [
            {
                'id': 'm1',
                'title': 'The Living Ocean',
                'lessons': [
                    {
                        'id': 'm1l1',
                        'title': 'Two Currents, Two Worlds',
                        'minutes': 12,
                        'intro': (
                            'Stand at Cape Agulhas and you are at the boundary of two ocean engines. '
                            'To the east, the warm Agulhas Current; to the west, the cold Benguela. '
                            'Between them they decide our weather, our fisheries and our shipping '
                            'routes.'
                        ),
                        'sections': [
                            {
                                'heading': 'The warm Agulhas',
                                'body': (
                                    'The Agulhas carries warm Indian Ocean water southwest along the east '
                                    'coast at up to 5 knots, moving more water than all the world\'s rivers '
                                    'combined. It feeds rainfall to KwaZulu-Natal, warms east coast seas to '
                                    'subtropical temperatures, and at the continent\'s tip "retroflects" — '
                                    'snaps back on itself — shedding giant eddies that carry Indian Ocean '
                                    'water into the Atlantic and influence climate worldwide.'
                                ),
                            },
                            {
                                'heading': 'The cold, rich Benguela',
                                'body': (
                                    'On the west coast, southerly winds push surface water offshore and '
                                    'deep, icy, nutrient-rich water rises to replace it — upwelling. Those '
                                    'nutrients fuel plankton blooms that feed sardines, anchovies, snoek '
                                    'and the seabird colonies of the West Coast. Cold sea, rich sea: the '
                                    'Benguela supports one of the most productive fisheries on Earth.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Agulhas: warm, fast, east coast, flows southwest.',
                            'Benguela: cold, slow, west coast, driven by upwelling.',
                            'Upwelling lifts nutrients that power the food chain.',
                            'Agulhas eddies leak Indian Ocean water into the Atlantic — a global climate link.',
                        ],
                        'quiz': {
                            'question': 'Why is the cold Benguela Current so rich in marine life?',
                            'options': [
                                'Cold water contains more salt',
                                'Upwelling lifts deep nutrients that fuel plankton blooms',
                                'Fish prefer to swim in colder water',
                                'It receives nutrients from the Orange River alone',
                            ],
                            'answer': 1,
                            'explanation': 'Wind-driven upwelling drags deep, nutrient-loaded water to the sunlit surface. Plankton bloom, fish feed on plankton, and everything else feeds on the fish.',
                        },
                    },
                    {
                        'id': 'm1l2',
                        'title': 'Marine Ecosystems of South Africa',
                        'minutes': 12,
                        'intro': (
                            'From kelp forests off Cape Town to coral reefs at Sodwana Bay, South '
                            'Africa packs polar-to-tropical marine habitats into one coastline — '
                            'home to over 13 000 marine species, many found nowhere else.'
                        ),
                        'sections': [
                            {
                                'heading': 'Kelp forests and rocky shores',
                                'body': (
                                    'Giant kelp forms underwater forests along the cold west and southwest '
                                    'coasts — habitat for abalone, rock lobster and the octopus made famous '
                                    'by "My Octopus Teacher", filmed in False Bay. Rocky shores between '
                                    'tides are natural laboratories: every metre up the shore is a harsher '
                                    'world of sun and surf, and life zones itself in visible bands.'
                                ),
                            },
                            {
                                'heading': 'From sardine run to coral reefs',
                                'body': (
                                    'Each winter the sardine run sees billions of fish ride a cold inshore '
                                    'counter-current up the east coast, chased by dolphins, sharks, whales '
                                    'and gannets — the greatest shoal on Earth. Further north, Sodwana '
                                    'Bay\'s reefs in the iSimangaliso World Heritage Site host Africa\'s '
                                    'southernmost corals. Marine Protected Areas now cover key habitats, '
                                    'and marine biologists, skippers and dive guides all build careers on '
                                    'them.'
                                ),
                            },
                        ],
                        'key_points': [
                            'SA spans cold kelp forests to tropical coral reefs in one coastline.',
                            'The sardine run is one of the largest animal migrations on the planet.',
                            'Marine Protected Areas safeguard breeding and feeding grounds.',
                            'Biodiversity underpins tourism and fishing jobs.',
                        ],
                        'quiz': {
                            'question': 'The sardine run happens when sardines…',
                            'options': [
                                'Migrate up the east coast in a cold inshore counter-current',
                                'Spawn in the warm Mozambique Channel',
                                'Escape the Benguela upwelling zone',
                                'Follow cargo ships for food scraps',
                            ],
                            'answer': 0,
                            'explanation': 'In winter a tongue of cool water hugs the east coast inshore of the warm Agulhas, and sardines surge north inside it — pursued by nearly everything that eats fish.',
                        },
                    },
                ],
            },
            {
                'id': 'm2',
                'title': 'The Blue Economy',
                'lessons': [
                    {
                        'id': 'm2l1',
                        'title': 'Operation Phakisa & Ocean Wealth',
                        'minutes': 11,
                        'intro': (
                            'South Africa\'s ocean territory is bigger than its land. In 2014 the '
                            'government launched Operation Phakisa ("hurry up" in Sesotho) to unlock '
                            'that blue economy — shipping, aquaculture, energy and coastal tourism.'
                        ),
                        'sections': [
                            {
                                'heading': 'What the ocean economy includes',
                                'body': (
                                    'Marine transport and manufacturing (ports, ship repair, boatbuilding), '
                                    'offshore oil and gas, aquaculture, and coastal tourism are the focus '
                                    'areas. The ocean economy already supports hundreds of thousands of '
                                    'jobs, and Phakisa\'s goal is to grow it into one of the country\'s '
                                    'largest employers — with skills, not just resources, as the limiting '
                                    'factor.'
                                ),
                            },
                            {
                                'heading': 'Why skills are the bottleneck',
                                'body': (
                                    'Ships need officers, ports need engineers, fish farms need '
                                    'technicians, and surveys need scientists. Institutions like SAIMI '
                                    '(the South African International Maritime Institute), Lawhill Maritime '
                                    'Centre and maritime high schools exist precisely to fill this gap — '
                                    'which is why a learner finishing this course is looking at a genuine '
                                    'career pipeline, not a hobby.'
                                ),
                            },
                        ],
                        'key_points': [
                            'SA\'s ocean territory exceeds its land area.',
                            'Operation Phakisa targets shipping, aquaculture, energy and tourism.',
                            'The scarce resource is skilled people, not ocean space.',
                            'A real institutional pipeline exists: school → maritime college → sea.',
                        ],
                        'quiz': {
                            'question': '"Operation Phakisa" is best described as…',
                            'options': [
                                'A naval defence exercise held off Durban',
                                'A government plan to grow the ocean (blue) economy',
                                'A fishing quota system for small-scale fishers',
                                'A weather warning system for the Cape of Storms',
                            ],
                            'answer': 1,
                            'explanation': 'Phakisa ("hurry up") is the national initiative to fast-track growth and jobs from marine transport, manufacturing, aquaculture, energy and coastal tourism.',
                        },
                    },
                    {
                        'id': 'm2l2',
                        'title': 'Sustainable Fisheries & Aquaculture',
                        'minutes': 11,
                        'intro': (
                            'Fish are renewable — if we let them renew. The science of sustainable '
                            'fishing is a balancing act between feeding people today and keeping '
                            'stocks alive for tomorrow, and South Africa is both a success story and '
                            'a cautionary tale.'
                        ),
                        'sections': [
                            {
                                'heading': 'Quotas, bycatch and MPAs',
                                'body': (
                                    'Scientists estimate each stock\'s maximum sustainable yield and set '
                                    'annual quotas (Total Allowable Catch). The hake trawl fishery — our '
                                    'most valuable — earned international MSC certification by respecting '
                                    'them. Abalone (perlemoen) shows the opposite path: poaching collapsed '
                                    'wild stocks despite quotas. Marine Protected Areas act as banks where '
                                    'fish populations can rebuild and spill over into fished areas.'
                                ),
                            },
                            {
                                'heading': 'Farming the sea',
                                'body': (
                                    'Aquaculture — farming mussels, oysters, abalone and finfish — is the '
                                    'fastest-growing food sector on Earth. Saldanha Bay\'s mussel farms and '
                                    'land-based abalone farms along the southern Cape already export '
                                    'globally and employ coastal communities. It is part biology, part '
                                    'engineering, part business: a genuinely multidisciplinary career.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Quotas cap catches at what a stock can replace each year.',
                            'SA hake is internationally certified sustainable; abalone was poached to collapse.',
                            'MPAs let populations rebuild and spill over.',
                            'Aquaculture is the world\'s fastest-growing food production sector.',
                        ],
                        'quiz': {
                            'question': 'A Total Allowable Catch (TAC) is set so that…',
                            'options': [
                                'Every boat catches exactly the same amount',
                                'The catch stays within what the stock can biologically replace',
                                'Exports never exceed local consumption',
                                'Only large companies may fish commercially',
                            ],
                            'answer': 1,
                            'explanation': 'TACs are science-based ceilings: harvest at or below the stock\'s replacement rate and you can fish the same waters forever.',
                        },
                    },
                ],
            },
        ],
        'simulation': {
            'type': 'helm',
            'title': 'Research Transect: Benguela Survey',
            'briefing': (
                'You command the research vessel Ukwabelana on a plankton survey off the West '
                'Coast. Visit each sampling station in sequence while the Benguela\'s '
                'wind-driven surface drift pushes you north. Scientific data is only valid if '
                'you hit every station — and the foul ground near the islands will end your '
                'cruise early.'
            ),
            'pass_score': 60,
            'max_nm': 60,
            'config': {
                'world': {'w': 1600, 'h': 1000},
                'start': {'x': 200, 'y': 870, 'heading': 30},
                'vessel': {'max_speed': 4.6, 'turn_rate': 75},
                'current': {'x': 0.1, 'y': -0.6},
                'time_par': 100,
                'time_limit': 250,
                'waypoints': [
                    {'x': 480, 'y': 700, 'r': 48, 'label': 'Station A'},
                    {'x': 900, 'y': 760, 'r': 48, 'label': 'Station B'},
                    {'x': 1240, 'y': 560, 'r': 46, 'label': 'Station C'},
                    {'x': 980, 'y': 300, 'r': 46, 'label': 'Station D'},
                    {'x': 480, 'y': 180, 'r': 50, 'label': 'Station E'},
                ],
                'hazards': [
                    {'x': 700, 'y': 480, 'r': 115, 'label': 'Bird Island Reef'},
                    {'x': 1340, 'y': 230, 'r': 105, 'label': 'Foul Ground'},
                    {'x': 200, 'y': 420, 'r': 95, 'label': 'Kelp Beds'},
                ],
            },
        },
    },

    # ------------------------------------------------------------------ 4
    {
        'slug': 'maritime-safety',
        'title': 'Maritime Safety & Survival',
        'tagline': 'The sea forgives nothing — train until safety is instinct.',
        'description': (
            'Why ships follow rules written in past tragedies, how to survive in the water, '
            'what to do when fire breaks out where no fire brigade can reach you, and how '
            'search and rescue actually finds people. The most important course on the '
            'platform.'
        ),
        'category': 'Safety',
        'grade_level': 'Grade 9–12',
        'difficulty': 'Beginner',
        'icon': 'health_and_safety',
        'theme': {'from': '#C62828', 'to': '#8E0000'},
        'modules': [
            {
                'id': 'm1',
                'title': 'A Culture of Safety',
                'lessons': [
                    {
                        'id': 'm1l1',
                        'title': 'SOLAS: Rules Written in Loss',
                        'minutes': 11,
                        'intro': (
                            'On a freezing April night in 1912, the "unsinkable" Titanic sank with '
                            'lifeboats for barely half the people aboard. The world\'s answer was '
                            'SOLAS — the Safety of Life at Sea convention — still the master rulebook '
                            'of shipping today.'
                        ),
                        'sections': [
                            {
                                'heading': 'What SOLAS demands',
                                'body': (
                                    'Lifeboat and liferaft capacity for every soul on board. Fire '
                                    'detection and fixed extinguishing systems. Radio watchkeeping and '
                                    'distress equipment. Stability standards, drills, training '
                                    'certificates. Every flag state writes SOLAS into national law — in '
                                    'South Africa, SAMSA (the SA Maritime Safety Authority) inspects ships '
                                    'and can detain any vessel that falls short.'
                                ),
                            },
                            {
                                'heading': 'Safety culture beats paperwork',
                                'body': (
                                    'Rules only work when crews believe in them. Modern maritime safety '
                                    'borrows from aviation: report near-misses without blame, brief before '
                                    'every risky job, and empower the most junior deckhand to stop unsafe '
                                    'work. Investigations of almost every modern casualty find the same '
                                    'thing — the procedure existed; the culture failed.'
                                ),
                            },
                        ],
                        'key_points': [
                            'SOLAS was born from the Titanic disaster (first version 1914).',
                            'Lifesaving capacity for 100% of people aboard is non-negotiable.',
                            'SAMSA enforces these standards in South African waters.',
                            'Anyone on board may stop unsafe work — rank does not outrank risk.',
                        ],
                        'quiz': {
                            'question': 'Which body enforces international safety standards on ships in SA waters?',
                            'options': ['SARS', 'SAMSA', 'SANParks', 'The Weather Service'],
                            'answer': 1,
                            'explanation': 'The South African Maritime Safety Authority surveys ships, certifies seafarers and may detain substandard vessels under port state control.',
                        },
                    },
                    {
                        'id': 'm1l2',
                        'title': 'Personal Survival Techniques',
                        'minutes': 12,
                        'intro': (
                            'If you ever go into the sea unplanned, the next ten minutes follow a '
                            'script written by physiology. Knowing the script — cold shock, the 1-10-1 '
                            'rule, HELP position — multiplies your odds enormously.'
                        ),
                        'sections': [
                            {
                                'heading': 'Cold shock and 1-10-1',
                                'body': (
                                    'Hitting cold water triggers a gasp reflex and panicked breathing for '
                                    'about 1 minute — float, don\'t swim, and get your breathing under '
                                    'control. You then have roughly 10 minutes of useful muscle movement to '
                                    'get out, get to a raft, or secure yourself. After that, about 1 hour '
                                    'before hypothermia takes consciousness. One minute, ten minutes, one '
                                    'hour: spend them in that order of priority.'
                                ),
                            },
                            {
                                'heading': 'Lifejackets, HELP and huddle',
                                'body': (
                                    'A lifejacket converts the survival problem from "keep swimming" to '
                                    '"keep warm and be seen". Alone, pull knees to chest in the HELP '
                                    'position (Heat Escape Lessening Posture); in a group, huddle chest-to-'
                                    'chest. Stay with the boat or wreckage — searchers find big objects, '
                                    'not heads in swell. The NSRI, South Africa\'s volunteer sea rescue '
                                    'service, teaches exactly this in its free Survival Swimming lessons '
                                    'nationwide.'
                                ),
                            },
                        ],
                        'key_points': [
                            '1-10-1: one minute to control breathing, ten of movement, one hour of warmth.',
                            'Float first — cold-shock drowning kills faster than hypothermia.',
                            'HELP position and group huddles slow heat loss.',
                            'Stay with the vessel or wreckage; it is what rescuers can see.',
                        ],
                        'quiz': {
                            'question': 'In the first minute after falling into cold water you should…',
                            'options': [
                                'Swim hard for shore before your muscles cool',
                                'Float, control your breathing and resist the urge to thrash',
                                'Remove heavy clothing immediately',
                                'Dive under to check for obstacles',
                            ],
                            'answer': 1,
                            'explanation': 'Cold shock forces gasping and hyperventilation. Floating calmly through that first minute — letting breathing settle — is the single biggest survival decision.',
                        },
                    },
                    {
                        'id': 'm1l3',
                        'title': 'Fire On Board',
                        'minutes': 11,
                        'intro': (
                            'At sea there is no fire brigade — the crew is the fire brigade. Ships '
                            'are steel boxes full of fuel, cargo and electricity, so firefighting '
                            'doctrine is drilled until it is muscle memory.'
                        ),
                        'sections': [
                            {
                                'heading': 'The fire triangle at sea',
                                'body': (
                                    'Fire needs heat, fuel and oxygen; remove any side and it dies. Class B '
                                    '(oil) fires are smothered with foam, never water — water sinks under '
                                    'burning oil, flashes to steam and hurls the fire outward. Class C '
                                    '(electrical) demands CO₂ or dry powder. Engine rooms carry fixed CO₂ '
                                    'flooding systems that can drown the entire compartment in minutes — '
                                    'after the crew is counted out.'
                                ),
                            },
                            {
                                'heading': 'Containment is the ship\'s superpower',
                                'body': (
                                    'Steel bulkheads divide ships into fire zones; fire doors and '
                                    'ventilation flaps starve a blaze of oxygen. The first response to a '
                                    'cabin fire is often simply: close the door, cut the vents, cool the '
                                    'boundaries. Every crew member learns this at STCW Basic Safety '
                                    'Training — the one-week course that is the entry ticket to any '
                                    'seagoing job, offered at academies in Cape Town and Durban.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Remove heat, fuel or oxygen and fire dies — pick the side you can reach.',
                            'Never put water on burning oil; smother it with foam.',
                            'Closing doors and vents is firefighting, not avoidance.',
                            'STCW Basic Safety Training is the legal entry requirement for sea work.',
                        ],
                        'quiz': {
                            'question': 'Why must you never spray water onto a burning-oil (Class B) fire?',
                            'options': [
                                'Water is too scarce on ships to waste',
                                'Water sinks, flashes to steam and violently spreads the burning oil',
                                'Oil fires are too cold for water to affect',
                                'Salt water conducts electricity into the flames',
                            ],
                            'answer': 1,
                            'explanation': 'Water drops beneath the lighter oil, instantly boils, and the expanding steam erupts through the surface throwing burning fuel in all directions.',
                        },
                    },
                ],
            },
            {
                'id': 'm2',
                'title': 'Emergency Response',
                'lessons': [
                    {
                        'id': 'm2l1',
                        'title': 'Man Overboard & Search Patterns',
                        'minutes': 12,
                        'intro': (
                            '"MAN OVERBOARD, STARBOARD SIDE!" From that shout, a choreography '
                            'begins that every bridge team rehearses: mark, turn, point, search. A '
                            'head in the water is visible for seconds at a time — the method is what '
                            'finds it.'
                        ),
                        'sections': [
                            {
                                'heading': 'Immediate actions',
                                'body': (
                                    'Throw a lifebuoy (with light and smoke) instantly — it marks the spot '
                                    'and gives the casualty flotation. Post a lookout whose only job is to '
                                    'point continuously at the person. Hit the MOB button on the GPS. Then '
                                    'turn: the Williamson turn brings the ship back down her own track on a '
                                    'reciprocal course — built for exactly this moment.'
                                ),
                            },
                            {
                                'heading': 'Search patterns',
                                'body': (
                                    'If contact is lost, ships fly geometry: the expanding square spirals '
                                    'outward from the last known position; the sector search sweeps a '
                                    'clover-leaf through it; parallel tracks comb large areas with multiple '
                                    'vessels. In South Africa, MRCC Cape Town coordinates rescues across '
                                    'one of the largest search regions on Earth, tasking the NSRI, ships '
                                    'and aircraft. You will fly an expanding-pattern search yourself in '
                                    'this course\'s simulation.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Lifebuoy first, dedicated pointer second, MOB mark third.',
                            'The Williamson turn returns a ship along its own wake.',
                            'Expanding square: spiral out from the last known position.',
                            'MRCC Cape Town coordinates SA\'s vast search-and-rescue region.',
                        ],
                        'quiz': {
                            'question': 'The first physical action when someone falls overboard is to…',
                            'options': [
                                'Stop the engines immediately',
                                'Throw a lifebuoy to mark the position and give flotation',
                                'Lower the rescue boat',
                                'Sound five short blasts',
                            ],
                            'answer': 1,
                            'explanation': 'The buoy does two jobs at once: it supports the casualty and visually anchors the datum the whole search will be built around.',
                        },
                    },
                    {
                        'id': 'm2l2',
                        'title': 'First Aid Far From Help',
                        'minutes': 11,
                        'intro': (
                            'A ship three days from port is its own hospital. Maritime first aid is '
                            'ordinary first aid with one brutal addition: time. You stabilise, you '
                            'communicate, and you keep someone alive until the coast can reach you.'
                        ),
                        'sections': [
                            {
                                'heading': 'Priorities: DR ABC',
                                'body': (
                                    'Danger — make the scene safe; a rescuer who becomes a casualty doubles '
                                    'the problem. Response — check consciousness. Airway, Breathing, '
                                    'Circulation: open the airway, check breathing, start CPR (30 '
                                    'compressions to 2 breaths) if absent, and control serious bleeding '
                                    'with direct pressure. Hypothermia casualties are rewarmed gently — '
                                    'handled roughly, a cold heart can stop.'
                                ),
                            },
                            {
                                'heading': 'Radio medical advice',
                                'body': (
                                    'Ships are never truly alone: via GMDSS radio, any vessel can reach '
                                    'telemedical assistance — in SA waters, through MRCC Cape Town — where '
                                    'doctors guide treatment step by step. Serious cases trigger medevac by '
                                    'rescue helicopter, which is why every report follows a strict format: '
                                    'position, patient, vital signs, what you\'ve done. Clear comms is a '
                                    'clinical skill.'
                                ),
                            },
                        ],
                        'key_points': [
                            'DR ABC: Danger, Response, Airway, Breathing, Circulation.',
                            'CPR rhythm: 30 compressions to 2 breaths, hard and fast.',
                            'Rewarm hypothermia gently — rough handling can stop the heart.',
                            'Telemedical advice by radio turns any ship into a guided clinic.',
                        ],
                        'quiz': {
                            'question': 'In DR ABC, the "D" reminds rescuers to first…',
                            'options': [
                                'Defibrillate the casualty',
                                'Check the scene for danger to themselves',
                                'Document the time of the incident',
                                'Dress all visible wounds',
                            ],
                            'answer': 1,
                            'explanation': 'Scene safety comes before everything. A second casualty — the rescuer — turns one emergency into two and halves the help available.',
                        },
                    },
                ],
            },
        ],
        'simulation': {
            'type': 'helm',
            'title': 'SAR Mission: Man Overboard off Sea Point',
            'briefing': (
                'NSRI Station 3 has launched you in the rescue craft Spirit of Vodacom. A '
                'swimmer was swept out off Sea Point and MRCC has given you a datum. Run the '
                'expanding search pattern through every marker — the pattern IS the rescue. '
                'A freshening south-easter is pushing you offshore, and the surf line over '
                'the reefs is no place for a rescue boat.'
            ),
            'pass_score': 60,
            'max_nm': 60,
            'config': {
                'world': {'w': 1600, 'h': 1000},
                'start': {'x': 820, 'y': 920, 'heading': 0},
                'vessel': {'max_speed': 5.6, 'turn_rate': 95},
                'current': {'x': 0.5, 'y': -0.4},
                'time_par': 90,
                'time_limit': 220,
                'waypoints': [
                    {'x': 820, 'y': 620, 'r': 46, 'label': 'Datum'},
                    {'x': 1020, 'y': 620, 'r': 44, 'label': 'Leg 1'},
                    {'x': 1020, 'y': 420, 'r': 44, 'label': 'Leg 2'},
                    {'x': 620, 'y': 420, 'r': 44, 'label': 'Leg 3'},
                    {'x': 620, 'y': 760, 'r': 44, 'label': 'Leg 4'},
                    {'x': 1180, 'y': 230, 'r': 50, 'label': 'Casualty!'},
                ],
                'hazards': [
                    {'x': 320, 'y': 260, 'r': 130, 'label': 'Whale Rock Surf'},
                    {'x': 1420, 'y': 700, 'r': 110, 'label': 'Kelp & Reef'},
                    {'x': 240, 'y': 760, 'r': 95, 'label': 'Backline Surf'},
                ],
            },
        },
    },

    # ------------------------------------------------------------------ 5
    {
        'slug': 'ports-logistics',
        'title': 'Ports, Shipping & Global Logistics',
        'tagline': 'How a phone crosses three oceans to reach your pocket.',
        'description': (
            'Ninety percent of everything you own travelled by sea. Trace the journey '
            'through container ships, mega-ports and the logistics chains that link a '
            'factory in Asia to a shop in Soweto — and meet the careers that keep South '
            'Africa\'s eight commercial ports moving.'
        ),
        'category': 'Logistics',
        'grade_level': 'Grade 9–12',
        'difficulty': 'Beginner',
        'icon': 'directions_boat',
        'theme': {'from': '#5E35B1', 'to': '#311B92'},
        'modules': [
            {
                'id': 'm1',
                'title': 'How Trade Moves',
                'lessons': [
                    {
                        'id': 'm1l1',
                        'title': 'The Container Revolution',
                        'minutes': 11,
                        'intro': (
                            'In 1956 a trucking magnate named Malcom McLean welded boxes to a ship\'s '
                            'deck and accidentally rebuilt the world economy. The humble steel '
                            'container cut the cost of moving goods by over 90% — globalisation in a '
                            '6-metre box.'
                        ),
                        'sections': [
                            {
                                'heading': 'Why a box changed everything',
                                'body': (
                                    'Before containers, gangs of stevedores hand-carried sacks and crates; '
                                    'a ship could spend a week in port. A standard box (the TEU — twenty-'
                                    'foot equivalent unit) moves from truck to train to ship without ever '
                                    'being opened, and a modern crane swings one ashore every 90 seconds. '
                                    'Port time collapsed from weeks to hours, and shipping became so cheap '
                                    'it is often the smallest cost in a product\'s price.'
                                ),
                            },
                            {
                                'heading': 'The scale of it',
                                'body': (
                                    'The largest container ships carry over 24 000 TEU — stacked end to '
                                    'end, that single cargo would stretch about 145 km, roughly Johannesburg '
                                    'to Vereeniging and back. They are run by crews of barely 25 people, '
                                    'which tells you how automated and systematised the industry has '
                                    'become — and why its jobs increasingly look like engineering and data '
                                    'work, not manual labour.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Containerisation cut cargo-handling costs by ~90%.',
                            'TEU (twenty-foot equivalent unit) is the industry\'s unit of count.',
                            'Standardisation lets one box move by truck, rail and ship unopened.',
                            'Mega-ships: 24 000+ TEU moved by crews of ~25.',
                        ],
                        'quiz': {
                            'question': 'The shipping container transformed world trade primarily by…',
                            'options': [
                                'Making ships travel significantly faster',
                                'Standardising cargo so handling became fast, cheap and mechanised',
                                'Eliminating the need for ports entirely',
                                'Allowing food to be refrigerated at sea',
                            ],
                            'answer': 1,
                            'explanation': 'The box itself is the technology: one standard shape means cranes, trucks, trains and ships all interlock, collapsing port time from weeks to hours.',
                        },
                    },
                    {
                        'id': 'm1l2',
                        'title': 'Inside the Port of Durban',
                        'minutes': 12,
                        'intro': (
                            'Durban is sub-Saharan Africa\'s busiest port: around 60% of South '
                            'Africa\'s container traffic crosses its quays. Spend a day inside and '
                            'you will see a city-sized machine with thousands of moving parts — and '
                            'thousands of careers.'
                        ),
                        'sections': [
                            {
                                'heading': 'Anatomy of a working port',
                                'body': (
                                    'Marine pilots board arriving ships at sea and guide them in — local '
                                    'knowledge is compulsory. Tugs muscle the ship onto the berth. Ship-to-'
                                    'shore gantry cranes lift boxes to straddle carriers that stack the '
                                    'yard, while the terminal operating system tracks every container\'s '
                                    'position, weight and destination in real time. Beyond the fence, '
                                    'trucks and Transnet rail haul the boxes inland to Gauteng.'
                                ),
                            },
                            {
                                'heading': 'Who works here',
                                'body': (
                                    'Transnet National Ports Authority runs the harbour itself; Transnet '
                                    'Port Terminals operates the cranes and yards. Between them: harbour '
                                    'masters, pilots, tug skippers, crane operators, planners, marine '
                                    'engineers, customs officers, clearing agents and logistics analysts. '
                                    'Richards Bay, up the coast, runs the world\'s largest coal export '
                                    'terminal; Cape Town moves the fruit harvest; Saldanha ships iron ore. '
                                    'Each port is a different machine.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Durban handles ~60% of SA\'s container traffic.',
                            'Pilots, tugs, cranes and yard systems hand a ship along a precise chain.',
                            'Terminal operating systems track every box in real time.',
                            'Each SA port specialises: coal (Richards Bay), ore (Saldanha), fruit (Cape Town).',
                        ],
                        'quiz': {
                            'question': 'Why must a marine pilot board large ships entering Durban?',
                            'options': [
                                'To inspect the cargo for customs',
                                'Local-knowledge pilotage is compulsory for safe harbour navigation',
                                'To replace the captain for the rest of the voyage',
                                'To operate the ship\'s cranes during discharge',
                            ],
                            'answer': 1,
                            'explanation': 'Harbour pilotage is compulsory: the pilot brings intimate knowledge of local channels, currents and berths that no visiting captain can match.',
                        },
                    },
                    {
                        'id': 'm1l3',
                        'title': 'Ship Types & Their Cargoes',
                        'minutes': 10,
                        'intro': (
                            'Ships are shaped by what they carry. Learn to read silhouettes on the '
                            'horizon and you can name the cargo, the route and half the economics at '
                            'a glance.'
                        ),
                        'sections': [
                            {
                                'heading': 'The big five',
                                'body': (
                                    'Container ships: decks stacked with boxes, liner schedules like bus '
                                    'timetables. Bulk carriers: long flat hatches hiding coal, ore or '
                                    'grain. Tankers: low, pipe-covered decks carrying crude oil, fuel or '
                                    'chemicals. Ro-ros: floating parking garages that vehicles drive onto. '
                                    'Gas carriers: unmistakable spheres or domes of LNG and LPG. Around '
                                    'them swarm the workboats — tugs, dredgers, supply vessels and '
                                    'fishing fleets.'
                                ),
                            },
                            {
                                'heading': 'Tramp vs liner trades',
                                'body': (
                                    'Liners sail fixed routes on fixed schedules (container services). '
                                    'Tramp ships go wherever cargo pays, fixed voyage by voyage on '
                                    'chartering markets — the Uber of the oceans, complete with surge '
                                    'pricing. Freight rates swing wildly with world events, which is why '
                                    'shipbrokers and charterers in glass offices watch the news as keenly '
                                    'as captains watch the weather.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Hull shape and deck gear reveal a ship\'s cargo from kilometres away.',
                            'Liner = fixed schedule; tramp = follows the cargo market.',
                            'Gas carriers\' spheres are the most recognisable silhouette at sea.',
                            'Shipbroking and chartering are maritime careers fought in offices, not on decks.',
                        ],
                        'quiz': {
                            'question': 'A ship with long flat hatch covers and no deck cranes is most likely a…',
                            'options': [
                                'Gas carrier',
                                'Bulk carrier loading at equipped ports',
                                'Ro-ro vehicle carrier',
                                'Fishing trawler',
                            ],
                            'answer': 1,
                            'explanation': 'Gearless bulk carriers present a clean run of hatches and rely on shore equipment — exactly what you see at Richards Bay\'s coal terminal or Saldanha\'s ore berths.',
                        },
                    },
                ],
            },
            {
                'id': 'm2',
                'title': 'The Logistics Chain',
                'lessons': [
                    {
                        'id': 'm2l1',
                        'title': 'From Factory Floor to Front Door',
                        'minutes': 12,
                        'intro': (
                            'Follow one box of phones from a factory in Shenzhen to a store in '
                            'Johannesburg and you meet a dozen professions, three legal systems and '
                            'a paper trail older than steam. Logistics is the choreography of all of '
                            'it.'
                        ),
                        'sections': [
                            {
                                'heading': 'The journey of one container',
                                'body': (
                                    'Factory → truck → Shenzhen terminal → mother ship to Singapore → '
                                    'transhipment onto an Africa service → 18 days across the Indian Ocean '
                                    '→ Durban → customs clearance → Transnet rail to City Deep, '
                                    'Johannesburg\'s inland "dry port" → distribution centre → store. '
                                    'Total sea freight cost per phone: often less than the charging cable. '
                                    'Total coordination: a freight forwarder choreographing every handover.'
                                ),
                            },
                            {
                                'heading': 'Documents move the cargo',
                                'body': (
                                    'No paper, no cargo. The bill of lading is simultaneously a receipt, a '
                                    'contract and the title deed to the goods — whoever holds it owns the '
                                    'cargo. Customs declarations, certificates of origin and inspection '
                                    'certificates gate each border. Master one truth of logistics: '
                                    'information moves the cargo; the crane only lifts it.'
                                ),
                            },
                        ],
                        'key_points': [
                            'A single import touches ship, rail, road, port and customs systems.',
                            'City Deep in Johannesburg is an inland container terminal ("dry port").',
                            'The bill of lading is receipt, contract and ownership document in one.',
                            'Freight forwarders are the conductors of the logistics orchestra.',
                        ],
                        'quiz': {
                            'question': 'Why is the bill of lading so important in shipping?',
                            'options': [
                                'It lists the crew members aboard the vessel',
                                'It serves as receipt, carriage contract and document of title to the goods',
                                'It records the ship\'s fuel consumption for the voyage',
                                'It is the captain\'s licence to enter foreign ports',
                            ],
                            'answer': 1,
                            'explanation': 'The B/L is the legal heart of trade: proof the carrier received the goods, the contract to deliver them, and ownership — banks even lend against it.',
                        },
                    },
                    {
                        'id': 'm2l2',
                        'title': 'Careers That Move the World',
                        'minutes': 10,
                        'intro': (
                            'The logistics chain employs millions, and South Africa\'s position on '
                            'the east–west trade routes makes it a natural hub. Here is the honest '
                            'map of where the jobs are and what they need from you.'
                        ),
                        'sections': [
                            {
                                'heading': 'On the water and on the quay',
                                'body': (
                                    'Deck and engine officers (via maritime studies at CPUT in Cape Town or '
                                    'DUT in Durban, then cadetships at sea), tug masters, marine pilots — '
                                    'the apex of port seamanship — crane operators, vessel traffic '
                                    'controllers and port engineers. Sea time pays well and travels the '
                                    'world; the trade-off is months away from home, and the qualification '
                                    'route runs through STCW certificates and SAMSA oral exams.'
                                ),
                            },
                            {
                                'heading': 'Behind the screens',
                                'body': (
                                    'Freight forwarding, customs brokering, ship\'s agency, chartering, '
                                    'marine insurance and supply-chain analytics — careers built on '
                                    'mathematics, languages and systems thinking rather than sea legs. '
                                    'Logistics and supply chain management degrees (offered at most SA '
                                    'universities) feed straight into them, and the industry chronically '
                                    'short of young analysts who can code. Your maths marks matter here '
                                    'more than your swimming.'
                                ),
                            },
                        ],
                        'key_points': [
                            'Seagoing officer routes run through CPUT/DUT and cadetships.',
                            'Marine pilot is one of the highest-skilled jobs in any port.',
                            'Shore careers: forwarding, customs, chartering, insurance, analytics.',
                            'Maths + systems thinking opens the office side of maritime trade.',
                        ],
                        'quiz': {
                            'question': 'Which SA institutions offer recognised maritime studies for future ship\'s officers?',
                            'options': [
                                'UNISA and UJ only',
                                'CPUT (Cape Town) and DUT (Durban)',
                                'No South African institution offers them',
                                'Only foreign academies in the Philippines',
                            ],
                            'answer': 1,
                            'explanation': 'Cape Peninsula University of Technology and Durban University of Technology run the country\'s established maritime studies programmes feeding officer cadetships.',
                        },
                    },
                ],
            },
        ],
        'simulation': {
            'type': 'helm',
            'title': 'Container Run: Richards Bay Channel',
            'briefing': (
                'You are piloting the feeder ship MV Thukela out of Richards Bay — the '
                'world\'s largest coal export harbour — bound for the anchorage. Thread the '
                'departure channel in order while a flood tide sets you sideways onto the '
                'training wall. Big ship, narrow water: plan your turns early.'
            ),
            'pass_score': 60,
            'max_nm': 60,
            'config': {
                'world': {'w': 1600, 'h': 1000},
                'start': {'x': 200, 'y': 200, 'heading': 120},
                'vessel': {'max_speed': 4.4, 'turn_rate': 55},
                'current': {'x': 0.3, 'y': 0.5},
                'time_par': 100,
                'time_limit': 250,
                'waypoints': [
                    {'x': 540, 'y': 360, 'r': 50, 'label': 'Coal Terminal Knuckle'},
                    {'x': 880, 'y': 430, 'r': 48, 'label': 'Channel Buoy 6'},
                    {'x': 1130, 'y': 600, 'r': 48, 'label': 'Channel Buoy 2'},
                    {'x': 1400, 'y': 800, 'r': 54, 'label': 'Fairway / Anchorage'},
                ],
                'hazards': [
                    {'x': 760, 'y': 700, 'r': 140, 'label': 'Training Wall'},
                    {'x': 1060, 'y': 260, 'r': 120, 'label': 'Dredge Spoil Ground'},
                    {'x': 420, 'y': 620, 'r': 90, 'label': 'Small Craft Basin'},
                ],
            },
        },
    },
]


def course_totals(course):
    """Compute (lesson_count, total_nm_available) for a course document."""
    # Be defensive: a module may omit 'lessons' (bad data); treat as zero-length.
    lesson_count = sum(len(m.get('lessons') or []) for m in course.get('modules', []))
    nm = NM_ENROLL + lesson_count * NM_LESSON + NM_COURSE_COMPLETE
    if course.get('simulation'):
        nm += course['simulation'].get('max_nm', 0)
    return lesson_count, nm


# ---------------------------------------------------------------------------
# Opportunities page content (static, curated for SA learners)
# ---------------------------------------------------------------------------

OPPORTUNITIES = [
    {
        'category': 'Study & Bursaries',
        'icon': 'school',
        'accent': '#2E8EF7',
        'items': [
            {
                'title': 'Lawhill Maritime Centre — Simon\'s Town School',
                'body': 'South Africa\'s flagship maritime high school programme (Grades 10–12). Strong bursary support from the shipping industry; many alumni are now ships\' officers worldwide.',
                'tag': 'High school',
            },
            {
                'title': 'CPUT & DUT Maritime Studies',
                'body': 'Diplomas and degrees in Nautical Studies and Marine Engineering at Cape Peninsula University of Technology and Durban University of Technology — the standard route to officer cadetships.',
                'tag': 'University',
            },
            {
                'title': 'SAIMI & SAMSA Bursary Programmes',
                'body': 'The SA International Maritime Institute and SA Maritime Safety Authority regularly fund maritime studies. Watch their announcements from Grade 11 and apply early.',
                'tag': 'Bursary',
            },
            {
                'title': 'Transnet Maritime School of Excellence',
                'body': 'Funded training pipelines for port careers: tug crews, crane operators, marine engineering apprenticeships and more, across SA\'s eight commercial ports.',
                'tag': 'Apprenticeship',
            },
        ],
    },
    {
        'category': 'Careers at Sea',
        'icon': 'sailing',
        'accent': '#39D5C8',
        'items': [
            {
                'title': 'Deck Officer → Captain',
                'body': 'Navigate and command merchant ships. Route: maritime studies, cadetship sea time, SAMSA oral exams, then climb Third Mate → Chief Mate → Master.',
                'tag': 'Officer',
            },
            {
                'title': 'Marine Engineer Officer',
                'body': 'Run the power plant of a ship. Engineers are scarcer than deck officers and command excellent salaries at sea and ashore afterwards.',
                'tag': 'Officer',
            },
            {
                'title': 'South African Navy',
                'body': 'Combat officers, divers, technical ratings and engineers via the Military Skills Development System (MSDS) — applications open annually.',
                'tag': 'Defence',
            },
            {
                'title': 'Fishing & Offshore Industry',
                'body': 'Skippers, factory managers, observers and offshore supply crews. Entry via STCW Basic Safety Training and skipper tickets from accredited academies.',
                'tag': 'Industry',
            },
        ],
    },
    {
        'category': 'Careers Ashore',
        'icon': 'apartment',
        'accent': '#F5B83D',
        'items': [
            {
                'title': 'Marine Pilot & Tug Master',
                'body': 'The elite of port seamanship: pilots board visiting ships to guide them in. Long apprenticeship, exceptional reward — among the top maritime salaries in the country.',
                'tag': 'Port',
            },
            {
                'title': 'Freight Forwarding & Customs Brokering',
                'body': 'Choreograph cargo across borders. Logistics/supply-chain diplomas or learnerships with forwarding firms get you in; systems skills accelerate you.',
                'tag': 'Logistics',
            },
            {
                'title': 'Marine Science & Conservation',
                'body': 'Oceanography, fisheries science and MPA management via BSc routes (UCT, NMU, UWC). Operation Phakisa keeps growing demand for ocean scientists.',
                'tag': 'Science',
            },
            {
                'title': 'Ship Repair & Boatbuilding',
                'body': 'Welders, fitters, electricians and naval architects in Cape Town and Durban\'s repair quays — South Africa builds world-class catamarans for export.',
                'tag': 'Trade',
            },
        ],
    },
]
