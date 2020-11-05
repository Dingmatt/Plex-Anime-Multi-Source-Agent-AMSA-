# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

__all__ = [
    'HTML5TreeBuilder',
    ]

import warnings
import re
from bs4.builder import (
    PERMISSIVE,
    HTML,
    HTML_5,
    HTMLTreeBuilder,
    )
from bs4.element import (
    NamespacedAttribute,
    whitespace_re,
)
import html5lib
from html5lib.constants import (
    namespaces,
    prefixes,
    )
from bs4.element import (
    Comment,
    Doctype,
    NavigableString,
    Tag,
    )

try:
    # Pre-0.99999999
    from html5lib.treebuilders import _base as treebuilder_base
    new_html5lib = False
except ImportError, e:
    # 0.99999999 and up
    from html5lib.treebuilders import base as treebuilder_base
    new_html5lib = True

class HTML5TreeBuilder(HTMLTreeBuilder):
    """Use html5lib to build a tree."""

    NAME = "html5lib"

    features = [NAME, PERMISSIVE, HTML_5, HTML]

    def prepare_markup(self, markup, user_specified_encoding,
                       document_declared_encoding=None, exclude_encodings=None):
        """
        Prepare markup document.

        Args:
            self: (todo): write your description
            markup: (todo): write your description
            user_specified_encoding: (todo): write your description
            document_declared_encoding: (todo): write your description
            exclude_encodings: (bool): write your description
        """
        # Store the user-specified encoding for use later on.
        self.user_specified_encoding = user_specified_encoding

        # document_declared_encoding and exclude_encodings aren't used
        # ATM because the html5lib TreeBuilder doesn't use
        # UnicodeDammit.
        if exclude_encodings:
            warnings.warn("You provided a value for exclude_encoding, but the html5lib tree builder doesn't support exclude_encoding.")
        yield (markup, None, None, False)

    # These methods are defined by Beautiful Soup.
    def feed(self, markup):
        """
        Parse the given html document.

        Args:
            self: (todo): write your description
            markup: (todo): write your description
        """
        if self.soup.parse_only is not None:
            warnings.warn("You provided a value for parse_only, but the html5lib tree builder doesn't support parse_only. The entire document will be parsed.")
        parser = html5lib.HTMLParser(tree=self.create_treebuilder)

        extra_kwargs = dict()
        if not isinstance(markup, unicode):
            if new_html5lib:
                extra_kwargs['override_encoding'] = self.user_specified_encoding
            else:
                extra_kwargs['encoding'] = self.user_specified_encoding
        doc = parser.parse(markup, **extra_kwargs)

        # Set the character encoding detected by the tokenizer.
        if isinstance(markup, unicode):
            # We need to special-case this because html5lib sets
            # charEncoding to UTF-8 if it gets Unicode input.
            doc.original_encoding = None
        else:
            original_encoding = parser.tokenizer.stream.charEncoding[0]
            if not isinstance(original_encoding, basestring):
                # In 0.99999999 and up, the encoding is an html5lib
                # Encoding object. We want to use a string for compatibility
                # with other tree builders.
                original_encoding = original_encoding.name
            doc.original_encoding = original_encoding

    def create_treebuilder(self, namespaceHTMLElements):
        """
        Create a new treebuilderbuilderbuilder element

        Args:
            self: (todo): write your description
            namespaceHTMLElements: (str): write your description
        """
        self.underlying_builder = TreeBuilderForHtml5lib(
            namespaceHTMLElements, self.soup)
        return self.underlying_builder

    def test_fragment_to_document(self, fragment):
        """See `TreeBuilder`."""
        return u'<html><head></head><body>%s</body></html>' % fragment


