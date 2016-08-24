# coding=utf-8
__author__ = 'axelcdv'

import argparse
import re


class XliffParser(object):
    in_filename = None
    out_filename = None

    file_parser = None

    def __init__(self, in_filename, out_filename):
        self.in_filename = in_filename
        self.out_filename = out_filename
        self.file_parser = FileTagParser()

    def parse_file(self):
        with open(self.in_filename) as file:
            for line in file:
                self.parse_line(line)

    def parse_line(self, line):
        if self.file_parser.open:
            if self.file_parser.parse_line(line=line):
                # Finished file section, write it
                print 'Writing file %s' % self.file_parser
                self.file_parser.write(self.out_filename)
                self.file_parser = FileTagParser()
        elif self.file_parser.is_open_tag(line):
            self.file_parser.open = True
            self.file_parser.parse_open_tag(line)
            # print 'Open %s' % self.file_parser
        else:
            pass


class TagParser(object):
    tag = None

    open = False

    content = None

    def __init__(self, tag=None):
        if tag:
            self.tag = tag
        self.content = []

    def __str__(self):
        return '{tag} - {content}'.format(tag=self.tag, content=self.content)

    def parse_line(self, line):
        """
        Return True when this parser has finished parsing its segment
        :param line:
        :rtype: bool
        """
        content_match = re.match('^\s*(?:<{tag}>)?(.*?)(?:</{tag}>)?\s*$'.format(
            tag=self.tag
        ), line)
        self.content.append(content_match.groups()[0])

        self.open = not bool(self.is_close_tag(line))
        return not self.open

    def parse_open_tag(self, line):
        raise NotImplementedError

    def is_open_tag(self, line):
        return re.match('^\s*<{tag}.*>.*$'.format(tag=self.tag), line)

    def is_close_tag(self, line):
        return re.match('^.*</{tag}>$'.format(tag=self.tag), line)


class TransUnitParser(TagParser):
    tag = 'trans-unit'

    unit_id = None

    expected_tag = 'source'  # target, note

    source_tag = None

    target_tag = None

    note_tag = None

    def __init__(self, tag=None):
        super(TransUnitParser, self).__init__('trans-unit')
        self.source_tag = TagParser(tag='source')

        self.target_tag = TagParser(tag='target')

        self.note_tag = TagParser(tag='note')

    def __str__(self):
        return '{id} - {source} - {target} - {note}'.format(
            id=self.unit_id, source=self.source_tag.content,
            target=self.target_tag.content, note=self.note_tag.content)

    def parse_open_tag(self, line):
        match = re.match('.*<trans-unit id="(.*?)">', line)
        self.unit_id = match.groups()[0]
        self.open = True

    def parse_line(self, line):
        # print 'parsing line %s, expected: %s' % (line, self.expected_tag)
        if self.expected_tag == 'source':
            if self.source_tag.open or self.source_tag.is_open_tag(line):
                closed = self.source_tag.parse_line(line)
                # print 'Parsed source line'

                if closed:
                    # print 'Closed source: %s' % self.source_tag.content
                    self.expected_tag = 'target'
        elif self.expected_tag == 'target':
            if self.target_tag.open or self.target_tag.is_open_tag(line):
                closed = self.target_tag.parse_line(line)

                if closed:
                    # print 'Closed target: %s' % self.target_tag.content
                    self.expected_tag = 'note'
        elif self.expected_tag == 'note':
            if self.note_tag.open or self.note_tag.is_open_tag(line):
                closed = self.note_tag.parse_line(line)

                if closed:
                    # print 'Closed note: %s' % self.note_tag.content
                    self.expected_tag = ''
        elif self.is_close_tag(line):
            self.open = False
            # print 'Close unit %s' % self.unit_id
            return True

        return False

    @property
    def parsed_content(self):
        return [self.source_tag.content, self.target_tag.content, self.note_tag.content]

    def write(self, out):
        out.writelines([self.header, '\n'])
        out.writelines(['"{source}" = "{target}";'.format(
            source = self.unit_id,
            target = '\n'.join(self.target_tag.content).replace('"', '\\"')
        ), '\n'])

    @property
    def header(self):
        return '/* {} */'.format('\n'.join(self.note_tag.content))

class FileTagParser(TagParser):
    tag = 'file'

    original = None
    source_language = None
    target_language = None

    trans_unit = None
    units = None

    def __init__(self, tag=None):
        super(FileTagParser, self).__init__(tag=tag)
        self.trans_unit = TransUnitParser()
        self.units = []

    def __str__(self):
        return '{tag} - {original} - {source} - {target} (open: {open})'.format(
            tag=self.tag,
            original = self.original,
            source = self.source_language,
            target = self.target_language,
            open = self.open
        )

    def parse_open_tag(self, line):
        match = re.match('^\s*<file original="(.*?)" datatype.* '
                         'source-language="(.*?)" target-language="(.*?)">\s*$', line)
        self.original, self.source_language, self.target_language = match.groups()[:3]


    def parse_line(self, line):
        if self.is_close_tag(line):
            self.open = False
            # print 'Close %s' % self
            return True
        elif self.trans_unit.open:
            if self.trans_unit.parse_line(line):
                # print 'Close trans unit %s' % self.trans_unit
                self.units.append(self.trans_unit)
                self.trans_unit = TransUnitParser()
        elif self.trans_unit.is_open_tag(line):
            self.trans_unit.parse_open_tag(line)
            # print 'Open trans unit %s' % self.trans_unit

        return False

    def write(self, base):
        with open(base + self.target_filename, 'w') as out:
            out.write(self.header)
            out.write('\n')
            for unit in self.units:
                unit.write(out)
                out.write('\n')

            out.write('\n')

    @property
    def target_filename(self):
        path = self.original.replace(
            '%s.lproj' % self.source_language, '%s.lproj' % self.target_language
        ).replace('Base.lproj', '%s.lproj' % self.target_language)
        path = path.split('/')
        path[-1] = path[-1].split('.')[0]
        return '%s.strings' % '/'.join(path)

    @property
    def header(self):
        return '/* {original} -> {target} */'.format(
            original=self.original, target=self.target_language)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output')
    parser.add_argument('-t', '--test', action='store_true')
    args = parser.parse_args()

    processor = XliffParser(args.input, args.output)
    processor.parse_file()

