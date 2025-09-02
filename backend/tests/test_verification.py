"""
Simple verification test to ensure testing framework is working
"""

def test_basic_math():
    """Test basic math operations"""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5.0


def test_string_operations():
    """Test string operations"""
    assert "hello".upper() == "HELLO"
    assert "world".capitalize() == "World"


def test_list_operations():
    """Test list operations"""
    test_list = [1, 2, 3]
    assert len(test_list) == 3
    assert 2 in test_list
    assert test_list[0] == 1


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