class TreeBuilderForHtml5lib(treebuilder_base.TreeBuilder):

    def __init__(self, namespaceHTMLElements, soup=None):
        """
        Initialize the element

        Args:
            self: (todo): write your description
            namespaceHTMLElements: (str): write your description
            soup: (str): write your description
        """
        if soup:
            self.soup = soup
        else:
            from bs4 import BeautifulSoup
            self.soup = BeautifulSoup("", "html.parser")
        super(TreeBuilderForHtml5lib, self).__init__(namespaceHTMLElements)

    def documentClass(self):
        """
        Return the html element

        Args:
            self: (todo): write your description
        """
        self.soup.reset()
        return Element(self.soup, self.soup, None)

    def insertDoctype(self, token):
        """
        Inserts a new public type.

        Args:
            self: (todo): write your description
            token: (str): write your description
        """
        name = token["name"]
        publicId = token["publicId"]
        systemId = token["systemId"]

        doctype = Doctype.for_name_and_ids(name, publicId, systemId)
        self.soup.object_was_parsed(doctype)

    def elementClass(self, name, namespace):
        """
        Create a new element

        Args:
            self: (todo): write your description
            name: (str): write your description
            namespace: (str): write your description
        """
        tag = self.soup.new_tag(name, namespace)
        return Element(tag, self.soup, namespace)

    def commentClass(self, data):
        """
        Parse a comment

        Args:
            self: (todo): write your description
            data: (array): write your description
        """
        return TextNode(Comment(data), self.soup)

    def fragmentClass(self):
        """
        Return a fragment element

        Args:
            self: (todo): write your description
        """
        from bs4 import BeautifulSoup
        self.soup = BeautifulSoup("", "html.parser")
        self.soup.name = "[document_fragment]"
        return Element(self.soup, self.soup, None)

    def appendChild(self, node):
        """
        Add a new child to this element.

        Args:
            self: (todo): write your description
            node: (todo): write your description
        """
        # XXX This code is not covered by the BS4 tests.
        self.soup.append(node.element)

    def getDocument(self):
        """
        Returns the html document

        Args:
            self: (todo): write your description
        """
        return self.soup

    def getFragment(self):
        """
        Return the xmlbuilder of this node

        Args:
            self: (todo): write your description
        """
        return treebuilder_base.TreeBuilder.getFragment(self).element

    def testSerializer(self, element):
        """
        Test for the element.

        Args:
            self: (todo): write your description
            element: (todo): write your description
        """
        from bs4 import BeautifulSoup
        rv = []
        doctype_re = re.compile(r'^(.*?)(?: PUBLIC "(.*?)"(?: "(.*?)")?| SYSTEM "(.*?)")?$')

        def serializeElement(element, indent=0):
            """
            Serialize the element as xml.

            Args:
                element: (todo): write your description
                indent: (int): write your description
            """
            if isinstance(element, BeautifulSoup):
                pass
            if isinstance(element, Doctype):
                m = doctype_re.match(element)
                if m:
                    name = m.group(1)
                    if m.lastindex > 1:
                        publicId = m.group(2) or ""
                        systemId = m.group(3) or m.group(4) or ""
                        rv.append("""|%s<!DOCTYPE %s "%s" "%s">""" %
                                  (' ' * indent, name, publicId, systemId))
                    else:
                        rv.append("|%s<!DOCTYPE %s>" % (' ' * indent, name))
                else:
                    rv.append("|%s<!DOCTYPE >" % (' ' * indent,))
            elif isinstance(element, Comment):
                rv.append("|%s<!-- %s -->" % (' ' * indent, element))
            elif isinstance(element, NavigableString):
                rv.append("|%s\"%s\"" % (' ' * indent, element))
            else:
                if element.namespace:
                    name = "%s %s" % (prefixes[element.namespace],
                                      element.name)
                else:
                    name = element.name
                rv.append("|%s<%s>" % (' ' * indent, name))
                if element.attrs:
                    attributes = []
                    for name, value in element.attrs.items():
                        if isinstance(name, NamespacedAttribute):
                            name = "%s %s" % (prefixes[name.namespace], name.name)
                        if isinstance(value, list):
                            value = " ".join(value)
                        attributes.append((name, value))

                    for name, value in sorted(attributes):
                        rv.append('|%s%s="%s"' % (' ' * (indent + 2), name, value))
                indent += 2
                for child in element.children:
                    serializeElement(child, indent)
        serializeElement(element, 0)

        return "\n".join(rv)

