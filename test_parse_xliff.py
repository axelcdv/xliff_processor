# coding=utf-8
__author__ = 'axelcdv'
import pytest
from parse_xliff import *


@pytest.fixture()
def source_line():
    return '\t<source>Label</source>'

@pytest.fixture()
def multi_source_line():
    return ['\t<source>Label', 'Hello</source>']

def test_is_open_tag(source_line):
    assert TagParser(tag='source').is_open_tag(source_line)

def test_is_close_tag(source_line):
    assert TagParser(tag='source').is_close_tag(source_line)

def test_parse_line(source_line):
    parser = TagParser(tag='source')
    result = parser.parse_line(source_line)
    assert parser.content == ['Label']
    assert result
    assert not parser.open

def test_parse_multi_line(multi_source_line):
    parser = TagParser(tag='source')
    assert not parser.parse_line(multi_source_line[0])
    assert parser.parse_line(multi_source_line[1])
    assert parser.content == ['Label', 'Hello']


def parse_multi_note():
    lines = [
        '<note>Account: advanced settings',
        'advanced settings title</note>',
    ]
    parser = TagParser(tag='note')
    assert not parser.parse_line(lines[0])
    assert parser.parse_line(lines[1])
    assert parser.content == ['Account: advanced settings', 'advanced settings title']


@pytest.fixture()
def trans_unit():
    return [
        '\t<trans-unit id="MyUnit">',
        '\t\t<source>Label</source>',
        '\t\t<target>Mon label</target>',
        '\t\t<note>Just a label</note>',
        '\t</trans-unit>'
    ]

def test_parse_trans_unit(trans_unit):
    parser = TransUnitParser()
    for line in trans_unit:
        parser.parse_line(line)

    assert parser.source_tag.content == ['Label']
    assert parser.target_tag.content == ['Mon label']
    assert parser.note_tag.content == ['Just a label']

    assert not parser.open


@pytest.fixture()
def file_lines():
    return [
        '<file original="MyProject/en.lproj/Localizable.strings" datatype="plaintext" xml:space="preserve" source-language="en" target-language="en">',
        '<header>',
        '<tool tool-id="lokalise.co" tool-name="Lokalise"/>',
        '</header>',
        '<body>',

        '<trans-unit id="--">',
        '<source>--</source>',
        '<target>Retrieving temperature</target>',
        '<note>Default title</note>',
        '</trans-unit>',

        '<trans-unit id="Advanced settings">',
        '<source>Advanced settings</source>',
        '<target>Advanced settings</target>',
        '<note>Account: advanced settings',
        'Settings view title</note>',
        '</trans-unit>',

        '<trans-unit id="CSV Help text">',
        '<source>CSV Help text</source>',
        '<target>Download all the measurements made by your thermostat in a .CSV file. Enter the start and end date of your desired period. You will receive the file by email.</target>',
        '<note>CSV export help text</note>',
        '</trans-unit>',

        '</file>'
    ]

def test_open_file(file_lines):
    parser = FileTagParser()
    assert parser.is_open_tag(file_lines[0])
    assert parser.is_close_tag(file_lines[-1])

def test_parse_file(file_lines):
    parser = FileTagParser()
    parser.parse_open_tag(file_lines[0])
    for line in file_lines[1:]:
        parser.parse_line(line)

    assert len(parser.units) == 3
    assert parser.original == 'MyProject/en.lproj/Localizable.strings'
    assert parser.source_language == 'en'
    assert parser.target_language == 'en'
    assert parser.target_filename== 'Localizable.strings'


