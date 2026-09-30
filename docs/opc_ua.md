# OPC UA

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
