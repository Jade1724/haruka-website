"""Golden Q/A set grounded in the real portfolio content (projects + experience).

Reference answers are the ground truth for RAGAS (context recall, correctness)
and the expected output for DeepEval's G-Eval. Kept factual and content-derived
so the gate is meaningful; adversarial/off-topic cases live in ``redteam.py``.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GoldenItem:
    question: str
    reference: str  # ground-truth answer
    expected_url: str | None = None  # a route/link a good answer should surface


GOLDEN: list[GoldenItem] = [
    GoldenItem(
        question="Does Haruka have a project building a VR game?",
        reference=(
            "Yes — Apple Thinning, an agriculture VR training game for thinning apple "
            "fruitlets, built with the Godot engine to run on the Oculus Quest 2, as part "
            "of University of Canterbury's computer vision lab. The public repo is "
            "https://github.com/uc-vision/apple-thinning."
        ),
        expected_url="https://github.com/uc-vision/apple-thinning",
    ),
    GoldenItem(
        question="What database does the B2B Sales Recommendation System use?",
        reference=(
            "The B2B Sales Recommendation System uses a Snowflake database. It is an AI "
            "sales recommendation system using RAG, built with Next.js, FastAPI, and Azure "
            "OpenAI."
        ),
    ),
    GoldenItem(
        question="What is Spectral Detect and what was it built with?",
        reference=(
            "Spectral Detect is an invasive plant detection and location-tracking full-stack "
            "web app built with Vue.js, Spring Boot, and MariaDB, hosted on AWS. It was a "
            "University of Canterbury master's project to help the Department of Conservation "
            "automatically detect euphorbia paralias from UAV imagery."
        ),
    ),
    GoldenItem(
        question="Where can I see Haruka's work history?",
        reference=(
            "On the Experience page (/experience), which lists Haruka's career timeline — "
            "work history and education."
        ),
        expected_url="/experience",
    ),
    GoldenItem(
        question="What is Haruka's current job?",
        reference=(
            "Haruka is an AI Engineer at Spark New Zealand, from 2023 to the present, "
            "developing applications and systems integrated with AI, including an "
            "AI-decisioning marketing system and a B2B sales recommendation system."
        ),
    ),
    GoldenItem(
        question="Where did Haruka intern before, and what did they work on?",
        reference=(
            "Haruka was a Software Developer Intern at Umajin (2022–2023), working on a React "
            "dashboard app for an automotive oil company client and a WebXR application using "
            "THREE.js with Jest testing."
        ),
    ),
    GoldenItem(
        question="What did Haruka study at university?",
        reference=(
            "At the University of Canterbury, Haruka completed a Professional Master of "
            "Computer Science (a project-based degree building a full-stack web app to "
            "automate invasive plant detection) and a Bachelor of Science with a double major "
            "in Computer Science and Physics."
        ),
    ),
    GoldenItem(
        question="What tech stack is the Fruit Maturity Clearance project built with?",
        reference=(
            "The Fruit Maturity Clearance Project is built with Next.js, .NET, and SQL Server "
            "on Azure. It is a maturity clearance system for fruit growers, packhouses, and "
            "labs to digitally track fruit quality and maturity."
        ),
    ),
    GoldenItem(
        question="What is this portfolio website built with?",
        reference=(
            "The portfolio website is built with Next.js, Tailwind CSS, and FastAPI, hosted "
            "on Vercel. It features a project showcase, a career timeline, and a dev journal "
            "scraped from a private Obsidian repository."
        ),
        expected_url="/",
    ),
]
