import __init__

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Any
import hashlib

from ds import PersistentDict, PersistentList

class TestPersistentDict(PersistentDict[str, Any]):
    """Concrete implementation for testing"""
    def hash(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()


class TestPersistentDictWithSubdirs(PersistentDict[str, Any]):
    """Test implementation that creates subdirectories"""
    def hash(self, key: str) -> str:
        h = hashlib.md5(key.encode()).hexdigest()
        return f"{h[:2]}/{h[2:]}"


class TestPersistentDictAPI:
    """Test that PersistentDict behaves like a regular dict"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def pdict(self, temp_dir):
        return TestPersistentDict(root=temp_dir / "test_dict")
    
    def test_init_creates_directory(self, temp_dir):
        root = temp_dir / "new_dict"
        assert not root.exists()
        pdict = TestPersistentDict(root=root)
        assert root.exists()
        assert (root / '.meta').exists()
    
    def test_len_empty(self, pdict):
        assert len(pdict) == 0
    
    def test_setitem_getitem(self, pdict):
        pdict['key1'] = 'value1'
        assert pdict['key1'] == 'value1'
        assert len(pdict) == 1
    
    def test_setitem_overwrites(self, pdict):
        pdict['key1'] = 'value1'
        pdict['key1'] = 'value2'
        assert pdict['key1'] == 'value2'
        assert len(pdict) == 1  # Length shouldn't change on overwrite
    
    def test_contains(self, pdict):
        assert 'key1' not in pdict
        pdict['key1'] = 'value1'
        assert 'key1' in pdict
    
    def test_keyerror_on_missing_key(self, pdict):
        with pytest.raises(KeyError):
            _ = pdict['nonexistent']
    
    def test_get_with_default(self, pdict):
        assert pdict.get('nonexistent') is None
        assert pdict.get('nonexistent', 'default') == 'default'
        
        pdict['key1'] = 'value1'
        assert pdict.get('key1') == 'value1'
        assert pdict.get('key1', 'default') == 'value1'
    
    def test_pop(self, pdict):
        pdict['key1'] = 'value1'
        pdict['key2'] = 'value2'
        
        assert pdict.pop('key1') == 'value1'
        assert 'key1' not in pdict
        assert len(pdict) == 1
        
        assert pdict.pop('nonexistent', 'default') == 'default'
        
        with pytest.raises(KeyError):
            pdict.pop('nonexistent')
    
    def test_update_dict(self, pdict):
        regular_dict = {'a': 1, 'b': 2}
        pdict.update(regular_dict)
        
        assert pdict['a'] == 1
        assert pdict['b'] == 2
        assert len(pdict) == 2
    
    def test_update_kwargs(self, pdict):
        pdict.update(x=10, y=20)
        
        assert pdict['x'] == 10
        assert pdict['y'] == 20
        assert len(pdict) == 2
    
    def test_update_iterable(self, pdict):
        pairs = [('p', 100), ('q', 200)]
        pdict.update(pairs)
        
        assert pdict['p'] == 100
        assert pdict['q'] == 200
        assert len(pdict) == 2
    
    def test_update_another_persistent_dict(self, temp_dir):
        pdict1 = TestPersistentDict(root=temp_dir / "dict1")
        pdict2 = TestPersistentDict(root=temp_dir / "dict2")
        
        pdict1['a'] = 1
        pdict1['b'] = 2
        
        pdict2.update(pdict1)
        
        assert pdict2['a'] == 1
        assert pdict2['b'] == 2
        assert len(pdict2) == 2
    
    def test_keys_values_items(self, pdict):
        data = {'a': 1, 'b': 2, 'c': 3}
        pdict.update(data)
        
        keys = list(pdict.keys())
        values = list(pdict.values())
        items = list(pdict.items())
        
        assert set(keys) == set(data.keys())
        assert set(values) == set(data.values())
        assert set(items) == set(data.items())
    
    def test_iter(self, pdict):
        data = {'x': 10, 'y': 20, 'z': 30}
        pdict.update(data)
        
        keys_from_iter = list(pdict)
        assert set(keys_from_iter) == set(data.keys())
    
    def test_complex_values(self, pdict):
        """Test that complex objects can be stored"""
        complex_obj = {'nested': [1, 2, {'deep': 'value'}]}
        pdict['complex'] = complex_obj
        
        retrieved = pdict['complex']
        assert retrieved == complex_obj
    
    def test_subdirectories(self, temp_dir):
        """Test that hash function can create subdirectories"""
        pdict = TestPersistentDictWithSubdirs(root=temp_dir / "subdir_test")
        pdict['test'] = 'value'
        
        assert pdict['test'] == 'value'
        # Check that subdirectory was created
        subdirs = [p for p in (temp_dir / "subdir_test").iterdir() if p.is_dir() and p.name != '.meta']
        assert len(subdirs) > 0
    
    def test_persistence_across_instances(self, temp_dir):
        """Test that data persists when creating new instances"""
        root = temp_dir / "persistent_test"
        
        # Create first instance and add data
        pdict1 = TestPersistentDict(root=root)
        pdict1['persistent'] = 'data'
        assert len(pdict1) == 1
        
        # Create second instance from same root
        pdict2 = TestPersistentDict(root=root)
        assert pdict2['persistent'] == 'data'
        assert len(pdict2) == 1


class TestPersistentListAPI:
    """Test that PersistentList behaves like a regular list"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def plist(self, temp_dir):
        return PersistentList[Any](root=temp_dir / "test_list")
    
    def test_init_creates_directory(self, temp_dir):
        root = temp_dir / "new_list"
        assert not root.exists()
        plist = PersistentList(root=root)
        assert root.exists()
        assert (root / '.meta').exists()
    
    def test_len_empty(self, plist: PersistentList):
        assert len(plist) == 0
    
    def test_append(self, plist: PersistentList):
        plist.append('item1')
        assert len(plist) == 1
        assert plist[0] == 'item1'
        
        plist.append('item2')
        assert len(plist) == 2
        assert plist[1] == 'item2'
    
    def test_getitem_setitem(self, plist: PersistentList):
        plist.append('initial')
        assert plist[0] == 'initial'
        
        plist[0] = 'modified'
        assert plist[0] == 'modified'
        assert len(plist) == 1
    
    def test_negative_indexing(self, plist: PersistentList):
        plist.extend(['a', 'b', 'c'])
        
        assert plist[-1] == 'c'
        assert plist[-2] == 'b'
        assert plist[-3] == 'a'
        
        plist[-1] = 'modified'
        assert plist[2] == 'modified'
    
    def test_index_error(self, plist: PersistentList):
        with pytest.raises(IndexError):
            _ = plist[0]
        
        plist.append('item')
        with pytest.raises(IndexError):
            _ = plist[1]
        
        with pytest.raises(IndexError):
            _ = plist[-2]
    
    def test_insert(self, plist: PersistentList):
        plist.extend(['a', 'b', 'c'])
        
        plist.insert(1, 'inserted')
        assert plist[0] == 'a'
        assert plist[1] == 'inserted'
        assert plist[2] == 'b'
        assert plist[3] == 'c'
        assert len(plist) == 4
    
    def test_insert_at_end(self, plist: PersistentList):
        plist.extend(['a', 'b'])
        plist.insert(10, 'end')  # Should insert at end
        
        assert plist[2] == 'end'
        assert len(plist) == 3
    
    def test_insert_negative(self, plist: PersistentList):
        plist.extend(['a', 'b', 'c'])
        plist.insert(-1, 'before_last')
        
        assert plist[2] == 'before_last'
        assert plist[3] == 'c'
        assert len(plist) == 4
    
    def test_pop_default(self, plist: PersistentList):
        plist.extend(['a', 'b', 'c'])
        
        assert plist.pop() == 'c'
        assert len(plist) == 2
        assert plist[-1] == 'b'
    
    def test_pop_index(self, plist: PersistentList):
        plist.extend(['a', 'b', 'c'])
        
        assert plist.pop(1) == 'b'
        assert len(plist) == 2
        assert plist[0] == 'a'
        assert plist[1] == 'c'
    
    def test_pop_empty(self, plist: PersistentList):
        with pytest.raises(IndexError):
            plist.pop()
    
    def test_pop_out_of_range(self, plist: PersistentList):
        plist.append('item')
        with pytest.raises(IndexError):
            plist.pop(5)
    
    def test_remove(self, plist: PersistentList):
        plist.extend(['a', 'b', 'a', 'c'])
        
        plist.remove('a')  # Should remove first occurrence
        assert plist[0] == 'b'
        assert plist[1] == 'a'
        assert plist[2] == 'c'
        assert len(plist) == 3
    
    def test_remove_not_found(self, plist: PersistentList):
        plist.extend(['a', 'b', 'c'])
        with pytest.raises(ValueError):
            plist.remove('x')
    
    def test_extend(self, plist: PersistentList):
        plist.extend(['a', 'b'])
        assert len(plist) == 2
        
        plist.extend(['c', 'd', 'e'])
        assert len(plist) == 5
        assert plist[4] == 'e'
    
    def test_complex_objects(self, plist: PersistentList):
        """Test that complex objects can be stored"""
        obj1 = {'dict': 'value'}
        obj2 = [1, 2, 3]
        obj3 = ('tuple', 'data')
        
        plist.extend([obj1, obj2, obj3])
        
        assert plist[0] == obj1
        assert plist[1] == obj2
        assert plist[2] == obj3
    
    def test_persistence_across_instances(self, temp_dir):
        """Test that data persists when creating new instances"""
        root = temp_dir / "persistent_list_test"
        
        # Create first instance and add data
        plist1 = PersistentList(root=root)
        plist1.extend(['persistent', 'data'])
        assert len(plist1) == 2
        
        # Create second instance from same root
        plist2 = PersistentList(root=root)
        assert plist2[0] == 'persistent'
        assert plist2[1] == 'data'
        assert len(plist2) == 2


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_empty_operations(self, temp_dir):
        pdict = TestPersistentDict(root=temp_dir / "empty_dict")
        plist = PersistentList(root=temp_dir / "empty_list")
        
        assert len(pdict) == 0
        assert len(plist) == 0
        assert list(pdict.keys()) == []
        assert list(pdict.values()) == []
        assert list(pdict.items()) == []
    
    def test_large_data(self, temp_dir):
        """Test with larger datasets"""
        pdict = TestPersistentDict(root=temp_dir / "large_dict")
        plist = PersistentList(root=temp_dir / "large_list")
        
        many_items = 1000
        for i in range(many_items):
            pdict[str(i)] = i
            plist.append(i)
        
        assert len(pdict) == many_items
        assert len(plist) == many_items
        
        assert pdict['50'] == 50
        assert plist[75] == 75
    
    def test_unicode_keys_values(self, temp_dir):
        """Test with unicode strings"""
        pdict = TestPersistentDict(root=temp_dir / "unicode_dict")
        plist = PersistentList(root=temp_dir / "unicode_list")
        
        pdict['ключ'] = 'значение'
        pdict['🔑'] = '🔓'
        
        plist.extend(['элемент', '🚀', '数据'])
        
        assert pdict['ключ'] == 'значение'
        assert pdict['🔑'] == '🔓'
        assert plist[0] == 'элемент'
        assert plist[1] == '🚀'
        assert plist[2] == '数据'


if __name__ == "__main__":
    pytest.main([__file__])