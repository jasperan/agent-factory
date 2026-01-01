"""
Tests for Factory.io integration tools.

Prerequisites:
- Factory.io running on localhost:7410
- Web API enabled (app.web_server = True)
- Test scene loaded with at least one sensor and one actuator

Run tests:
    poetry run pytest tests/test_factoryio_tools.py -v
"""

import pytest
from agent_factory.tools.factoryio import (
    FactoryIOConnectionTool,
    FactoryIOTagTool,
    FactoryIOReadWriteTool
)


@pytest.fixture
def connection_tool():
    """Fixture for FactoryIOConnectionTool."""
    return FactoryIOConnectionTool()


@pytest.fixture
def tag_tool():
    """Fixture for FactoryIOTagTool."""
    return FactoryIOTagTool()


@pytest.fixture
def readwrite_tool():
    """Fixture for FactoryIOReadWriteTool."""
    return FactoryIOReadWriteTool()


class TestFactoryIOConnection:
    """Test FactoryIOConnectionTool."""

    def test_health_check_success(self, connection_tool):
        """Test successful health check."""
        result = connection_tool._run(action="health_check")
        assert "SUCCESS" in result
        assert "7410" in result
        assert "reachable" in result

    def test_list_tags_summary(self, connection_tool):
        """Test tag summary retrieval."""
        result = connection_tool._run(action="list_tags_summary")
        assert "Tag Summary" in result
        assert "Total:" in result

    def test_unknown_action(self, connection_tool):
        """Test unknown action error handling."""
        result = connection_tool._run(action="invalid_action")
        assert "ERROR" in result
        assert "Unknown action" in result


class TestFactoryIOTag:
    """Test FactoryIOTagTool."""

    def test_list_all_tags(self, tag_tool):
        """Test listing all tags."""
        result = tag_tool._run(action="list")
        assert "count" in result
        assert "tags" in result

        import json
        data = json.loads(result)
        assert data["count"] > 0
        assert len(data["tags"]) > 0

    def test_list_with_type_filter(self, tag_tool):
        """Test filtering by type."""
        result = tag_tool._run(action="list", tag_type="Bit")

        import json
        data = json.loads(result)
        # Verify all tags are Bit type
        for tag in data["tags"]:
            assert tag["type"] == "Bit"

    def test_list_with_kind_filter(self, tag_tool):
        """Test filtering by kind."""
        result = tag_tool._run(action="list", tag_kind="Input")

        import json
        data = json.loads(result)
        # Verify all tags are Input kind
        for tag in data["tags"]:
            assert tag["kind"] == "Input"

    def test_list_with_name_filter(self, tag_tool):
        """Test filtering by name."""
        result = tag_tool._run(action="list", name_filter="conveyor")

        import json
        data = json.loads(result)
        # Verify all tags contain "conveyor" (case-insensitive)
        for tag in data["tags"]:
            assert "conveyor" in tag["name"].lower()

    def test_get_tag_by_name(self, tag_tool):
        """Test getting specific tag by name."""
        # First get a tag name
        list_result = tag_tool._run(action="list")
        import json
        tags = json.loads(list_result)["tags"]

        if tags:
            tag_name = tags[0]["name"]
            result = tag_tool._run(action="get_by_name", tag_name=tag_name)
            assert tag_name in result

    def test_get_nonexistent_tag(self, tag_tool):
        """Test getting tag that doesn't exist."""
        result = tag_tool._run(action="get_by_name", tag_name="NonexistentTag12345")
        assert "ERROR" in result or "not found" in result.lower()


class TestFactoryIOReadWrite:
    """Test FactoryIOReadWriteTool."""

    def test_read_tag_values(self, readwrite_tool, tag_tool):
        """Test reading tag values."""
        # Get a valid tag name first
        tag_result = tag_tool._run(action="list")
        import json
        tags = json.loads(tag_result)["tags"]

        if tags:
            tag_name = tags[0]["name"]
            result = readwrite_tool._run(action="read", tag_names=[tag_name])

            data = json.loads(result)
            assert data["success"] is True
            assert tag_name in data["values"]

    def test_read_multiple_tags(self, readwrite_tool, tag_tool):
        """Test reading multiple tag values."""
        # Get at least 2 tag names
        tag_result = tag_tool._run(action="list")
        import json
        tags = json.loads(tag_result)["tags"]

        if len(tags) >= 2:
            tag_names = [tags[0]["name"], tags[1]["name"]]
            result = readwrite_tool._run(action="read", tag_names=tag_names)

            data = json.loads(result)
            assert data["success"] is True
            assert all(name in data["values"] for name in tag_names)

    def test_write_tag_value(self, readwrite_tool, tag_tool):
        """Test writing tag value (requires Output tag)."""
        # Find an Output Bit tag
        tag_result = tag_tool._run(action="list", tag_type="Bit", tag_kind="Output")
        import json
        tags = json.loads(tag_result)["tags"]

        if tags:
            tag_name = tags[0]["name"]

            # Write True
            result = readwrite_tool._run(
                action="write",
                tag_values={tag_name: True}
            )

            data = json.loads(result)
            assert data["success"] is True
            assert tag_name in data["tags"]

            # Verify write by reading back
            read_result = readwrite_tool._run(action="read", tag_names=[tag_name])
            read_data = json.loads(read_result)
            assert read_data["values"][tag_name] is True

    def test_write_to_input_fails(self, readwrite_tool, tag_tool):
        """Test that writing to Input tag fails."""
        # Find an Input tag
        tag_result = tag_tool._run(action="list", tag_kind="Input")
        import json
        tags = json.loads(tag_result)["tags"]

        if tags:
            tag_name = tags[0]["name"]

            # Try to write (should fail)
            result = readwrite_tool._run(
                action="write",
                tag_values={tag_name: True}
            )

            data = json.loads(result)
            # Should have error
            assert data["success"] is False or "errors" in data


class TestFactoryIOIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow(self, connection_tool, tag_tool, readwrite_tool):
        """Test complete workflow: connect → discover → read → write."""
        # 1. Health check
        health = connection_tool._run(action="health_check")
        assert "SUCCESS" in health

        # 2. Discover Output Bit tags
        tags = tag_tool._run(action="list", tag_type="Bit", tag_kind="Output")
        import json
        tag_data = json.loads(tags)

        if tag_data["count"] > 0:
            tag_name = tag_data["tags"][0]["name"]

            # 3. Read initial value
            initial = readwrite_tool._run(action="read", tag_names=[tag_name])
            initial_data = json.loads(initial)
            assert initial_data["success"] is True

            # 4. Write new value
            write_result = readwrite_tool._run(
                action="write",
                tag_values={tag_name: True}
            )
            write_data = json.loads(write_result)
            assert write_data["success"] is True

            # 5. Read to verify
            verify = readwrite_tool._run(action="read", tag_names=[tag_name])
            verify_data = json.loads(verify)
            assert verify_data["values"][tag_name] is True


# Fixtures for testing error conditions
@pytest.mark.skip(reason="Requires Factory.io to be stopped")
def test_connection_failure():
    """Test behavior when Factory.io is not running."""
    # This test would only pass when Factory.io is stopped
    tool = FactoryIOConnectionTool()
    tool.base_url = "http://localhost:9999"  # Wrong port
    result = tool._run(action="health_check")
    assert "ERROR" in result
    assert "Cannot connect" in result
