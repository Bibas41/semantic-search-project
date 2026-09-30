"""
Creates the synthetic test document collection for the Semantic Search mini-project.
The documents are synthetic course-style notes written with AI assistance for testing.
They contain no personal, confidential or copyrighted material.
"""
from pathlib import Path

DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(exist_ok=True)

documents = {

"plc_basics.md": """# PLC Basics

## What is a PLC
A programmable logic controller (PLC) is an industrial computer that controls machines and processes. It reads signals from input devices such as push buttons and sensors, runs a user program, and switches output devices such as motors, valves and lamps. PLCs are built to survive dust, vibration, heat and electrical noise found on factory floors.

## The scan cycle
A PLC works in a repeating loop called the scan cycle. First it reads all inputs into memory, then it executes the program from top to bottom, and finally it updates all outputs. A typical scan takes a few milliseconds. If the program is very long, the scan time grows and the machine reacts more slowly.

## Programming languages
The IEC 61131-3 standard defines five PLC languages: Ladder Diagram (LD), Function Block Diagram (FBD), Structured Text (ST), Instruction List (IL) and Sequential Function Chart (SFC). Ladder logic looks like electrical relay diagrams and is popular with electricians. Structured Text looks like Pascal and is useful for calculations.

## Common mistakes
Beginners often forget that outputs are only updated at the end of the scan, or they write the same output coil in two places, which causes confusing behaviour. Always comment your rungs and test with the machine in a safe state.
""",

"industrial_sensors.md": """# Industrial Sensors

## Proximity sensors
Inductive proximity sensors detect metal objects without touching them by using an electromagnetic field. They are cheap, robust and common for detecting parts on a conveyor. Capacitive sensors can also detect non-metal materials such as plastic, wood or liquid inside a tank.

## Optical sensors
Photoelectric sensors use a light beam. In a through-beam setup the emitter and receiver face each other and an object is detected when it breaks the beam. Retro-reflective sensors bounce the light off a reflector. Dirt on the lens is a common cause of false signals.

## Distance and level
Ultrasonic sensors measure distance by timing sound echoes, which makes them useful for measuring the fill level of silos and tanks. Laser distance sensors are more precise but more expensive.

## Temperature measurement
A PT100 is a resistance temperature detector whose resistance is 100 ohms at 0 degrees Celsius. Thermocouples cover higher temperatures but are less accurate.

## Signal types
Analog sensors often send a 4-20 mA current signal. The 4 mA "live zero" makes it possible to detect a broken wire, because a broken cable gives 0 mA instead of a valid value.
""",

"predictive_maintenance.md": """# Predictive Maintenance

## Maintenance strategies
Reactive maintenance means fixing a machine after it breaks. Preventive maintenance replaces parts on a fixed schedule, for example every 2000 operating hours, even if they are still fine. Predictive maintenance uses data from the machine to estimate when a failure is likely and plans the repair just before it happens.

## Condition monitoring
Vibration sensors on bearings and motors are the most common data source. A worn bearing produces vibration at characteristic frequencies that can be seen with a frequency analysis (FFT). Temperature, motor current and oil quality are also monitored.

## Machine learning
Anomaly detection models learn what normal operation looks like and raise an alarm when new data looks different. With enough failure history, regression models can estimate the remaining useful life (RUL) of a component.

## Benefits and challenges
Predictive maintenance reduces unplanned downtime and spare part costs. The main challenges are poor-quality sensor data, too few recorded failures to learn from, and false alarms that make operators ignore the system.
""",

"mqtt_iot_communication.md": """# MQTT for IoT Communication

## Publish and subscribe
MQTT is a lightweight messaging protocol designed for devices with limited bandwidth and power. Devices do not talk to each other directly. A publisher sends a message to a topic on a central server called the broker, and every client that has subscribed to that topic receives it.

## Topics
Topics are text paths such as factory/line1/temperature. Wildcards let a client subscribe to many topics at once: + matches one level and # matches all remaining levels.

## Quality of Service
MQTT has three QoS levels. QoS 0 sends a message at most once with no confirmation. QoS 1 guarantees delivery at least once, but duplicates are possible. QoS 2 guarantees exactly once delivery but is the slowest.

## Retained messages and last will
A retained message is stored by the broker and sent to new subscribers immediately. The last will message is published by the broker if a device disconnects unexpectedly, which helps detect offline sensors.

## Security
By default MQTT sends data in plain text on port 1883. In production, use TLS encryption on port 8883, usernames and passwords or client certificates, and access rules on the broker.
""",

"opc_ua.md": """# OPC UA

## Purpose
OPC Unified Architecture (OPC UA) is a platform-independent standard for exchanging data between industrial machines, controllers and software such as SCADA and MES systems. It solves the problem that equipment from different vendors speaks different protocols.

## Information model
OPC UA does not only send raw values. It describes data with an address space of nodes that have names, data types, units and relationships. A client can browse a server and understand what a value such as MotorSpeed means without reading a separate manual.

## Communication patterns
The classic model is client-server: a client reads or writes values on a server. OPC UA also supports publish-subscribe, which can run over MQTT for cloud connectivity.

## Security
Security is built into the standard with certificates, encryption and user authentication. Security modes can be None, Sign, or SignAndEncrypt. Using None is only acceptable in isolated test networks.

## OPC UA versus MQTT
OPC UA is richer and self-describing, which suits machine-to-machine integration on the factory floor. MQTT is simpler and lighter, which suits sending many sensor values to the cloud.
""",

"robot_safety.md": """# Industrial Robot Safety

## Risk assessment
Before a robot cell is used, a risk assessment identifies hazards such as crushing, impact and flying parts, and decides how to reduce them. The standards ISO 10218 and ISO/TS 15066 give requirements for industrial and collaborative robots.

## Guarding
Traditional robots work inside fences. Interlocked doors stop the robot when opened. Light curtains and safety laser scanners detect a person entering the working area and trigger a safe stop.

## Collaborative robots
Collaborative robots (cobots) are designed to work near people. They limit their speed and force and stop when they detect a collision. Even a cobot needs a risk assessment, because a sharp tool on a slow robot can still injure someone.

## Emergency stop and lockout
Every cell needs clearly marked emergency stop buttons. Before maintenance inside the cell, workers use lockout/tagout: they switch off and lock the energy sources with a personal padlock so that nobody can restart the machine while they are inside.
""",

"machine_vision_quality.md": """# Machine Vision for Quality Inspection

## Components
A machine vision system consists of an industrial camera, a lens, lighting, and software that analyses the images. Lighting is often the most important part: backlighting shows the outline of a part, while low-angle light makes scratches and dents visible.

## Classic image processing
Rule-based methods measure dimensions, count holes, read barcodes, or compare a part to a golden reference image. They work well when parts and lighting are very consistent.

## Deep learning inspection
Convolutional neural networks (CNNs) can learn to recognise defects such as cracks, stains or missing components from labelled example images. They handle natural variation better than fixed rules but need a good training dataset, including enough images of rare defects.

## Measuring performance
A false reject is a good part that is thrown away; a false accept is a defective part that reaches the customer. Tuning the system is a trade-off between these two errors, and the right balance depends on the cost of each mistake.
""",

"digital_twin.md": """# Digital Twins

## Definition
A digital twin is a virtual model of a physical machine, production line or whole factory that is kept up to date with real data from the physical system. The twin can be used to monitor, analyse and test changes without touching the real equipment.

## Virtual commissioning
Before a new production line is built, engineers connect the real PLC program to a simulated model of the line. Programming errors are found in the simulation instead of during start-up, which saves time and prevents damage.

## Operation and optimisation
During operation, the twin shows the current state of the process and can run what-if simulations, for example testing a new production schedule or predicting the effect of a slower conveyor.

## Limitations
A digital twin is only as good as its model and data. Building an accurate model takes a lot of work, and the twin becomes misleading if the physical system is changed and the model is not updated.
""",

"logic_gates_74ls.txt": """LOGIC GATE CHIPS AND KARNAUGH MAPS - LAB NOTES

74LS series chips
The 74LS family is a group of TTL logic chips that run on a 5 V supply. The 74LS00 contains four 2-input NAND gates. The 74LS08 contains four 2-input AND gates. The 74LS32 contains four 2-input OR gates. The 74LS04 contains six inverters (NOT gates). On the common 14-pin package, pin 14 is VCC (+5 V) and pin 7 is ground.

Wiring tips
Always connect power and ground before testing a circuit. Unused inputs on TTL chips float high but should be tied to a defined level to avoid noise. A missing ground connection is the most common reason a breadboard circuit does not work.

Karnaugh maps
A Karnaugh map (K-map) is a grid used to simplify Boolean expressions. Neighbouring cells differ by only one variable. Grouping 1s in rectangles of 1, 2, 4 or 8 cells removes variables and gives a simpler circuit with fewer gates. Groups may wrap around the edges of the map.

Universal gates
NAND and NOR are called universal gates because any other logic function can be built using only one of them.
""",

"energy_efficiency_motors.md": """# Energy Efficiency in Industry

## Electric motors
Electric motors use a large share of industrial electricity. Motor efficiency classes are defined in IEC 60034-30-1, from IE1 (standard) to IE4 (super premium) and IE5. Replacing an old oversized motor with a correctly sized high-efficiency motor can pay back within a few years.

## Variable frequency drives
A variable frequency drive (VFD) changes the speed of an AC motor by changing the frequency of the supply. For pumps and fans, power consumption falls roughly with the cube of the speed, so running a fan at 80 percent speed uses only about half of the power.

## Compressed air
Compressed air is one of the most expensive forms of energy in a factory. Leaks in pipes and fittings can waste 20 to 30 percent of the compressor output. Regular leak detection with ultrasonic detectors and switching off the air supply outside working hours give quick savings.

## Monitoring
Energy meters on major machines show where energy is used. Without measurement, it is hard to know which improvements are worth the investment.
""",

"faq.csv": """question,answer,topic
"What does PLC stand for?","Programmable logic controller, an industrial computer that controls machines.",automation
"Why is 4-20 mA used instead of 0-20 mA?","The 4 mA live zero makes it possible to detect a broken wire.",sensors
"Which MQTT QoS level guarantees exactly once delivery?","QoS 2.",iot
"What is the default MQTT port?","1883 without encryption and 8883 with TLS.",iot
"What is a cobot?","A collaborative robot that is designed to work safely near people by limiting speed and force.",safety
"What is lockout/tagout?","A procedure where energy sources are switched off and locked before maintenance.",safety
"What does RUL mean in maintenance?","Remaining useful life, the estimated time until a component fails.",maintenance
"Which pin is ground on a 74LS00?","Pin 7 is ground and pin 14 is VCC.",electronics
"What is virtual commissioning?","Testing a PLC program against a simulated model before the real line is built.",digital-twin
"What is a false reject in vision inspection?","A good part that the system wrongly rejects as defective.",vision
""",
}

for name, text in documents.items():
    path = DOCS_DIR / name
    path.write_text(text.strip() + "\n", encoding="utf-8")
    print("Created", path)

print(f"Done: {len(documents)} documents in {DOCS_DIR}/")