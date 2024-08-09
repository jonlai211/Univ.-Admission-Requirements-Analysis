# University Admission Requirements Analysis

### Project Structure

```
.
├── logs
├── output
│   ├── scrape
│   ├── search
│   └── task_1.csv
├── README.md
├── src
│   ├── question_map.py
│   └── university_map.py
├── task_1.py
└── utils
    ├── chat.py
    ├── __init__.py
    ├── scrape.py
    └── search.py
```

### University

```python
MAP_UNIV = {
    "mit": "Massachusetts Institute of Technology",
    "caltech": "California Institute of Technology",
    "upenn": "University of Pennsylvania",
    "nyu": "New York University",
    "umich": "University of Michigan-Ann Arbor",
    "uiuc": "University of Illinois at Urbana-Champaign",
    "bu": "Boston University",
    "usc": "University of Southern California"
}
```

### Question

```python
MAP_QUESTION = {
    "select": "undergraduate admission requirements (selection criteria or selection process)",
    "material": "undergraduate admissions required application materials",
    "timeline": "undergraduate admissions application timeline and deadlines",
    "stats": "undergraduate admissions latest admitted or enrolled student statistics or class profile"
}
```

### Usage

To run the `task_1.py` script from the command line with parameters for the university and question. For example:

```zsh
python task_1.py --univ mit --question select
```

### Task 1 Output Example

| ID | University | Question Type | URL |
|----|------------|---------------|-----|
| 0  | mit        | select        | https://facts.mit.edu/undergraduate-admissions/ |
| 1  | mit        | select        | https://catalog.mit.edu/mit/undergraduate-education/admissions/ |
| 2  | mit        | select        | https://architecture.mit.edu/undergraduate-admissions |
| 3  | mit        | select        | https://mitadmissions.org/apply/process/what-we-look-for/ |
| 4  | mit        | select        | https://mitadmissions.org/apply/firstyear/international/ |
