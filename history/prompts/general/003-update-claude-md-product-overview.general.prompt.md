---
id: 003
title: Update CLAUDE.md with Product Overview
stage: general
date: 2026-03-14
surface: agent
model: claude-sonnet-4.5
feature: none
branch: master
user: saifullah
command: none
labels: ["documentation", "product-overview", "learnpybyai", "setup"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - CLAUDE.md
tests:
---

## Prompt

ok so now i will discuss the project with you. I will share the product overview with you. Go through it deeply and understand each and every thing of it. Then  update the clasude.md file with your understanding

LearnPyByAi is an AI-powered Python tutoring platform. This section provides the complete business requirements.

## **Product Overview**

LearnPyByAI helps students learn Python programming through conversational AI agents. Students can chat with tutors, write and run code, take quizzes, and track their progress. Teachers can monitor class performance and generate custom exercises.

| Role | Features |
| ----- | ----- |
| **Student** | Chat with Python tutor, write & run code, take coding quizzes, view progress |
| **Teacher** | View class progress, receive struggle alerts, generate coding exercises |

## **Python Curriculum**

| Module | Topics Covered |
| ----- | ----- |
| 1\. Basics | Variables, Data Types, Input/Output, Operators, Type Conversion |
| 2\. Control Flow | Conditionals (if/elif/else), For Loops, While Loops, Break/Continue |
| 3\. Data Structures | Lists, Tuples, Dictionaries, Sets |
| 4\. Functions | Defining Functions, Parameters, Return Values, Scope |
| 5\. OOP | Classes & Objects, Attributes & Methods, Inheritance, Encapsulation |
| 6\. Files | Reading/Writing Files, CSV Processing, JSON Handling |
| 7\. Errors | Try/Except, Exception Types, Custom Exceptions, Debugging |
| 8\. Libraries | Installing Packages, Working with APIs, Virtual Environments |

## **AI Agent System**

LearnPyByAI uses a multi-agent architecture where specialized agents handle different aspects of tutoring.

| Agent | Purpose & Capabilities |
| ----- | ----- |
| **Triage Agent** | Routes queries to specialists: "explain" → Concepts, "error" → Debug |
| **Concepts Agent** | Explains Python concepts with examples, adapts to student level |
| **Code Review Agent** | Analyzes code for correctness, style (PEP 8), efficiency, readability |
| **Debug Agent** | Parses errors, identifies root causes, provides hints before solutions |
| **Exercise Agent** | Generates and auto-grades coding challenges |
| **Progress Agent** | Tracks mastery scores and provides progress summaries |

## **Business Rules**

### **Mastery Calculation**

Topic Mastery \= weighted average of:

* Exercise completion: 40%
* Quiz scores: 30%
* Code quality ratings: 20%
* Consistency (streak): 10%

**Mastery Levels:**

* 0-40% → Beginner (Red) | 41-70% → Learning (Yellow)
* 71-90% → Proficient (Green) | 91-100% → Mastered (Blue)

### **Struggle Detection Triggers**

* Same error type 3+ times
* Stuck on exercise \> 10 minutes
* Quiz score \< 50%
* Student says "I don't understand" or "I'm stuck"
* 5+ failed code executions in a row

### **Code Execution Sandbox**

* Timeout: 5 seconds | Memory: 50MB
* No file system access (except temp) | No network access
* Allowed imports: standard library only (MVP)

## **Demo Scenario**

This scenario demonstrates the key features of LearnPyByAI:

1. **Student Maya** logs in → Dashboard shows: "Module 2: Loops \- 60% complete"
2. Maya asks: *"How do for loops work in Python?"*
3. Concepts Agent explains with code examples and visualizations
4. Maya writes a for loop in the Monaco editor, runs it successfully
5. Agent offers a quiz → Maya gets 4/5 → Mastery updates to 68%
6. **Student James** struggles with list comprehensions → Gets 3 wrong answers
7. Struggle alert sent to teacher Mr. Rodriguez
8. Teacher views James's code attempts, types: "Create easy exercises on list comprehensions"
9. Exercise Agent generates exercises → Teacher assigns with one click
10. James receives notification → Completes exercises → Confidence restored

## Response snapshot

Updated CLAUDE.md file with comprehensive LearnPyByAI product context including:

1. **Project Context** - Product name (LearnPyByAI/LearnPyByAi), domain (AI-powered Python tutoring), and core value proposition
2. **User Roles & Capabilities** - Student features (chat, code execution, quizzes, progress) and Teacher features (monitoring, alerts, exercise generation)
3. **Python Curriculum Structure** - All 8 modules: Basics, Control Flow, Data Structures, Functions, OOP, Files, Errors, Libraries
4. **Multi-Agent Architecture** - 6 specialized agents:
   - Triage Agent (query routing)
   - Concepts Agent (explanations)
   - Code Review Agent (PEP 8, correctness)
   - Debug Agent (error analysis)
   - Exercise Agent (challenge generation)
   - Progress Agent (mastery tracking)
5. **Business Logic & Rules**:
   - Mastery calculation: Exercise 40%, Quiz 30%, Code quality 20%, Streak 10%
   - Mastery levels: Beginner (0-40%), Learning (41-70%), Proficient (71-90%), Mastered (91-100%)
   - Struggle detection: 3+ same errors, 10min stuck, <50% quiz, explicit help requests, 5+ failed executions
6. **Code Execution Sandbox Constraints** - 5s timeout, 50MB memory, no filesystem/network, standard library only
7. **Key User Flows** - Student learning flow and teacher intervention flow with demo scenario

## Outcome

- ✅ Impact: CLAUDE.md now contains complete LearnPyByAI product context for all future development work
- 🧪 Tests: None (documentation update)
- 📁 Files: Updated CLAUDE.md with product overview section
- 🔁 Next prompts: Ready for feature specification, architecture planning, or implementation tasks
- 🧠 Reflection: Product context is now embedded in agent instructions, ensuring all future work aligns with LearnPyByAI requirements

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A (documentation task)
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): Begin feature specification or architecture planning for LearnPyByAI platform
