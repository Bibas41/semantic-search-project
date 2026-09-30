# Predictive Maintenance

## Maintenance strategies
Reactive maintenance means fixing a machine after it breaks. Preventive maintenance replaces parts on a fixed schedule, for example every 2000 operating hours, even if they are still fine. Predictive maintenance uses data from the machine to estimate when a failure is likely and plans the repair just before it happens.

## Condition monitoring
Vibration sensors on bearings and motors are the most common data source. A worn bearing produces vibration at characteristic frequencies that can be seen with a frequency analysis (FFT). Temperature, motor current and oil quality are also monitored.

## Machine learning
Anomaly detection models learn what normal operation looks like and raise an alarm when new data looks different. With enough failure history, regression models can estimate the remaining useful life (RUL) of a component.

## Benefits and challenges
Predictive maintenance reduces unplanned downtime and spare part costs. The main challenges are poor-quality sensor data, too few recorded failures to learn from, and false alarms that make operators ignore the system.
