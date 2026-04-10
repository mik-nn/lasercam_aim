# SKILLS.md — Knowledge and Capabilities for Each Agent Role

This document defines the knowledge base, capabilities, and decision boundaries for each agent. Skills ensure that agents operate consistently and with domain expertise.

## 1. Architecture Agent Skills

Knowledge:
- Full understanding of architecture.md and structure.md  
- Deep knowledge of module boundaries  
- Understanding of MVP vs final tool differences  
- Awareness of external behaviour contract  

Capabilities:
- Approve or reject architectural changes  
- Detect cross-module violations  
- Maintain long-term architectural integrity  

## 2. Vision Agent Skills

Knowledge:
- Marker design principles (vision.md, markers.md)  
- OpenCV image processing techniques  
- Geometric transforms and center estimation  
- Lighting, distortion, and robustness constraints  

Capabilities:
- Implement and refine detection algorithms  
- Validate marker robustness  
- Provide reference implementations for C/C++ port  
- Maintain consistent detection semantics  

## 3. Simulator Agent Skills

Knowledge:
- Simulation model (simulator.md)  
- Gantry kinematics  
- Camera FOV modelling  
- Laser offset modelling  
- Coordinate mapping fundamentals  

Capabilities:
- Implement and update simulation logic  
- Validate behaviour before hardware integration  
- Provide synthetic test cases  

## 4. Bridge Agent Skills

Knowledge:
- LightBurn Print & Cut workflow  
- WinAPI window enumeration  
- Hotkey interception  
- State machine logic  

Capabilities:
- Implement LightBurn bridge  
- Maintain state machine correctness  
- Ensure identical behaviour across MVP and final tool  

## 5. UI Agent Skills

Knowledge:
- User workflow (workflow-print-and-cut.md)  
- Camera preview overlays  
- Marker confirmation UX  
- Qt and wxPython UI patterns  

Capabilities:
- Implement UI behaviour  
- Maintain consistent user experience  
- Coordinate with Vision and Bridge Agents  

## 6. Core Logic Agent Skills

Knowledge:
- Coordinate mapping mathematics  
- Movement logic (simulated and real)  
- External behaviour contract  
- System sequencing rules  

Capabilities:
- Implement core logic  
- Ensure correct module interactions  
- Maintain behavioural consistency  

## 7. Documentation Agent Skills

Knowledge:
- All documentation files  
- Documentation-driven development principles  
- Versioning and consistency rules  

Capabilities:
- Maintain and update documentation  
- Enforce documentation accuracy  
- Validate that code matches documentation  

## 8. Testing Agent Skills

Knowledge:
- Testing methodology (testing.md)  
- Automated test frameworks  
- Regression prevention strategies  
- Behaviour consistency requirements  

Capabilities:
- Implement automated tests  
- Maintain test-summary.md  
- Validate correctness across MVP and final tool  

## 9. Shared Skills Across All Agents

All agents must know:
- AGENTS.md workflow rules  
- Plan Mode requirements  
- Inline memory anchors (AICODE-*)  
- Documentation update rules  
- Behaviour consistency requirements  

This skill system ensures that each agent operates with clear domain expertise and predictable behaviour.