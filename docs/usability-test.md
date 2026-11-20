# Usability test with students

SCRUM-19 · 14 Nov 2026

**Result: all 3 participants could make, rename and download a summary.** The main problem was getting the transcript out of Panopto in Canvas, which happens before our app is opened. Average scores (1 to 5): easy to use 4.7, waiting time acceptable 4.0, would use it 4.3.

## Setup

| Item | Value |
| --- | --- |
| Participants | 3 students who are not in the team and take or took a course with Panopto recordings: 2 CSAI, 1 Psychology (P1 to P3) |
| Laptop | Windows laptop with NVIDIA RTX 4080 Laptop GPU, Qwen2.5-7B-Instruct in LM Studio (see [model selection](../model-selection/README.md)) |
| Transcript | SE for CSAI Lecture 03. **Not committed** (course material) |
| Session | About 15 minutes each: the same introduction read out loud, 7 tasks, thinking aloud, then 5 questions |
| Data kept | Participant code, study programme, generation times, problems and quotes. No names, no recordings |

## Tasks

The tasks were read out one at a time without naming buttons or menus.

| # | Read to the participant | Success when |
| --- | --- | --- |
| T1 | "The transcript of a lecture is on the Desktop. Load it into the app." | File name shows in the uploader |
| T2 | "Make a summary that is a bit longer than the standard one." | "Detailed" selected and Generate clicked |
| T3 | "Wait for the summary. Tell me if anything is unclear while you wait." | Summary shown on screen |
| T4 | "Give the summary the title Week 3 - AI systems." | Heading shows that title |
| T5 | "Save the summary as a Word file on this laptop." | .docx in the Downloads folder with the new title |
| T6 | "Put the summary in a message to a friend." | Copy button used, text pasted in Notepad |
| T7 | "Look at the summary: is there anything you would not trust?" | Their answer noted |

## Results per task

| Task | Result (3 participants) | Notes |
| --- | --- | --- |
| T1 Load the transcript | 3 of 3, all needed help | Nobody knew where to download the transcript from the Panopto video in Canvas. Loading it into the app was easy once they had the file |
| T2 Longer summary | 3 of 3, no help | Found "Detailed" right away |
| T3 Wait for the summary | 3 of 3 | Nobody minded the wait |
| T4 Set the title | 3 of 3, no help | |
| T5 Save as Word file | 3 of 3, no help | |
| T6 Copy into a message | 3 of 3, 1 needed help | 1 participant did not understand what "Copy summary" does until it was explained |
| T7 Anything you would not trust? | No trust issues | Summaries looked consistent; 1 participant wanted a longer, more detailed summary for exam preparation |

## Generation time

| Summary | P1 | P2 | P3 | Average |
| --- | --- | --- | --- | --- |
| Standard (Medium) | 56 s | 47 s | 52 s | 52 s |
| Detailed | 1 min 29 s | 1 min 43 s | 1 min 49 s | 1 min 40 s |

## Problems

Blocker = could not finish the task, Major = finished but slow or with help, Minor = small confusion or wish.

| Participant | Task | What happened / what they said | Severity |
| --- | --- | --- | --- |
| P1, P2, P3 | T1 | Could not find where to download the transcript from the Panopto video in Canvas; managed after it was explained. This is Panopto's interface, not our app, but it is the first step for every user | Major |
| 1 of 3 | T6 | Did not understand what "Copy summary" does; used it easily after the explanation | Major |
| 1 of 3 | T7 | "A longer, more detailed summary would be better for studying for exams" | Minor |
| P1, P2, P3 | After the test | Idea: flashcards or exam-style questions made from the lecture | Feature idea |

## Questions after the test

Q1 to Q3: scores from 1 (no) to 5 (yes). Q4 and Q5: from the conversation after the tasks.

| Question | Answer (3 participants) |
| --- | --- |
| Q1 Easy to make a summary? | 5, 5, 4 (average 4.7) |
| Q2 Waiting time acceptable? | 4, 4, 4 (average 4.0) |
| Q3 Would you use it? | 5, 4, 4 (average 4.3) |
| Q4 Most confusing moment? | Finding the transcript download in Panopto/Canvas (all 3); the copy button (1) |
| Q5 One thing to change? | A longer, more detailed summary for exam study (1); flashcards or exam-style questions (all 3) |

## Suggested follow-up

- Short help text in the app or README on how to download a Panopto transcript from Canvas
- Clearer copy button, for example "Copy summary to clipboard" with a "Copied!" message
- Check the length of the "Detailed" level
- Backlog idea: flashcards or exam-style questions from the lecture

## Limitations

- Only 3 participants, all from one university.
- Only generation times were measured, not the time for the other tasks.
- Tested on a laptop with a GPU. Without a GPU the model is about 10 times slower (7.3 instead of 70.5 tokens per second in the [model selection](../model-selection/README.md) test), so the waiting time should be tested again on such a laptop.