class AttrList(object):
    def __init__(self, element):
        """
        Initialize an element.

        Args:
            self: (todo): write your description
            element: (todo): write your description
        """
        self.element = element
        self.attrs = dict(self.element.attrs)
    def __iter__(self):
        """
        Return an iterator over all the attributes.

        Args:
            self: (todo): write your description
        """
        return list(self.attrs.items()).__iter__()
    def __setitem__(self, name, value):
        """
        Sets a list of an element.

        Args:
            self: (todo): write your description
            name: (str): write your description
            value: (str): write your description
        """
        # If this attribute is a multi-valued attribute for this element,
        # turn its value into a list.
        list_attr = HTML5TreeBuilder.cdata_list_attributes
        if (name in list_attr['*']
            or (self.element.name in list_attr
                and name in list_attr[self.element.name])):
            # A node that is being cloned may have already undergone
            # this procedure.
            if not isinstance(value, list):
                value = whitespace_re.split(value)
        self.element[name] = value
    def items(self):
        """
        Returns an iterable of items.

        Args:
            self: (todo): write your description
        """
        return list(self.attrs.items())
    def keys(self):
        """
        Returns the list of all the keys.

        Args:
            self: (todo): write your description
        """
        return list(self.attrs.keys())
    def __len__(self):
        """
        Returns the length of the field.

        Args:
            self: (todo): write your description
        """
        return len(self.attrs)
    def __getitem__(self, name):
        """
        Return the value from the given name.

        Args:
            self: (todo): write your description
            name: (str): write your description
        """
        return self.attrs[name]
    def __contains__(self, name):
        """
        Returns true if the given attribute exists.

        Args:
            self: (todo): write your description
            name: (str): write your description
        """
        return name in list(self.attrs.keys())


