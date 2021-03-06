import string
from copy import deepcopy
from pathlib import Path
from typing import Dict

import pytest

from controller.utils import read_json
from model.config import Settings
from model.exceptions import InvalidTreeJsonFormatException, InvalidNodeTypeException
from model.tree import Node, Tree, Collection, NodeTypes, Verification, DisconnectedNode


class TestNode(object):
    # valid node files and objects
    node_attributes_children = Node("node", "1", {"a": True}, ["2", "3"])
    node_attributes_children_json = read_json(Path('json/nodes/valid/NodeAttributesChildren.json'))
    node_children_no_attributes = Node("node", "1", {}, ["2", "3"])
    node_children_no_attributes_json = read_json(Path('json/nodes/valid/NodeChildrenNoAttributes.json'))
    node_attributes_no_children = Node("node", "1", {"a": True})
    node_attributes_no_children_json = read_json(Path('json/nodes/valid/NodeAttributesNoChildren.json'))
    node_no_attributes_children = Node("node", "1")
    node_no_attributes_children_json = read_json(Path('json/nodes/valid/NodeNoAttributesChildren.json'))

    # invalid node files
    node_no_id = read_json(Path('json/nodes/invalid/NodeNoId.json'))
    node_no_title = read_json(Path('json/nodes/invalid/NodeNoTitle.json'))
    node_wrong_children_type = read_json(Path('json/nodes/invalid/NodeWrongChildrenType.json'))
    node_wrong_id_type = read_json(Path('json/nodes/invalid/NodeWrongIdType.json'))
    node_wrong_title_type = read_json(Path('json/nodes/invalid/NodeWrongTitleType.json'))

    def test_from_json(self):
        assert self.node_attributes_children == Node.from_json(self.node_attributes_children_json)
        assert self.node_attributes_no_children == Node.from_json(self.node_attributes_no_children_json)
        assert self.node_children_no_attributes == Node.from_json(self.node_children_no_attributes_json)
        assert self.node_no_attributes_children == Node.from_json(self.node_no_attributes_children_json)

    def test_id_generator_default_settings(self):
        generated_id = Node.generate_id()
        assert len(generated_id) == 16
        assert all(c.islower() or c.isdigit() for c in generated_id)

    def test_id_generator_custom_settings(self):
        generated_id = Node.generate_id(10, string.ascii_uppercase)
        assert len(generated_id) == 10
        assert all(c.isupper for c in generated_id)

    def test_from_json_incorrect_missing_title(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Node.from_json(self.node_no_id)

    def test_from_json_incorrect_no_id(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Node.from_json(self.node_no_title)

    def test_from_json_wrong_types(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Node.from_json(self.node_wrong_children_type)
        with pytest.raises(InvalidTreeJsonFormatException):
            Node.from_json(self.node_wrong_id_type)
        with pytest.raises(InvalidTreeJsonFormatException):
            Node.from_json(self.node_wrong_title_type)

    def test_add_child(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.add_child("4")
        assert ["2", "3", "4"] == node.children

    def test_remove_child_existent(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.remove_child("2")
        assert ["3"] == node.children

    def test_remove_child_not_existent(self):
        node = Node.from_json(self.node_no_attributes_children_json)
        node.remove_child("2")
        assert [] == node.children

    def test_add_attribute(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.add_attribute("b", False)
        assert {"a": True, "b": False} == node.attributes

    def test_remove_attribute_existent(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.remove_attribute("a")
        assert {} == node.attributes

    def test_remove_attribute_not_existent(self):
        node = Node.from_json(self.node_no_attributes_children_json)
        node.remove_attribute("a")
        assert {} == node.attributes

    def test_create_json(self):
        assert self.node_attributes_children_json == self.node_attributes_children.create_json()
        assert self.node_attributes_no_children_json == self.node_attributes_no_children.create_json()
        assert self.node_children_no_attributes_json == self.node_children_no_attributes.create_json()
        assert self.node_no_attributes_children_json == self.node_no_attributes_children.create_json()

    def test_add_property(self):
        node = Node.from_json(self.node_attributes_children_json)
        node.add_property("b", False)
        assert {"b": False} == node.attributes.get("properties")
        node.add_property("c", "1")
        assert {"b": False, "c": "1"} == node.attributes.get("properties")

    def test_update_properties(self):
        node = Node.from_json(self.node_attributes_no_children_json)
        node.update_properties({"b": 'false'})
        assert 'properties' in node.attributes
        assert 'b' in node.attributes['properties']
        assert 'false' is node.attributes['properties']['b']
        node.update_properties({})
        assert 'properties' not in node.attributes
        node = Node.from_json(self.node_attributes_no_children_json)
        node.update_properties({})
        assert 'properties' not in node.attributes

    def test_remove_property(self):
        node = Node.from_json(self.node_attributes_children_json)
        assert "properties" not in node.attributes
        node.remove_property("a")
        assert "properties" not in node.attributes
        node.add_property("a", "c")
        assert "properties" in node.attributes
        assert "a" in node.attributes.get("properties")
        node.remove_property("a")
        assert "a" not in node.properties()

    def test_properties(self):
        node = Node.from_json(self.node_attributes_no_children_json)
        assert not node.properties()
        node.add_property("a", "b")
        assert {"a": "b"} == node.properties()

    def test_str(self):
        node = Node('b', 'a', {'a': "b"}, ["c"])
        assert str(node) == str(node.create_json())
        assert repr(node) == str(node)


class TestTree(object):
    # valid trees
    tree_dance_strategy = read_json(Path('json/trees/valid/DanceStrategy.json'))
    tree_demo_twente_strategy = read_json(Path('json/trees/valid/DemoTeamTwenteStrategy.json'))
    tree_simple_tree = read_json(Path('json/trees/valid/SimpleTree.json'))
    tree_enter_formation_tactic = read_json(Path('json/trees/valid/EnterFormationTactic.json'))

    # invalid trees
    # trees with missing required attributes
    tree_no_data = read_json(Path('json/trees/invalid/DanceStrategyNoData.json'))
    tree_no_name = read_json(Path('json/trees/invalid/DanceStrategyNoName.json'))
    tree_no_nodes = read_json(Path('json/trees/invalid/DanceStrategyNoNodes.json'))
    tree_no_root = read_json(Path('json/trees/invalid/DanceStrategyNoRoot.json'))
    tree_no_title = read_json(Path('json/trees/invalid/DanceStrategyNoTitle.json'))
    tree_no_trees = read_json(Path('json/trees/invalid/DanceStrategyNoTrees.json'))
    # trees with wrong attribute type
    tree_wrong_name_type = read_json(Path('json/trees/invalid/DanceStrategyWrongNameType.json'))
    tree_wrong_root_type = read_json(Path('json/trees/invalid/DanceStrategyWrongRootType.json'))
    tree_wrong_title_type = read_json(Path('json/trees/invalid/DanceStrategyWrongTitleType.json'))
    # trees with other wrong types
    tree_wrong_trees0_type = read_json(Path('json/trees/invalid/DanceStrategyWrongTrees0Type.json'))
    # trees without nodes or trees
    tree_empty_trees = read_json(Path('json/trees/invalid/DanceStrategyEmptyTrees.json'))
    tree_empty_nodes = read_json(Path('json/trees/invalid/DanceStrategyEmptyNodes.json'))
    # tree file with more than one tree
    tree_too_many_trees = read_json(Path('json/trees/invalid/DanceStrategyTooManyTrees.json'))

    def test_from_json_valid(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        assert tree.name == 'DanceStrategy'
        assert tree.root == 'tfbqmsn62cc9okkj'
        assert len(tree.nodes) == 3

    def test_from_json_valid2(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        assert tree.name == 'DemoTeamTwenteStrategy'
        assert tree.root == 'ydjw9of7ndf88'
        assert len(tree.nodes) == 4

    def test_from_json_valid3(self):
        tree = Tree("SimpleTree", "1", {"1": Node("Sequence", "1")})
        assert tree == Tree.from_json(self.tree_simple_tree)

    def test_from_json_invalid_trees0_type(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_wrong_trees0_type)

    def test_from_json_invalid_wrong_attribute_types(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_wrong_name_type)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_wrong_root_type)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_wrong_title_type)

    def test_from_json_invalid_missing_attributes(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_data)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_name)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_nodes)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_root)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_title)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_no_trees)

    def test_from_json_empty_trees_nodes(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_empty_nodes)
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_empty_trees)

    def test_from_json_too_many_trees(self):
        with pytest.raises(InvalidTreeJsonFormatException):
            Tree.from_json(self.tree_too_many_trees)

    def test_add_node(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        tree.add_node(Node("title", "1"))
        assert "1"in tree.nodes.keys()

    def test_remove_node(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        assert True is tree.remove_node(tree.nodes.get("sftlsc94h3q1p"))
        assert "sftlsc94h3q1p" not in tree.nodes.keys()
        # remove the root and check if all root is set to ''
        tree = Tree.from_json(self.tree_dance_strategy)
        assert True is tree.remove_node(tree.nodes.get(tree.root))
        assert tree.root == ''

    def test_add_subtree(self):
        tree = Tree.from_json(self.tree_simple_tree)
        subtree = Tree.from_json(self.tree_demo_twente_strategy)
        main_node = tree.nodes.get('1')
        tree.add_subtree(subtree, main_node.id)
        assert len(main_node.children) == 1
        repeater_node = tree.nodes.get(main_node.children[0])
        assert repeater_node.title == 'Repeater'
        assert len(repeater_node.children) == 1
        parallel_sequence_node = tree.nodes.get(repeater_node.children[0])
        assert 'ParallelSequence' == parallel_sequence_node.title
        assert 2 == len(parallel_sequence_node.children)

    def test_update_subtree(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        subtree = Tree.from_json(self.tree_simple_tree)
        tree.update_subtree(subtree, tree.root, subtree.root)
        assert 2 == len(tree.nodes)
        tree.update_subtree(subtree, tree.root)
        assert 2 == len(tree.nodes)

    def test_update_subtree_invalid(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        subtree = Tree.from_json(self.tree_simple_tree)
        tree.update_subtree(subtree, 'abcd')
        tree.update_subtree(subtree, tree.root, 'abcd')
        assert 4 == len(tree.nodes)

    def test_add_subtree_invalid(self):
        tree = Tree.from_json(self.tree_simple_tree)
        tree.add_subtree(tree, "abc")
        tree.add_subtree(tree, tree.nodes.get(tree.root).id, "def")
        assert 1 == len(tree.nodes)

    def test_remove_subtree(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        tree.remove_subtree(tree.root)
        assert list() == tree.nodes.get(tree.root).children
        assert 1 == len(tree.nodes)

    def test_remove_subtree_invalid(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        tree.remove_subtree('abcd')
        assert 4 == len(tree.nodes)

    def test_remove_node_not_existent(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        assert False is tree.remove_node(Node("title", "non existent node"))
        assert "non existent node" not in tree.nodes.keys()

    def test_remove_node_by_id(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        assert True is tree.remove_node_by_id("sftlsc94h3q1p")
        assert "sftlsc94h3q1p" not in tree.nodes.keys()
        # remove the root and check if all root is set to ''
        tree = Tree.from_json(self.tree_dance_strategy)
        assert True is tree.remove_node_by_id(tree.root)
        assert tree.root == ''

    def test_propagate_role(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        tree.propagate_role(tree.root, "t")
        for node_id, node in tree.nodes.items():
            if node_id != tree.root:
                assert 'properties' in node.attributes
                assert 'ROLE' in node.attributes['properties']
                assert 't' in node.attributes['properties']['ROLE']

    def test_propagate_role_invalid(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        tree.propagate_role("abcd", "t")
        for node_id, node in tree.nodes.items():
            assert 'properties' not in node.attributes

    def test_remove_propagate(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        tree.propagate_role(tree.root, "t")
        tree.remove_propagation(tree.root)
        for node_id, node in tree.nodes.items():
            if node_id != tree.root:
                assert 'ROLE' not in node.attributes['properties']

    def test_remove_node_by_id_not_existent(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        tree.remove_node_by_id("non existent node")
        assert "non existent node" not in tree.nodes.keys()

    def test_remove_node_and_children_by_id(self):
        # test removing a node that does not exist
        tree = Tree.from_json(self.tree_dance_strategy)
        assert False is tree.remove_node_and_children_by_id("non_existing_id")
        # test removing a node without children
        tree.add_node(Node("test_node", "test_node"))
        assert True is tree.remove_node_and_children_by_id("test_node")
        # test removing a node  with non existing children
        tree.add_node(Node("test_node", "test_node", children=['non_existing_node']))
        assert False is tree.remove_node_and_children_by_id("test_node")
        # remove the root and check if all nodes are removed
        assert True is tree.remove_node_and_children_by_id(tree.root)
        assert tree.root == ''
        assert len(tree.nodes) == 0

    def test_create_json1(self):
        tree = Tree.from_json(self.tree_dance_strategy)
        assert self.tree_dance_strategy == tree.create_json()

    def test_create_json2(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        assert self.tree_demo_twente_strategy == tree.create_json()

    def test_create_json3(self):
        tree = Tree.from_json(self.tree_simple_tree)
        assert self.tree_simple_tree == tree.create_json()

    def test_str(self):
        tree = Tree.from_json(self.tree_simple_tree)
        assert str(tree.create_json()) == str(tree)
        assert str(tree.create_json()) == repr(tree)

    def test_find_parent_node_if_exists(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        assert not tree.find_parent_node_if_exists(tree.nodes.get(tree.root))
        assert tree.nodes.get(tree.root) == tree.find_parent_node_if_exists(tree.nodes.get('abcdefgh314'))

    def test_find_role_subtree_node_above_node(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        assert not tree.find_role_subtree_node_above_node(tree.nodes.get('abcdefgh314'))
        tree = Tree.from_json(self.tree_enter_formation_tactic)
        assert tree.nodes.get('0ia3adfsyai4m') == \
            tree.find_role_subtree_node_above_node(tree.nodes.get('3j1eplzumct1ky2l'))

    def test_find_role_subtree_below_node(self):
        tree = Tree.from_json(self.tree_enter_formation_tactic)
        assert 7 == len(tree.find_role_subtree_nodes_below_node(tree.nodes.get(tree.root)))
        tree.nodes.get(tree.root).add_child('abcd')
        assert 7 == len(tree.find_role_subtree_nodes_below_node(tree.nodes.get(tree.root)))

    def test_find_role_subtree_nodes_if_exist(self):
        tree = Tree.from_json(self.tree_demo_twente_strategy)
        assert [] == tree.find_role_subtree_nodes_if_exist('abcd')
        tree = tree.from_json(self.tree_enter_formation_tactic)
        nodes = tree.find_role_subtree_nodes_if_exist('EnterFormationRole')
        assert 7 == len(nodes)
        assert tree.nodes.get('0ia3adfsyai4m') in nodes
        assert tree.nodes.get('mz9t0qn1r1brww') in nodes
        assert tree.nodes.get('3j1eplzumct1ky2l') not in nodes


class TestCollection(object):
    path = Path("json/collection/")
    complete_path = Path('json/jsons/')
    assister_role = Tree.from_json(read_json(Path('json/collection/roles/Assister.json')))
    attack_strategy = Tree.from_json(read_json(Path('json/collection/strategies/AttackStrategy.json')))
    attactic_tactic = Tree.from_json(read_json(Path('json/collection/tactics/Attactic.json')))
    collection: Dict[str, Dict[str, Tree]] = {
        "roles": {"Assister.json": assister_role},
        "strategies": {"AttackStrategy.json": attack_strategy},
        "tactics": {"Attactic.json": attactic_tactic},
        "keeper": {}
    }

    def test_from_path(self):
        collection = Collection.from_path(self.path)
        # collection should not contain the invalid roles/InvalidRole.json
        collection.path = None
        assert 'InvalidRole' not in collection.collection.get('roles').keys()
        assert Collection(self.collection) == collection

    def test_from_path_default(self):
        def_json = Settings.default_json_folder()
        Settings.alter_default_json_folder(self.path)
        collection = Collection.from_path()
        Settings.alter_default_json_folder(def_json)
        # collection should not contain the invalid roles/InvalidRole.json
        assert 'InvalidRole' not in collection.collection.get('roles').keys()
        assert Collection(self.collection) == collection

    def test_build_collection(self):
        collection = Collection()
        collection.build_collection(self.path)
        # check if hidden file is not added to collection
        assert '.hiddendir' not in collection.collection.keys()
        assert '_categoryunderscore' not in collection.collection.keys()
        assert '.hiddenTree.json' not in collection.collection.get('roles')
        # check if file with wrong file extension is not added
        assert 'TreeWithoutJsonFileExtension' not in collection.collection.get('roles')
        assert Collection(self.collection) == collection

    def test_write_collection(self, tmpdir):
        collection = Collection.from_path(self.path)
        collection.write_collection(tmpdir)
        read = Collection.from_path(tmpdir)
        # sets path equal, so objects are equal
        collection.path = None
        read.path = None
        assert read == collection

    def test_write_collection_default_path1(self, tmpdir):
        def_path = Settings.default_json_folder()
        Settings.alter_default_json_folder(tmpdir)
        collection = Collection.from_path()
        collection.write_collection()
        read = Collection.from_path(tmpdir)
        Settings.alter_default_json_folder(def_path)
        # sets path equal, so objects are equal
        collection.path = None
        read.path = None
        assert collection == read

    def test_write_collection_default_path2(self, tmpdir):
        collection = Collection.from_path()
        collection.path = tmpdir
        collection.write_collection()
        read = Collection.from_path(tmpdir)
        # sets path equal, so objects are equal
        collection.path = None
        read.path = None
        assert collection == read

    def test_write_collection_new_file(self, tmpdir):
        collection = Collection.from_path(self.path)
        collection.write_collection(tmpdir)
        collection.add_tree("roles", "tree.json", Tree("name", "1", {"1": Node("node", "1")}))
        collection.write_collection(tmpdir)
        read = Collection.from_path(tmpdir)
        # sets path equal, so objects are equal
        collection.path = None
        read.path = None
        assert read == collection

    def test_write_collection_new_file_new_dir(self, tmpdir):
        collection = Collection({"roles": {"Role.json": Tree("Role", "1", {"1": Node("1", "1")})},
                                 "tactics": {},
                                 "strategies": {},
                                 "keeper": {}})
        collection.write_collection(tmpdir)
        collection.path = tmpdir
        assert collection == Collection.from_path(tmpdir)

    def test_add_tree_folder_exists(self):
        collection = Collection.from_path(self.path)
        tree = Tree("name", "1", {"1": Node("node", "1")})
        collection.add_tree("keeper", "tree.json", tree)
        assert "tree.json" in collection.collection.get('keeper')

    def test_add_tree_folder_not_exists(self):
        collection = Collection.from_path(self.path)
        tree = Tree("name", "1", {"1": Node("node", "1")})
        collection.add_tree("test", "tree.json", tree)
        assert "tree.json" in collection.collection.get('test')

    def test_remove_tree_exists(self):
        collection = Collection.from_path(self.path)
        assert "Assister.json" in collection.collection.get('roles')
        collection.remove_tree("roles", "Assister.json")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_remove_tree_not_exists(self):
        collection = Collection.from_path(self.path)
        collection.remove_tree("roles", "Assister.json")
        assert "Assister.json" not in collection.collection.get('roles')
        collection.remove_tree("roles", "Assister.json")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_remove_tree_by_name_exists(self):
        collection = Collection.from_path(self.path)
        assert "Assister.json" in collection.collection.get('roles')
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_remove_tree_by_name_not_exists(self):
        collection = Collection.from_path(self.path)
        # add a tree, so the if statement goes to the else
        collection.add_tree("roles", "test", Tree('roles', '1'))
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_get_tree_by_name(self):
        collection = Collection.from_path(self.path)
        assert not collection.get_tree_by_name('abcdefgh')
        assert collection.get_tree_by_name('Assister') == TestCollection.assister_role

    def test_remove_tree_by_name_dir_not_exists(self):
        collection = Collection.from_path(self.path)
        collection.remove_tree_by_name("test", "Assister")
        assert "test" not in collection.collection.keys()

    def test_remove_tree_by_name_tree_not_exists(self):
        collection = Collection.from_path(self.path)
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')
        collection.remove_tree_by_name('roles', "Assister")
        assert "Assister.json" not in collection.collection.get('roles')

    def test_categories_and_filenames(self):
        collection = Collection(self.collection)
        collection.collection['keeper'] = {}
        categories_and_filenames = {
            'roles': ['Assister.json'],
            'tactics': ['Attactic.json'],
            'strategies': ['AttackStrategy.json'],
            'keeper': []
        }
        assert categories_and_filenames == collection.categories_and_filenames()

    def test_get_root_nodes_by_category(self):
        collection = Collection.from_path(self.path)
        result = collection.get_root_nodes_by_category("strategies")
        assert "ydjw9of7ndf88" == result[0][0]
        assert "AttackStrategy" == result[0][1]
        result = collection.get_root_nodes_by_category("tactics")
        assert "57mrxn20qviax5qc" == result[0][0]
        assert "Attactic" == result[0][1]
        result = collection.get_root_nodes_by_category("roles")
        assert "sx6fvrxlaoudhmmq9" == result[0][0]
        assert "Assister" == result[0][1]
        result = collection.get_root_nodes_by_category("invalid_category")
        assert len(result) == 0

    def test_get_category_from_node(self):
        collection = Collection.from_path(self.path)
        result = collection.get_category_from_node("ydjw9of7ndf88")
        assert result == "strategies"
        result = collection.get_category_from_node("57mrxn20qviax5qc")
        assert result == "tactics"
        result = collection.get_category_from_node("sx6fvrxlaoudhmmq9")
        assert result == "roles"
        result = collection.get_category_from_node("invalid_category")
        assert not result

    def test_verify_trees(self):
        collection = Collection.from_path(Settings.default_json_folder(), only_verify_mathematical_properties=False)
        for category in collection.collection:
            for file in collection.collection[category]:
                # skip these two files as there is a decorator with two children
                if not (file == "GetBallTestTactic.json" or file == "GetBallTestStrategy.json"):
                    assert 0 is len(collection.verify_tree(collection.collection[category][file], category))

    def test_write_tree(self, tmpdir):
        collection = Collection.from_path(self.path)
        tree = self.attack_strategy
        collection.write_tree(tree, Path(tmpdir) / "test.json")
        path = tmpdir / 'test.json'
        read = Tree.from_json(read_json(path))
        assert tree == read

    def test_json_path(self):
        collection = Collection.from_path(self.path)
        assert collection.jsons_path() == self.path
        collection = Collection.from_path()
        assert collection.jsons_path() == Settings.default_json_folder()

    def test_update_subtrees_in_collection_from_main_tree(self):
        collection = Collection.from_path(self.complete_path)
        collection_copy = deepcopy(collection)
        collection_copy.update_subtrees_in_collection(collection_copy.get_tree_by_name('EnterFormationRole'))
        tree = collection_copy.get_tree_by_name('EnterFormationTactic')
        assert collection_copy.get_tree_by_name('EnterFormationTactic') != \
            collection.get_tree_by_name('EnterFormationTactic')
        old_tree = collection.get_tree_by_name('EnterFormationTactic')
        role_nodes = tree.find_role_subtree_nodes_if_exist('EnterFormationRole')
        for role_node in role_nodes:
            child = role_node.children[0]
            assert child not in old_tree.nodes
            child_node = tree.nodes.get(child)
            old_child_id = old_tree.nodes.get(role_node.id).children[0]
            old_child_node = old_tree.nodes.get(old_child_id)
            assert old_child_node.title == child_node.title
            assert old_child_node.id != child_node.id
            assert len(old_child_node.children) == len(child_node.children)

    def test_update_subtrees_in_collection_from_subtree(self):
        collection = Collection.from_path(self.complete_path)
        tree = collection.get_tree_by_name('EnterFormationTactic')
        tree.nodes.get('x988e2xb3y8h0hmxq').title = 'TestChange'
        collection.update_subtrees_in_collection(tree, tree.nodes.get('l795jdit0tls4k52'))
        role_tree = collection.get_tree_by_name('EnterFormationRole')
        assert len(role_tree.nodes.items()) == 2
        root_node = role_tree.nodes.get(role_tree.root)
        assert root_node.title == 'TestChange'
        assert len(root_node.children) == 1
        assert role_tree.nodes.get(root_node.children[0]).title == 'EnterFormation'

    def test_update_subtrees_in_collection_role_propagation(self):
        # check if role propagation is skipped
        collection = Collection.from_path(self.complete_path)
        node = Node('Role', attributes={'role': 'EnterFormationRole'})
        tree = collection.get_tree_by_name('DemoTeamTwenteStrategy')
        tree.add_node(node)
        tree.nodes.get(tree.root).add_child(node.id)
        other_tree = collection.get_tree_by_name('EnterFormationRole')
        collection.update_subtrees_in_collection(other_tree)
        child = tree.nodes.get(node.children[0])
        assert 'properties' not in child.attributes

    def test_update_subtrees_in_collection_invalid(self):
        # no role subtree
        collection = Collection.from_path(self.complete_path)
        collection_copy = deepcopy(collection)
        tree = collection.get_tree_by_name('DemoTeamTwenteStrategy')
        collection.update_subtrees_in_collection(tree, tree.nodes.get(tree.root))
        assert collection_copy == collection
        # role subtree no children
        node = Node('Role', attributes={'role': 'EnterFormationRole'})
        tree_copy = deepcopy(tree)
        tree.add_node(node)
        tree.nodes.get(tree.root).add_child(node.id)
        collection.update_subtrees_in_collection(tree, node)
        collection.collection['strategies']['DemoTeamTwenteStrategy.json'] = tree_copy
        assert collection == collection_copy


class TestVerification(object):

    path = Path("json/collection/")
    assister_role = Tree.from_json(read_json(Path('json/collection/roles/Assister.json')))
    attack_strategy = Tree.from_json(read_json(Path('json/collection/strategies/AttackStrategy.json')))
    attactic_tactic = Tree.from_json(read_json(Path('json/collection/tactics/Attactic.json')))

    # invalid trees
    simple_cyclic_tree = Tree.from_json(read_json(Path('json/verification/SimpleCyclicTree.json')))
    simple_unconnected_tree = Tree.from_json(read_json(Path('json/verification/SimpleTreeWithUnconnectedNodes.json')))
    simple_invalid_composites_tree = Tree.from_json(read_json(Path('json/verification/InvalidCompositesTree.json')))
    simple_invalid_decorator_tree = Tree.from_json(read_json(Path('json/verification/InvalidDecoratorTree.json')))
    # 1 has a failing node with a non matching property
    simple_invalid_role_inheritance_tree_1 = Tree.from_json(read_json(
        Path('json/verification/InvalidRoleInheritanceTree1.json')))
    # 2 has a failing node without the properties key
    simple_invalid_role_inheritance_tree_2 = Tree.from_json(read_json(
        Path('json/verification/InvalidRoleInheritanceTree2.json')))
    # 1 Has no root node defined
    simple_invalid_root_node_tree1 = Tree.from_json(read_json(Path(
        'json/verification/InvalidRootNodeTree1.json')))
    # 2 Has a root node which doesn't exist in the list of nodes
    simple_invalid_root_node_tree2 = Tree.from_json(read_json(Path(
        'json/verification/InvalidRootNodeTree2.json')))

    # SSR-Tree
    ssr_tree = Tree.from_json(read_json(Path('json/verification/StrategyStrategyRoleTree.json')))
    # TTR-Tree
    ttr_tree = Tree.from_json(read_json(Path('json/verification/TacticTacticRoleTree.json')))
    # RR-Tree
    rr_tree = Tree.from_json(read_json(Path('json/verification/RoleRoleTree.json')))

    # valid trees
    simple_non_cyclic_tree = Tree.from_json(read_json(Path('json/verification/SimpleNonCyclicTree.json')))
    complex_tree = Tree.from_json(read_json(Path('json/verification/SimpleDefendTactic.json')))
    offensive_strategy_tree = Tree.from_json(read_json(Path('json/verification/OffensiveStrategy.json')))
    keeper_strategy_tree = Tree.from_json(read_json(Path('json/jsons/strategies/KeeperStrategy.json')))

    collection: Dict[str, Dict[str, Tree]] = {
        "roles": {"Assister.json": assister_role, "InvalidCompositesTree.json": simple_invalid_composites_tree,
                  "RoleRoleTree.json": rr_tree},
        "strategies": {"AttackStrategy.json": attack_strategy, "OffensiveStrategy.json": offensive_strategy_tree,
                       "KeeperStrategy.json": keeper_strategy_tree,
                       "StrategyStrategyRole.json": ssr_tree},
        "tactics": {"Attactic.json": attactic_tactic, "SimpleDefendTactic.json": complex_tree,
                    "InvalidRoleInheritanceTree1": simple_invalid_role_inheritance_tree_1,
                    "TacticTacticRole.json": ttr_tree}
    }

    def test_simple_tree_with_cycle(self):
        tree = self.simple_cyclic_tree
        assert 1 is len(Verification.contains_cycles(tree, {}))

    def test_simple_valid_tree(self):
        collection = Collection(self.collection)
        tree = self.simple_non_cyclic_tree
        assert 0 is len(collection.verify_tree(tree))

    def test_simple_unconnected_tree(self):
        tree = self.simple_unconnected_tree
        assert 1 is len(Verification.has_unconnected_nodes(tree))

    def test_invalid_role_inheritance_tree_1(self):
        collection = Collection(self.collection)
        tree = self.simple_invalid_role_inheritance_tree_1
        assert 0 is not len(collection.verify_tree(tree))

    def test_invalid_role_inheritance_tree_2(self):
        collection = Collection(self.collection)
        tree = self.simple_invalid_role_inheritance_tree_2
        assert 0 is not len(collection.verify_tree(tree))

    def test_invalid_composites_tree(self):
        collection = Collection(self.collection)
        tree = self.simple_invalid_composites_tree
        assert 0 is not len(collection.verify_tree(tree, "roles"))

    def test_invalid_decorator_tree(self):
        collection = Collection(self.collection)
        tree = self.simple_invalid_decorator_tree
        assert 0 is not len(collection.verify_tree(tree, "roles"))

    def test_complex_tree(self):
        collection = Collection(self.collection)
        tree = self.complex_tree
        result = collection.get_category_from_node(tree.root)
        assert "tactics" == result
        assert 0 is len(collection.verify_tree(tree, "tactics"))

    def test_offensive_strategy(self):
        collection = Collection(self.collection)
        tree = self.offensive_strategy_tree
        assert 0 is len(collection.verify_tree(tree, "strategies"))

    def test_incorrect_root_nodes_by_writing(self):
        collection = Collection(self.collection)
        tree1 = self.simple_invalid_root_node_tree1
        tree2 = self.simple_invalid_root_node_tree2
        assert len(collection.write_tree(tree1, Path('json/verification/InvalidRootNodeTree1.json'), True)) != 0
        assert len(collection.write_tree(tree2, Path('json/verification/InvalidRootNodeTree2.json'), True)) != 0

    def test_ssr_tree(self):
        collection = Collection(self.collection)
        tree = self.ssr_tree
        assert 1 is len(collection.verify_tree(tree, "strategies"))

    def test_ttr_tree(self):
        collection = Collection(self.collection)
        tree = self.ttr_tree
        assert 1 is len(collection.verify_tree(tree, "tactics"))

    def test_rr_tree(self):
        collection = Collection(self.collection)
        tree = self.rr_tree
        assert 1 is len(collection.verify_tree(tree, "roles"))

    def test_walk_tree(self):
        tree = self.simple_non_cyclic_tree
        assert 3 == len(Verification.walk_tree(tree, tree.nodes.get(tree.root)))
        tree.nodes.get(tree.root).add_child('abcdeffg')
        assert 3 == len(Verification.walk_tree(tree, tree.nodes.get(tree.root)))
        tree.nodes.get(tree.root).add_child(tree.root)
        assert 3 == len(Verification.walk_tree(tree, tree.nodes.get(tree.root)))


class TestNodeTypes:
    def test_from_csv(self):
        node_types = NodeTypes.from_csv(Settings.default_node_types_folder())
        assert '.hiddenfile.csv' not in node_types.node_types.keys()
        assert 'filewithotherextension.abc' not in node_types.node_types.keys()
        assert 'composites' in node_types.node_types.keys()
        assert 'conditions' in node_types.node_types.keys()
        assert 'decorators' in node_types.node_types.keys()
        assert 'other' in node_types.node_types.keys()
        assert 'skills' in node_types.node_types.keys()

    def test_from_csv_custom_path(self, tmpdir):
        node_types = NodeTypes.from_csv()
        node_types.write(tmpdir)
        node_types_custom = NodeTypes.from_csv(tmpdir)
        assert node_types == node_types_custom

    def test_write_default_path(self, tmpdir):
        # case where path is not set and not called
        node_types = NodeTypes.from_csv()
        def_path = Settings.default_node_types_folder()
        Settings.alter_default_node_types_folder(tmpdir)
        # test if writing does not return in an error
        node_types.write()
        read = NodeTypes.from_csv(tmpdir)
        Settings.alter_default_node_types_folder(def_path)
        assert node_types == read

    def test_write_default_path2(self, tmpdir):
        # case where the path has been set, but not called in self.write()
        node_types = NodeTypes.from_csv()
        node_types.path = tmpdir
        # test if writing does not return in an error
        node_types.write()
        read = NodeTypes.from_csv(tmpdir)
        assert node_types == read

    # noinspection PyTypeChecker
    def test_node_type_validity(self):
        with pytest.raises(InvalidNodeTypeException):
            NodeTypes.check_node_type_validity([])
        with pytest.raises(InvalidNodeTypeException):
            NodeTypes.check_node_type_validity([True])
        assert True is NodeTypes.check_node_type_validity(['a'])

    def test_create_node_from_type_exists(self):
        node_from_node_type = NodeTypes.create_node_from_node_type(["Sequence", "a", "b"])
        assert "Sequence" == node_from_node_type.title
        assert "a" in node_from_node_type.attributes.get("properties").keys()
        assert "b" in node_from_node_type.attributes.get("properties").keys()

    def test_add_node_type(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # check if a new category gets created if it does not exist
        node_types.add_node_type("test", "test_node")
        assert 'test'in node_types.node_types.keys()
        assert 'test_node' in node_types.node_types.get('test')[0]
        # check a node type with attributes
        node_types.add_node_type("test1", "test_node1", ["a"])
        assert 'test_node1' in node_types.node_types.get("test1")[0]
        assert 2 == len(node_types.node_types.get('test1')[0])
        # add one to an existing category
        node_types.add_node_type('test', 'test_node2')
        assert 2 == len(node_types.node_types.get('test'))

    def test_remove_node_type(self, tmpdir):
        node_types = NodeTypes.from_csv()
        node_types.add_node_type("test", "test")
        node_types.remove_node_type("test", ["test"])
        assert 0 == len(node_types.node_types.get('test'))
        # remove a nde from a category that does not exist
        node_types.remove_node_type("abcdefg", ["sequence"])
        assert "abcdefg" not in node_types.node_types.keys()
        # remove a node that does not exist
        node_types.add_category("abcdefg")
        assert 0 == len(node_types.node_types.get("abcdefg"))
        node_types.remove_node_type("abcdefg", ["sequence"])
        assert 0 == len(node_types.node_types.get("abcdefg"))

    def test_update_node_type(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # update a node type where the category does not exist
        node_types.update_node_type("test", "test", ['test', "a"])
        assert 'test' not in node_types.node_types.keys()
        # update a node type that does not exist
        node_types.add_category('test')
        node_types.update_node_type("test", "test", ['test', "a"])
        assert 'test' in node_types.node_types.keys()
        assert 0 == len(node_types.node_types.get('test'))
        # update a node type that exists
        node_types.add_node_type('test', 'test')
        node_types.update_node_type("test", ["test"], ['test', "a"])
        assert 'test' in node_types.node_types.keys()
        assert 1 == len(node_types.node_types.get('test'))
        assert ["test", "a"] == node_types.node_types.get('test')[0]

    def test_add_category(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # add a new category that already exists
        assert 'conditions' in node_types.node_types.keys()
        conditions = node_types.node_types.get('conditions')
        node_types.add_category('conditions')
        assert 'conditions' in node_types.node_types
        assert conditions == node_types.node_types.get('conditions')
        # test creating a new category
        assert 'test' not in node_types.node_types
        node_types.add_category("test")
        assert 'test' in node_types.node_types

    def test_remove_category(self, tmpdir):
        node_types = NodeTypes.from_csv()
        # test removing existing category
        assert 'conditions' in node_types.node_types
        node_types.remove_category("conditions")
        assert 'conditions' not in node_types.node_types
        # test removing a non existing node_type category
        assert 'test' not in node_types.node_types
        node_types.remove_category("conditions")
        assert 'test' not in node_types.node_types

    def test_get_node_type_by_name(self):
        node_types = NodeTypes.from_csv()
        # assert that the node_type test does not exist
        for category, types in node_types.node_types.items():
            for node_type in types:
                assert node_type[0] != "test"
        assert [] == node_types.get_node_type_by_name('test')
        # check for a existing node
        assert [('composites', ["Sequence"])] == node_types.get_node_type_by_name('Sequence')
        assert [('conditions', ["HasBall"]), ("conditions", ["HasBall"])] == node_types.get_node_type_by_name("HasBall")

    def test_get_node_type_by_node(self):
        node_types = NodeTypes.from_csv()
        # assert that the node_type test does not exist
        for category, types in node_types.node_types.items():
            for node_type in types:
                assert node_type[0] != "test"
        assert [] == node_types.get_node_type_by_node(Node("test", "a"))
        # check for a existing node
        assert [('composites', ["Sequence"])] == node_types.get_node_type_by_node(Node('Sequence', 'a'))

    def test_str(self):
        node_types = NodeTypes.from_csv()
        assert str(node_types.node_types) == str(node_types)
        assert repr(node_types) == str(node_types)

    def test_disconnected_node_init(self):
        DisconnectedNode(Node('abcd'))
        DisconnectedNode()
