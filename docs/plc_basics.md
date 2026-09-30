# PLC Basics

## What is a PLC
A programmable logic controller (PLC) is an industrial computer that controls machines and processes. It reads signals from input devices such as push buttons and sensors, runs a user program, and switches output devices such as motors, valves and lamps. PLCs are built to survive dust, vibration, heat and electrical noise found on factory floors.

## The scan cycle
A PLC works in a repeating loop called the scan cycle. First it reads all inputs into memory, then it executes the program from top to bottom, and finally it updates all outputs. A typical scan takes a few milliseconds. If the program is very long, the scan time grows and the machine reacts more slowly.

## Programming languages
The IEC 61131-3 standard defines five PLC languages: Ladder Diagram (LD), Function Block Diagram (FBD), Structured Text (ST), Instruction List (IL) and Sequential Function Chart (SFC). Ladder logic looks like electrical relay diagrams and is popular with electricians. Structured Text looks like Pascal and is useful for calculations.

## Common mistakes
Beginners often forget that outputs are only updated at the end of the scan, or they write the same output coil in two places, which causes confusing behaviour. Always comment your rungs and test with the machine in a safe state.
