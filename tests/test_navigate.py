import __init__
import pytest

from text.json import navigate


class TestNavigateSuccess:
    """Test cases for successful navigation."""

    @pytest.fixture
    def sample_data(self):
        return {
            "users": [
                {"name": "Alice", "age": 30, "active": True},
                {"name": "Bob", "age": 25, "active": False}
            ],
            "config": {
                "debug": True,
                "version": "1.0",
                "settings": {
                    "timeout": 5000,
                    "retries": 3
                }
            },
            "numbers": [1, 2, 3, [4, 5, 6]],
            "empty_list": [],
            "empty_dict": {},
            "null_value": None,
            "zero": 0,
            "false_value": False,
            "string_value": "hello world"
        }

    def test_navigate_simple_access(self, sample_data):
        """Test accessing a simple dictionary field."""
        testvec = [
            (["string_value"], "hello world"),
            (["numbers", 0], 1),
            (["config", "settings", "timeout"], 5000),
            (["users", 0, "name"], "Alice"),
            (["users", 1, "age"], 25),
            (["numbers", 3, 1], 5),
            ([], sample_data),
            (["null_value"], None),
            (["zero"], 0),
            (["false_value"], False),
            (["users", 0, "active"], True),
            (["users", 1, "active"], False),
            (["config", "debug"], True),
        ]
        
        for path, expected in testvec:
            actual = navigate(sample_data, path)
            assert actual == str(expected)


class TestNavigateError:
    """Test cases for IndexError scenarios."""

    @pytest.fixture
    def sample_data(self):
        return {
            "items": ["a", "b", "c", {"id": 1}, {"id": 2}],
            "nested": [{"inner": [1, 2]}],
            "empty": [],
            "user": {"name": "Alice", "age": 30, "scores": [85, 90, 92]},
            "config": {},
            "numbers": [1, 2, 3],
            "mixed": [{"type": "dict"}, [1, 2, 3], "string", 1, 2.5, "string", None],
            "value": 42,
            "text": "hello",
            "flag": True,
        }

    def test_index_error(self, sample_data):
        paths = [
            ["items", 7],
            ["items", -1],
            ["empty", 0],
            ["nested", 0, "inner", 10],
        ]
        for path in paths:
            with pytest.raises(IndexError):
                navigate(sample_data, path)

    def test_key_error(self, sample_data):
        paths = [
            ["nonexistent"],
            ["user", "email"],
            ["config", "setting"],
            ["items", 3, "name"],
        ]
        for path in paths:
            with pytest.raises(KeyError):
                navigate(sample_data, path)

    def test_type_error(self, sample_data):
        paths = [
            ["numbers", "first"],
            ["user", 0],
            ["mixed", 1, "invalid"],
            ["user", "scores", "bad_index"],
        ]
        for path in paths:
            with pytest.raises(TypeError):
                navigate(sample_data, path)

    def test_value_error(self, sample_data):
        paths = [
            [3.14],
            ["items", None],
            [True],
            [["nested", "key"]],
            ["value", "property"],
            ["text", 0],
        ]
        for path in paths:
            with pytest.raises(ValueError):
                navigate(sample_data, path)

class TestNavigatePerformance:
    def test_deep_nesting(self):
        data = {"root": {}}
        current = data["root"]
        path = ["root"]
        
        for i in range(100):
            key = f"level_{i}"
            current[key] = {}
            current = current[key]
            path.append(key)
        
        current["final"] = "deep_value"
        path.append("final")
        
        result = navigate(data, path)
        assert result == "deep_value"
    
    def test_large_list(self):
        large_list = list(range(10000))
        data = {"large_list": large_list}
        
        assert navigate(data, ["large_list", 0]) == "0"
        assert navigate(data, ["large_list", 5000]) == "5000"
        assert navigate(data, ["large_list", 9999]) == "9999"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
