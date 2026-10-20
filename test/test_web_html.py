"""Untrusted monitoring data must remain text in the browser's HTML parser."""

import json
from html.parser import HTMLParser

import pytest

from PyOrchestrate.web_interface.server import create_html_response


class MonitoringHTML(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.scripts = []
        self._in_script = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag == "script":
            self._in_script = True
            self.scripts.append("")

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False

    def handle_data(self, data):
        if self._in_script:
            self.scripts[-1] += data


@pytest.mark.parametrize(
    "message",
    [
        '</script><img src=x onerror="alert(1)">',
        '</ScRiPt ><script>alert("probe")</script>',
        '<!--<script> & "quotes" \\ backslash — café',
    ],
)
def test_payload_stays_inside_the_script_and_preserves_its_value(message):
    response = create_html_response("History", {"message": message}, "/api/history")
    page = MonitoringHTML(response.body.decode())

    assert len(page.scripts) == 1
    assert not any(tag == "img" for tag, _ in page.tags)
    assignment = next(
        line.strip()
        for line in page.scripts[0].splitlines()
        if "const jsonData =" in line
    )
    displayed_json = json.loads(assignment.removeprefix("const jsonData = ")[:-1])
    assert json.loads(displayed_json) == {"message": message}


def test_filter_values_cannot_add_attributes_or_elements():
    agent = '"><img src=x onerror="alert(1)">'
    response = create_html_response(
        "History",
        {},
        "/api/history",
        show_filters=True,
        current_params={"agent": agent, "last": '" autofocus onfocus="alert(1)'},
    )
    page = MonitoringHTML(response.body.decode())
    inputs = {attrs["id"]: attrs for tag, attrs in page.tags if tag == "input"}

    assert not any(tag == "img" for tag, _ in page.tags)
    assert inputs["filter-agent"]["value"] == agent
    assert inputs["filter-last"]["value"] == '" autofocus onfocus="alert(1)'
    assert "autofocus" not in inputs["filter-last"]
    assert "onfocus" not in inputs["filter-last"]


def test_page_metadata_cannot_add_html_elements():
    markup = "</title><img src=x onerror=alert(1)>"
    response = create_html_response(markup, {"timestamp": markup}, markup)
    page = MonitoringHTML(response.body.decode())

    assert not any(tag == "img" for tag, _ in page.tags)