class Element(treebuilder_base.Node):
    def __init__(self, element, soup, namespace):
        """
        Initialize the element.

        Args:
            self: (todo): write your description
            element: (todo): write your description
            soup: (str): write your description
            namespace: (str): write your description
        """
        treebuilder_base.Node.__init__(self, element.name)
        self.element = element
        self.soup = soup
        self.namespace = namespace

    def appendChild(self, node):
        """
        Append child todo.

        Args:
            self: (todo): write your description
            node: (todo): write your description
        """
        string_child = child = None
        if isinstance(node, basestring):
            # Some other piece of code decided to pass in a string
            # instead of creating a TextElement object to contain the
            # string.
            string_child = child = node
        elif isinstance(node, Tag):
            # Some other piece of code decided to pass in a Tag
            # instead of creating an Element object to contain the
            # Tag.
            child = node
        elif node.element.__class__ == NavigableString:
            string_child = child = node.element
            node.parent = self
        else:
            child = node.element
            node.parent = self

        if not isinstance(child, basestring) and child.parent is not None:
            node.element.extract()

        if (string_child and self.element.contents
            and self.element.contents[-1].__class__ == NavigableString):
            # We are appending a string onto another string.
            # TODO This has O(n^2) performance, for input like
            # "a</a>a</a>a</a>..."
            old_element = self.element.contents[-1]
            new_element = self.soup.new_string(old_element + string_child)
            old_element.replace_with(new_element)
            self.soup._most_recent_element = new_element
        else:
            if isinstance(node, basestring):
                # Create a brand new NavigableString from this string.
                child = self.soup.new_string(node)

            # Tell Beautiful Soup to act as if it parsed this element
            # immediately after the parent's last descendant. (Or
            # immediately after the parent, if it has no children.)
            if self.element.contents:
                most_recent_element = self.element._last_descendant(False)
            elif self.element.next_element is not None:
                # Something from further ahead in the parse tree is
                # being inserted into this earlier element. This is
                # very annoying because it means an expensive search
                # for the last element in the tree.
                most_recent_element = self.soup._last_descendant()
            else:
                most_recent_element = self.element

            self.soup.object_was_parsed(
                child, parent=self.element,
                most_recent_element=most_recent_element)

    def getAttributes(self):
        """
        : return : the requested attribute.

        Args:
            self: (todo): write your description
        """
        if isinstance(self.element, Comment):
            return {}
        return AttrList(self.element)

    def setAttributes(self, attributes):
        """
        Set the attributes todo attributes.

        Args:
            self: (todo): write your description
            attributes: (dict): write your description
        """

        if attributes is not None and len(attributes) > 0:

            converted_attributes = []
            for name, value in list(attributes.items()):
                if isinstance(name, tuple):
                    new_name = NamespacedAttribute(*name)
                    del attributes[name]
                    attributes[new_name] = value

            self.soup.builder._replace_cdata_list_attribute_values(
                self.name, attributes)
            for name, value in attributes.items():
                self.element[name] = value

            # The attributes may contain variables that need substitution.
            # Call set_up_substitutions manually.
            #
            # The Tag constructor called this method when the Tag was created,
            # but we just set/changed the attributes, so call it again.
            self.soup.builder.set_up_substitutions(self.element)
    attributes = property(getAttributes, setAttributes)

    def insertText(self, data, insertBefore=None):
        """
        Insert text into the data.

        Args:
            self: (todo): write your description
            data: (todo): write your description
            insertBefore: (todo): write your description
        """
        text = TextNode(self.soup.new_string(data), self.soup)
        if insertBefore:
            self.insertBefore(text, insertBefore)
        else:
            self.appendChild(text)

    def insertBefore(self, node, refNode):
        """
        Inserts the child node * node.

        Args:
            self: (todo): write your description
            node: (todo): write your description
            refNode: (todo): write your description
        """
        index = self.element.index(refNode.element)
        if (node.element.__class__ == NavigableString and self.element.contents
            and self.element.contents[index-1].__class__ == NavigableString):
            # (See comments in appendChild)
            old_node = self.element.contents[index-1]
            new_str = self.soup.new_string(old_node + node.element)
            old_node.replace_with(new_str)
        else:
            self.element.insert(index, node.element)
            node.parent = self

    def removeChild(self, node):
        """
        Removes the given node from the node.

        Args:
            self: (todo): write your description
            node: (todo): write your description
        """
        node.element.extract()

    def reparentChildren(self, new_parent):
        """Move all of this tag's children into another tag."""
        # print "MOVE", self.element.contents
        # print "FROM", self.element
        # print "TO", new_parent.element

        element = self.element
        new_parent_element = new_parent.element
        # Determine what this tag's next_element will be once all the children
        # are removed.
        final_next_element = element.next_sibling

        new_parents_last_descendant = new_parent_element._last_descendant(False, False)
        if len(new_parent_element.contents) > 0:
            # The new parent already contains children. We will be
            # appending this tag's children to the end.
            new_parents_last_child = new_parent_element.contents[-1]
            new_parents_last_descendant_next_element = new_parents_last_descendant.next_element
        else:
            # The new parent contains no children.
            new_parents_last_child = None
            new_parents_last_descendant_next_element = new_parent_element.next_element

        to_append = element.contents
        if len(to_append) > 0:
            # Set the first child's previous_element and previous_sibling
            # to elements within the new parent
            first_child = to_append[0]
            if new_parents_last_descendant:
                first_child.previous_element = new_parents_last_descendant
            else:
                first_child.previous_element = new_parent_element
            first_child.previous_sibling = new_parents_last_child
            if new_parents_last_descendant:
                new_parents_last_descendant.next_element = first_child
            else:
                new_parent_element.next_element = first_child
            if new_parents_last_child:
                new_parents_last_child.next_sibling = first_child

            # Find the very last element being moved. It is now the
            # parent's last descendant. It has no .next_sibling and
            # its .next_element is whatever the previous last
            # descendant had.
            last_childs_last_descendant = to_append[-1]._last_descendant(False, True)

            last_childs_last_descendant.next_element = new_parents_last_descendant_next_element
            if new_parents_last_descendant_next_element:
                # TODO: This code has no test coverage and I'm not sure
                # how to get html5lib to go through this path, but it's
                # just the other side of the previous line.
                new_parents_last_descendant_next_element.previous_element = last_childs_last_descendant
            last_childs_last_descendant.next_sibling = None

        for child in to_append:
            child.parent = new_parent_element
            new_parent_element.contents.append(child)

        # Now that this element has no children, change its .next_element.
        element.contents = []
        element.next_element = final_next_element

        # print "DONE WITH MOVE"
        # print "FROM", self.element
        # print "TO", new_parent_element

    def cloneNode(self):
        """
        Return a copy of - wise.

        Args:
            self: (todo): write your description
        """
        tag = self.soup.new_tag(self.element.name, self.namespace)
        node = Element(tag, self.soup, self.namespace)
        for key,value in self.attributes:
            node.attributes[key] = value
        return node

    def hasContent(self):
        """
        The content :

        Args:
            self: (todo): write your description
        """
        return self.element.contents

    def getNameTuple(self):
        """
        Return the name of the name.

        Args:
            self: (todo): write your description
        """
        if self.namespace == None:
            return namespaces["html"], self.name
        else:
            return self.namespace, self.name

    nameTuple = property(getNameTuple)

class TextNode(Element):
    def __init__(self, element, soup):
        """
        Initialize the element.

        Args:
            self: (todo): write your description
            element: (todo): write your description
            soup: (str): write your description
        """
        treebuilder_base.Node.__init__(self, None)
        self.element = element
        self.soup = soup

    def cloneNode(self):
        """
        Create a new node.

        Args:
            self: (todo): write your description
        """
        raise NotImplementedError
