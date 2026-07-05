import json

from mecha_llm.sources.content_json import load_content_docs


def _write_content(tmp_path):
    data = {
        "projects": [
            {
                "title": "Apple Thinning VR",
                "projectType": "Research",
                "links": [{"type": "github", "url": "https://github.com/uc-vision/apple-thinning"}],
                "description": "Agriculture simulation VR game built with Godot for Oculus Quest 2.",
            },
            {
                "title": "Fruit Maturity Clearance",
                "projectType": "Commercial",
                "links": [],
                "description": "Maturity clearance system for fruit growers.",
            },
        ],
        "work": [
            {
                "title": "AI Engineer",
                "startYear": 2023,
                "endYear": None,
                "organisation": {"name": "Spark New Zealand"},
                "description": "Worked on AI systems.",
            }
        ],
        "education": [
            {
                "title": "Bachelor of Science",
                "startYear": 2018,
                "endYear": 2022,
                "organisation": {"name": "University of Canterbury"},
                "description": "CS and Physics.",
            }
        ],
    }
    path = tmp_path / "content.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_loads_projects_work_education(tmp_path):
    docs = load_content_docs(_write_content(tmp_path))
    by_type = {}
    for d in docs:
        by_type.setdefault(d.source_type, []).append(d)

    assert len(by_type["project"]) == 2
    assert len(by_type["experience"]) == 2  # 1 work + 1 education


def test_project_captures_repo_and_routes_to_home(tmp_path):
    docs = load_content_docs(_write_content(tmp_path))
    vr = next(d for d in docs if d.title == "Apple Thinning VR")
    assert vr.repo_url == "https://github.com/uc-vision/apple-thinning"
    assert vr.url == "/"
    assert vr.source_type == "project"
    assert "VR game" in vr.text


def test_experience_routes_to_experience_page(tmp_path):
    docs = load_content_docs(_write_content(tmp_path))
    exp = next(d for d in docs if d.source_type == "experience")
    assert exp.url == "/experience"
    assert exp.repo_url is None


def test_present_role_has_no_end_year_crash(tmp_path):
    docs = load_content_docs(_write_content(tmp_path))
    ai = next(d for d in docs if "AI Engineer" in d.title)
    assert "Present" in ai.text
