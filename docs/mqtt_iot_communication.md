# MQTT for IoT Communication

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
