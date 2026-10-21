"""Tests for the project model and the on-disk library."""

from __future__ import annotations

import json

import pytest

from storytobook.domain.chapter import Chapter
from storytobook.domain.project import Project, ProjectStatus
from storytobook.errors import ProjectNotFoundError


class TestProject:
    def test_defaults(self):
        project = Project()
        assert project.status is ProjectStatus.DRAFT
        assert project.chapters == []
        assert project.id

    def test_round_trip(self):
        project = Project(title="T", author="A", transcript="hello")
        project.chapters = [Chapter(title="Chapter 1", text="hello")]
        restored = Project.from_dict(project.to_dict())
        assert restored.title == "T"
        assert restored.author == "A"
        assert restored.transcript == "hello"
        assert restored.chapters[0].title == "Chapter 1"
        assert restored.chapters[0].text == "hello"

    def test_unknown_status_falls_back_to_draft(self):
        assert Project.from_dict({"status": "nonsense"}).status is ProjectStatus.DRAFT

    def test_word_and_chapter_counts(self):
        project = Project(transcript="one two three four")
        project.chapters = [Chapter(text="one two"), Chapter(text="three four")]
        assert project.word_count == 4
        assert project.chapter_count == 2

    def test_display_name_falls_back(self):
        assert Project(title="  ").display_name == "Untitled Story"


class TestLibrary:
    def test_create_writes_a_project(self, library):
        project = library.create(title="New Book")
        assert library.project_dir(project.id).exists()
        assert (library.project_dir(project.id) / "project.json").exists()
        assert library.load(project.id).title == "New Book"

    def test_list_returns_newest_first(self, library):
        first = library.create(title="First")
        second = library.create(title="Second")
        projects = library.list()
        assert {p.id for p in projects} == {first.id, second.id}
        assert projects[0].id == second.id

    def test_load_missing_project(self, library):
        with pytest.raises(ProjectNotFoundError):
            library.load("does-not-exist")

    def test_save_is_atomic_and_leaves_no_temp_file(self, library, project):
        library.save(project)
        directory = library.project_dir(project.id)
        assert not list(directory.glob("*.tmp"))

    def test_save_writes_valid_json(self, library, project):
        library.save(project)
        raw = json.loads((library.project_dir(project.id) / "project.json").read_text("utf-8"))
        assert raw["title"] == project.title

    def test_delete_removes_everything(self, library, project):
        library.save(project)
        library.delete(project.id)
        assert not library.project_dir(project.id).exists()

    def test_delete_missing_project(self, library):
        with pytest.raises(ProjectNotFoundError):
            library.delete("nope")

    def test_transcript_is_written_to_its_own_file(self, library, project):
        project.transcript = "The story so far."
        library.save(project)
        assert library.transcript_path(project.id).read_text("utf-8") == "The story so far."

    def test_duplicate_copies_content(self, library, project):
        project.transcript = "Original text"
        project.author = "Ada"
        library.save(project)

        copy = library.duplicate(project.id)
        assert copy.id != project.id
        assert copy.transcript == "Original text"
        assert copy.author == "Ada"
        assert library.load(copy.id).title.endswith("(copy)")

    def test_usage_counts(self, library, project):
        project.transcript = "one two three"
        library.save(project)
        usage = library.usage()
        assert usage["projects"] == 1
        assert usage["words"] == 3

    def test_corrupt_project_is_skipped(self, library, project):
        library.save(project)
        (library.project_dir(project.id) / "project.json").write_text("{not json", "utf-8")
        assert library.list() == []
