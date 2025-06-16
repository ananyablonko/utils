import __init__
import pytest
import json

from pathlib import Path

from backend.utils.common.tree.tree import Tree, MaxDepthExceededError

class TestTreeClass:
    """Test suite for the Tree class."""

    def test_contains(self):
        tree = Tree("Introduction")
        assert "Introduction" in tree

    def test_str_representation(self):
        tree = Tree("Course Overview")
        assert "Tree" in str(tree)
        assert "Course Overview" in str(tree)

    def test_insert_node(self):
        tree = Tree("Math")
        tree.insert("Math", "Algebra")
        data = dict(parent_name="Algebra", node_name="Factoring")
        tree.insert(**data, index=None)
        
        assert "Algebra" in tree
        assert "Factoring" in tree
        assert tree["Algebra"].parent == tree["Math"]
        assert tree["Factoring"].parent == tree["Algebra"]

    def test_insert_with_index(self):
        tree = Tree("Programming")
        tree.insert("Programming", "Python")
        tree.insert("Programming", "JavaScript")
        tree.insert("Programming", "Java", index=1)
        
        assert tree["Programming"].children[0].name == "Python"
        assert tree["Programming"].children[1].name == "Java"
        assert tree["Programming"].children[2].name == "JavaScript"

    def test_title_rename(self):
        tree = Tree("Chemistry")
        tree.insert("Chemistry", "Organic")
        
        tree.name = "Chemistry 101"
        
        assert tree.name == "Chemistry 101"
        assert "Chemistry 101" in tree
        assert "Chemistry" not in tree
        assert tree["Organic"].parent is not None
        assert tree["Organic"].parent.name == "Chemistry 101"

    def test_node_index(self):
        tree = Tree("History")
        tree.insert("History", "Ancient")
        tree.insert("History", "Medieval")
        tree.insert("History", "Modern")
        
        assert tree["Ancient"].index == 0
        assert tree["Medieval"].index == 1
        assert tree["Modern"].index == 2

    def test_node_depth(self):
        tree = Tree("Biology")
        tree.insert("Biology", "Cells")
        tree.insert("Cells", "Organelles")
        tree.insert("Organelles", "Mitochondria")
        
        assert tree["Biology"].depth == 0
        assert tree["Cells"].depth == 1
        assert tree["Organelles"].depth == 2
        assert tree["Mitochondria"].depth == 3

    def test_node_uid(self):
        tree = Tree("Literature")
        tree.insert("Literature", "Poetry")
        tree.insert("Literature", "Prose")
        tree.insert("Poetry", "Sonnets")
        tree.insert("Poetry", "Haiku")
        
        assert tree["Poetry"].uid == [0]
        assert tree["Prose"].uid == [1]
        assert tree["Sonnets"].uid == [0, 0]
        assert tree["Haiku"].uid == [0, 1]

    def test_node_serialization(self):
        tree = Tree("Geography")
        tree.insert("Geography", "Continents")
        
        node_dict = tree["Continents"].model_dump()
        assert node_dict["name"] == "Continents"
        assert "children" in node_dict and node_dict["children"] == []
        assert "uid" in node_dict and node_dict["uid"] == [0]

    def test_pop_leaf(self):
        """Test that pop works correctly for leaf nodes"""
        tree = Tree("Root")
        tree.insert("Root", "Branch")
        tree.insert("Branch", "Leaf")
        
        # Pop a leaf node
        popped = tree.pop("Leaf")
        assert popped.name == "Leaf"
        assert "Leaf" not in tree
        assert len(tree["Branch"].children) == 0
        
        # Branch should still exist
        assert "Branch" in tree

    def test_pop_with_children(self):
        tree = Tree("Music")
        tree.insert("Music", "Classical")
        tree.insert("Classical", "Baroque")
        tree.insert("Classical", "Romantic")
        
        tree.pop("Classical")
        assert "Classical" not in tree
        assert "Baroque" not in tree
        assert "Romantic" not in tree

    def test_pop_with_grandchildren(self):
        """Test that pop recursively removes all descendants"""
        tree = Tree("Art")
        
        # Create a nested structure: Art -> Painting -> Oil Painting -> Portrait
        tree.insert("Art", "Painting")
        tree.insert("Art", "Sculpture") 
        tree.insert("Painting", "Oil Painting")
        tree.insert("Painting", "Watercolor")
        tree.insert("Oil Painting", "Portrait")
        tree.insert("Oil Painting", "Landscape")
        tree.insert("Watercolor", "Abstract")
        
        # Verify structure before pop
        assert "Painting" in tree
        assert "Oil Painting" in tree
        assert "Watercolor" in tree
        assert "Portrait" in tree
        assert "Landscape" in tree
        assert "Abstract" in tree
        assert "Sculpture" in tree
        assert len(tree["Art"].children) == 2
        assert len(tree["Painting"].children) == 2
        assert len(tree["Oil Painting"].children) == 2
        assert len(tree["Watercolor"].children) == 1
        
        # Pop the "Painting" branch - should remove all its descendants
        popped_node = tree.pop("Painting")
        
        # Verify the popped node is returned correctly
        assert popped_node.name == "Painting"
        
        # Verify all descendants are removed from the tree
        assert "Painting" not in tree
        assert "Oil Painting" not in tree
        assert "Watercolor" not in tree
        assert "Portrait" not in tree
        assert "Landscape" not in tree
        assert "Abstract" not in tree
        
        # Verify unrelated nodes remain
        assert "Sculpture" in tree
        assert len(tree["Art"].children) == 1
        assert tree["Art"].children[0].name == "Sculpture"
        
    def test_pop_illegal(self):
        """Test that pop raises error for nonexistent node and root node"""
        tree = Tree("Root")
        
        with pytest.raises(KeyError):
            tree.pop("NonExistent")

        with pytest.raises(ValueError, match="Cannot pop root node"):
            tree.pop(tree.name)

    def test_node_get(self):
        tree = Tree("Sports")
        tree.insert("Sports", "Football")
        
        assert tree.get("Football") == tree["Football"]
        assert tree.get("Basketball") is None
        assert tree.get("Basketball", "Not found") == "Not found"

    def test_setitem_with_dict(self):
        tree = Tree("Economics")
        
        node_dict = dict(
            parent_name="Economics",
            node_name="Microeconomics",
            index=0
        )
        
        tree["Microeconomics"] = node_dict
        assert "Microeconomics" in tree

    def test_iterator(self):
        tree = Tree("Computer Science")
        tree.insert("Computer Science", "Algorithms")
        tree.insert("Computer Science", "Data Structures")
        tree.insert("Algorithms", "Sorting")
        
        nodes = list(tree)
        assert len(nodes) == 4
        assert nodes[0].name == "Computer Science"
        assert "Algorithms" in [s.name for s in nodes]
        assert "Data Structures" in [s.name for s in nodes]
        assert "Sorting" in [s.name for s in nodes]

    def test_max_depth_limit(self):
        tree = Tree("Limited Course", max_depth=2)
        tree.insert("Limited Course", "Chapter 1")
        tree.insert("Chapter 1", "Section 1.1")
        
        # This should fail as it exceeds max_depth (which is 2, allowing depth 0, 1, 2)
        with pytest.raises(MaxDepthExceededError):
            tree.insert("Section 1.1", "Subnode 1.1.1")

        with pytest.raises(MaxDepthExceededError):
            tree.max_depth = 0

    def test_duplicate_node_names(self):
        tree = Tree("Mathematics")
        tree.insert("Mathematics", "Calculus")
        
        with pytest.raises(ValueError):
            tree.insert("Mathematics", "Calculus")

    def test_illegal_rename(self):
        """Test renaming t an already existing node name."""
        tree = Tree("Physics")
        tree.insert("Physics", "Mechanics")
        tree.insert("Physics", "Thermodynamics")
        
        with pytest.raises(ValueError):  # not allowed at all, must use "rename_node" method
            tree["Mechanics"].name = "Mechanics"

        with pytest.raises(ValueError):
            tree.rename_node("Mechanics", "Thermodynamics")

    def test_nonexistent_parent(self):
        tree = Tree("Course")
        
        with pytest.raises(KeyError):
            tree.insert("NonExistentParent", "Topic")

    def test_change_node_index(self):
        tree = Tree("Languages")
        tree.insert("Languages", "English")
        tree.insert("Languages", "Spanish")
        tree.insert("Languages", "French")
        
        # Change the index of Spanish from 1 to 0
        tree["Spanish"].index = 0
        
        assert tree["Languages"].children[0].name == "Spanish"
        assert tree["Languages"].children[1].name == "English"
        assert tree["Languages"].children[2].name == "French"

    def test_change_root_node_index(self):
        tree = Tree("Root")
        
        with pytest.raises(ValueError):
            tree["Root"].index = 0

    def test_to_from_dict(self):
        with open(str(Path(__file__).resolve().parent / "samples" / "lesson_plan.json"), 'r') as f:
            tree_dict = json.load(f)
        tree = Tree(**tree_dict)
        assert tree.model_dump() == tree_dict


if __name__ == '__main__':
    TestTreeClass().test_to_from_dict()